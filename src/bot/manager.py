"""
Единый менеджер торгового бота - ядро системы
Путь: /var/www/www-root/data/www/systemetech.ru/src/bot/manager.py
"""
import asyncio
import logging
import psutil
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import random

from ..core.config import config
from ..core.database import SessionLocal
from ..core.models import Trade, Signal, BotState, TradingPair, TradeStatus, OrderSide
from ..exchange.client import ExchangeClient
from ..strategies.factory import StrategyFactory
from ..analysis.market_analyzer import MarketAnalyzer
from ..notifications.telegram import TelegramNotifier
from .trader import Trader
from .risk_manager import RiskManager

logger = logging.getLogger(__name__)

class BotStatus(Enum):
    """Статусы бота"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"

class BotManager:
    """
    Единый менеджер для всего бота
    Управляет всеми компонентами системы
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """Singleton паттерн"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Инициализация только один раз"""
        if not BotManager._initialized:
            # Основные компоненты
            self.exchange = ExchangeClient()
            self.analyzer = MarketAnalyzer()
            self.notifier = TelegramNotifier()
            self.strategy_factory = StrategyFactory()
            self.trader = Trader(self.exchange)
            self.risk_manager = RiskManager()
            
            # Состояние
            self.status = BotStatus.STOPPED
            self.positions: Dict[str, Trade] = {}
            self.active_pairs: List[str] = []
            
            # Управление процессом
            self._main_task: Optional[asyncio.Task] = None
            self._stop_event = asyncio.Event()
            self._process_info: Dict = {}
            
            # Статистика
            self.start_time: Optional[datetime] = None
            self.cycles_count = 0
            self.trades_today = 0
            
            # Инициализация из БД
            self._load_state_from_db()
            
            BotManager._initialized = True
            logger.info("✅ BotManager инициализирован")
    
    # === УПРАВЛЕНИЕ ЖИЗНЕННЫМ ЦИКЛОМ ===
    
    async def start(self) -> Tuple[bool, str]:
        """Запуск бота"""
        if self.status in [BotStatus.RUNNING, BotStatus.STARTING]:
            return False, f"Бот уже {self.status.value}"
        
        try:
            self.status = BotStatus.STARTING
            logger.info("🚀 Начинаем запуск бота...")
            
            # Проверки перед запуском
            if not await self._pre_start_checks():
                raise ValueError("Проверки перед запуском не пройдены")
            
            # Загружаем конфигурацию
            await self._load_configuration()
            
            # Обновляем состояние в БД
            self._update_bot_state_db(is_running=True)
            
            # Запускаем основной цикл
            self._stop_event.clear()
            self._main_task = asyncio.create_task(self._trading_loop())
            
            # Обновляем информацию о процессе
            self._update_process_info()
            
            # Отправляем уведомление
            await self.notifier.send_startup_message(
                pairs=self.active_pairs,
                mode='TESTNET' if config.BYBIT_TESTNET else 'MAINNET'
            )
            
            self.status = BotStatus.RUNNING
            self.start_time = datetime.now()
            
            logger.info("✅ Бот успешно запущен")
            return True, "Бот успешно запущен"
            
        except Exception as e:
            self.status = BotStatus.ERROR
            error_msg = f"Ошибка запуска: {str(e)}"
            logger.error(f"❌ {error_msg}", exc_info=True)
            self._update_bot_state_db(is_running=False)
            return False, error_msg
    
    async def stop(self) -> Tuple[bool, str]:
        """Остановка бота"""
        if self.status not in [BotStatus.RUNNING, BotStatus.ERROR]:
            return False, f"Бот не запущен (статус: {self.status.value})"
        
        try:
            self.status = BotStatus.STOPPING
            logger.info("🛑 Начинаем остановку бота...")
            
            # Сигнализируем об остановке
            self._stop_event.set()
            
            # Ждем завершения основной задачи
            if self._main_task:
                try:
                    await asyncio.wait_for(self._main_task, timeout=10.0)
                except asyncio.TimeoutError:
                    logger.warning("⚠️ Таймаут остановки, принудительное завершение")
                    self._main_task.cancel()
                    try:
                        await self._main_task
                    except asyncio.CancelledError:
                        pass
            
            # Закрываем все открытые позиции
            await self._close_all_positions("Bot shutdown")
            
            # Обновляем состояние в БД
            self._update_bot_state_db(is_running=False)
            
            # Сохраняем статистику
            self._save_statistics()
            
            # Отправляем уведомление
            await self.notifier.send_shutdown_message(
                runtime=(datetime.now() - self.start_time) if self.start_time else None,
                trades_count=self.trades_today
            )
            
            self.status = BotStatus.STOPPED
            logger.info("✅ Бот успешно остановлен")
            return True, "Бот успешно остановлен"
            
        except Exception as e:
            self.status = BotStatus.ERROR
            error_msg = f"Ошибка остановки: {str(e)}"
            logger.error(f"❌ {error_msg}", exc_info=True)
            return False, error_msg
    
    # === ОСНОВНОЙ ТОРГОВЫЙ ЦИКЛ ===
    
    async def _trading_loop(self):
        """Основной торговый цикл"""
        logger.info("🔄 Запуск торгового цикла")
        
        while not self._stop_event.is_set():
            try:
                self.cycles_count += 1
                cycle_start = datetime.now()
                
                logger.debug(f"📊 Цикл анализа #{self.cycles_count}")
                
                # 1. Проверяем лимиты
                if not self._check_trading_limits():
                    logger.info("📈 Достигнуты дневные лимиты торговли")
                    await self._human_delay(300, 600)  # Пауза 5-10 минут
                    continue
                
                # 2. Обновляем баланс
                await self._update_balance()
                
                # 3. Анализируем рынок для всех активных пар
                for symbol in self.active_pairs:
                    if self._stop_event.is_set():
                        break
                    
                    try:
                        # Анализируем пару
                        market_data = await self.analyzer.analyze_symbol(symbol)
                        if not market_data:
                            continue
                        
                        # Генерируем сигнал
                        signal = await self._generate_signal(symbol, market_data)
                        if not signal:
                            continue
                        
                        # Сохраняем сигнал в БД
                        self._save_signal(signal)
                        
                        # Исполняем сигнал если нужно
                        if signal.action in ['BUY', 'SELL'] and signal.confidence >= 0.6:
                            await self._execute_signal_human_like(signal)
                        
                    except Exception as e:
                        logger.error(f"❌ Ошибка анализа {symbol}: {e}")
                        await self.notifier.send_error(f"Ошибка анализа {symbol}: {str(e)}")
                
                # 4. Управляем открытыми позициями
                await self._manage_positions()
                
                # 5. Обновляем статистику
                self._update_statistics()
                
                # 6. Человеческая пауза между циклами
                cycle_duration = (datetime.now() - cycle_start).total_seconds()
                logger.debug(f"⏱️ Цикл #{self.cycles_count} выполнен за {cycle_duration:.1f}с")
                
                await self._human_delay()
                
            except asyncio.CancelledError:
                logger.info("🛑 Торговый цикл отменен")
                break
            except Exception as e:
                logger.error(f"❌ Ошибка в торговом цикле: {e}", exc_info=True)
                await self.notifier.send_error(f"Ошибка торгового цикла: {str(e)}")
                await self._human_delay(60, 180)  # Пауза 1-3 минуты при ошибке
        
        logger.info("🏁 Торговый цикл завершен")
    
    # === ГЕНЕРАЦИЯ И ИСПОЛНЕНИЕ СИГНАЛОВ ===
    
    async def _generate_signal(self, symbol: str, market_data: Dict) -> Optional[Signal]:
        """Генерация торгового сигнала"""
        try:
            # Получаем стратегию для пары
            pair_config = self._get_pair_config(symbol)
            strategy = self.strategy_factory.create(pair_config.strategy)
            
            # Анализируем
            analysis = await strategy.analyze(market_data['df'], symbol)
            
            if analysis.action == 'WAIT':
                return None
            
            # Создаем сигнал
            signal = Signal(
                symbol=symbol,
                action=analysis.action,
                confidence=analysis.confidence,
                price=market_data['current_price'],
                stop_loss=analysis.stop_loss,
                take_profit=analysis.take_profit,
                strategy=strategy.name,
                reason=analysis.reason
            )
            
            return signal
            
        except Exception as e:
            logger.error(f"❌ Ошибка генерации сигнала для {symbol}: {e}")
            return None
    
    async def _execute_signal_human_like(self, signal: Signal):
        """Исполнение сигнала с имитацией человека"""
        # Проверяем риски
        if not self.risk_manager.check_signal(signal, self.positions, self._get_current_balance()):
            logger.info(f"🚫 Сигнал {signal.symbol} отклонен риск-менеджментом")
            return
        
        # Имитируем время на принятие решения
        thinking_time = random.uniform(5, 20)
        logger.debug(f"🤔 Обдумываем сигнал {signal.symbol} в течение {thinking_time:.1f}с")
        await asyncio.sleep(thinking_time)
        
        # Иногда "сомневаемся" и пропускаем сигнал
        if config.ENABLE_HUMAN_MODE and random.random() < 0.1:  # 10% шанс
            logger.info(f"😕 Решили пропустить сигнал {signal.symbol} (сомнения)")
            return
        
        # Иногда "отвлекаемся" и откладываем
        if config.ENABLE_HUMAN_MODE and random.random() < 0.05:  # 5% шанс
            delay = random.uniform(30, 120)
            logger.info(f"📱 Отвлеклись, откладываем исполнение на {delay:.0f}с")
            await asyncio.sleep(delay)
        
        # Исполняем через trader
        trade = await self.trader.execute_signal(signal)
        if trade:
            self.positions[signal.symbol] = trade
            signal.executed = True
            signal.executed_at = datetime.utcnow()
            signal.trade_id = trade.id
            self._update_signal_db(signal)
            
            await self.notifier.send_trade_opened(
                symbol=signal.symbol,
                side=signal.action,
                amount=trade.quantity,
                price=trade.entry_price
            )
    
    # === УПРАВЛЕНИЕ ПОЗИЦИЯМИ ===
    
    async def _manage_positions(self):
        """Управление открытыми позициями"""
        for symbol, trade in list(self.positions.items()):
            try:
                # Получаем текущую цену
                ticker = await self.exchange.fetch_ticker(symbol)
                current_price = ticker['last']
                
                # Проверяем стоп-лосс и тейк-профит
                should_close = False
                reason = ""
                
                if trade.side == OrderSide.BUY:
                    if current_price <= trade.stop_loss:
                        should_close = True
                        reason = "Stop loss triggered"
                    elif current_price >= trade.take_profit:
                        should_close = True
                        reason = "Take profit triggered"
                else:  # SELL
                    if current_price >= trade.stop_loss:
                        should_close = True
                        reason = "Stop loss triggered"
                    elif current_price <= trade.take_profit:
                        should_close = True
                        reason = "Take profit triggered"
                
                # Закрываем позицию если нужно
                if should_close:
                    await self._close_position(trade, current_price, reason)
                    del self.positions[symbol]
                
            except Exception as e:
                logger.error(f"❌ Ошибка управления позицией {symbol}: {e}")
    
    async def _close_position(self, trade: Trade, current_price: float, reason: str):
        """Закрытие позиции"""
        try:
            # Закрываем через exchange
            result = await self.trader.close_position(trade, current_price)
            
            if result:
                # Обновляем trade
                trade.exit_price = current_price
                trade.status = TradeStatus.CLOSED
                trade.closed_at = datetime.utcnow()
                trade.calculate_profit()
                trade.notes = reason
                
                # Сохраняем в БД
                self._update_trade_db(trade)
                
                # Уведомляем
                await self.notifier.send_trade_closed(
                    symbol=trade.symbol,
                    side=trade.side.value,
                    profit=trade.profit,
                    reason=reason
                )
                
                # Обновляем статистику
                if trade.profit > 0:
                    self.risk_manager.update_statistics('win', trade.profit)
                else:
                    self.risk_manager.update_statistics('loss', abs(trade.profit))
                
        except Exception as e:
            logger.error(f"❌ Ошибка закрытия позиции: {e}")
    
    # === ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ===
    
    async def _pre_start_checks(self) -> bool:
        """Проверки перед запуском"""
        # Проверка конфигурации
        if not config.BYBIT_API_KEY or config.BYBIT_API_KEY == 'your_testnet_api_key_here':
            logger.error("❌ API ключи не настроены")
            return False
        
        # Проверка подключения к бирже
        try:
            await self.exchange.test_connection()
        except Exception as e:
            logger.error(f"❌ Не удалось подключиться к бирже: {e}")
            return False
        
        # Проверка БД
        try:
            db = SessionLocal()
            db.execute("SELECT 1")
            db.close()
        except Exception as e:
            logger.error(f"❌ Не удалось подключиться к БД: {e}")
            return False
        
        return True
    
    async def _load_configuration(self):
        """Загрузка конфигурации из БД"""
        db = SessionLocal()
        try:
            # Загружаем активные пары
            pairs = db.query(TradingPair).filter(
                TradingPair.is_active == True
            ).all()
            
            self.active_pairs = [pair.symbol for pair in pairs]
            
            if not self.active_pairs:
                self.active_pairs = config.TRADING_PAIRS
                logger.warning(f"Используем пары из конфига: {self.active_pairs}")
            
            # Загружаем открытые позиции
            open_trades = db.query(Trade).filter(
                Trade.status == TradeStatus.OPEN
            ).all()
            
            self.positions = {trade.symbol: trade for trade in open_trades}
            
            logger.info(f"📋 Загружено: {len(self.active_pairs)} пар, {len(self.positions)} позиций")
            
        finally:
            db.close()
    
    async def _human_delay(self, min_seconds: float = None, max_seconds: float = None):
        """Умная задержка с имитацией человека"""
        if not config.ENABLE_HUMAN_MODE:
            await asyncio.sleep(60)  # Стандартная минута
            return
        
        # Используем настройки или переданные параметры
        min_delay = min_seconds or config.MIN_DELAY_SECONDS
        max_delay = max_seconds or config.MAX_DELAY_SECONDS
        
        # Базовая задержка
        delay = random.uniform(min_delay, max_delay)
        
        # Учитываем время суток (человек медленнее ночью)
        hour = datetime.now().hour
        if 0 <= hour < 6:  # Ночь
            delay *= random.uniform(1.5, 2.5)
        elif 6 <= hour < 9:  # Утро
            delay *= random.uniform(1.2, 1.5)
        
        # Учитываем "усталость" (больше циклов = больше задержка)
        if self.cycles_count > 100:
            fatigue_factor = min(2.0, 1 + (self.cycles_count - 100) / 200)
            delay *= fatigue_factor
        
        # Иногда делаем длинные паузы (перерывы)
        if random.random() < 0.02:  # 2% шанс
            delay = random.uniform(300, 900)  # 5-15 минут
            logger.info(f"☕ Имитация перерыва: {delay/60:.1f} минут")
        
        # Очень редко делаем очень длинные паузы (обед/отдых)
        elif random.random() < 0.005:  # 0.5% шанс
            delay = random.uniform(1800, 3600)  # 30-60 минут
            logger.info(f"🍔 Имитация длинного перерыва: {delay/60:.1f} минут")
        
        # Разбиваем задержку для возможности быстрой остановки
        remaining = delay
        while remaining > 0 and not self._stop_event.is_set():
            sleep_time = min(1.0, remaining)
            await asyncio.sleep(sleep_time)
            remaining -= sleep_time
    
    # === РАБОТА С БД ===
    
    def _load_state_from_db(self):
        """Загрузка состояния из БД при инициализации"""
        db = SessionLocal()
        try:
            bot_state = db.query(BotState).first()
            if bot_state and bot_state.is_running:
                logger.warning("⚠️ Бот был запущен при последнем выключении")
                bot_state.is_running = False
                db.commit()
        except Exception as e:
            logger.error(f"Ошибка загрузки состояния: {e}")
        finally:
            db.close()
    
    def _update_bot_state_db(self, is_running: bool):
        """Обновление состояния бота в БД"""
        db = SessionLocal()
        try:
            state = db.query(BotState).first()
            if not state:
                state = BotState()
                db.add(state)
            
            state.is_running = is_running
            if is_running:
                state.start_time = datetime.utcnow()
            else:
                state.stop_time = datetime.utcnow()
            
            state.total_trades = self.trades_today
            state.current_balance = self._get_current_balance()
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Ошибка обновления состояния в БД: {e}")
        finally:
            db.close()
    
    def _save_signal(self, signal: Signal):
        """Сохранение сигнала в БД"""
        db = SessionLocal()
        try:
            db.add(signal)
            db.commit()
        except Exception as e:
            logger.error(f"Ошибка сохранения сигнала: {e}")
        finally:
            db.close()
    
    def _update_signal_db(self, signal: Signal):
        """Обновление сигнала в БД"""
        db = SessionLocal()
        try:
            db.merge(signal)
            db.commit()
        except Exception as e:
            logger.error(f"Ошибка обновления сигнала: {e}")
        finally:
            db.close()
    
    def _update_trade_db(self, trade: Trade):
        """Обновление сделки в БД"""
        db = SessionLocal()
        try:
            db.merge(trade)
            db.commit()
        except Exception as e:
            logger.error(f"Ошибка обновления сделки: {e}")
        finally:
            db.close()
    
    # === ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ===
    
    def _check_trading_limits(self) -> bool:
        """Проверка дневных лимитов"""
        return self.trades_today < config.MAX_DAILY_TRADES
    
    async def _update_balance(self):
        """Обновление баланса"""
        try:
            balance = await self.exchange.fetch_balance()
            # Сохраняем в БД
            db = SessionLocal()
            try:
                for currency, amount in balance.items():
                    if amount['total'] > 0:
                        balance_record = Balance(
                            currency=currency,
                            total=amount['total'],
                            free=amount['free'],
                            used=amount['used']
                        )
                        db.add(balance_record)
                db.commit()
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Ошибка обновления баланса: {e}")
    
    def _get_current_balance(self) -> float:
        """Получение текущего баланса в USDT"""
        db = SessionLocal()
        try:
            latest_balance = db.query(Balance).filter(
                Balance.currency == 'USDT'
            ).order_by(Balance.timestamp.desc()).first()
            
            return latest_balance.total if latest_balance else config.INITIAL_CAPITAL
        finally:
            db.close()
    
    def _get_pair_config(self, symbol: str) -> TradingPair:
        """Получение конфигурации пары"""
        db = SessionLocal()
        try:
            pair = db.query(TradingPair).filter(
                TradingPair.symbol == symbol
            ).first()
            
            if not pair:
                # Создаем дефолтную конфигурацию
                pair = TradingPair(
                    symbol=symbol,
                    strategy='multi_indicator',
                    stop_loss_percent=config.STOP_LOSS_PERCENT,
                    take_profit_percent=config.TAKE_PROFIT_PERCENT
                )
            
            return pair
        finally:
            db.close()
    
    def _update_process_info(self):
        """Обновление информации о процессе"""
        try:
            process = psutil.Process()
            self._process_info = {
                'pid': process.pid,
                'memory_mb': round(process.memory_info().rss / 1024 / 1024, 2),
                'cpu_percent': process.cpu_percent(),
                'threads': process.num_threads(),
                'create_time': datetime.fromtimestamp(process.create_time())
            }
        except Exception as e:
            logger.error(f"Ошибка получения информации о процессе: {e}")
    
    def _update_statistics(self):
        """Обновление статистики"""
        db = SessionLocal()
        try:
            # Считаем сделки за сегодня
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            self.trades_today = db.query(Trade).filter(
                Trade.created_at >= today_start
            ).count()
            
        finally:
            db.close()
    
    def _save_statistics(self):
        """Сохранение статистики при остановке"""
        db = SessionLocal()
        try:
            state = db.query(BotState).first()
            if state:
                # Считаем общую статистику
                total_trades = db.query(Trade).count()
                profitable_trades = db.query(Trade).filter(
                    Trade.profit > 0
                ).count()
                total_profit = db.query(Trade).with_entities(
                    db.func.sum(Trade.profit)
                ).scalar() or 0
                
                state.total_trades = total_trades
                state.profitable_trades = profitable_trades
                state.total_profit = total_profit
                
                db.commit()
        finally:
            db.close()
    
    async def _close_all_positions(self, reason: str):
        """Закрытие всех открытых позиций"""
        for symbol, trade in list(self.positions.items()):
            try:
                ticker = await self.exchange.fetch_ticker(symbol)
                current_price = ticker['last']
                await self._close_position(trade, current_price, reason)
                del self.positions[symbol]
            except Exception as e:
                logger.error(f"Ошибка закрытия позиции {symbol}: {e}")
    
    # === ПУБЛИЧНЫЕ МЕТОДЫ ДЛЯ API ===
    
    def get_status(self) -> Dict:
        """Получение полного статуса бота"""
        return {
            'status': self.status.value,
            'is_running': self.status == BotStatus.RUNNING,
            'active_pairs': self.active_pairs,
            'open_positions': len(self.positions),
            'positions_details': {
                symbol: {
                    'side': trade.side.value,
                    'entry_price': trade.entry_price,
                    'quantity': trade.quantity,
                    'profit': trade.profit
                }
                for symbol, trade in self.positions.items()
            },
            'statistics': {
                'start_time': self.start_time.isoformat() if self.start_time else None,
                'uptime': str(datetime.now() - self.start_time) if self.start_time else None,
                'cycles_count': self.cycles_count,
                'trades_today': self.trades_today
            },
            'process_info': self._process_info,
            'config': {
                'mode': 'TESTNET' if config.BYBIT_TESTNET else 'MAINNET',
                'max_positions': config.MAX_POSITIONS,
                'human_mode': config.ENABLE_HUMAN_MODE
            }
        }
    
    async def update_pairs(self, pairs: List[str]) -> Tuple[bool, str]:
        """Обновление торговых пар"""
        try:
            db = SessionLocal()
            
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
                    pair = TradingPair(
                        symbol=symbol,
                        is_active=True,
                        strategy='multi_indicator'
                    )
                    db.add(pair)
            
            db.commit()
            db.close()
            
            self.active_pairs = pairs
            logger.info(f"✅ Обновлены торговые пары: {pairs}")
            
            return True, f"Активировано пар: {len(pairs)}"
            
        except Exception as e:
            logger.error(f"Ошибка обновления пар: {e}")
            return False, str(e)
    
    async def close_position(self, symbol: str) -> Tuple[bool, str]:
        """Ручное закрытие позиции"""
        if symbol not in self.positions:
            return False, f"Позиция {symbol} не найдена"
        
        try:
            trade = self.positions[symbol]
            ticker = await self.exchange.fetch_ticker(symbol)
            current_price = ticker['last']
            
            await self._close_position(trade, current_price, "Manual close")
            del self.positions[symbol]
            
            return True, f"Позиция {symbol} закрыта"
            
        except Exception as e:
            logger.error(f"Ошибка закрытия позиции: {e}")
            return False, str(e)

# Глобальный экземпляр менеджера
bot_manager = BotManager()