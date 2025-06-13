import asyncio
import os
from datetime import datetime
import logging
from typing import Dict, List, Optional
from dotenv import load_dotenv
import pandas as pd

from ..exchange.bybit_client import HumanizedBybitClient
from ..strategies.advanced_strategies import MultiIndicatorStrategy, SafeScalpingStrategy
from ..strategies.simple_momentum import SimpleMomentumStrategy
from ..notifications.telegram_notifier import TelegramNotifier, NotificationMessage
from .database import SessionLocal
from .models import Trade, Signal, TradingPair, BotState, TradeStatus, OrderSide

load_dotenv()
logger = logging.getLogger(__name__)

class BotManager:
    """Единый менеджер для управления торговым ботом"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BotManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.client = HumanizedBybitClient()
            self.notifier = TelegramNotifier()
            self.strategies = {
                'multi_indicator': MultiIndicatorStrategy(),
                'scalping': SafeScalpingStrategy(),
                'momentum': SimpleMomentumStrategy()
            }
            self.active_pairs = []
            self.positions = {}  # symbol -> Trade
            self.is_running = False
            self.max_positions = int(os.getenv('MAX_POSITIONS', 3))
            self.stop_event = asyncio.Event()
            self.main_task = None
            self.initialized = True
            
            # Загружаем состояние из БД
            self._load_state()
    
    def _load_state(self):
        """Загрузка состояния бота из БД"""
        db = SessionLocal()
        try:
            # Загружаем активные позиции
            open_trades = db.query(Trade).filter(Trade.status == TradeStatus.OPEN).all()
            for trade in open_trades:
                self.positions[trade.symbol] = trade
            
            # Загружаем активные пары
            pairs = db.query(TradingPair).filter(TradingPair.is_active == True).all()
            self.active_pairs = [pair.symbol for pair in pairs]
            
            if not self.active_pairs:
                self.active_pairs = [os.getenv('TRADING_SYMBOL', 'BTCUSDT')]
            
            logger.info(f"Загружено позиций: {len(self.positions)}, активных пар: {len(self.active_pairs)}")
            
        finally:
            db.close()
    
    async def start(self):
        """Запуск бота"""
        if self.is_running:
            logger.warning("Бот уже запущен")
            return False
        
        self.is_running = True
        self.stop_event.clear()
        
        # Обновляем состояние в БД
        db = SessionLocal()
        try:
            state = db.query(BotState).first()
            if not state:
                state = BotState()
                db.add(state)
            
            state.is_running = True
            state.start_time = datetime.utcnow()
            db.commit()
        finally:
            db.close()
        
        # Отправляем уведомление
        await self.notifier.send_notification(NotificationMessage(
            title="🚀 Бот запущен",
            text=f"Торговля по парам: {', '.join(self.active_pairs)}",
            level="INFO"
        ))
        
        # Запускаем основной цикл
        self.main_task = asyncio.create_task(self._main_loop())
        logger.info("Бот успешно запущен")
        return True
    
    async def stop(self):
        """Остановка бота"""
        if not self.is_running:
            logger.warning("Бот уже остановлен")
            return False
        
        self.is_running = False
        self.stop_event.set()
        
        # Ждем завершения основного цикла
        if self.main_task:
            await self.main_task
        
        # Обновляем состояние в БД
        db = SessionLocal()
        try:
            state = db.query(BotState).first()
            if state:
                state.is_running = False
                state.stop_time = datetime.utcnow()
                db.commit()
        finally:
            db.close()
        
        # Отправляем уведомление
        await self.notifier.send_notification(NotificationMessage(
            title="🛑 Бот остановлен",
            text="Торговля приостановлена",
            level="INFO"
        ))
        
        logger.info("Бот успешно остановлен")
        return True
    
    async def _main_loop(self):
        """Основной торговый цикл"""
        logger.info("Запуск основного торгового цикла")
        
        while self.is_running:
            try:
                # Анализируем все пары
                await self._analyze_all_pairs()
                
                # Проверяем открытые позиции
                await self._check_open_positions()
                
                # Обновляем статистику
                await self._update_statistics()
                
                # Ждем следующий цикл или сигнал остановки
                try:
                    await asyncio.wait_for(
                        self.stop_event.wait(),
                        timeout=60.0  # Проверка каждую минуту
                    )
                except asyncio.TimeoutError:
                    pass
                    
            except Exception as e:
                logger.error(f"Ошибка в основном цикле: {e}")
                await self.notifier.send_notification(NotificationMessage(
                    title="⚠️ Ошибка в боте",
                    text=str(e),
                    level="ERROR"
                ))
                await asyncio.sleep(30)
    
    async def _analyze_all_pairs(self):
        """Анализ всех активных пар"""
        for symbol in self.active_pairs:
            try:
                # Пропускаем если уже есть позиция
                if symbol in self.positions:
                    continue
                
                # Проверяем лимит позиций
                if len(self.positions) >= self.max_positions:
                    break
                
                # Анализируем пару
                signal = await self._analyze_pair(symbol)
                
                if signal and signal.action != 'WAIT':
                    await self._execute_signal(symbol, signal)
                
                # Небольшая пауза между парами
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Ошибка анализа {symbol}: {e}")
    
    async def _analyze_pair(self, symbol: str) -> Optional[Signal]:
        """Анализ одной торговой пары"""
        try:
            # Получаем данные
            ohlcv = self.client.exchange.fetch_ohlcv(
                symbol,
                timeframe='5m',
                limit=200
            )
            
            df = pd.DataFrame(
                ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # Получаем настройки пары
            db = SessionLocal()
            try:
                pair_settings = db.query(TradingPair).filter(
                    TradingPair.symbol == symbol
                ).first()
                
                strategy_name = pair_settings.strategy if pair_settings else 'multi_indicator'
                strategy = self.strategies.get(strategy_name, self.strategies['multi_indicator'])
                
            finally:
                db.close()
            
            # Анализируем стратегией
            result = strategy.analyze(df)
            
            if hasattr(result, 'action') and result.action != 'WAIT':
                # Создаем сигнал
                signal = Signal(
                    symbol=symbol,
                    action=result.action,
                    confidence=result.confidence,
                    price=df['close'].iloc[-1],
                    stop_loss=result.stop_loss if hasattr(result, 'stop_loss') else None,
                    take_profit=result.take_profit if hasattr(result, 'take_profit') else None,
                    strategy=strategy_name,
                    reason=result.reason if hasattr(result, 'reason') else ''
                )
                
                # Сохраняем сигнал в БД
                db = SessionLocal()
                try:
                    db.add(signal)
                    db.commit()
                    db.refresh(signal)
                finally:
                    db.close()
                
                logger.info(f"Сигнал {signal.action} для {symbol}, уверенность: {signal.confidence:.2f}")
                return signal
                
        except Exception as e:
            logger.error(f"Ошибка анализа {symbol}: {e}")
        
        return None
    
    async def _execute_signal(self, symbol: str, signal: Signal):
        """Исполнение торгового сигнала"""
        try:
            # Получаем баланс
            balance = await self.client.fetch_balance()
            free_balance = balance.get('USDT', {}).get('free', 0)
            
            if free_balance <= 10:  # Минимум 10 USDT
                logger.warning("Недостаточно средств для открытия позиции")
                return
            
            # Получаем текущую цену
            ticker = await self.client.fetch_ticker(symbol)
            current_price = ticker['last']
            
            # Расчет размера позиции
            db = SessionLocal()
            try:
                pair_settings = db.query(TradingPair).filter(
                    TradingPair.symbol == symbol
                ).first()
                
                position_size_percent = float(os.getenv('MAX_POSITION_SIZE_PERCENT', 5))
                if pair_settings and pair_settings.max_position_size:
                    position_size_percent = min(position_size_percent, pair_settings.max_position_size)
                
            finally:
                db.close()
            
            position_value = free_balance * (position_size_percent / 100)
            amount = position_value / current_price
            
            # Исполнение ордера
            order = await self.client.create_order(
                symbol,
                signal.action.lower(),
                amount
            )
            
            if order:
                # Создаем запись о сделке
                db = SessionLocal()
                try:
                    trade = Trade(
                        symbol=symbol,
                        side=OrderSide[signal.action],
                        entry_price=current_price,
                        quantity=amount,
                        status=TradeStatus.OPEN,
                        strategy=signal.strategy,
                        stop_loss=signal.stop_loss,
                        take_profit=signal.take_profit
                    )
                    db.add(trade)
                    
                    # Обновляем сигнал
                    db_signal = db.query(Signal).filter(Signal.id == signal.id).first()
                    if db_signal:
                        db_signal.executed = True
                        db_signal.executed_at = datetime.utcnow()
                        db_signal.trade_id = trade.id
                    
                    db.commit()
                    db.refresh(trade)
                    
                    # Добавляем в активные позиции
                    self.positions[symbol] = trade
                    
                    # Отправляем уведомление
                    await self.notifier.send_trade_opened(trade)
                    
                    logger.info(f"Позиция открыта: {signal.action} {amount:.4f} {symbol} @ {current_price}")
                    
                finally:
                    db.close()
                    
        except Exception as e:
            logger.error(f"Ошибка исполнения сигнала: {e}")
    
    async def _check_open_positions(self):
        """Проверка открытых позиций"""
        for symbol, trade in list(self.positions.items()):
            try:
                ticker = await self.client.fetch_ticker(symbol)
                current_price = ticker['last']
                
                should_close = False
                reason = ""
                
                # Проверяем стоп-лосс и тейк-профит
                if trade.side == OrderSide.BUY:
                    if trade.stop_loss and current_price <= trade.stop_loss:
                        should_close = True
                        reason = "Stop Loss"
                    elif trade.take_profit and current_price >= trade.take_profit:
                        should_close = True
                        reason = "Take Profit"
                else:  # SELL
                    if trade.stop_loss and current_price >= trade.stop_loss:
                        should_close = True
                        reason = "Stop Loss"
                    elif trade.take_profit and current_price <= trade.take_profit:
                        should_close = True
                        reason = "Take Profit"
                
                # Также можем добавить trailing stop и другую логику
                
                if should_close:
                    await self._close_position(trade, current_price, reason)
                    
            except Exception as e:
                logger.error(f"Ошибка проверки позиции {symbol}: {e}")
    
    async def _close_position(self, trade: Trade, exit_price: float, reason: str):
        """Закрытие позиции"""
        try:
            # Закрываем позицию на бирже
            close_side = 'sell' if trade.side == OrderSide.BUY else 'buy'
            order = await self.client.create_order(
                trade.symbol,
                close_side,
                trade.quantity
            )
            
            if order:
                # Обновляем запись в БД
                db = SessionLocal()
                try:
                    db_trade = db.query(Trade).filter(Trade.id == trade.id).first()
                    if db_trade:
                        db_trade.exit_price = exit_price
                        db_trade.status = TradeStatus.CLOSED
                        db_trade.closed_at = datetime.utcnow()
                        db_trade.calculate_profit()
                        db.commit()
                        
                        # Удаляем из активных позиций
                        del self.positions[trade.symbol]
                        
                        # Отправляем уведомление
                        await self.notifier.send_trade_closed(db_trade)
                        
                        logger.info(
                            f"Позиция закрыта по {reason}: {trade.symbol} @ {exit_price}, "
                            f"Прибыль: ${db_trade.profit:.2f} ({db_trade.profit_percent:.2f}%)"
                        )
                        
                finally:
                    db.close()
                    
        except Exception as e:
            logger.error(f"Ошибка закрытия позиции: {e}")
    
    async def _update_statistics(self):
        """Обновление статистики бота"""
        db = SessionLocal()
        try:
            state = db.query(BotState).first()
            if not state:
                state = BotState()
                db.add(state)
            
            # Обновляем статистику
            state.total_trades = db.query(Trade).count()
            state.profitable_trades = db.query(Trade).filter(
                Trade.status == TradeStatus.CLOSED,
                Trade.profit > 0
            ).count()
            
            total_profit = db.query(Trade).filter(
                Trade.status == TradeStatus.CLOSED
            ).with_entities(Trade.profit).all()
            
            state.total_profit = sum(p[0] or 0 for p in total_profit)
            
            # Получаем текущий баланс
            balance = await self.client.fetch_balance()
            state.current_balance = balance.get('USDT', {}).get('total', 0)
            
            db.commit()
            
        finally:
            db.close()
    
    def get_status(self) -> dict:
        """Получение текущего статуса бота"""
        return {
            'is_running': self.is_running,
            'active_pairs': self.active_pairs,
            'open_positions': len(self.positions),
            'positions': {
                symbol: {
                    'side': trade.side.value,
                    'entry_price': trade.entry_price,
                    'quantity': trade.quantity,
                    'current_profit': trade.profit
                }
                for symbol, trade in self.positions.items()
            }
        }
    
    async def update_pairs(self, pairs: List[str]):
        """Обновление активных торговых пар"""
        self.active_pairs = pairs
        
        # Обновляем в БД
        db = SessionLocal()
        try:
            # Деактивируем все пары
            db.query(TradingPair).update({TradingPair.is_active: False})
            
            # Активируем выбранные
            for symbol in pairs:
                pair = db.query(TradingPair).filter(
                    TradingPair.symbol == symbol
                ).first()
                
                if pair:
                    pair.is_active = True
                else:
                    # Создаем новую пару
                    pair = TradingPair(
                        symbol=symbol,
                        is_active=True
                    )
                    db.add(pair)
            
            db.commit()
            logger.info(f"Обновлены активные пары: {pairs}")
            
        finally:
            db.close()
    
    async def manual_close_position(self, symbol: str):
        """Ручное закрытие позиции"""
        if symbol in self.positions:
            trade = self.positions[symbol]
            ticker = await self.client.fetch_ticker(symbol)
            current_price = ticker['last']
            await self._close_position(trade, current_price, "Manual Close")
            return True
        return False

# Глобальный экземпляр менеджера
bot_manager = BotManager()