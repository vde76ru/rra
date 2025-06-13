import asyncio
import os
from datetime import datetime
import logging
from typing import Dict, List
from dotenv import load_dotenv
import pandas as pd

from src.exchange.bybit_client import HumanizedBybitClient
from src.strategies.advanced_strategies import MultiIndicatorStrategy, SafeScalpingStrategy
from src.core.database import SessionLocal
from src.core.models import Trade, Signal, TradingPair
from src.notifications.telegram_notifier import TelegramNotifier, NotificationMessage

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/trading.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()

class AdvancedCryptoBot:
    """Продвинутый торговый бот с мультивалютной поддержкой"""
    
    def __init__(self):
        self.client = HumanizedBybitClient()
        self.notifier = TelegramNotifier()
        self.strategies = {
            'multi_indicator': MultiIndicatorStrategy(),
            'scalping': SafeScalpingStrategy()
        }
        self.active_pairs = []
        self.positions = {}  # symbol -> position
        self.is_running = False
        self.max_positions = int(os.getenv('MAX_POSITIONS', 1))
        
    async def load_active_pairs(self):
        """Загрузка активных торговых пар из БД"""
        db = SessionLocal()
        pairs = db.query(TradingPair).filter(TradingPair.is_active == True).all()
        self.active_pairs = [pair.symbol for pair in pairs]
        db.close()
        
        if not self.active_pairs:
            self.active_pairs = [os.getenv('TRADING_SYMBOL', 'BTCUSDT')]
        
        logger.info(f"Активные пары: {self.active_pairs}")
    
    async def analyze_pair(self, symbol: str):
        """Анализ одной торговой пары"""
        try:
            # Получаем данные
            ohlcv = self.client.exchange.fetch_ohlcv(
                symbol,
                timeframe='5m',
                limit=200  # Больше данных для надежности
            )
            
            df = pd.DataFrame(
                ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # Анализируем разными стратегиями
            signals = []
            
            # Multi-indicator стратегия
            signal = self.strategies['multi_indicator'].analyze(df)
            if signal.action != 'WAIT':
                signals.append(('multi_indicator', signal))
            
            # Scalping стратегия (только для боковых рынков)
            if self._is_sideways_market(df):
                signal = self.strategies['scalping'].analyze(df)
                if signal.action != 'WAIT':
                    signals.append(('scalping', signal))
            
            # Выбираем лучший сигнал
            if signals:
                best_strategy, best_signal = max(signals, key=lambda x: x[1].confidence)
                
                logger.info(f"{symbol}: {best_signal.action} сигнал от {best_strategy}, "
                          f"уверенность: {best_signal.confidence:.2f}")
                
                # Отправляем уведомление о сигнале
                await self.notifier.send_notification(NotificationMessage(
                    title=f"📊 Сигнал: {symbol}",
                    text=f"{best_signal.action} сигнал\nСтратегия: {best_strategy}",
                    level="INFO",
                    data={
                        "Уверенность": f"{best_signal.confidence:.2%}",
                        "Причина": best_signal.reason,
                        "Risk/Reward": f"{best_signal.risk_reward_ratio:.2f}"
                    }
                ))
                
                return best_signal
            
        except Exception as e:
            logger.error(f"Ошибка анализа {symbol}: {e}")
        
        return None
    
    def _is_sideways_market(self, df: pd.DataFrame) -> bool:
        """Определение бокового рынка"""
        # Простая проверка на основе изменения цены за последние 50 баров
        price_change = (df['close'].iloc[-1] - df['close'].iloc[-50]) / df['close'].iloc[-50]
        return abs(price_change) < 0.02  # Менее 2% изменения
    
    async def execute_signal(self, symbol: str, signal):
        """Исполнение торгового сигнала"""
        # Проверяем лимиты
        if len(self.positions) >= self.max_positions:
            logger.warning(f"Достигнут лимит позиций ({self.max_positions})")
            return
        
        if symbol in self.positions:
            logger.info(f"Уже есть открытая позиция по {symbol}")
            return
        
        # Получаем баланс
        balance = await self.client.fetch_balance()
        free_balance = balance.get('USDT', {}).get('free', 0)
        
        if free_balance <= 0:
            logger.warning("Недостаточно средств")
            return
        
        # Получаем текущую цену
        ticker = await self.client.fetch_ticker(symbol)
        current_price = ticker['last']
        
        # Расчет размера позиции
        position_size_percent = float(os.getenv('MAX_POSITION_SIZE_PERCENT', 5))
        position_value = free_balance * (position_size_percent / 100)
        amount = position_value / current_price
        
        # Исполнение ордера
        order = await self.client.create_order(
            symbol,
            signal.action.lower(),
            amount
        )
        
        if order:
            # Сохраняем в БД
            db = SessionLocal()
            trade = Trade(
                symbol=symbol,
                side=signal.action,
                entry_price=current_price,
                quantity=amount,
                status='OPEN',
                strategy='advanced',
                stop_loss=signal.stop_loss,
                take_profit=signal.take_profit
            )
            db.add(trade)
            db.commit()
            db.close()
            
            self.positions[symbol] = trade
            
            # Уведомление об открытии
            await self.notifier.send_trade_opened(trade)
            
            logger.info(f"Позиция открыта: {signal.action} {amount} {symbol} @ {current_price}")
    
    async def check_open_positions(self):
        """Проверка открытых позиций на SL/TP"""
        for symbol, position in list(self.positions.items()):
            try:
                ticker = await self.client.fetch_ticker(symbol)
                current_price = ticker['last']
                
                should_close = False
                reason = ""
                
                if position.side == 'BUY':
                    if current_price <= position.stop_loss:
                        should_close = True
                        reason = "Stop Loss"
                    elif current_price >= position.take_profit:
                        should_close = True
                        reason = "Take Profit"
                else:  # SELL
                    if current_price >= position.stop_loss:
                        should_close = True
                        reason = "Stop Loss"
                    elif current_price <= position.take_profit:
                        should_close = True
                        reason = "Take Profit"
                
                if should_close:
                    # Закрываем позицию
                    close_side = 'sell' if position.side == 'BUY' else 'buy'
                    order = await self.client.create_order(
                        symbol,
                        close_side,
                        position.quantity
                    )
                    
                    if order:
                        # Обновляем в БД
                        db = SessionLocal()
                        trade = db.query(Trade).filter(Trade.id == position.id).first()
                        trade.exit_price = current_price
                        trade.profit = (current_price - trade.entry_price) * trade.quantity
                        if position.side == 'SELL':
                            trade.profit = -trade.profit
                        trade.status = 'CLOSED'
                        trade.closed_at = datetime.utcnow()
                        db.commit()
                        db.close()
                        
                        # Уведомление о закрытии
                        await self.notifier.send_trade_closed(trade)
                        
                        logger.info(f"Позиция закрыта по {reason}: {symbol} @ {current_price}, "
                                  f"Profit: {trade.profit:.2f}")
                        
                        del self.positions[symbol]
                        
            except Exception as e:
                logger.error(f"Ошибка проверки позиции {symbol}: {e}")
    
    async def analyze_all_pairs(self):
        """Анализ всех активных пар"""
        # Разбиваем на батчи чтобы не перегружать
        batch_size = 3
        
        for i in range(0, len(self.active_pairs), batch_size):
            batch = self.active_pairs[i:i + batch_size]
            
            # Анализируем параллельно
            tasks = [self.analyze_pair(symbol) for symbol in batch]
            signals = await asyncio.gather(*tasks)
            
            # Обрабатываем сигналы
            for symbol, signal in zip(batch, signals):
                if signal and signal.action != 'WAIT':
                    await self.execute_signal(symbol, signal)
            
            # Пауза между батчами
            await asyncio.sleep(2)
    
    async def run(self):
        """Основной цикл бота"""
        self.is_running = True
        
        # Загружаем активные пары
        await self.load_active_pairs()
        
        # Отправляем уведомление о запуске
        await self.notifier.send_notification(NotificationMessage(
            title="🚀 Бот запущен",
            text=f"Торговля по парам: {', '.join(self.active_pairs)}",
            level="INFO"
        ))
        
        logger.info("Бот запущен")
        
        while self.is_running:
            try:
                # Анализируем все пары
                await self.analyze_all_pairs()
                
                # Проверяем открытые позиции
                await self.check_open_positions()
                
                # Пауза между циклами
                await asyncio.sleep(60)  # Проверка раз в минуту
                
            except Exception as e:
                logger.error(f"Ошибка в основном цикле: {e}")
                
                await self.notifier.send_notification(NotificationMessage(
                    title="🚨 Ошибка бота",
                    text=str(e),
                    level="ERROR"
                ))
                
                await asyncio.sleep(30)
    
    def stop(self):
        """Остановка бота"""
        self.is_running = False
        logger.info("Бот остановлен")

# Глобальный экземпляр бота
bot_instance = None

async def main():
    global bot_instance
    bot_instance = AdvancedCryptoBot()
    await bot_instance.run()

if __name__ == "__main__":
    asyncio.run(main())