#!/usr/bin/env python3
"""
Единый менеджер торгового бота
Объединяет всю логику управления в одном месте
"""
import asyncio
import logging
import psutil
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from enum import Enum

from ..core.config import config
from ..core.database import SessionLocal
from ..core.models import Trade, Signal, BotState, TradingPair, TradeStatus
from ..exchange.client import ExchangeClient
from ..strategies import StrategyFactory
from ..analysis.market_analyzer import MarketAnalyzer
from ..notifications.telegram import TelegramNotifier

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
    Единый менеджер для всех операций бота
    Объединяет функционал всех предыдущих менеджеров
    """
    
    _instance = None
    
    def __new__(cls):
        """Singleton паттерн"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Инициализация только один раз"""
        if not hasattr(self, 'initialized'):
            # Основные компоненты
            self.exchange = ExchangeClient()
            self.analyzer = MarketAnalyzer()
            self.notifier = TelegramNotifier()
            self.strategy_factory = StrategyFactory()
            
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
            
            self.initialized = True
            logger.info("✅ BotManager инициализирован")
    
    # === УПРАВЛЕНИЕ ЖИЗНЕННЫМ ЦИКЛОМ ===
    
    async def start(self) -> Tuple[bool, str]:
        """Запуск бота с полной проверкой"""
        if self.status in [BotStatus.RUNNING, BotStatus.STARTING]:
            return False, f"Бот уже {self.status.value}"
        
        try:
            self.status = BotStatus.STARTING
            logger.info("🚀 Начинаем запуск бота...")
            
            # 1. Проверяем конфигурацию
            if not self._validate_config():
                raise ValueError("Некорректная конфигурация")
            
            # 2. Проверяем подключение к бирже
            await self._check_exchange_connection()
            
            # 3. Загружаем конфигурацию из БД
            await self._load_configuration()
            
            # 4. Обновляем состояние в БД
            await self._update_bot_state(is_running=True)
            
            # 5. Запускаем основной цикл
            self._stop_event.clear()
            self._main_task = asyncio.create_task(self._trading_loop())
            
            # 6. Обновляем информацию о процессе
            self._update_process_info()
            
            # 7. Отправляем уведомление
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
            logger.error(f"❌ {error_msg}")
            await self._update_bot_state(is_running=False)
            return False, error_msg
    
    async def stop(self) -> Tuple[bool, str]:
        """Остановка бота с корректным завершением"""
        if self.status not in [BotStatus.RUNNING, BotStatus.ERROR]:
            return False, f"Бот не запущен (статус: {self.status.value})"
        
        try:
            self.status = BotStatus.STOPPING
            logger.info("🛑 Начинаем остановку бота...")
            
            # 1. Сигнализируем об остановке
            self._stop_event.set()
            
            # 2. Ждем завершения основной задачи
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
            
            # 3. Закрываем все открытые позиции
            await self._close_all_positions("Bot shutdown")
            
            # 4. Обновляем состояние в БД
            await self._update_bot_state(is_running=False)
            
            # 5. Сохраняем статистику
            await self._save_statistics()
            
            # 6. Отправляем уведомление
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
            logger.error(f"❌ {error_msg}")
            return False, error_msg
    
    async def restart(self) -> Tuple[bool, str]:
        """Перезапуск бота"""
        logger.info("🔄 Перезапуск бота...")
        
        # Останавливаем
        stop_success, stop_msg = await self.stop()
        if not stop_success:
            return False, f"Не удалось остановить: {stop_msg}"
        
        # Ждем
        await asyncio.sleep(2)
        
        # Запускаем
        return await self.start()
    
    # === ОСНОВНОЙ ТОРГОВЫЙ ЦИКЛ ===
    
    async def _trading_loop(self):
        """Основной торговый цикл с имитацией человека"""
        logger.info("🔄 Запуск торгового цикла")
        
        while not self._stop_event.is_set():
            try:
                self.cycles_count += 1
                cycle_start = datetime.now()
                
                logger.debug(f"📊 Цикл анализа #{self.cycles_count}")
                
                # 1. Проверяем лимиты
                if not await self._check_trading_limits():
                    logger.info("📈 Достигнуты дневные лимиты торговли")
                    await self._human_delay(300, 600)  # Пауза 5-10 минут
                    continue
                
                # 2. Анализируем рынок
                market_data = await self.analyzer.analyze_market(self.active_pairs)
                
                # 3. Генерируем сигналы
                signals = await self._generate_signals(market_data)
                
                # 4. Исполняем сигналы с имитацией человека
                for signal in signals:
                    if self._stop_event.is_set():
                        break
                    await self._execute_signal_human_like(signal)
                
                # 5. Управляем открытыми позициями
                await self._manage_positions()
                
                # 6. Обновляем статистику
                await self._update_statistics()
                
                # 7. Человеческая пауза между циклами
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
    
    # === ИМИТАЦИЯ ЧЕЛОВЕЧЕСКОГО ПОВЕДЕНИЯ ===
    
    async def _human_delay(self, min_seconds: float = None, max_seconds: float = None):
        """Умная задержка с имитацией человека"""
        if not config.ENABLE_HUMAN_MODE:
            await asyncio.sleep(60)  # Стандартная минута
            return
        
        import random
        
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
    
    async def _execute_signal_human_like(self, signal: Signal):
        """Исполнение сигнала с имитацией человека"""
        # Имитируем время на принятие решения
        thinking_time = random.uniform(5, 20)
        logger.debug(f"🤔 Обдумываем сигнал {signal.symbol} в течение {thinking_time:.1f}с")
        await asyncio.sleep(thinking_time)
        
        # Иногда "сомневаемся" и пропускаем сигнал
        if random.random() < 0.1:  # 10% шанс
            logger.info(f"😕 Решили пропустить сигнал {signal.symbol} (сомнения)")
            return
        
        # Иногда "отвлекаемся" и откладываем
        if random.random() < 0.05:  # 5% шанс
            delay = random.uniform(30, 120)
            logger.info(f"📱 Отвлеклись, откладываем исполнение на {delay:.0f}с")
            await asyncio.sleep(delay)
        
        # Исполняем с небольшими случайными корректировками размера
        await self._execute_signal(signal)
    
    # === ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ===
    
    def _validate_config(self) -> bool:
        """Проверка конфигурации"""
        if not config.BYBIT_API_KEY or config.BYBIT_API_KEY == 'your_testnet_api_key_here':
            logger.error("❌ API ключи не настроены")
            return False
        
        if not config.TRADING_PAIRS:
            logger.error("❌ Не указаны торговые пары")
            return False
        
        return True
    
    async def _check_exchange_connection(self):
        """Проверка подключения к бирже"""
        try:
            balance = await self.exchange.fetch_balance()
            usdt_balance = balance.get('USDT', {}).get('free', 0)
            logger.info(f"💰 Баланс: {usdt_balance:.2f} USDT")
        except Exception as e:
            raise ConnectionError(f"Не удалось подключиться к бирже: {e}")
    
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
    
    async def _update_bot_state(self, is_running: bool):
        """Обновление состояния в БД"""
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
            state.current_balance = await self._get_current_balance()
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Ошибка обновления состояния в БД: {e}")
        finally:
            db.close()
    
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
            
            return True, f"Позиция {symbol} закрыта"
            
        except Exception as e:
            logger.error(f"Ошибка закрытия позиции: {e}")
            return False, str(e)
    
    # Остальные методы (_generate_signals, _execute_signal, etc.) 
    # остаются как в оригинальном коде, но теперь в одном месте

# Глобальный экземпляр
bot_manager = BotManager()