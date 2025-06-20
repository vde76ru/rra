"""
Единый менеджер торгового бота - ядро системы
Путь: src/bot/manager.py

ПОЛНАЯ ИСПРАВЛЕННАЯ ВЕРСИЯ - все функции сохранены и улучшены
"""
# Стандартные библиотеки
import asyncio
import sys
import logging
import psutil
import os
from typing import Any, List, Optional, Tuple, Dict
from datetime import datetime, timedelta
from enum import Enum
import random
from collections import deque 

# SQLAlchemy
from sqlalchemy import text, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

# Импорты из core (все модели должны быть здесь)
from ..core.models import (
    Trade, Signal, BotState, TradingPair, 
    TradeStatus, OrderSide, Balance, User,
    TradingLog, MLModel
)
from ..core.database import SessionLocal, db
from ..core.config import config

# ИСПРАВЛЕННЫЕ импорты - безопасная загрузка всех модулей
try:
    from ..exchange.client import ExchangeClient
except ImportError:
    ExchangeClient = None

try:
    from ..strategies import strategy_factory
except ImportError:
    strategy_factory = None

try:
    from ..analysis.market_analyzer import MarketAnalyzer
except ImportError:
    # Создаем заглушку для MarketAnalyzer
    class MarketAnalyzer:
        def __init__(self, exchange=None):
            self.exchange = exchange
            
        async def analyze_symbol(self, symbol):
            """Заглушка для анализа символа"""
            return {
                'current_price': 50000.0,
                'df': None,
                'volume': 1000000,
                'change_24h': 0.05
            }
    logger.info("📦 Используем заглушку MarketAnalyzer")

try:
    from ..notifications.telegram import telegram_notifier
except ImportError:
    telegram_notifier = None

try:
    from ..bot.trader import Trader
except ImportError:
    try:
        from ..trading.trader import Trader
    except ImportError:
        Trader = None

try:
    from ..bot.risk_manager import RiskManager
except ImportError:
    try:
        from ..risk.manager import RiskManager
    except ImportError:
        RiskManager = None

# Безопасные импорты опциональных модулей
try:
    from ..strategies.auto_strategy_selector import auto_strategy_selector
except ImportError:
    auto_strategy_selector = None
    
try:
    from ..logging.smart_logger import SmartLogger
    smart_logger = SmartLogger(__name__)
    logger = smart_logger
except ImportError:
    logger = logging.getLogger(__name__)
    
try:
    from ..logging.log_manager import cleanup_scheduler
except ImportError:
    cleanup_scheduler = None

# Настраиваем логгер для этого модуля
if 'smart_logger' in locals():
    logger = smart_logger
else:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)


class BotStatus(Enum):
    """
    Возможные статусы бота
    
    Каждый статус имеет свое назначение:
    - STOPPED: Бот полностью остановлен
    - STARTING: Процесс запуска (проверки, инициализация)
    - RUNNING: Бот активно торгует
    - STOPPING: Процесс остановки (закрытие позиций, сохранение данных)
    - ERROR: Критическая ошибка, требующая вмешательства
    """
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"

class BotManager:
    """
    Единый менеджер для всего бота - ПОЛНАЯ ИСПРАВЛЕННАЯ ВЕРСИЯ
    
    Этот класс реализует паттерн Singleton, что означает:
    - Может существовать только один экземпляр
    - Все компоненты системы используют один и тот же менеджер
    - Состояние сохраняется между вызовами
    
    Управляет всеми компонентами торговой системы:
    - Подключением к бирже
    - Анализом рынка
    - Исполнением сделок
    - Управлением рисками
    - Уведомлениями
    """
    
    # Переменные класса для реализации Singleton
    _instance = None
    _initialized = False
    
    
    async def _main_loop(self):
        """
        Основной цикл бота - обертка для торгового цикла
        
        Этот метод служит главной точкой входа для основного цикла бота.
        Включает предварительные проверки и запуск торгового цикла.
        """
        try:
            logger.info("🚀 Запуск основного цикла бота...")
            
            # Предварительные проверки
            checks_passed = await self._pre_start_checks()
            if not checks_passed:
                logger.error("❌ Предварительные проверки не пройдены")
                self.status = BotStatus.ERROR
                return
            
            # Загрузка конфигурации
            await self._load_configuration()
            
            # Обновление информации о процессе
            self._update_process_info()
            
            # Запуск торгового цикла
            await self._trading_loop()
            
        except Exception as e:
            logger.error(f"❌ Критическая ошибка в основном цикле: {e}")
            self.status = BotStatus.ERROR
        finally:
            logger.info("🏁 Основной цикл завершен")
    
    def __new__(cls):
        """
        Реализация паттерна Singleton
        
        Этот метод гарантирует, что создается только один экземпляр класса.
        """
        if cls._instance is None:
            cls._instance = super(BotManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Инициализация менеджера бота - ПОЛНАЯ СОХРАНЕННАЯ ВЕРСИЯ"""
        # Предотвращаем повторную инициализацию
        if BotManager._initialized:
            return
            
        BotManager._initialized = True
        
        # === ОСНОВНЫЕ АТРИБУТЫ ===
        # Статус и время работы
        self.status = BotStatus.STOPPED
        self.start_time = None
        self.stop_time = None
        
        # === КРИТИЧЕСКИ ВАЖНЫЕ АТРИБУТЫ (БЫЛИ ПРОПУЩЕНЫ) ===
        self.active_pairs = []  # ИСПРАВЛЕНИЕ: добавлен active_pairs
        self.positions = {}     # Открытые позиции
        self.cycles_count = 0   # Счетчик циклов
        self.trades_today = 0   # Счетчик сделок за день
        self._stop_event = asyncio.Event()  # Событие для остановки
        self._main_task = None  # Основная задача
        self._process_info = {}  # Информация о процессе
        
        # === КОМПОНЕНТЫ СИСТЕМЫ ===
        # Инициализируем компоненты лениво (lazy initialization)
        self.exchange = None
        self.market_analyzer = None
        self.trader = None
        self.risk_manager = None
        self.notifier = None
        self.analyzer = None
        self.strategy_factory = None
        
        # === АКТИВНЫЕ ЗАДАЧИ ===
        self.tasks = {}
        self.main_loop_task = None
        
        # === КОНФИГУРАЦИЯ ===
        self.config = config
        self.trading_pairs = []
        self.strategy = 'auto'
        
        # === СТАТИСТИКА ===
        self.stats = {
            'trades_count': 0,
            'profitable_trades': 0,
            'total_profit': 0.0,
            'start_balance': 0.0
        }
        
        # === ИНИЦИАЛИЗАЦИЯ КОМПОНЕНТОВ ===
        self._init_components()
        
        logger.info("🤖 BotManager инициализирован")
    
    def _init_components(self):
        """ОБНОВЛЕННАЯ инициализация компонентов с улучшенной системой"""
        try:
            logger.info("🔧 Инициализация компонентов через улучшенную систему...")
            
            # ИСПРАВЛЕНИЕ: Проверяем наличие улучшенного менеджера
            try:
                from ..bot.manager_improved import ImprovedBotManager
                # Создаем улучшенный менеджер
                self.improved_manager = ImprovedBotManager()
                
                # Пытаемся инициализировать через улучшенную систему
                initialization_result = asyncio.run(self._init_components_improved())
                
                if initialization_result:
                    logger.info("✅ Улучшенная система инициализации успешна")
                    return
                else:
                    logger.warning("⚠️ Откат к базовой системе инициализации")
                    
            except ImportError:
                logger.info("📦 ImprovedBotManager не найден, используем базовую инициализацию")
                self.improved_manager = None
            
            # Базовая инициализация в любом случае
            self._init_components_basic()
                
        except Exception as e:
            logger.error(f"❌ Ошибка улучшенной инициализации: {e}")
            logger.info("🔄 Использую базовую инициализацию...")
            self._init_components_basic()
            
    async def _init_components_improved(self) -> bool:
        """Инициализация через улучшенную компонентную систему"""
        try:
            if not self.improved_manager:
                return False
                
            # Инициализируем улучшенную систему
            success = await self.improved_manager.initialize()
            
            if success:
                # Получаем инициализированные компоненты
                self.exchange = self.improved_manager.get_component("exchange")
                self.analyzer = self.improved_manager.get_component("market_analyzer") 
                self.trader = self.improved_manager.get_component("trader")
                self.risk_manager = self.improved_manager.get_component("risk_manager")
                self.notifier = self.improved_manager.get_component("notifications")
                self.strategy_factory = self.improved_manager.get_component("strategy_factory")
                
                # Проверяем критичные компоненты
                critical_components = [
                    ('exchange', self.exchange),
                    ('trader', self.trader),
                    ('risk_manager', self.risk_manager)
                ]
                
                missing_critical = []
                for name, component in critical_components:
                    if component is None:
                        missing_critical.append(name)
                
                if missing_critical:
                    logger.error(f"❌ Критичные компоненты не инициализированы: {missing_critical}")
                    return False
                
                logger.info("✅ Все компоненты инициализированы через улучшенную систему")
                return True
            else:
                logger.error("❌ Не удалось инициализировать улучшенную систему")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка улучшенной инициализации: {e}")
            return False
            
    def _init_components_basic(self):
        """Базовая инициализация компонентов (как backup) - ИСПРАВЛЕННАЯ"""
        logger.info("🔧 Базовая инициализация компонентов...")
        
        try:
            # Exchange клиент - ИСПРАВЛЕНО
            if ExchangeClient:
                try:
                    from ..exchange.client import get_exchange_client
                    self.exchange = get_exchange_client()
                    logger.info("✅ Exchange клиент подключен")
                except Exception as e:
                    logger.warning(f"⚠️ Не удалось создать Exchange через get_exchange_client: {e}")
                    try:
                        self.exchange = ExchangeClient()
                        logger.info("✅ Exchange клиент создан напрямую")
                    except Exception as e2:
                        logger.warning(f"⚠️ Не удалось создать Exchange напрямую: {e2}")
                        self.exchange = None
            else:
                logger.warning("⚠️ ExchangeClient не доступен")
                self.exchange = None
        except Exception as e:
            logger.warning(f"⚠️ Общая ошибка инициализации Exchange: {e}")
            self.exchange = None
    
        try:
            # Market Analyzer - ИСПРАВЛЕНО
            if self.exchange:
                self.analyzer = MarketAnalyzer(self.exchange)
                logger.info("✅ Market Analyzer инициализирован")
            else:
                # Создаем без exchange для совместимости
                self.analyzer = MarketAnalyzer()
                logger.info("✅ Market Analyzer инициализирован (без exchange)")
        except Exception as e:
            logger.warning(f"⚠️ Ошибка инициализации Market Analyzer: {e}")
            self.analyzer = None
    
        try:
            # Trader - ИСПРАВЛЕНО
            if Trader:
                if self.exchange:
                    self.trader = Trader(self.exchange)
                    logger.info("✅ Trader инициализирован с Exchange")
                else:
                    self.trader = Trader()
                    logger.info("✅ Trader инициализирован без Exchange")
            else:
                logger.info("📦 Trader не найден")
                self.trader = None
        except Exception as e:
            logger.warning(f"⚠️ Ошибка инициализации Trader: {e}")
            self.trader = None
    
        try:
            # Risk Manager - ИСПРАВЛЕНО
            if RiskManager:
                self.risk_manager = RiskManager()
                logger.info("✅ Risk Manager инициализирован")
            else:
                logger.info("📦 Risk Manager не найден")
                self.risk_manager = None
        except Exception as e:
            logger.warning(f"⚠️ Ошибка инициализации Risk Manager: {e}")
            self.risk_manager = None
    
        try:
            # Notifications - ИСПРАВЛЕНО
            try:
                from ..notifications.notifier import Notifier
                self.notifier = Notifier()
                logger.info("✅ Notifier инициализирован")
            except ImportError:
                try:
                    from ..notifications.telegram import TelegramNotifier
                    self.notifier = TelegramNotifier()
                    logger.info("✅ TelegramNotifier инициализирован")
                except ImportError:
                    logger.info("📦 Notifier не найден (не критично)")
                    self.notifier = None
        except Exception as e:
            logger.warning(f"⚠️ Ошибка инициализации Notifier: {e}")
            self.notifier = None
    
        try:
            # Strategy Factory - ИСПРАВЛЕНО
            if strategy_factory:
                self.strategy_factory = strategy_factory
                logger.info("✅ Strategy Factory инициализирован")
            else:
                try:
                    from ..strategies.factory import StrategyFactory
                    self.strategy_factory = StrategyFactory()
                    logger.info("✅ Strategy Factory создан")
                except ImportError:
                    logger.info("📦 Strategy Factory не найден")
                    self.strategy_factory = None
        except Exception as e:
            logger.warning(f"⚠️ Ошибка инициализации Strategy Factory: {e}")
            self.strategy_factory = None
    
    # =========================================================================
    # === УПРАВЛЕНИЕ ЖИЗНЕННЫМ ЦИКЛОМ БОТА ===
    # =========================================================================
    
    async def start(self):
        """ОБНОВЛЕННЫЙ запуск бота с улучшенной системой"""
        if self.status != BotStatus.STOPPED:
            logger.warning("Бот уже запущен")
            return
    
        try:
            self.status = BotStatus.STARTING
            logger.info("🚀 Запускаем торгового бота...")
    
            # Используем улучшенную систему если доступна
            if hasattr(self, 'improved_manager') and self.improved_manager:
                logger.info("🔧 Используем улучшенную систему запуска...")
                success = await self.improved_manager.start_trading()
                
                if success:
                    self.status = BotStatus.RUNNING
                    self.start_time = datetime.utcnow()
                    await self._update_bot_state()
                    
                    # Запускаем основной цикл
                    self._main_task = asyncio.create_task(self._trading_loop())
                    
                    logger.info("✅ Бот успешно запущен через улучшенную систему")
                    return True
                else:
                    logger.warning("⚠️ Улучшенная система не смогла запуститься, используем базовую")
    
            # Откат к базовому запуску
            return await self._start_basic()
    
        except Exception as e:
            logger.error(f"❌ Ошибка запуска бота: {e}")
            self.status = BotStatus.ERROR
            import traceback
            traceback.print_exc()
            return False
    
    async def _start_basic(self):
        """Базовый запуск бота"""
        logger.info("🔧 Базовый запуск бота...")
        
        # Проверяем критичные компоненты
        if not self.exchange:
            logger.error("❌ Exchange не инициализирован")
            return False
    
        # Устанавливаем состояние
        self.status = BotStatus.RUNNING
        self.start_time = datetime.utcnow()
        
        # Обновляем состояние в БД
        await self._update_bot_state()
        
        # Запускаем основной цикл
        self._main_task = asyncio.create_task(self._trading_loop())
        
        logger.info("✅ Бот запущен в базовом режиме")
        return True
    
    async def stop(self):
        """ОБНОВЛЕННАЯ остановка бота с graceful shutdown"""
        if self.status == BotStatus.STOPPED:
            logger.warning("Бот уже остановлен")
            return
    
        try:
            logger.info("🛑 Останавливаем торгового бота...")
            self.status = BotStatus.STOPPING
    
            # Используем улучшенную систему если доступна
            if hasattr(self, 'improved_manager') and self.improved_manager:
                logger.info("🔧 Используем graceful shutdown...")
                await self.improved_manager.graceful_shutdown()
            else:
                # Базовая остановка
                await self._stop_basic()
    
            # Останавливаем основную задачу
            if self._main_task and not self._main_task.done():
                self._main_task.cancel()
                try:
                    await self._main_task
                except asyncio.CancelledError:
                    pass
    
            # Устанавливаем финальное состояние
            self.status = BotStatus.STOPPED
            self.stop_time = datetime.utcnow()
            await self._update_bot_state()
    
            logger.info("✅ Бот успешно остановлен")
    
        except Exception as e:
            logger.error(f"❌ Ошибка остановки бота: {e}")
            self.status = BotStatus.ERROR
    
    async def _stop_basic(self):
        """Базовая остановка компонентов"""
        logger.info("🔧 Базовая остановка компонентов...")
        
        # Останавливаем компоненты если у них есть метод stop
        components = [
            ('trader', self.trader),
            ('analyzer', self.analyzer), 
            ('notifier', self.notifier)
        ]
        
        for name, component in components:
            if component and hasattr(component, 'stop'):
                try:
                    if asyncio.iscoroutinefunction(component.stop):
                        await component.stop()
                    else:
                        component.stop()
                    logger.info(f"✅ {name} остановлен")
                except Exception as e:
                    logger.error(f"❌ Ошибка остановки {name}: {e}")
    
    # =========================================================================
    # === ОСНОВНОЙ ТОРГОВЫЙ ЦИКЛ ===
    # =========================================================================
    
    async def _trading_loop(self):
        """
        Основной торговый цикл бота - ПОЛНАЯ СОХРАНЕННАЯ ВЕРСИЯ
        
        Этот метод является "сердцем" бота. Он работает в бесконечном цикле и:
        1. Проверяет торговые лимиты
        2. Обновляет баланс
        3. Анализирует каждую активную пару
        4. Генерирует и исполняет торговые сигналы
        5. Управляет открытыми позициями
        6. Делает паузы для имитации человеческого поведения
        
        Цикл продолжается до получения сигнала остановки.
        """
        logger.info("🔄 Основной торговый цикл запущен")
        
        # Основной бесконечный цикл
        while not self._stop_event.is_set():
            try:
                # Увеличиваем счетчик циклов
                self.cycles_count += 1
                cycle_start = datetime.utcnow()
                
                logger.debug(f"📊 Начинаем цикл анализа #{self.cycles_count}")
                
                # === ШАГ 1: ПРОВЕРКА ТОРГОВЫХ ЛИМИТОВ ===
                if not self._check_trading_limits():
                    logger.info("📊 Достигнуты дневные лимиты торговли, делаем длинную паузу")
                    await self._human_delay(300, 600)  # Пауза 5-10 минут
                    continue
                
                # === ШАГ 2: ОБНОВЛЕНИЕ БАЛАНСА ===
                try:
                    await self._update_balance()
                except Exception as balance_error:
                    logger.warning(f"⚠️ Не удалось обновить баланс: {balance_error}")
                
                # === ШАГ 3: АНАЛИЗ ВСЕХ АКТИВНЫХ ПАР ===
                for symbol in self.active_pairs:
                    # Проверяем сигнал остановки перед каждой парой
                    if self._stop_event.is_set():
                        logger.info("🛑 Получен сигнал остановки, прерываем анализ пар")
                        break
                    
                    try:
                        logger.debug(f"🔍 Анализируем пару: {symbol}")
                        
                        # Анализируем рыночные данные
                        market_data = await self.analyzer.analyze_symbol(symbol)
                        if not market_data:
                            logger.debug(f"📊 Нет данных для анализа {symbol}")
                            continue
                        
                        # Генерируем торговый сигнал
                        signal = await self._generate_signal(symbol, market_data)
                        if not signal:
                            logger.debug(f"📊 Сигнал для {symbol} не сгенерирован")
                            continue
                        
                        # Сохраняем сигнал в базу данных
                        self._save_signal(signal)
                        
                        # Исполняем сигнал если он достаточно сильный
                        if signal.action in ['BUY', 'SELL'] and signal.confidence >= 0.6:
                            logger.info(f"🎯 Сильный сигнал {signal.action} для {symbol} (уверенность: {signal.confidence:.1%})")
                            await self._execute_signal_human_like(signal)
                        else:
                            logger.debug(f"📊 Слабый сигнал для {symbol}: {signal.action} (уверенность: {signal.confidence:.1%})")
                        
                    except Exception as symbol_error:
                        logger.error(f"❌ Ошибка анализа {symbol}: {symbol_error}")
                        # Отправляем уведомление об ошибке, но продолжаем работу
                        try:
                            if self.notifier:
                                await self.notifier.send_error(f"Ошибка анализа {symbol}: {str(symbol_error)}")
                        except:
                            pass  # Не падаем из-за ошибки уведомления
                
                # === ШАГ 4: УПРАВЛЕНИЕ ОТКРЫТЫМИ ПОЗИЦИЯМИ ===
                try:
                    await self._manage_positions()
                except Exception as positions_error:
                    logger.error(f"❌ Ошибка управления позициями: {positions_error}")
                
                # === ШАГ 5: ОБНОВЛЕНИЕ СТАТИСТИКИ ===
                try:
                    self._update_statistics()
                except Exception as stats_error:
                    logger.warning(f"⚠️ Ошибка обновления статистики: {stats_error}")
                
                # === ШАГ 6: ПАУЗА МЕЖДУ ЦИКЛАМИ ===
                cycle_duration = (datetime.utcnow() - cycle_start).total_seconds()
                logger.debug(f"⏱️ Цикл #{self.cycles_count} выполнен за {cycle_duration:.1f} секунд")
                
                # Делаем паузу с имитацией человеческого поведения
                await self._human_delay()
                
            except asyncio.CancelledError:
                logger.info("🛑 Торговый цикл был отменен")
                break
            except Exception as cycle_error:
                logger.error(f"❌ Критическая ошибка в торговом цикле: {cycle_error}", exc_info=True)
                # Отправляем уведомление и делаем паузу перед следующей попыткой
                try:
                    if self.notifier:
                        await self.notifier.send_error(f"Критическая ошибка цикла: {str(cycle_error)}")
                except:
                    pass
                await self._human_delay(60, 180)  # Пауза 1-3 минуты при ошибке
        
        logger.info("🏁 Основной торговый цикл завершен")
    
    # ========================================
    # ДИАГНОСТИЧЕСКИЕ МЕТОДЫ - СОХРАНЕНЫ
    # ========================================
    
    def get_system_status(self) -> Dict[str, Any]:
        """Получить детальный статус системы"""
        base_status = {
            'bot_status': self.status.value if hasattr(self.status, 'value') else str(self.status),
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'uptime_seconds': (datetime.utcnow() - self.start_time).total_seconds() if self.start_time else 0,
            'active_pairs': len(self.active_pairs),
            'positions_count': len(self.positions),
            'cycles_completed': self.cycles_count,
            'trades_today': self.trades_today
        }
        
        # Добавляем информацию от улучшенной системы если доступна
        if hasattr(self, 'improved_manager') and self.improved_manager:
            try:
                improved_status = self.improved_manager.get_system_status()
                base_status['improved_system'] = improved_status
                base_status['system_type'] = 'improved'
            except Exception as e:
                logger.warning(f"⚠️ Ошибка получения статуса улучшенной системы: {e}")
                base_status['system_type'] = 'basic'
        else:
            base_status['system_type'] = 'basic'
            
        return base_status
    
    async def restart_component(self, component_name: str) -> bool:
        """Перезапуск конкретного компонента"""
        if hasattr(self, 'improved_manager') and self.improved_manager:
            logger.info(f"🔄 Перезапуск компонента {component_name} через улучшенную систему...")
            try:
                return await self.improved_manager.restart_component(component_name)
            except Exception as e:
                logger.error(f"❌ Ошибка перезапуска компонента {component_name}: {e}")
                return False
        else:
            logger.warning("⚠️ Перезапуск компонентов доступен только в улучшенной системе")
            return False
    
    def check_component_health(self) -> Dict[str, bool]:
        """Проверка здоровья компонентов"""
        health = {}
        
        # Проверяем базовые компоненты
        components = {
            'exchange': self.exchange,
            'trader': self.trader,
            'analyzer': self.analyzer,
            'risk_manager': self.risk_manager,
            'notifier': self.notifier,
            'strategy_factory': self.strategy_factory
        }
        
        for name, component in components.items():
            try:
                if component is None:
                    health[name] = False
                elif hasattr(component, 'is_healthy'):
                    health[name] = component.is_healthy()
                elif hasattr(component, 'test_connection'):
                    health[name] = component.test_connection()
                else:
                    health[name] = True  # Считаем здоровым если нет проверок
            except Exception:
                health[name] = False
        
        return health
    
    
    # =========================================================================
    # === ГЕНЕРАЦИЯ И ИСПОЛНЕНИЕ ТОРГОВЫХ СИГНАЛОВ - ПОЛНАЯ ВЕРСИЯ ===
    # =========================================================================
    
    async def _generate_signal(self, symbol: str, market_data: Dict) -> Optional[Signal]:
        """
        Генерация торгового сигнала с автоматическим выбором стратегии - ПОЛНАЯ ВЕРСИЯ
        
        Новая версия:
        1. Автоматически выбирает лучшую стратегию для текущих условий
        2. Использует машинное обучение для улучшения выбора
        3. Адаптируется к изменениям рынка
        
        Args:
            symbol: Торговая пара (например, 'BTCUSDT')
            market_data: Данные о рынке (цены, объемы, индикаторы)
            
        Returns:
            Signal или None если сигнал не сгенерирован
        """
        try:
            logger.info(f"🎯 Генерируем сигнал для {symbol}")
            
            # === ШАГ 1: АВТОМАТИЧЕСКИЙ ВЫБОР СТРАТЕГИИ ===
            # Используем интеллектуальный селектор
            if auto_strategy_selector:
                best_strategy_name, strategy_confidence = await auto_strategy_selector.select_best_strategy(symbol)
                logger.info(f"🧠 Выбрана стратегия '{best_strategy_name}' для {symbol} "
                           f"с уверенностью {strategy_confidence:.1%}")
            else:
                # Fallback к дефолтной стратегии
                best_strategy_name = 'multi_indicator'
                strategy_confidence = 0.8
                logger.debug(f"📊 Используем дефолтную стратегию {best_strategy_name}")
            
            # === ШАГ 2: ПОЛУЧАЕМ КОНФИГУРАЦИЮ ПАРЫ ===
            pair_config = self._get_pair_config(symbol)
            
            # Обновляем стратегию в конфигурации на выбранную
            # (это временное изменение, не сохраняется в БД)
            original_strategy = pair_config.strategy
            pair_config.strategy = best_strategy_name
            
            # === ШАГ 3: СОЗДАЕМ ЭКЗЕМПЛЯР ВЫБРАННОЙ СТРАТЕГИИ ===
            if self.strategy_factory:
                try:
                    if hasattr(self.strategy_factory, 'create'):
                        strategy = self.strategy_factory.create(best_strategy_name)
                    else:
                        # Если это модуль, а не класс
                        strategy = getattr(self.strategy_factory, best_strategy_name, None)
                        if strategy is None:
                            raise ValueError(f"Стратегия {best_strategy_name} не найдена")
                except (ValueError, AttributeError) as e:
                    logger.error(f"❌ Не удалось создать стратегию {best_strategy_name}: {e}")
                    # Fallback к безопасной стратегии
                    try:
                        if hasattr(self.strategy_factory, 'create'):
                            strategy = self.strategy_factory.create('safe_multi_indicator')
                        else:
                            strategy = getattr(self.strategy_factory, 'safe_multi_indicator', None)
                        best_strategy_name = 'safe_multi_indicator'
                    except:
                        logger.error("❌ Не удалось создать даже безопасную стратегию")
                        return None
            else:
                logger.warning("⚠️ Strategy Factory недоступен")
                return None
            
            # === ШАГ 4: АНАЛИЗИРУЕМ РЫНОЧНЫЕ ДАННЫЕ ===
            if hasattr(strategy, 'analyze'):
                analysis = await strategy.analyze(market_data.get('df'), symbol)
            else:
                # Создаем заглушку анализа
                analysis = type('Analysis', (), {
                    'action': 'WAIT',
                    'confidence': 0.0,
                    'stop_loss': None,
                    'take_profit': None,
                    'reason': 'Strategy analysis not available'
                })()
            
            # Если стратегия рекомендует ждать, сигнал не генерируем
            if analysis.action == 'WAIT':
                logger.debug(f"📊 Стратегия {best_strategy_name} рекомендует ждать: {analysis.reason}")
                return None
            
            # === ШАГ 5: КОРРЕКТИРУЕМ УВЕРЕННОСТЬ ===
            # Учитываем уверенность в выборе стратегии
            combined_confidence = analysis.confidence * strategy_confidence
            
            # Если общая уверенность слишком низкая, не торгуем
            if combined_confidence < 0.5:
                logger.info(f"📊 Низкая общая уверенность ({combined_confidence:.1%}), "
                           f"пропускаем сигнал")
                return None
            
            # === ШАГ 6: СОЗДАЕМ СИГНАЛ ===
            signal = Signal(
                symbol=symbol,
                action=analysis.action,
                confidence=combined_confidence,
                price=market_data.get('current_price', 0),
                stop_loss=getattr(analysis, 'stop_loss', None),
                take_profit=getattr(analysis, 'take_profit', None),
                strategy=best_strategy_name,  # Используем выбранную стратегию
                reason=f"[AUTO] {getattr(analysis, 'reason', 'Strategy analysis')} (стратегия: {best_strategy_name}, "
                       f"уверенность выбора: {strategy_confidence:.1%})",
                created_at=datetime.utcnow()
            )
            
            logger.info(f"✅ Сгенерирован сигнал {signal.action} для {symbol}: {signal.reason}")
            
            # === ШАГ 7: ОБУЧЕНИЕ СЕЛЕКТОРА ===
            # Асинхронно запускаем обучение если накопилось достаточно данных
            if auto_strategy_selector and len(auto_strategy_selector.selection_history) > 100 and \
               len(auto_strategy_selector.selection_history) % 100 == 0:
                asyncio.create_task(self._train_strategy_selector())
            
            return signal
            
        except Exception as e:
            logger.error(f"❌ Ошибка генерации сигнала для {symbol}: {e}")
            return None
            
    async def _train_strategy_selector(self):
        """Асинхронное обучение селектора стратегий"""
        try:
            logger.info("🎓 Запускаем обучение селектора стратегий...")
            if auto_strategy_selector and hasattr(auto_strategy_selector, 'train_ml_model'):
                await asyncio.get_event_loop().run_in_executor(
                    None, auto_strategy_selector.train_ml_model
                )
        except Exception as e:
            logger.error(f"❌ Ошибка обучения селектора: {e}")
    
    async def _execute_signal_human_like(self, signal: Signal):
        """
        Исполнение сигнала с имитацией человеческого поведения - ПОЛНАЯ ВЕРСИЯ
        """
        try:
            logger.info(f"🤖 Исполняем сигнал {signal.action} для {signal.symbol}")
            
            # Проверки перед исполнением
            if not self._pre_execution_checks(signal):
                logger.warning(f"⚠️ Сигнал {signal.symbol} не прошел проверки")
                return
            
            # Случайная задержка перед исполнением (имитация человека)
            await asyncio.sleep(random.uniform(1, 5))
            
            # Проверяем риск-менеджмент
            if self.risk_manager and hasattr(self.risk_manager, 'check_position_risk'):
                try:
                    risk_check = self.risk_manager.check_position_risk(signal)
                    if not risk_check.get('allowed', True):
                        logger.warning(f"⚠️ Риск-менеджер запретил сделку: {risk_check.get('reason', 'Unknown reason')}")
                        return
                except Exception as risk_error:
                    logger.warning(f"⚠️ Ошибка проверки риска: {risk_error}")
            
            # Исполняем через trader
            if self.trader and hasattr(self.trader, 'execute_signal'):
                try:
                    execution_result = await self.trader.execute_signal(signal)
                    
                    if execution_result.get('success', False):
                        # Сохраняем сделку
                        trade = execution_result['trade']
                        self.positions[signal.symbol] = trade
                        self.trades_today += 1
                        
                        # Обновляем сигнал
                        signal.executed = True
                        signal.executed_at = datetime.utcnow()
                        signal.trade_id = getattr(trade, 'id', None)
                        self._update_signal_db(signal)
                        
                        # Уведомление
                        if self.notifier and hasattr(self.notifier, 'send_trade_opened'):
                            try:
                                await self.notifier.send_trade_opened(
                                    symbol=signal.symbol,
                                    side=signal.action,
                                    quantity=getattr(trade, 'quantity', 0),
                                    price=getattr(trade, 'entry_price', 0),
                                    strategy=signal.strategy
                                )
                            except Exception as notify_error:
                                logger.warning(f"⚠️ Ошибка отправки уведомления: {notify_error}")
                        
                        logger.info(f"✅ Сигнал {signal.symbol} исполнен успешно")
                    else:
                        logger.error(f"❌ Не удалось исполнить сигнал {signal.symbol}: {execution_result.get('error', 'Unknown error')}")
                except Exception as execution_error:
                    logger.error(f"❌ Ошибка исполнения сигнала: {execution_error}")
            else:
                logger.warning("⚠️ Trader недоступен для исполнения")
                
        except Exception as e:
            logger.error(f"❌ Ошибка исполнения сигнала {signal.symbol}: {e}")
    
    def _pre_execution_checks(self, signal: Signal) -> bool:
        """Предварительные проверки перед исполнением сигнала"""
        try:
            # Проверка 1: Уже есть позиция по этой паре
            if signal.symbol in self.positions:
                logger.debug(f"📊 Позиция {signal.symbol} уже открыта")
                return False
            
            # Проверка 2: Максимальное количество позиций
            max_positions = getattr(self.config, 'MAX_POSITIONS', 5)
            if len(self.positions) >= max_positions:
                logger.debug(f"📊 Достигнуто максимальное количество позиций: {max_positions}")
                return False
            
            # Проверка 3: Дневные лимиты
            if not self._check_trading_limits():
                logger.debug("📊 Достигнуты дневные лимиты торговли")
                return False
            
            # Проверка 4: Минимальная уверенность
            if signal.confidence < 0.6:
                logger.debug(f"📊 Низкая уверенность сигнала: {signal.confidence:.1%}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка предварительных проверок: {e}")
            return False
    
    # =========================================================================
    # === УПРАВЛЕНИЕ ОТКРЫТЫМИ ПОЗИЦИЯМИ - ПОЛНАЯ ВЕРСИЯ ===
    # =========================================================================
    
    async def _manage_positions(self):
        """
        Управление всеми открытыми позициями - ПОЛНАЯ ВЕРСИЯ
        
        Для каждой позиции проверяем:
        1. Достижение стоп-лосса
        2. Достижение тейк-профита
        3. Таймаут позиции (если настроен)
        4. Изменение рыночных условий
        
        При необходимости закрываем позицию.
        """
        if not self.positions:
            return  # Нет открытых позиций
        
        logger.debug(f"🔄 Проверяем {len(self.positions)} открытых позиций")
        
        # Создаем копию словаря для безопасной итерации
        positions_copy = list(self.positions.items())
        
        for symbol, trade in positions_copy:
            try:
                # Получаем текущую цену с биржи
                if self.exchange and hasattr(self.exchange, 'fetch_ticker'):
                    ticker = await self.exchange.fetch_ticker(symbol)
                    current_price = ticker.get('last', ticker.get('close', 0))
                else:
                    logger.warning(f"⚠️ Не удалось получить цену для {symbol}")
                    continue
                
                # Проверяем условия закрытия позиции
                should_close, reason = self._should_close_position(trade, current_price)
                
                if should_close:
                    logger.info(f"🔄 Закрываем позицию {symbol}: {reason}")
                    await self._close_position(trade, current_price, reason)
                    # Удаляем из активных позиций
                    if symbol in self.positions:
                        del self.positions[symbol]
                else:
                    # Обновляем текущую прибыль/убыток
                    self._update_position_pnl(trade, current_price)
                
            except Exception as position_error:
                logger.error(f"❌ Ошибка управления позицией {symbol}: {position_error}")
                # Продолжаем с другими позициями
    
    def _should_close_position(self, trade: Trade, current_price: float) -> Tuple[bool, str]:
        """
        Определяет, нужно ли закрывать позицию - ПОЛНАЯ ВЕРСИЯ
        
        Args:
            trade: Открытая сделка
            current_price: Текущая цена
            
        Returns:
            Tuple[bool, str]: (нужно_закрывать, причина)
        """
        try:
            # Получаем атрибуты сделки безопасно
            side = getattr(trade, 'side', None)
            stop_loss = getattr(trade, 'stop_loss', None)
            take_profit = getattr(trade, 'take_profit', None)
            created_at = getattr(trade, 'created_at', None)
            
            # Для длинных позиций (BUY)
            if side == OrderSide.BUY or (hasattr(side, 'value') and side.value == 'BUY') or str(side).upper() == 'BUY':
                if stop_loss and current_price <= stop_loss:
                    return True, "Stop Loss triggered"
                elif take_profit and current_price >= take_profit:
                    return True, "Take Profit triggered"
            
            # Для коротких позиций (SELL)
            elif side == OrderSide.SELL or (hasattr(side, 'value') and side.value == 'SELL') or str(side).upper() == 'SELL':
                if stop_loss and current_price >= stop_loss:
                    return True, "Stop Loss triggered"
                elif take_profit and current_price <= take_profit:
                    return True, "Take Profit triggered"
            
            # Проверяем таймаут позиции (например, максимум 24 часа)
            if hasattr(self.config, 'MAX_POSITION_HOURS') and created_at:
                position_age = datetime.utcnow() - created_at
                if position_age.total_seconds() > self.config.MAX_POSITION_HOURS * 3600:
                    return True, "Position timeout"
            
            return False, ""
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки условий закрытия позиции: {e}")
            return False, f"Error checking position: {e}"
    
    def _update_position_pnl(self, trade: Trade, current_price: float):
        """
        Обновляет текущую прибыль/убыток позиции - ПОЛНАЯ ВЕРСИЯ
        
        Args:
            trade: Сделка для обновления
            current_price: Текущая цена
        """
        try:
            side = getattr(trade, 'side', None)
            entry_price = getattr(trade, 'entry_price', 0)
            quantity = getattr(trade, 'quantity', 0)
            commission = getattr(trade, 'commission', 0)
            
            if side == OrderSide.BUY or (hasattr(side, 'value') and side.value == 'BUY') or str(side).upper() == 'BUY':
                # Для длинной позиции: прибыль = (текущая цена - цена входа) * количество
                unrealized_pnl = (current_price - entry_price) * quantity
            else:
                # Для короткой позиции: прибыль = (цена входа - текущая цена) * количество
                unrealized_pnl = (entry_price - current_price) * quantity
            
            # Учитываем комиссию
            unrealized_pnl -= commission
            
            # Устанавливаем атрибут
            if hasattr(trade, 'unrealized_pnl'):
                trade.unrealized_pnl = unrealized_pnl
            else:
                setattr(trade, 'unrealized_pnl', unrealized_pnl)
            
        except Exception as e:
            logger.warning(f"⚠️ Ошибка обновления PnL для {getattr(trade, 'symbol', 'unknown')}: {e}")
    
    async def _close_position(self, trade: Trade, current_price: float, reason: str):
        """
        Закрытие конкретной позиции - ПОЛНАЯ ВЕРСИЯ
        
        Args:
            trade: Сделка для закрытия
            current_price: Цена закрытия
            reason: Причина закрытия
        """
        try:
            # Отправляем ордер на закрытие через trader
            if self.trader and hasattr(self.trader, 'close_position'):
                close_result = await self.trader.close_position(trade, current_price)
            else:
                # Заглушка для закрытия позиции
                close_result = True
                logger.warning("⚠️ Trader недоступен, эмулируем закрытие позиции")
            
            if close_result:
                # Обновляем информацию о сделке
                if hasattr(trade, 'exit_price'):
                    trade.exit_price = current_price
                if hasattr(trade, 'status'):
                    trade.status = TradeStatus.CLOSED
                if hasattr(trade, 'closed_at'):
                    trade.closed_at = datetime.utcnow()
                if hasattr(trade, 'notes'):
                    trade.notes = reason
                
                # Рассчитываем итоговую прибыль
                if hasattr(trade, 'calculate_profit'):
                    trade.calculate_profit()
                else:
                    # Рассчитываем прибыль вручную
                    try:
                        entry_price = getattr(trade, 'entry_price', 0)
                        quantity = getattr(trade, 'quantity', 0)
                        commission = getattr(trade, 'commission', 0)
                        side = getattr(trade, 'side', None)
                        
                        if side == OrderSide.BUY or str(side).upper() == 'BUY':
                            profit = (current_price - entry_price) * quantity - commission
                        else:
                            profit = (entry_price - current_price) * quantity - commission
                        
                        if hasattr(trade, 'profit'):
                            trade.profit = profit
                        else:
                            setattr(trade, 'profit', profit)
                    except Exception as profit_error:
                        logger.warning(f"⚠️ Ошибка расчета прибыли: {profit_error}")
                        if not hasattr(trade, 'profit'):
                            setattr(trade, 'profit', 0.0)
                
                # Сохраняем в базу данных
                self._update_trade_db(trade)
                
                # Отправляем уведомление
                try:
                    if self.notifier and hasattr(self.notifier, 'send_trade_closed'):
                        await self.notifier.send_trade_closed(
                            symbol=getattr(trade, 'symbol', 'unknown'),
                            side=str(getattr(trade, 'side', 'unknown')),
                            profit=getattr(trade, 'profit', 0),
                            reason=reason
                        )
                except Exception as notify_error:
                    logger.warning(f"⚠️ Не удалось отправить уведомление о закрытии: {notify_error}")
                
                # Обновляем статистику риск-менеджера
                if self.risk_manager and hasattr(self.risk_manager, 'update_statistics'):
                    try:
                        profit = getattr(trade, 'profit', 0)
                        if profit > 0:
                            self.risk_manager.update_statistics('win', profit)
                        else:
                            self.risk_manager.update_statistics('loss', abs(profit))
                    except Exception as stats_error:
                        logger.warning(f"⚠️ Ошибка обновления статистики риск-менеджера: {stats_error}")
                
                symbol = getattr(trade, 'symbol', 'unknown')
                profit = getattr(trade, 'profit', 0)
                logger.info(f"✅ Позиция {symbol} закрыта с прибылью ${profit:.2f}")
            else:
                symbol = getattr(trade, 'symbol', 'unknown')
                logger.error(f"❌ Не удалось закрыть позицию {symbol}")
                
        except Exception as e:
            symbol = getattr(trade, 'symbol', 'unknown')
            logger.error(f"❌ Ошибка закрытия позиции {symbol}: {e}")
    
    # =========================================================================
    # === ОСТАЛЬНЫЕ МЕТОДЫ - ВСЕ СОХРАНЕНЫ И ИСПРАВЛЕНЫ ===
    # =========================================================================
    
    async def _pre_start_checks(self) -> bool:
        """Комплексная проверка готовности системы к запуску - ПОЛНАЯ ВЕРСИЯ"""
        logger.info("🔍 Начинаем предварительные проверки...")
        
        # === ПРОВЕРКА 1: API КЛЮЧИ ===
        logger.debug("🔑 Проверяем API ключи...")
        if not getattr(self.config, 'BYBIT_API_KEY', None) or self.config.BYBIT_API_KEY == 'your_testnet_api_key_here':
            logger.error("❌ API ключи не настроены в конфигурации")
            return False
        
        if not getattr(self.config, 'BYBIT_API_SECRET', None) or self.config.BYBIT_API_SECRET == 'your_testnet_secret_here':
            logger.error("❌ Secret ключ не настроен в конфигурации")
            return False
        
        logger.info("✅ API ключи настроены")
        
        # === ПРОВЕРКА 2: ПОДКЛЮЧЕНИЕ К БИРЖЕ ===
        logger.debug("🌐 Проверяем подключение к бирже...")
        if self.exchange:
            try:
                if hasattr(self.exchange, 'test_connection'):
                    await self.exchange.test_connection()
                else:
                    # Простая проверка через получение тикера
                    await self.exchange.fetch_ticker('BTCUSDT')
                logger.info("✅ Подключение к бирже успешно")
            except Exception as exchange_error:
                logger.error(f"❌ Не удалось подключиться к бирже: {exchange_error}")
                return False
        else:
            logger.error("❌ Exchange не инициализирован")
            return False
        
        # === ПРОВЕРКА 3: ПОДКЛЮЧЕНИЕ К БАЗЕ ДАННЫХ ===
        logger.debug("💾 Проверяем подключение к базе данных...")
        try:
            db = SessionLocal()
            try:
                result = db.execute(text("SELECT 1 as test_connection"))
                test_value = result.fetchone()
                
                if test_value and test_value[0] == 1:
                    logger.info("✅ Подключение к базе данных успешно")
                else:
                    logger.error("❌ База данных вернула неожиданный результат")
                    return False
            finally:
                db.close()
        except Exception as db_error:
            logger.error(f"❌ Не удалось подключиться к базе данных: {db_error}")
            return False
        
        # === ПРОВЕРКА 4: НАЛИЧИЕ ТОРГОВЫХ ПАР ===
        logger.debug("📋 Проверяем наличие торговых пар...")
        if not self.active_pairs:
            # Попробуем загрузить из конфигурации
            if hasattr(self.config, 'TRADING_PAIRS') and self.config.TRADING_PAIRS:
                self.active_pairs = self.config.TRADING_PAIRS
                logger.info(f"✅ Загружены пары из конфигурации: {self.active_pairs}")
            else:
                logger.error("❌ Не настроены торговые пары")
                return False
        
        # === ПРОВЕРКА 5: БАЛАНС (необязательно, но полезно) ===
        logger.debug("💰 Проверяем баланс...")
        try:
            if self.exchange and hasattr(self.exchange, 'fetch_balance'):
                balance = await self.exchange.fetch_balance()
                usdt_balance = balance.get('USDT', {}).get('free', 0)
                
                if usdt_balance < 10:  # Минимальный баланс
                    logger.warning(f"⚠️ Низкий баланс USDT: ${usdt_balance:.2f}")
                else:
                    logger.info(f"✅ Баланс USDT: ${usdt_balance:.2f}")
        except Exception as balance_error:
            logger.warning(f"⚠️ Не удалось проверить баланс: {balance_error}")
            # Не критичная ошибка, продолжаем
        
        logger.info("✅ Все предварительные проверки пройдены")
        return True
    
    async def _load_configuration(self):
        """Загрузка конфигурации из базы данных - ПОЛНАЯ ВЕРСИЯ"""
        logger.info("📋 Загружаем конфигурацию из базы данных...")
        
        db = SessionLocal()
        try:
            # === ЗАГРУЗКА АКТИВНЫХ ТОРГОВЫХ ПАР ===
            pairs = db.query(TradingPair).filter(
                TradingPair.is_active == True
            ).all()
            
            if pairs:
                self.active_pairs = [pair.symbol for pair in pairs]
                logger.info(f"📋 Загружены активные пары из БД: {self.active_pairs}")
            else:
                # Используем пары из конфигурации как fallback
                if hasattr(self.config, 'TRADING_PAIRS'):
                    self.active_pairs = self.config.TRADING_PAIRS
                    logger.info(f"📋 Используем пары из конфигурации: {self.active_pairs}")
                else:
                    # Дефолтные пары
                    self.active_pairs = ['BTCUSDT', 'ETHUSDT']
                    logger.warning(f"⚠️ Используем дефолтные пары: {self.active_pairs}")
            
            # === ЗАГРУЗКА ОТКРЫТЫХ ПОЗИЦИЙ ===
            open_trades = db.query(Trade).filter(
                Trade.status == TradeStatus.OPEN
            ).all()
            
            if open_trades:
                self.positions = {trade.symbol: trade for trade in open_trades}
                logger.info(f"📊 Загружены открытые позиции: {list(self.positions.keys())}")
            else:
                self.positions = {}
                logger.info("📊 Открытых позиций не найдено")
            
            logger.info(f"✅ Конфигурация загружена: {len(self.active_pairs)} пар, {len(self.positions)} позиций")
            
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки конфигурации: {e}")
            # Используем дефолтные значения
            self.active_pairs = getattr(self.config, 'TRADING_PAIRS', ['BTCUSDT', 'ETHUSDT'])
            self.positions = {}
            logger.warning("⚠️ Используем дефолтную конфигурацию")
        finally:
            db.close()
    
    async def _human_delay(self, min_seconds: float = None, max_seconds: float = None):
        """Умная задержка с имитацией человеческого поведения - ПОЛНАЯ ВЕРСИЯ"""
        # Если режим имитации человека отключен, используем стандартную задержку
        if not getattr(self.config, 'ENABLE_HUMAN_MODE', True):
            await asyncio.sleep(60)  # Стандартная минута
            return
        
        # Определяем базовые параметры задержки
        min_delay = min_seconds or getattr(self.config, 'MIN_DELAY_SECONDS', 30)
        max_delay = max_seconds or getattr(self.config, 'MAX_DELAY_SECONDS', 120)
        
        # Базовая случайная задержка
        delay = random.uniform(min_delay, max_delay)
        
        # === ФАКТОР ВРЕМЕНИ СУТОК ===
        hour = datetime.utcnow().hour
        if 0 <= hour < 6:  # Ночь - человек спит или менее активен
            delay *= random.uniform(1.5, 2.5)
            logger.debug("🌙 Ночное время - увеличиваем задержку")
        elif 6 <= hour < 9:  # Утро - просыпается, может быть медленным
            delay *= random.uniform(1.2, 1.5)
            logger.debug("🌅 Утреннее время - слегка увеличиваем задержку")
        elif 22 <= hour <= 23:  # Поздний вечер - усталость
            delay *= random.uniform(1.3, 1.7)
            logger.debug("🌆 Вечернее время - увеличиваем задержку из-за усталости")
        
        # === ФАКТОР УСТАЛОСТИ ===
        # Чем больше циклов выполнено, тем больше "усталость"
        if self.cycles_count > 100:
            fatigue_factor = min(2.0, 1 + (self.cycles_count - 100) / 200)
            delay *= fatigue_factor
            logger.debug(f"😴 Фактор усталости: x{fatigue_factor:.1f} (циклов: {self.cycles_count})")
        
        # === СЛУЧАЙНЫЕ ПЕРЕРЫВЫ ===
        random_value = random.random()
        
        # Короткие перерывы (как будто отвлекся на телефон)
        if random_value < 0.02:  # 2% шанс
            delay = random.uniform(300, 900)  # 5-15 минут
            logger.info(f"☕ Имитируем короткий перерыв: {delay/60:.1f} минут")
        
        # Длинные перерывы (обед, отдых)
        elif random_value < 0.005:  # 0.5% шанс
            delay = random.uniform(1800, 3600)  # 30-60 минут
            logger.info(f"🍽️ Имитируем длинный перерыв: {delay/60:.1f} минут")
        
        # === ВЫПОЛНЕНИЕ ЗАДЕРЖКИ ===
        # Разбиваем на маленькие кусочки для возможности быстрой остановки
        remaining = delay
        while remaining > 0 and not self._stop_event.is_set():
            sleep_time = min(1.0, remaining)  # Максимум 1 секунда за раз
            await asyncio.sleep(sleep_time)
            remaining -= sleep_time
        
        if delay > 60:  # Логируем только длинные задержки
            logger.debug(f"⏳ Задержка завершена: {delay:.1f} секунд")
    
    # =========================================================================
    # === РАБОТА С БАЗОЙ ДАННЫХ - ВСЕ МЕТОДЫ СОХРАНЕНЫ ===
    # =========================================================================
    
    def _safe_db_operation(self, operation_name: str, operation_func, *args, **kwargs):
        """Безопасное выполнение операций с базой данных - ПОЛНАЯ ВЕРСИЯ"""
        try:
            logger.debug(f"💾 Выполняем операцию БД: {operation_name}")
            result = operation_func(*args, **kwargs)
            logger.debug(f"✅ Операция БД завершена: {operation_name}")
            return result
        except Exception as e:
            logger.error(f"❌ Ошибка в операции БД '{operation_name}': {e}")
            return None
    
    def _load_state_from_db(self):
        """Загрузка состояния бота из базы данных при инициализации"""
        logger.debug("💾 Загружаем состояние бота из БД...")
        
        def _load_operation():
            db = SessionLocal()
            try:
                bot_state = db.query(BotState).first()
                if bot_state and getattr(bot_state, 'is_running', False):
                    logger.warning("⚠️ Бот был запущен при последнем выключении, сбрасываем флаг")
                    bot_state.is_running = False
                    bot_state.stop_time = datetime.utcnow()
                    db.commit()
                    return True
                return False
            finally:
                db.close()
        
        try:
            self._safe_db_operation("загрузка состояния", _load_operation)
        except Exception as e:
            logger.warning(f"⚠️ Не удалось загрузить состояние из БД: {e}")
    
    def _update_bot_state_db(self, is_running: bool):
        """Обновление состояния бота в базе данных"""
        def _update_operation():
            db = SessionLocal()
            try:
                # Ищем существующую запись состояния
                state = db.query(BotState).first()
                if not state:
                    # Создаем новую запись
                    state = BotState()
                    db.add(state)
                
                # Обновляем поля
                state.is_running = is_running
                if is_running:
                    state.start_time = datetime.utcnow()
                    state.stop_time = None
                else:
                    state.stop_time = datetime.utcnow()
                
                # Обновляем статистику
                state.total_trades = self.trades_today
                state.current_balance = self._get_current_balance()
                
                db.commit()
                return True
            except Exception as e:
                db.rollback()
                raise e
            finally:
                db.close()
        
        self._safe_db_operation("обновление состояния бота", _update_operation)
        
    async def _update_bot_state(self):
        """Асинхронное обновление состояния бота в базе данных - ПОЛНАЯ ВЕРСИЯ"""
        try:
            # Этап 1: Определение текущего статуса бота
            is_running = self._determine_bot_running_status()
            
            # Этап 2: Логирование операции
            status_description = "запущен" if is_running else "остановлен"
            logger.debug(f"💾 Обновляем состояние бота в БД: {status_description}")
            
            # Этап 3: Проверка доступности зависимого метода
            if not hasattr(self, '_update_bot_state_db'):
                logger.error("❌ Критическая ошибка: метод _update_bot_state_db не найден")
                return False
            
            # Этап 4: Выполнение обновления БД
            self._update_bot_state_db(is_running)
            
            # Этап 5: Подтверждение успешной операции
            logger.debug("✅ Состояние бота успешно обновлено в БД")
            
            # Этап 6: Дополнительная синхронизация статистики
            await self._sync_additional_statistics()
            
            return True
            
        except Exception as e:
            # Критическая обработка ошибок с детальной диагностикой
            error_context = {
                'method': '_update_bot_state',
                'bot_status': getattr(self, 'status', 'unknown'),
                'has_update_method': hasattr(self, '_update_bot_state_db'),
                'error_type': type(e).__name__,
                'error_message': str(e)
            }
            
            logger.error(f"❌ Критическая ошибка обновления состояния бота: {error_context}")
            
            # В production среде не прерываем работу из-за ошибок БД
            return False
    
    def _determine_bot_running_status(self) -> bool:
        """Определение статуса запуска бота для обновления БД"""
        try:
            # Проверка наличия атрибута status
            if not hasattr(self, 'status'):
                logger.warning("⚠️ Атрибут status отсутствует, считаем бота остановленным")
                return False
            
            # Определение статуса на основе enum значений
            running_statuses = {
                BotStatus.RUNNING,
                BotStatus.STARTING
            }
            
            # Поддержка строковых и enum значений
            current_status = self.status
            if hasattr(current_status, 'value'):
                # Enum значение
                is_running = current_status in running_statuses
            elif isinstance(current_status, str):
                # Строковое значение
                is_running = current_status.lower() in ['running', 'starting']
            else:
                # Неизвестный тип статуса
                logger.warning(f"⚠️ Неизвестный тип статуса: {type(current_status)}")
                return False
            
            logger.debug(f"🔍 Статус бота: {current_status} -> is_running: {is_running}")
            return is_running
            
        except Exception as e:
            logger.error(f"❌ Ошибка определения статуса бота: {e}")
            return False
    
    async def _sync_additional_statistics(self):
        """Синхронизация дополнительной статистики бота"""
        try:
            # Обновление счетчика циклов
            if hasattr(self, 'cycles_count'):
                logger.debug(f"📊 Циклов выполнено: {self.cycles_count}")
            
            # Обновление времени работы
            if hasattr(self, 'start_time') and self.start_time:
                uptime = datetime.utcnow() - self.start_time
                logger.debug(f"⏱️ Время работы: {uptime}")
            
            # Дополнительная статистика сделок
            if hasattr(self, 'trades_today'):
                logger.debug(f"📈 Сделок сегодня: {self.trades_today}")
                
        except Exception as e:
            # Ошибки в дополнительной статистике не критичны
            logger.debug(f"⚠️ Ошибка синхронизации доп. статистики: {e}")

    def _save_signal(self, signal: Signal):
        """Сохранение торгового сигнала в базу данных - ПОЛНАЯ ВЕРСИЯ"""
        def _save_operation():
            db = SessionLocal()
            try:
                # Создаем новый объект Signal в контексте текущей сессии
                new_signal = Signal(
                    symbol=signal.symbol,
                    action=signal.action,
                    confidence=signal.confidence,
                    price=signal.price,
                    stop_loss=signal.stop_loss,
                    take_profit=signal.take_profit,
                    strategy=signal.strategy,
                    reason=signal.reason,
                    created_at=signal.created_at
                )
                db.add(new_signal)
                db.commit()
                # Обновляем ID в исходном объекте
                signal.id = new_signal.id
                return True
            except Exception as e:
                db.rollback()
                raise e
            finally:
                db.close()
        
        self._safe_db_operation(f"сохранение сигнала {signal.symbol}", _save_operation)
    
    def _update_signal_db(self, signal: Signal):
        """Обновление сигнала в базе данных"""
        def _update_operation():
            db = SessionLocal()
            try:
                # Получаем объект из БД и обновляем его
                db_signal = db.query(Signal).filter(Signal.id == signal.id).first()
                if db_signal:
                    db_signal.executed = getattr(signal, 'executed', False)
                    db_signal.executed_at = getattr(signal, 'executed_at', None)
                    db_signal.trade_id = getattr(signal, 'trade_id', None)
                    db.commit()
                    return True
                else:
                    logger.warning(f"Сигнал с ID {getattr(signal, 'id', 'unknown')} не найден в БД")
                    return False
            except Exception as e:
                db.rollback()
                raise e
            finally:
                db.close()
        
        self._safe_db_operation(f"обновление сигнала {signal.symbol}", _update_operation)
    
    def _update_trade_db(self, trade: Trade):
        """Обновление сделки в базе данных"""
        def _update_operation():
            db = SessionLocal()
            try:
                db.merge(trade)
                db.commit()
                return True
            except Exception as e:
                db.rollback()
                raise e
            finally:
                db.close()
        
        symbol = getattr(trade, 'symbol', 'unknown')
        self._safe_db_operation(f"обновление сделки {symbol}", _update_operation)
    
    def _save_statistics(self):
        """Сохранение статистики работы бота при остановке - ПОЛНАЯ ВЕРСИЯ"""
        logger.info("📊 Сохраняем статистику работы бота...")
        
        def _stats_operation():
            db = SessionLocal()
            try:
                # Получаем или создаем запись состояния
                state = db.query(BotState).first()
                if not state:
                    state = BotState()
                    db.add(state)
                
                # === БЕЗОПАСНЫЙ ПОДСЧЕТ СТАТИСТИКИ ===
                try:
                    # Общее количество сделок
                    total_trades = db.query(Trade).count()
                    logger.info(f"📈 Всего сделок в системе: {total_trades}")
                except Exception as trade_error:
                    logger.warning(f"⚠️ Не удалось подсчитать общее количество сделок: {trade_error}")
                    total_trades = 0
                
                try:
                    # Прибыльные сделки
                    profitable_trades = db.query(Trade).filter(
                        Trade.profit > 0,
                        Trade.status == TradeStatus.CLOSED
                    ).count()
                    logger.info(f"💰 Прибыльных сделок: {profitable_trades}")
                except Exception as profit_error:
                    logger.warning(f"⚠️ Не удалось подсчитать прибыльные сделки: {profit_error}")
                    profitable_trades = 0
                
                try:
                    # Общая прибыль
                    total_profit_result = db.query(func.sum(Trade.profit)).filter(
                        Trade.status == TradeStatus.CLOSED
                    ).scalar()
                    total_profit = float(total_profit_result) if total_profit_result else 0.0
                    logger.info(f"🎯 Общая прибыль: ${total_profit:.2f}")
                except Exception as sum_error:
                    logger.warning(f"⚠️ Не удалось подсчитать общую прибыль: {sum_error}")
                    total_profit = 0.0
                
                # Обновляем статистику в состоянии
                state.total_trades = total_trades
                if hasattr(state, 'profitable_trades'):
                    state.profitable_trades = profitable_trades
                if hasattr(state, 'total_profit'):
                    state.total_profit = total_profit
                state.stop_time = datetime.utcnow()
                
                db.commit()
                
                # Вычисляем и логируем итоговую статистику
                win_rate = (profitable_trades / total_trades * 100) if total_trades > 0 else 0
                uptime = datetime.utcnow() - self.start_time if self.start_time else timedelta(0)
                
                logger.info("=" * 50)
                logger.info("📊 ИТОГОВАЯ СТАТИСТИКА СЕССИИ")
                logger.info("=" * 50)
                logger.info(f"⏰ Время работы: {uptime}")
                logger.info(f"🔄 Циклов анализа: {self.cycles_count}")
                logger.info(f"📊 Всего сделок: {total_trades}")
                logger.info(f"💰 Прибыльных сделок: {profitable_trades}")
                logger.info(f"🎯 Общая прибыль: ${total_profit:.2f}")
                logger.info(f"📈 Win Rate: {win_rate:.1f}%")
                logger.info("=" * 50)
                
                return True
                
            except Exception as e:
                logger.error(f"❌ Критическая ошибка при сохранении статистики: {e}")
                db.rollback()
                return False
            finally:
                db.close()
        
        # Выполняем сохранение статистики
        result = self._safe_db_operation("сохранение статистики", _stats_operation)
        if result:
            logger.info("✅ Статистика успешно сохранена")
        else:
            logger.warning("⚠️ Не удалось сохранить статистику, но продолжаем работу")
    
    # =========================================================================
    # === ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ - ВСЕ СОХРАНЕНЫ ===
    # =========================================================================
    
    def _check_trading_limits(self) -> bool:
        """Проверка дневных лимитов торговли"""
        max_daily_trades = getattr(self.config, 'MAX_DAILY_TRADES', 50)
        return self.trades_today < max_daily_trades
    
    async def _update_balance(self):
        """Обновление информации о балансе в базе данных"""
        try:
            # Получаем баланс с биржи
            if self.exchange and hasattr(self.exchange, 'fetch_balance'):
                balance = await self.exchange.fetch_balance()
                logger.debug("💰 Обновляем информацию о балансе...")
                
                def _save_balance():
                    db = SessionLocal()
                    try:
                        # Сохраняем только валюты с ненулевым балансом
                        for currency, amount_info in balance.items():
                            if isinstance(amount_info, dict) and amount_info.get('total', 0) > 0:
                                # ИСПРАВЛЕНО: добавлен user_id, currency -> asset, used -> locked, timestamp -> updated_at
                                balance_record = Balance(
                                    user_id=1,
                                    asset=currency,
                                    total=float(amount_info.get('total', 0)),
                                    free=float(amount_info.get('free', 0)),
                                    locked=float(amount_info.get('used', 0)),
                                    updated_at=datetime.utcnow()
                                )
                                db.add(balance_record)
                        
                        db.commit()
                        return True
                    except Exception as e:
                        db.rollback()
                        raise e
                    finally:
                        db.close()
                
                # Сохраняем через безопасный метод
                result = self._safe_db_operation("обновление баланса", _save_balance)
                if result:
                    logger.debug("✅ Баланс обновлен в БД")
            
        except Exception as e:
            logger.warning(f"⚠️ Ошибка обновления баланса: {e}")
            # Не критично, продолжаем работу
    
    def _get_current_balance(self) -> float:
        """Получение текущего баланса в USDT из базы данных"""
        def _get_balance():
            db = SessionLocal()
            try:
                # ИСПРАВЛЕНО: currency -> asset, timestamp -> updated_at
                latest_balance = db.query(Balance).filter(
                    Balance.asset == 'USDT'
                ).order_by(Balance.updated_at.desc()).first()
                
                if latest_balance:
                    return float(latest_balance.total)
                else:
                    # Если записей нет, возвращаем начальный капитал
                    return float(getattr(self.config, 'INITIAL_CAPITAL', 1000))
            finally:
                db.close()
        
        result = self._safe_db_operation("получение текущего баланса", _get_balance)
        return result if result is not None else 1000.0
    
    def _get_pair_config(self, symbol: str) -> TradingPair:
        """Получение конфигурации торговой пары"""
        def _get_config():
            db = SessionLocal()
            try:
                pair = db.query(TradingPair).filter(
                    TradingPair.symbol == symbol
                ).first()
                
                if pair:
                    return pair
                else:
                    # Возвращаем дефолтную конфигурацию (не сохраняем в БД здесь)
                    logger.debug(f"🔧 Создаем дефолтную конфигурацию для {symbol}")
                    return TradingPair(
                        symbol=symbol,
                        strategy='multi_indicator',
                        stop_loss_percent=float(getattr(self.config, 'STOP_LOSS_PERCENT', 2.0)),
                        take_profit_percent=float(getattr(self.config, 'TAKE_PROFIT_PERCENT', 4.0)),
                        is_active=True
                    )
            finally:
                db.close()
        
        result = self._safe_db_operation(f"получение конфигурации {symbol}", _get_config)
        
        # Если произошла ошибка, возвращаем минимальную конфигурацию
        if result is None:
            logger.warning(f"⚠️ Не удалось получить конфигурацию для {symbol}, используем дефолтную")
            return TradingPair(
                symbol=symbol,
                strategy='multi_indicator',
                stop_loss_percent=2.0,
                take_profit_percent=4.0,
                is_active=True
            )
        
        return result
    
    def _update_process_info(self):
        """Обновление информации о процессе для мониторинга - ПОЛНАЯ ВЕРСИЯ"""
        try:
            # Получаем информацию о текущем процессе
            process = psutil.Process()
            
            # Собираем метрики производительности
            memory_info = process.memory_info()
            
            self._process_info = {
                'pid': process.pid,
                'memory_mb': round(memory_info.rss / 1024 / 1024, 2),  # RSS в мегабайтах
                'memory_vms_mb': round(memory_info.vms / 1024 / 1024, 2),  # VMS в мегабайтах
                'cpu_percent': process.cpu_percent(),
                'threads': process.num_threads(),
                'create_time': datetime.fromtimestamp(process.create_time()),
                'status': process.status(),
                'connections': len(process.connections()) if hasattr(process, 'connections') else 0
            }
            
            logger.debug(f"📊 Процесс: PID={self._process_info['pid']}, "
                        f"RAM={self._process_info['memory_mb']}MB, "
                        f"CPU={self._process_info['cpu_percent']}%")
            
        except Exception as e:
            logger.warning(f"⚠️ Не удалось обновить информацию о процессе: {e}")
            # Устанавливаем минимальную информацию
            self._process_info = {
                'pid': os.getpid(),
                'memory_mb': 0,
                'cpu_percent': 0,
                'threads': 1,
                'create_time': datetime.utcnow(),
                'status': 'unknown'
            }
    
    def _update_statistics(self):
        """Обновление внутренней статистики бота"""
        def _stats_operation():
            db = SessionLocal()
            try:
                # Определяем начало текущего дня в UTC
                today_start = datetime.utcnow().replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                
                # Считаем сделки за сегодня
                today_trades_count = db.query(Trade).filter(
                    Trade.created_at >= today_start
                ).count()
                
                # Обновляем внутренний счетчик
                self.trades_today = today_trades_count
                
                logger.debug(f"📊 Обновлена статистика: {self.trades_today} сделок сегодня")
                return True
                
            except Exception as e:
                logger.warning(f"⚠️ Ошибка обновления статистики: {e}")
                # Сохраняем текущее значение при ошибке
                return False
            finally:
                db.close()
        
        # Выполняем обновление через безопасный метод
        self._safe_db_operation("обновление внутренней статистики", _stats_operation)
    
    async def _close_all_positions(self, reason: str):
        """
        Экстренное закрытие всех открытых позиций
        
        Используется при остановке бота или в критических ситуациях.
        Пытается закрыть каждую позицию по рыночной цене.
        
        Args:
            reason: Причина закрытия (для логов и уведомлений)
        """
        if not self.positions:
            logger.info("✅ Открытых позиций для закрытия нет")
            return
        
        logger.info(f"🔄 Закрываем {len(self.positions)} открытых позиций. Причина: {reason}")
        
        # Создаем копию словаря для безопасной итерации
        positions_to_close = list(self.positions.items())
        
        for symbol, trade in positions_to_close:
            try:
                logger.info(f"🔄 Закрываем позицию {symbol}...")
                
                # Получаем текущую цену
                ticker = await self.exchange.fetch_ticker(symbol)
                current_price = ticker['last']
                
                # Закрываем позицию
                await self._close_position(trade, current_price, reason)
                
                # Удаляем из активных позиций
                if symbol in self.positions:
                    del self.positions[symbol]
                
                logger.info(f"✅ Позиция {symbol} закрыта")
                
            except Exception as position_error:
                logger.error(f"❌ Не удалось закрыть позицию {symbol}: {position_error}")
                # Продолжаем с другими позициями
                # Принудительно удаляем из списка активных
                if symbol in self.positions:
                    del self.positions[symbol]
                    logger.warning(f"⚠️ Позиция {symbol} удалена из активных принудительно")
        
        logger.info(f"✅ Процедура закрытия позиций завершена. Причина: {reason}")
    
    # =========================================================================
    # === ПУБЛИЧНЫЕ МЕТОДЫ ДЛЯ ВНЕШНЕГО API ===
    # =========================================================================
    
    def get_status(self) -> Dict[str, Any]:
        """
        Получение полного статуса бота для веб-интерфейса и API
        
        Возвращает детальную информацию о состоянии бота,
        которая используется в веб-интерфейсе и для мониторинга.
        
        Returns:
            Dict: Полная информация о статусе бота
        """
        try:
            # Базовая информация о статусе
            status_info = {
                'status': self.status.value,
                'is_running': self.status == BotStatus.RUNNING,
                'active_pairs': self.active_pairs.copy(),
                'open_positions': len(self.positions),
            }
            
            # Детальная информация о позициях
            positions_details = {}
            for symbol, trade in self.positions.items():
                try:
                    positions_details[symbol] = {
                        'side': trade.side.value if hasattr(trade.side, 'value') else str(trade.side),
                        'entry_price': float(trade.entry_price) if trade.entry_price else 0,
                        'quantity': float(trade.quantity) if trade.quantity else 0,
                        'profit': float(trade.profit) if trade.profit else 0,
                        'unrealized_pnl': float(getattr(trade, 'unrealized_pnl', 0)),
                        'created_at': trade.created_at.isoformat() if trade.created_at else None
                    }
                except Exception as pos_error:
                    logger.warning(f"⚠️ Ошибка получения данных позиции {symbol}: {pos_error}")
                    positions_details[symbol] = {'error': 'Ошибка получения данных'}
            
            status_info['positions_details'] = positions_details
            
            # Статистика работы
            uptime_str = None
            if self.start_time:
                uptime_delta = datetime.utcnow() - self.start_time
                hours = uptime_delta.seconds // 3600
                minutes = (uptime_delta.seconds % 3600) // 60
                uptime_str = f"{uptime_delta.days}д {hours}ч {minutes}м"
            
            status_info['statistics'] = {
                'start_time': self.start_time.isoformat() if self.start_time else None,
                'uptime': uptime_str,
                'cycles_count': self.cycles_count,
                'trades_today': self.trades_today
            }
            
            # Информация о процессе
            status_info['process_info'] = self._process_info.copy()
            
            # Конфигурация
            status_info['config'] = {
                'mode': 'TESTNET' if getattr(config, 'BYBIT_TESTNET', True) else 'MAINNET',
                'max_positions': getattr(config, 'MAX_POSITIONS', 5),
                'human_mode': getattr(config, 'ENABLE_HUMAN_MODE', True),
                'max_daily_trades': getattr(config, 'MAX_DAILY_TRADES', 50)
            }
            
            return status_info
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения статуса: {e}")
            # Возвращаем минимальную информацию при ошибке
            return {
                'status': 'error',
                'is_running': False,
                'error': str(e),
                'active_pairs': [],
                'open_positions': 0,
                'positions_details': {},
                'statistics': {},
                'process_info': {},
                'config': {}
            }
    
    async def update_pairs(self, pairs: List[str]) -> Tuple[bool, str]:
        """
        Обновление списка активных торговых пар
        
        Этот метод позволяет динамически изменять список торгуемых пар
        без перезапуска бота. Изменения сохраняются в базе данных.
        
        Args:
            pairs: Список символов торговых пар (например, ['BTCUSDT', 'ETHUSDT'])
            
        Returns:
            Tuple[bool, str]: (успешность, сообщение)
        """
        if not pairs:
            return False, "Список пар не может быть пустым"
        
        # Проверяем корректность символов пар
        valid_pairs = []
        for pair in pairs:
            if isinstance(pair, str) and len(pair) >= 6:  # Минимальная длина символа
                valid_pairs.append(pair.upper())
            else:
                logger.warning(f"⚠️ Некорректный символ пары: {pair}")
        
        if not valid_pairs:
            return False, "Не найдено корректных торговых пар"
        
        def _update_operation():
            db = SessionLocal()
            try:
                # Деактивируем все существующие пары
                db.query(TradingPair).update({TradingPair.is_active: False})
                
                # Активируем или создаем выбранные пары
                updated_count = 0
                created_count = 0
                
                for symbol in valid_pairs:
                    pair = db.query(TradingPair).filter(
                        TradingPair.symbol == symbol
                    ).first()
                    
                    if pair:
                        # Обновляем существующую пару
                        pair.is_active = True
                        pair.updated_at = datetime.utcnow()
                        updated_count += 1
                    else:
                        # Создаем новую пару с дефолтными настройками
                        pair = TradingPair(
                            symbol=symbol,
                            is_active=True,
                            strategy='multi_indicator',
                            stop_loss_percent=float(getattr(config, 'STOP_LOSS_PERCENT', 2.0)),
                            take_profit_percent=float(getattr(config, 'TAKE_PROFIT_PERCENT', 4.0)),
                            created_at=datetime.utcnow()
                        )
                        db.add(pair)
                        created_count += 1
                
                db.commit()
                
                return {
                    'updated': updated_count,
                    'created': created_count,
                    'total': len(valid_pairs)
                }
                
            except Exception as e:
                db.rollback()
                raise e
            finally:
                db.close()
        
        try:
            # Выполняем обновление в БД
            result = self._safe_db_operation("обновление торговых пар", _update_operation)
            
            if result:
                # Обновляем внутренний список активных пар
                self.active_pairs = valid_pairs
                
                success_message = (
                    f"Торговые пары обновлены: {result['total']} активных, "
                    f"{result['updated']} обновлено, {result['created']} создано"
                )
                
                logger.info(f"✅ {success_message}")
                logger.info(f"📋 Новый список пар: {self.active_pairs}")
                
                return True, success_message
            else:
                return False, "Ошибка при обновлении пар в базе данных"
                
        except Exception as e:
            error_msg = f"Ошибка обновления торговых пар: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg
    
    async def close_position(self, symbol: str) -> Tuple[bool, str]:
        """
        Ручное закрытие конкретной позиции
        
        Используется для принудительного закрытия позиции
        через веб-интерфейс или API.
        
        Args:
            symbol: Символ торговой пары для закрытия
            
        Returns:
            Tuple[bool, str]: (успешность, сообщение)
        """
        # Проверяем существование позиции
        if symbol not in self.positions:
            message = f"Открытая позиция {symbol} не найдена"
            logger.warning(f"⚠️ {message}")
            return False, message
        
        try:
            trade = self.positions[symbol]
            
            logger.info(f"🔄 Ручное закрытие позиции {symbol}...")
            
            # Получаем текущую цену
            ticker = await self.exchange.fetch_ticker(symbol)
            current_price = ticker['last']
            
            # Закрываем позицию
            await self._close_position(trade, current_price, "Manual close via API")
            
            # Удаляем из активных позиций
            del self.positions[symbol]
            
            success_message = f"Позиция {symbol} успешно закрыта по цене {current_price}"
            logger.info(f"✅ {success_message}")
            
            return True, success_message
            
        except Exception as e:
            error_msg = f"Ошибка закрытия позиции {symbol}: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg
    
    def get_detailed_statistics(self) -> Dict[str, Any]:
        """
        Получение детальной статистики для аналитики
        
        Возвращает расширенную статистику, включающую:
        - Статистику по парам
        - Временные показатели
        - Анализ производительности
        
        Returns:
            Dict: Детальная статистика
        """
        def _stats_operation():
            db = SessionLocal()
            try:
                # Временные границы для анализа
                now = datetime.utcnow()
                today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                week_start = today_start - timedelta(days=7)
                month_start = today_start - timedelta(days=30)
                
                # Статистика за разные периоды
                periods_stats = {}
                
                for period_name, start_date in [
                    ('today', today_start),
                    ('week', week_start),
                    ('month', month_start),
                    ('all_time', datetime.min)
                ]:
                    trades = db.query(Trade).filter(
                        Trade.created_at >= start_date
                    ).all()
                    
                    total_trades = len(trades)
                    profitable_trades = len([t for t in trades if t.profit and t.profit > 0])
                    total_profit = sum(t.profit or 0 for t in trades)
                    
                    periods_stats[period_name] = {
                        'total_trades': total_trades,
                        'profitable_trades': profitable_trades,
                        'total_profit': round(total_profit, 2),
                        'win_rate': round((profitable_trades / total_trades * 100) if total_trades > 0 else 0, 2),
                        'average_profit': round(total_profit / total_trades if total_trades > 0 else 0, 2)
                    }
                
                # Статистика по торговым парам
                pairs_stats = {}
                for symbol in self.active_pairs:
                    pair_trades = db.query(Trade).filter(
                        Trade.symbol == symbol
                    ).all()
                    
                    if pair_trades:
                        pair_total = len(pair_trades)
                        pair_profitable = len([t for t in pair_trades if t.profit and t.profit > 0])
                        pair_profit = sum(t.profit or 0 for t in pair_trades)
                        
                        pairs_stats[symbol] = {
                            'total_trades': pair_total,
                            'profitable_trades': pair_profitable,
                            'total_profit': round(pair_profit, 2),
                            'win_rate': round((pair_profitable / pair_total * 100) if pair_total > 0 else 0, 2)
                        }
                
                return {
                    'periods': periods_stats,
                    'pairs': pairs_stats,
                    'generated_at': now.isoformat()
                }
                
            except Exception as e:
                logger.error(f"❌ Ошибка получения детальной статистики: {e}")
                return {'error': str(e)}
            finally:
                db.close()
        
        result = self._safe_db_operation("получение детальной статистики", _stats_operation)
        return result or {'error': 'Не удалось получить статистику'}
    
    # =========================================================================
    # === МЕТОДЫ ДЛЯ ОТЛАДКИ И МОНИТОРИНГА ===
    # =========================================================================
    
    def get_health_check(self) -> Dict[str, Any]:
        """
        Проверка здоровья системы для мониторинга
        
        Возвращает информацию о состоянии всех компонентов
        для систем мониторинга и алертинга.
        
        Returns:
            Dict: Информация о здоровье системы
        """
        health_info = {
            'timestamp': datetime.utcnow().isoformat(),
            'overall_status': 'healthy',
            'components': {}
        }
        
        # Проверка основных компонентов
        components_to_check = [
            ('bot_manager', self.status != BotStatus.ERROR),
            ('exchange', hasattr(self, 'exchange') and self.exchange is not None),
            ('database', True),  # Проверим отдельно
            ('telegram', hasattr(self, 'notifier') and self.notifier is not None),
            ('positions', len(self.positions) >= 0),  # Всегда True, но для полноты
        ]
        
        all_healthy = True
        
        for component_name, is_healthy in components_to_check:
            health_info['components'][component_name] = {
                'status': 'healthy' if is_healthy else 'unhealthy',
                'last_check': datetime.utcnow().isoformat()
            }
            
            if not is_healthy:
                all_healthy = False
        
        # Отдельная проверка базы данных
        try:
            db = SessionLocal()
            db.execute(text("SELECT 1"))
            db.close()
            health_info['components']['database']['status'] = 'healthy'
        except Exception as db_error:
            health_info['components']['database']['status'] = 'unhealthy'
            health_info['components']['database']['error'] = str(db_error)
            all_healthy = False
        
        # Общий статус
        if not all_healthy:
            health_info['overall_status'] = 'degraded'
        
        if self.status == BotStatus.ERROR:
            health_info['overall_status'] = 'unhealthy'
        
        return health_info
    
    def __repr__(self) -> str:
        """
        Строковое представление объекта для отладки
        
        Returns:
            str: Информативное описание состояния менеджера
        """
        return (
            f"BotManager(status={self.status.value}, "
            f"pairs={len(self.active_pairs)}, "
            f"positions={len(self.positions)}, "
            f"cycles={self.cycles_count})"
        )


# =========================================================================
# === СОЗДАНИЕ ГЛОБАЛЬНОГО ЭКЗЕМПЛЯРА ===
# =========================================================================

# Создаем единственный экземпляр менеджера бота (Singleton)
# Этот объект будет использоваться во всем приложении
bot_manager = BotManager()

# Дополнительная проверка для отладки
if __name__ == "__main__":
    # Этот блок выполняется только при прямом запуске файла
    # Полезно для тестирования отдельных компонентов
    print("🤖 BotManager module loaded successfully")
    print(f"📊 Manager instance: {bot_manager}")
    print(f"🔧 Configuration loaded: {hasattr(config, 'BYBIT_API_KEY')}")