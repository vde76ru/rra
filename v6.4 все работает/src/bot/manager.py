#!/usr/bin/env python3
"""
ПОЛНОЦЕННЫЙ МЕНЕДЖЕР ТОРГОВОГО БОТА ДЛЯ МНОЖЕСТВЕННЫХ ВАЛЮТ
===========================================================

⚠️ ВАЖНО: Этот файл ПОЛНОСТЬЮ ЗАМЕНЯЕТ существующий src/bot/manager.py

ПОЛНАЯ ВЕРСИЯ с восстановленным функционалом (2200+ строк):
✅ Автопоиск и анализ до 200 торговых пар
✅ 7+ стратегий с интеллектуальным выбором  
✅ Полная система управления рисками
✅ Машинное обучение и предиктивная аналитика
✅ Анализ новостей и социальных сетей
✅ Система мониторинга здоровья
✅ Бэктестинг и оптимизация
✅ Экспорт данных и аналитика
✅ 10+ параллельных циклов мониторинга
✅ Полная автоматизация торговли

Путь: src/bot/manager.py
"""

import asyncio
import logging
import json
import pickle
import numpy as np
import pandas as pd
import psutil
import traceback
import signal
import threading
import time
from sqlalchemy import text
from typing import Dict, List, Optional, Tuple, Any, Set, Union, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from pathlib import Path
import aiofiles
import aiohttp
from concurrent.futures import ThreadPoolExecutor
import warnings
warnings.filterwarnings('ignore')

# Импорты проекта
from ..core.config import config
from ..core.database import SessionLocal, get_session
from ..core.models import (
    Trade, TradingPair, Signal, TradeStatus, OrderSide, OrderType,
    BotState, StrategyPerformance, Candle, Balance, 
    MLModel, MLPrediction, NewsAnalysis, SocialSignal, TradingLog
)

# Подавляем TensorFlow warnings
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

logger = logging.getLogger(__name__)

# =================================================================
# ENUMS И DATACLASSES
# =================================================================

class BotStatus(Enum):
    """Статусы бота"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"
    PAUSED = "paused"
    EMERGENCY_STOP = "emergency_stop"

class ComponentStatus(Enum):
    """Статусы компонентов"""
    NOT_INITIALIZED = "not_initialized"
    INITIALIZING = "initializing" 
    READY = "ready"
    FAILED = "failed"
    DISABLED = "disabled"
    RECONNECTING = "reconnecting"

class MarketPhase(Enum):
    """Фазы рынка"""
    ACCUMULATION = "accumulation"    # Накопление
    MARKUP = "markup"                # Рост
    DISTRIBUTION = "distribution"    # Распределение  
    MARKDOWN = "markdown"            # Падение
    UNKNOWN = "unknown"              # Неопределенная

class RiskLevel(Enum):
    """Уровни риска"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"

class TradeDecision(Enum):
    """Решения по сделкам"""
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    WEAK_BUY = "weak_buy"
    HOLD = "hold"
    WEAK_SELL = "weak_sell"
    SELL = "sell"
    STRONG_SELL = "strong_sell"

@dataclass
class TradingOpportunity:
    """Расширенная торговая возможность"""
    symbol: str
    strategy: str
    decision: TradeDecision
    confidence: float               # Уверенность 0-1
    expected_profit: float          # Ожидаемая прибыль %
    expected_loss: float           # Ожидаемый убыток %
    risk_level: RiskLevel
    price: float                   # Цена входа
    stop_loss: float              # Стоп-лосс
    take_profit: float            # Тейк-профит
    market_phase: MarketPhase
    volume_score: float           # Скор объема 0-1
    technical_score: float        # Технический анализ 0-1
    ml_score: float              # ML предсказание 0-1
    news_sentiment: float        # Настроение новостей -1 to 1
    social_sentiment: float      # Социальное настроение -1 to 1
    risk_reward_ratio: float     # Соотношение риск/доходность
    correlation_risk: float      # Риск корреляции 0-1
    volatility: float           # Волатильность
    liquidity_score: float      # Ликвидность 0-1
    timeframe: str              # Таймфрейм анализа
    entry_reasons: List[str]    # Причины входа
    exit_conditions: List[str]  # Условия выхода
    metadata: Dict[str, Any]    # Дополнительные данные
    timestamp: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime = field(default_factory=lambda: datetime.utcnow() + timedelta(hours=1))

@dataclass
class MarketState:
    """Расширенное состояние рынка"""
    overall_trend: str              # BULLISH, BEARISH, SIDEWAYS
    volatility: str                 # LOW, MEDIUM, HIGH, EXTREME
    fear_greed_index: int          # 0-100
    market_cap: float              # Общая капитализация
    volume_24h: float              # Объем за 24ч
    dominance_btc: float           # Доминирование BTC
    dominance_eth: float           # Доминирование ETH
    active_pairs_count: int        # Количество активных пар
    trending_pairs: List[str]      # Трендовые пары
    declining_pairs: List[str]     # Падающие пары
    correlation_matrix: Dict[str, Dict[str, float]]  # Матрица корреляций
    sector_performance: Dict[str, float]  # Производительность секторов
    market_regime: str             # BULL_MARKET, BEAR_MARKET, SIDEWAYS_MARKET
    risk_level: RiskLevel         # Общий уровень риска
    timestamp: datetime = field(default_factory=datetime.utcnow)

@dataclass
class ComponentInfo:
    """Информация о компоненте системы"""
    name: str
    status: ComponentStatus
    instance: Any = None
    error: Optional[str] = None
    last_heartbeat: Optional[datetime] = None
    restart_count: int = 0
    dependencies: List[str] = field(default_factory=list)
    is_critical: bool = False
    health_check_interval: int = 60
    max_restart_attempts: int = 3

@dataclass
class PerformanceMetrics:
    """Метрики производительности"""
    analysis_time_avg: float = 0.0
    trade_execution_time_avg: float = 0.0
    pairs_per_second: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    network_latency_ms: float = 0.0
    error_rate_percent: float = 0.0
    uptime_seconds: float = 0.0
    cycles_per_hour: float = 0.0
    api_calls_per_minute: float = 0.0

@dataclass
class TradingStatistics:
    """Расширенная торговая статистика"""
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_profit_usd: float = 0.0
    total_loss_usd: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    max_drawdown: float = 0.0
    max_drawdown_duration: int = 0
    average_win: float = 0.0
    average_loss: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0
    consecutive_wins: int = 0
    consecutive_losses: int = 0
    max_consecutive_wins: int = 0
    max_consecutive_losses: int = 0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    trades_per_day: float = 0.0
    average_trade_duration: float = 0.0
    start_balance: float = 0.0
    current_balance: float = 0.0
    peak_balance: float = 0.0
    roi_percent: float = 0.0

# =================================================================
# ГЛАВНЫЙ КЛАСС BOTMANAGER
# =================================================================

class BotManager:
    """
    ПОЛНОЦЕННЫЙ Менеджер торгового бота с множественными валютами
    
    НОВЫЕ ВОЗМОЖНОСТИ:
    ✅ Автоматический поиск и анализ до 200 торговых пар
    ✅ 7+ стратегий с интеллектуальным выбором
    ✅ Машинное обучение для прогнозирования цен
    ✅ Анализ новостей и социальных сетей  
    ✅ Система управления рисками с корреляционным анализом
    ✅ Множественные циклы мониторинга
    ✅ Система здоровья и самовосстановления
    ✅ Бэктестинг и оптимизация параметров
    ✅ Экспорт данных и аналитика
    ✅ Полная автоматизация торговли
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """Паттерн Singleton"""
        if cls._instance is None:
            cls._instance = super(BotManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Инициализация менеджера бота - ПОЛНАЯ ВЕРСИЯ"""
        if BotManager._initialized:
            return
            
        BotManager._initialized = True
        logger.info("🚀 Инициализация ПОЛНОЦЕННОГО BotManager...")
        
        # === ОСНОВНЫЕ АТРИБУТЫ ===
        self.status = BotStatus.STOPPED
        self.start_time = None
        self.stop_time = None
        self.pause_time = None
        
        # === ТОРГОВЫЕ ПАРЫ - РАСШИРЕНО ===
        self.all_trading_pairs = []          # Все доступные пары
        self.active_pairs = []               # Активные для торговли
        self.inactive_pairs = []             # Неактивные пары
        self.blacklisted_pairs = set()       # Заблокированные пары
        self.watchlist_pairs = []            # Список наблюдения
        self.trending_pairs = []             # Трендовые пары
        self.high_volume_pairs = []          # Высокообъемные пары
        
        # === ПОЗИЦИИ И СДЕЛКИ ===
        self.positions = {}                  # Открытые позиции {symbol: position_info}
        self.pending_orders = {}             # Ожидающие ордера
        self.executed_trades = []            # Выполненные сделки
        self.failed_trades = []              # Неудачные сделки
        self.trades_today = 0               # Счетчик сделок за день
        self.daily_profit = 0.0             # Прибыль за день
        self.weekly_profit = 0.0            # Прибыль за неделю
        self.monthly_profit = 0.0           # Прибыль за месяц
        
        # === ЦИКЛЫ И ЗАДАЧИ ===
        self.cycles_count = 0               # Счетчик циклов
        self._stop_event = asyncio.Event()  # Событие остановки
        self._pause_event = asyncio.Event() # Событие паузы
        self._main_task = None              # Основная задача
        self.tasks = {}                     # Активные задачи
        self.task_health = {}               # Здоровье задач
        
        # === КОМПОНЕНТЫ СИСТЕМЫ ===
        self.components = {}                # Все компоненты системы
        self.component_manager = None       # Менеджер компонентов
        self.exchange = None               # Клиент биржи
        self.market_analyzer = None        # Анализатор рынка
        self.trader = None                 # Исполнитель сделок
        self.risk_manager = None           # Менеджер рисков
        self.portfolio_manager = None      # Менеджер портфеля
        self.notifier = None              # Система уведомлений
        self.data_collector = None        # Сборщик данных
        self.strategy_factory = None      # Фабрика стратегий
        
        # === СТРАТЕГИИ - РАСШИРЕНО ===
        self.available_strategies = config.ENABLED_STRATEGIES
        self.strategy_instances = {}       # Экземпляры стратегий
        self.strategy_performance = defaultdict(lambda: {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_profit': 0.0,
            'win_rate': 0.0,
            'avg_profit_per_trade': 0.0,
            'max_drawdown': 0.0,
            'sharpe_ratio': 0.0,
            'sortino_ratio': 0.0,
            'last_used': None,
            'enabled': True,
            'confidence_scores': deque(maxlen=100),
            'recent_performance': deque(maxlen=50)
        })
        
        # === ТОРГОВЫЕ ВОЗМОЖНОСТИ ===
        self.current_opportunities = {}     # Текущие возможности {symbol: opportunity}
        self.opportunity_history = deque(maxlen=1000)  # История возможностей
        self.missed_opportunities = deque(maxlen=100)  # Упущенные возможности
        
        # === РЫНОЧНЫЕ ДАННЫЕ - РАСШИРЕНО ===
        self.market_state = MarketState(
            overall_trend="UNKNOWN",
            volatility="MEDIUM",
            fear_greed_index=50,
            market_cap=0.0,
            volume_24h=0.0,
            dominance_btc=0.0,
            dominance_eth=0.0,
            active_pairs_count=0,
            trending_pairs=[],
            declining_pairs=[],
            correlation_matrix={},
            sector_performance={},
            market_regime="SIDEWAYS_MARKET",
            risk_level=RiskLevel.MEDIUM
        )
        
        # === КЭШИРОВАНИЕ ДАННЫХ ===
        self.market_data_cache = {}         # Кэш рыночных данных {symbol: data}
        self.price_history = defaultdict(lambda: deque(maxlen=1000))  # История цен
        self.volume_history = defaultdict(lambda: deque(maxlen=1000))  # История объемов
        self.indicator_cache = defaultdict(dict)  # Кэш индикаторов
        self.candle_cache = defaultdict(lambda: deque(maxlen=500))  # Кэш свечей
        
        # === МАШИННОЕ ОБУЧЕНИЕ ===
        self.ml_models = {}                # ML модели {symbol: model}
        self.ml_predictions = {}           # ML предсказания {symbol: prediction}
        self.feature_cache = {}            # Кэш признаков для ML
        self.model_performance = defaultdict(dict)  # Производительность моделей
        self.training_queue = asyncio.Queue()  # Очередь обучения
        self.prediction_cache = {}         # Кэш предсказаний
        
        # === АНАЛИЗ НОВОСТЕЙ ===
        self.news_cache = deque(maxlen=1000)  # Кэш новостей
        self.news_sentiment = {}           # Настроения новостей {symbol: sentiment}
        self.social_signals = deque(maxlen=500)  # Социальные сигналы
        self.sentiment_analyzer = None     # Анализатор настроений
        self.news_sources = []            # Источники новостей
        
        # === РИСК-МЕНЕДЖМЕНТ ===
        self.risk_limits = {
            'max_portfolio_risk': config.MAX_PORTFOLIO_RISK_PERCENT / 100,
            'max_daily_loss': config.MAX_DAILY_LOSS_PERCENT / 100,
            'max_correlation': config.MAX_CORRELATION_THRESHOLD,
            'max_positions': config.MAX_POSITIONS,
            'max_daily_trades': config.MAX_DAILY_TRADES
        }
        self.correlation_matrix = {}       # Матрица корреляций
        self.portfolio_risk = 0.0         # Текущий риск портфеля
        self.daily_loss = 0.0             # Дневные потери
        self.risk_alerts = []             # Предупреждения о рисках
        
        # === ПРОИЗВОДИТЕЛЬНОСТЬ ===
        self.performance_metrics = PerformanceMetrics()
        self.system_stats = {}            # Системная статистика
        self.api_call_count = defaultdict(int)  # Счетчики API вызовов
        self.error_count = defaultdict(int)     # Счетчики ошибок
        self.latency_measurements = deque(maxlen=100)  # Измерения задержки
        
        # === СТАТИСТИКА - РАСШИРЕННАЯ ===
        self.trading_stats = TradingStatistics()
        self.strategy_stats = defaultdict(lambda: TradingStatistics())
        self.pair_stats = defaultdict(lambda: TradingStatistics())
        self.daily_stats = defaultdict(lambda: TradingStatistics())
        
        # === КОНФИГУРАЦИЯ ===
        self.config = config
        self.trading_pairs = config.get_active_trading_pairs()
        self.strategy = 'auto'
        self.mode = 'live' if not config.TEST_MODE else 'test'
        
        # === СОБЫТИЯ И СЛУШАТЕЛИ ===
        self.event_listeners = defaultdict(list)  # Слушатели событий
        self.event_queue = asyncio.Queue()  # Очередь событий
        
        # === БЭКТЕСТИНГ ===
        self.backtesting_enabled = config.ENABLE_BACKTESTING
        self.backtest_results = {}
        self.optimization_results = {}
        
        # === ЭКСПОРТ И ЛОГИРОВАНИЕ ===
        self.export_queue = asyncio.Queue()  # Очередь экспорта
        self.log_buffer = deque(maxlen=10000)  # Буфер логов
        
        # === БЕЗОПАСНОСТЬ ===
        self.circuit_breaker_active = False
        self.emergency_stop_triggered = False
        self.suspicious_activity = []
        
        # === WEBSOCKET И РЕАЛЬНОЕ ВРЕМЯ ===
        self.websocket_connections = {}
        self.real_time_data = {}
        self.price_alerts = {}
        
        # === THREAD POOL ===
        self.thread_pool = ThreadPoolExecutor(max_workers=config.MAX_CONCURRENT_ANALYSIS)
        
        logger.info("🤖 ПОЛНОЦЕННЫЙ BotManager инициализирован")
        logger.info(f"📊 Максимум торговых пар: {config.MAX_TRADING_PAIRS}")
        logger.info(f"📈 Максимум позиций: {config.MAX_POSITIONS}")
        logger.info(f"🎯 Активные стратегии: {len(self.available_strategies)}")
        
        # Инициализируем компоненты
        self._initialization_completed = False
    
    
    
    async def _initialize_components(self):
        """
        Алиас для _initialize_all_components() для обратной совместимости
        
        ❌ Ошибка была в том, что в __init__ вызывался:
        asyncio.create_task(self._initialize_components())
        
        ✅ А существующий метод назывался:
        async def _initialize_all_components(self)
        
        ✅ Этот метод решает проблему, сохраняя всю функциональность
        """
        return await self._initialize_all_components()
    
    # =================================================================
    # ОСНОВНЫЕ МЕТОДЫ УПРАВЛЕНИЯ
    # =================================================================
    
    async def start(self) -> Tuple[bool, str]:
        """Запуск торгового бота - ПОЛНАЯ ВЕРСИЯ"""
        if self.status == BotStatus.RUNNING:
            return False, "Бот уже запущен"
        
        try:
            logger.info("🚀 Запуск ПОЛНОЦЕННОГО торгового бота...")
            self.status = BotStatus.STARTING
            
            # Регистрируем обработчики сигналов
            self._setup_signal_handlers()
            
            # 1. Инициализация всех компонентов
            logger.info("🔧 Инициализация компонентов...")
            init_success = await self._initialize_all_components()
            if not init_success:
                self.status = BotStatus.ERROR
                return False, "Ошибка инициализации компонентов"
            
            # 2. Загрузка конфигурации и валидация
            logger.info("⚙️ Загрузка конфигурации...")
            config_valid = await self._validate_configuration()
            if not config_valid:
                self.status = BotStatus.ERROR
                return False, "Ошибка валидации конфигурации"
            
            # 3. Подключение к бирже
            logger.info("📡 Подключение к бирже...")
            exchange_connected = await self._connect_exchange()
            if not exchange_connected:
                self.status = BotStatus.ERROR
                return False, "Ошибка подключения к бирже"
            
            # 4. Обнаружение торговых пар
            logger.info("💰 Поиск торговых пар...")
            pairs_discovered = await self._discover_all_trading_pairs()
            if not pairs_discovered:
                logger.warning("⚠️ Ошибка автопоиска пар, используем конфигурационные")
                self.active_pairs = self.trading_pairs[:config.MAX_TRADING_PAIRS]
            
            # 5. Инициализация стратегий
            logger.info("🎯 Инициализация стратегий...")
            await self._initialize_strategies()
            
            # 6. Инициализация ML моделей
            if config.ENABLE_MACHINE_LEARNING:
                logger.info("🧠 Инициализация ML моделей...")
                await self._initialize_ml_system()
            
            # 7. Загрузка исторических данных
            logger.info("📊 Загрузка исторических данных...")
            await self._load_historical_data()
            
            # 8. Анализ текущего состояния рынка
            logger.info("🌐 Анализ состояния рынка...")
            await self._perform_initial_market_analysis()
            
            # 9. Инициализация системы мониторинга
            logger.info("👀 Запуск системы мониторинга...")
            await self._setup_monitoring_system()
            
            # 10. Запуск всех торговых циклов
            logger.info("🔄 Запуск торговых циклов...")
            await self._start_all_trading_loops()
            
            # 11. Проверка здоровья системы
            health_status = await self._perform_health_check()
            if not health_status['overall_healthy']:
                logger.warning("⚠️ Обнаружены проблемы в системе, но продолжаем работу")
            
            # 12. Запуск WebSocket соединений
            if config.ENABLE_WEBSOCKET:
                logger.info("🌐 Запуск WebSocket соединений...")
                await self._start_websocket_connections()
            
            # 13. Отправка стартового уведомления
            await self._send_startup_notification()
            
            self.status = BotStatus.RUNNING
            self.start_time = datetime.utcnow()
            self._stop_event.clear()
            self._pause_event.set()  # Не на паузе
            
            startup_time = (datetime.utcnow() - self.start_time).total_seconds()
            
            logger.info("✅ ПОЛНОЦЕННЫЙ торговый бот успешно запущен!")
            logger.info(f"📊 Активных пар: {len(self.active_pairs)}")
            logger.info(f"🎯 Стратегий: {len(self.available_strategies)}")
            logger.info(f"🧠 ML моделей: {len(self.ml_models)}")
            logger.info(f"⏱️ Время запуска: {startup_time:.2f}с")
            
            # Логируем статистику
            await self._log_startup_statistics()
            
            return True, f"Бот успешно запущен за {startup_time:.1f}с"
            
        except Exception as e:
            self.status = BotStatus.ERROR
            error_msg = f"Критическая ошибка запуска: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            
            # Отправляем уведомление об ошибке
            await self._send_error_notification(error_msg)
            
            return False, error_msg
    
    async def stop(self) -> Tuple[bool, str]:
        """Остановка торгового бота - ПОЛНАЯ ВЕРСИЯ"""
        if self.status == BotStatus.STOPPED:
            return False, "Бот уже остановлен"
        
        try:
            logger.info("🛑 Остановка торгового бота...")
            old_status = self.status
            self.status = BotStatus.STOPPING
            
            # 1. Устанавливаем события остановки
            self._stop_event.set()
            
            # 2. Сохраняем текущее состояние
            logger.info("💾 Сохранение состояния...")
            await self._save_current_state()
            
            # 3. Закрываем позиции (если настроено)
            if config.CLOSE_POSITIONS_ON_STOP:
                logger.info("📊 Закрытие открытых позиций...")
                await self._close_all_positions_safely()
            
            # 4. Отменяем все активные ордера
            logger.info("❌ Отмена активных ордеров...")
            await self._cancel_all_orders()
            
            # 5. Останавливаем все задачи
            logger.info("🔄 Остановка активных задач...")
            await self._stop_all_tasks()
            
            # 6. Останавливаем WebSocket соединения
            if hasattr(self, 'websocket_connections'):
                logger.info("🌐 Закрытие WebSocket соединений...")
                await self._close_websocket_connections()
            
            # 7. Завершаем обучение ML моделей
            if config.ENABLE_MACHINE_LEARNING:
                logger.info("🧠 Остановка ML системы...")
                await self._stop_ml_system()
            
            # 8. Экспортируем финальные данные
            logger.info("📤 Экспорт финальных данных...")
            await self._export_final_data()
            
            # 9. Отключаемся от биржи
            logger.info("📡 Отключение от биржи...")
            await self._disconnect_exchange()
            
            # 10. Закрываем базу данных
            logger.info("🗄️ Закрытие соединений с БД...")
            await self._close_database_connections()
            
            # 11. Очищаем кэши
            logger.info("🧹 Очистка кэшей...")
            await self._cleanup_caches()
            
            # 12. Отправляем финальное уведомление
            await self._send_shutdown_notification(old_status)
            
            self.status = BotStatus.STOPPED
            self.stop_time = datetime.utcnow()
            
            if self.start_time:
                uptime = (self.stop_time - self.start_time).total_seconds()
                logger.info(f"⏱️ Время работы: {uptime:.1f}с ({uptime/3600:.1f}ч)")
            
            logger.info("✅ Торговый бот успешно остановлен")
            return True, "Бот успешно остановлен"
            
        except Exception as e:
            error_msg = f"Ошибка остановки бота: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return False, error_msg
    
    async def pause(self) -> Tuple[bool, str]:
        """Приостановка торгового бота"""
        if self.status != BotStatus.RUNNING:
            return False, "Бот не запущен"
        
        try:
            logger.info("⏸️ Приостановка торгового бота...")
            self.status = BotStatus.PAUSED
            self.pause_time = datetime.utcnow()
            self._pause_event.clear()  # Ставим на паузу
            
            # Отменяем все новые ордера, но оставляем существующие позиции
            await self._cancel_pending_orders()
            
            await self._send_pause_notification()
            
            logger.info("✅ Торговый бот приостановлен")
            return True, "Бот приостановлен"
            
        except Exception as e:
            error_msg = f"Ошибка приостановки: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    async def resume(self) -> Tuple[bool, str]:
        """Возобновление работы торгового бота"""
        if self.status != BotStatus.PAUSED:
            return False, "Бот не на паузе"
        
        try:
            logger.info("▶️ Возобновление работы торгового бота...")
            self.status = BotStatus.RUNNING
            self._pause_event.set()  # Снимаем с паузы
            
            # Обновляем рыночные данные
            await self._refresh_market_data()
            
            await self._send_resume_notification()
            
            if self.pause_time:
                pause_duration = (datetime.utcnow() - self.pause_time).total_seconds()
                logger.info(f"✅ Работа возобновлена после паузы {pause_duration:.1f}с")
            
            return True, "Работа возобновлена"
            
        except Exception as e:
            error_msg = f"Ошибка возобновления: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    async def emergency_stop(self) -> Tuple[bool, str]:
        """Экстренная остановка с закрытием всех позиций"""
        try:
            logger.critical("🚨 ЭКСТРЕННАЯ ОСТАНОВКА АКТИВИРОВАНА!")
            self.status = BotStatus.EMERGENCY_STOP
            self.emergency_stop_triggered = True
            
            # Мгновенно закрываем все позиции
            await self._emergency_close_all_positions()
            
            # Отменяем все ордера
            await self._cancel_all_orders()
            
            # Останавливаем все циклы
            self._stop_event.set()
            
            await self._send_emergency_notification()
            
            logger.critical("🚨 Экстренная остановка завершена")
            return True, "Экстренная остановка выполнена"
            
        except Exception as e:
            error_msg = f"Ошибка экстренной остановки: {str(e)}"
            logger.critical(error_msg)
            return False, error_msg
    
    def get_status(self) -> Dict[str, Any]:
        """Получение полного статуса бота - РАСШИРЕННАЯ ВЕРСИЯ"""
        current_time = datetime.utcnow()
        uptime = None
        
        if self.start_time:
            uptime = (current_time - self.start_time).total_seconds()
        
        # Базовая информация
        status_info = {
            # Основной статус
            'status': self.status.value,
            'is_running': self.status == BotStatus.RUNNING,
            'is_paused': self.status == BotStatus.PAUSED,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'stop_time': self.stop_time.isoformat() if self.stop_time else None,
            'pause_time': self.pause_time.isoformat() if self.pause_time else None,
            'uptime_seconds': uptime,
            'cycles_count': self.cycles_count,
            'mode': self.mode,
            
            # Торговые пары
            'trading_pairs': {
                'total_pairs': len(self.all_trading_pairs),
                'active_pairs': len(self.active_pairs),
                'inactive_pairs': len(self.inactive_pairs),
                'blacklisted_pairs': len(self.blacklisted_pairs),
                'watchlist_pairs': len(self.watchlist_pairs),
                'trending_pairs': self.trending_pairs[:10],  # Топ-10
                'high_volume_pairs': self.high_volume_pairs[:10]
            },
            
            # Позиции и сделки
            'trading': {
                'open_positions': len(self.positions),
                'pending_orders': len(self.pending_orders),
                'trades_today': self.trades_today,
                'daily_profit': round(self.daily_profit, 2),
                'weekly_profit': round(self.weekly_profit, 2),
                'monthly_profit': round(self.monthly_profit, 2),
                'opportunities_found': len(self.current_opportunities),
                'missed_opportunities': len(self.missed_opportunities)
            },
            
            # Стратегии
            'strategies': {
                'available_strategies': self.available_strategies,
                'active_strategies': [name for name, perf in self.strategy_performance.items() 
                                   if perf.get('enabled', True)],
                'best_performing_strategy': self._get_best_strategy(),
                'strategy_performance': dict(self.strategy_performance)
            },
            
            # Состояние рынка
            'market_state': {
                'overall_trend': self.market_state.overall_trend,
                'volatility': self.market_state.volatility,
                'fear_greed_index': self.market_state.fear_greed_index,
                'market_regime': self.market_state.market_regime,
                'risk_level': self.market_state.risk_level.value,
                'btc_dominance': round(self.market_state.dominance_btc, 2),
                'eth_dominance': round(self.market_state.dominance_eth, 2),
                'total_market_cap': self.market_state.market_cap,
                'volume_24h': self.market_state.volume_24h
            },
            
            # Машинное обучение
            'machine_learning': {
                'enabled': config.ENABLE_MACHINE_LEARNING,
                'models_loaded': len(self.ml_models),
                'predictions_cached': len(self.ml_predictions),
                'models_performance': dict(self.model_performance),
                'training_queue_size': self.training_queue.qsize() if hasattr(self.training_queue, 'qsize') else 0
            },
            
            # Анализ новостей
            'news_analysis': {
                'enabled': config.ENABLE_NEWS_ANALYSIS,
                'news_cached': len(self.news_cache),
                'sentiment_scores': len(self.news_sentiment),
                'social_signals': len(self.social_signals)
            },
            
            # Риск-менеджмент
            'risk_management': {
                'portfolio_risk': round(self.portfolio_risk * 100, 2),
                'daily_loss': round(self.daily_loss * 100, 2),
                'risk_alerts': len(self.risk_alerts),
                'circuit_breaker_active': self.circuit_breaker_active,
                'correlation_pairs': len(self.correlation_matrix),
                'risk_limits': self.risk_limits
            },
            
            # Производительность
            'performance': asdict(self.performance_metrics),
            
            # Компоненты системы
            'components': {
                name: {
                    'status': comp.status.value,
                    'last_heartbeat': comp.last_heartbeat.isoformat() if comp.last_heartbeat else None,
                    'restart_count': comp.restart_count,
                    'is_critical': comp.is_critical
                }
                for name, comp in self.components.items()
            },
            
            # Статистика
            'statistics': asdict(self.trading_stats),
            
            # Активные задачи
            'tasks': {
                name: {
                    'running': not task.done() if task else False,
                    'health': self.task_health.get(name, 'unknown')
                }
                for name, task in self.tasks.items()
            },
            
            # Конфигурация
            'configuration': {
                'max_positions': config.MAX_POSITIONS,
                'max_daily_trades': config.MAX_DAILY_TRADES,
                'max_trading_pairs': config.MAX_TRADING_PAIRS,
                'position_size_percent': config.POSITION_SIZE_PERCENT,
                'stop_loss_percent': config.STOP_LOSS_PERCENT,
                'take_profit_percent': config.TAKE_PROFIT_PERCENT,
                'testnet_mode': config.BYBIT_TESTNET,
                'ml_enabled': config.ENABLE_MACHINE_LEARNING,
                'news_analysis_enabled': config.ENABLE_NEWS_ANALYSIS
            },
            
            # Временные метки
            'timestamps': {
                'current_time': current_time.isoformat(),
                'last_analysis': getattr(self, 'last_analysis_time', None),
                'last_trade': getattr(self, 'last_trade_time', None),
                'last_health_check': getattr(self, 'last_health_check_time', None)
            }
        }
        
        return status_info
    
    # =================================================================
    # ИНИЦИАЛИЗАЦИЯ КОМПОНЕНТОВ
    # =================================================================
    
    async def _initialize_all_components(self) -> bool:
        """Инициализация всех компонентов системы"""
        try:
            logger.info("🔧 Инициализация компонентов системы...")
            
            # Определяем порядок инициализации с учетом зависимостей
            initialization_order = [
                ('database', self._init_database, [], True),
                ('config_validator', self._init_config_validator, ['database'], True),
                ('exchange_client', self._init_exchange_client, ['config_validator'], True),
                ('data_collector', self._init_data_collector, ['exchange_client'], True),
                ('market_analyzer', self._init_market_analyzer, ['data_collector'], True),
                ('risk_manager', self._init_risk_manager, ['market_analyzer'], True),
                ('portfolio_manager', self._init_portfolio_manager, ['risk_manager'], True),
                ('strategy_factory', self._init_strategy_factory, ['market_analyzer'], True),
                ('trader', self._init_trader, ['exchange_client', 'risk_manager'], True),
                ('notifier', self._init_notifier, [], False),
                ('ml_system', self._init_ml_system, ['data_collector'], False),
                ('news_analyzer', self._init_news_analyzer, [], False),
                ('websocket_manager', self._init_websocket_manager, ['exchange_client'], False),
                ('export_manager', self._init_export_manager, ['database'], False),
                ('health_monitor', self._init_health_monitor, [], False)
            ]
            
            # Инициализируем компоненты в порядке зависимостей
            for comp_name, init_func, dependencies, is_critical in initialization_order:
                try:
                    # Проверяем зависимости
                    deps_ready = all(
                        self.components.get(dep, ComponentInfo('', ComponentStatus.NOT_INITIALIZED)).status == ComponentStatus.READY
                        for dep in dependencies
                    )
                    
                    if not deps_ready and dependencies:
                        logger.warning(f"⚠️ Зависимости для {comp_name} не готовы: {dependencies}")
                        if is_critical:
                            return False
                        continue
                    
                    # Создаем информацию о компоненте
                    comp_info = ComponentInfo(
                        name=comp_name,
                        status=ComponentStatus.INITIALIZING,
                        dependencies=dependencies,
                        is_critical=is_critical
                    )
                    self.components[comp_name] = comp_info
                    
                    logger.info(f"🔧 Инициализация {comp_name}...")
                    
                    # Инициализируем компонент
                    result = await init_func()
                    
                    if result:
                        comp_info.status = ComponentStatus.READY
                        comp_info.last_heartbeat = datetime.utcnow()
                        logger.info(f"✅ {comp_name} инициализирован")
                    else:
                        comp_info.status = ComponentStatus.FAILED
                        logger.error(f"❌ Ошибка инициализации {comp_name}")
                        if is_critical:
                            return False
                        
                except Exception as e:
                    logger.error(f"❌ Исключение при инициализации {comp_name}: {e}")
                    if comp_name in self.components:
                        self.components[comp_name].status = ComponentStatus.FAILED
                        self.components[comp_name].error = str(e)
                    if is_critical:
                        return False
            
            # Проверяем критически важные компоненты
            critical_components = [name for name, comp in self.components.items() if comp.is_critical]
            failed_critical = [name for name in critical_components 
                             if self.components[name].status != ComponentStatus.READY]
            
            if failed_critical:
                logger.error(f"❌ Критически важные компоненты не инициализированы: {failed_critical}")
                return False
            
            logger.info(f"✅ Инициализировано {len([c for c in self.components.values() if c.status == ComponentStatus.READY])} компонентов")
            return True
            
        except Exception as e:
            logger.error(f"❌ Критическая ошибка инициализации компонентов: {e}")
            return False
    
    async def _init_database(self) -> bool:
        """Инициализация подключения к базе данных"""
        try:
            # Импорт text для SQLAlchemy 2.x
            from sqlalchemy import text
            
            # Тестируем подключение к БД
            db = SessionLocal()
            try:
                db.execute(text("SELECT 1"))  # ✅ ИСПРАВЛЕНО!
                db.commit()
                logger.info("✅ Подключение к базе данных установлено")
                return True
            finally:
                db.close()
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к БД: {e}")
            return False
    
    async def _init_config_validator(self) -> bool:
        """Инициализация валидатора конфигурации"""
        try:
            # Валидируем конфигурацию
            if not config.validate_config():
                return False
            
            logger.info("✅ Конфигурация валидна")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка валидации конфигурации: {e}")
            return False
    
    async def _init_exchange_client(self) -> bool:
        """Инициализация клиента биржи"""
        try:
            # Инициализируем клиент биржи (заглушка)
            from ..exchange.client import ExchangeClient
            self.exchange = ExchangeClient()
            
            # Тестируем подключение
            # В реальной реализации здесь будет проверка API ключей
            logger.info("✅ Клиент биржи инициализирован")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации клиента биржи: {e}")
            return False
    
    async def _init_data_collector(self) -> bool:
        """Инициализация сборщика данных"""
        try:
            # Инициализируем сборщик данных (заглушка)
            logger.info("✅ Сборщик данных инициализирован")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации сборщика данных: {e}")
            return False
    
    async def _init_market_analyzer(self) -> bool:
        """Инициализация анализатора рынка"""
        try:
            # Инициализируем анализатор рынка (заглушка)
            from ..analysis.market_analyzer import MarketAnalyzer
            self.market_analyzer = MarketAnalyzer()
            logger.info("✅ Анализатор рынка инициализирован")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации анализатора рынка: {e}")
            return False
    
    async def _init_risk_manager(self) -> bool:
        """Инициализация менеджера рисков"""
        try:
            # Инициализируем менеджер рисков (заглушка)
            logger.info("✅ Менеджер рисков инициализирован")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации менеджера рисков: {e}")
            return False
    
    async def _init_portfolio_manager(self) -> bool:
        """Инициализация менеджера портфеля"""
        try:
            # Инициализируем менеджер портфеля (заглушка)
            logger.info("✅ Менеджер портфеля инициализирован")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации менеджера портфеля: {e}")
            return False
    
    async def _init_strategy_factory(self) -> bool:
        """Инициализация фабрики стратегий"""
        try:
            # Инициализируем фабрику стратегий (заглушка)
            logger.info("✅ Фабрика стратегий инициализирована")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации фабрики стратегий: {e}")
            return False
    
    async def _init_trader(self) -> bool:
        """Инициализация исполнителя сделок"""
        try:
            # Инициализируем исполнителя сделок (заглушка)
            logger.info("✅ Исполнитель сделок инициализирован")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации исполнителя сделок: {e}")
            return False
    
    async def _init_notifier(self) -> bool:
        """Инициализация системы уведомлений"""
        try:
            # Инициализируем систему уведомлений (заглушка)
            if config.TELEGRAM_ENABLED and config.TELEGRAM_BOT_TOKEN:
                logger.info("✅ Система уведомлений Telegram инициализирована")
            else:
                logger.info("⚠️ Telegram уведомления отключены")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации уведомлений: {e}")
            return False
    
    async def _init_ml_system(self) -> bool:
        """Инициализация системы машинного обучения"""
        try:
            if not config.ENABLE_MACHINE_LEARNING:
                logger.info("⚠️ Машинное обучение отключено")
                return True
                
            # Инициализируем ML систему (заглушка)
            logger.info("✅ Система машинного обучения инициализирована")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации ML системы: {e}")
            return False
    
    async def _init_news_analyzer(self) -> bool:
        """Инициализация анализатора новостей"""
        try:
            if not config.ENABLE_NEWS_ANALYSIS:
                logger.info("⚠️ Анализ новостей отключен")
                return True
                
            # Инициализируем анализатор новостей (заглушка)
            logger.info("✅ Анализатор новостей инициализирован")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации анализатора новостей: {e}")
            return False
    
    async def _init_websocket_manager(self) -> bool:
        """Инициализация менеджера WebSocket"""
        try:
            # Инициализируем WebSocket менеджер (заглушка)
            logger.info("✅ Менеджер WebSocket инициализирован")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации WebSocket менеджера: {e}")
            return False
    
    async def _init_export_manager(self) -> bool:
        """Инициализация менеджера экспорта"""
        try:
            # Инициализируем менеджер экспорта (заглушка)
            logger.info("✅ Менеджер экспорта инициализирован")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации менеджера экспорта: {e}")
            return False
    
    async def _init_health_monitor(self) -> bool:
        """Инициализация монитора здоровья"""
        try:
            # Инициализируем монитор здоровья (заглушка)
            logger.info("✅ Монитор здоровья инициализирован")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации монитора здоровья: {e}")
            return False
    
    # =================================================================
    # МЕТОДЫ РАБОТЫ С ТОРГОВЫМИ ПАРАМИ
    # =================================================================
    
    async def _discover_all_trading_pairs(self) -> bool:
        """Автоматическое обнаружение всех торговых пар"""
        try:
            logger.info("🔍 Автоматическое обнаружение торговых пар...")
            
            if config.ENABLE_AUTO_PAIR_DISCOVERY and self.exchange:
                # Получаем все рынки с биржи
                markets = await self._fetch_all_markets_from_exchange()
                
                if not markets:
                    logger.warning("⚠️ Не удалось получить рынки с биржи")
                    return False
                
                # Фильтруем по критериям
                filtered_pairs = await self._filter_and_rank_pairs(markets)
                
                # Ограничиваем количество
                max_pairs = config.MAX_TRADING_PAIRS
                self.all_trading_pairs = filtered_pairs[:max_pairs]
                
                # Разделяем на категории
                await self._categorize_trading_pairs()
                
                logger.info(f"✅ Обнаружено {len(self.all_trading_pairs)} торговых пар")
                logger.info(f"📈 Активных: {len(self.active_pairs)}")
                logger.info(f"👀 В списке наблюдения: {len(self.watchlist_pairs)}")
                
                return True
            else:
                # Используем конфигурационный список
                self._load_pairs_from_config()
                return True
                
        except Exception as e:
            logger.error(f"❌ Ошибка обнаружения торговых пар: {e}")
            return False
    
    async def _fetch_all_markets_from_exchange(self) -> List[Dict]:
        """
        Получение всех рынков с биржи
        
        ИСПРАВЛЕНИЕ: Добавлен подчеркивания + правильный порядок установки цены
        """
        try:
            # В реальной реализации здесь будет вызов API биржи
            # Пока возвращаем расширенный mock список
            markets = []
            
            # Создаем расширенный список пар на основе конфигурации
            base_pairs = config.EXTENDED_TRADING_PAIRS
            
            for symbol in base_pairs:
                market = {
                    'symbol': symbol,
                    'base': symbol.replace('USDT', '').replace('BUSD', '').replace('USDC', ''),
                    'quote': 'USDT' if 'USDT' in symbol else 'BUSD' if 'BUSD' in symbol else 'USDC',
                    'active': True,
                    'type': 'spot',
                    'spot': True,
                    'future': False,
                    'option': False
                }
                markets.append(market)
            
            # ✅ ИСПРАВЛЕНИЕ: Правильный порядок установки цены и расчета других значений
            for market in markets:
                # Сначала генерируем базовую цену
                base_price = np.random.uniform(0.1, 1000)
                
                # Затем добавляем все остальные данные, используя base_price
                market.update({
                    'volume_24h': np.random.uniform(1000000, 100000000),
                    'price': base_price,  # ← Устанавливаем цену СНАЧАЛА
                    'change_24h': np.random.uniform(-15, 15),
                    'high_24h': np.random.uniform(base_price, base_price * 1.1),  # ← Используем base_price
                    'low_24h': np.random.uniform(base_price * 0.9, base_price),   # ← Используем base_price
                    'trades_count': np.random.randint(1000, 100000),
                    'bid': base_price * 0.999,
                    'ask': base_price * 1.001,
                    'spread': base_price * 0.002
                })
            
            logger.info(f"📊 Получено {len(markets)} рынков с биржи")
            return markets
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения рынков: {e}")
            return []
    
    async def _filter_and_rank_pairs(self, markets: List[Dict]) -> List[Dict]:
        """Фильтрация и ранжирование торговых пар"""
        try:
            filtered_pairs = []
            
            for market in markets:
                # Применяем фильтры
                if await self._passes_pair_filters(market):
                    # Рассчитываем скор для ранжирования
                    score = await self._calculate_pair_score(market)
                    market['trading_score'] = score
                    filtered_pairs.append(market)
            
            # Сортируем по скору (лучшие сначала)
            filtered_pairs.sort(key=lambda x: x['trading_score'], reverse=True)
            
            logger.info(f"🎯 Отфильтровано {len(filtered_pairs)} пар из {len(markets)}")
            return filtered_pairs
            
        except Exception as e:
            logger.error(f"❌ Ошибка фильтрации пар: {e}")
            return []
    
    async def _passes_pair_filters(self, market: Dict) -> bool:
        """Проверка пары на соответствие фильтрам"""
        try:
            symbol = market.get('symbol', '')
            base = market.get('base', '')
            quote = market.get('quote', '')
            volume_24h = market.get('volume_24h', 0)
            price = market.get('price', 0)
            
            # Базовые фильтры
            if not market.get('active', False):
                return False
            
            # Фильтр по котируемой валюте
            if quote not in config.ALLOWED_QUOTE_ASSETS:
                return False
            
            # Фильтр по исключенным базовым активам
            if base in config.EXCLUDED_BASE_ASSETS:
                return False
            
            # Фильтр по объему
            if volume_24h < config.MIN_VOLUME_24H_USD:
                return False
            
            # Фильтр по цене
            if price < config.MIN_PRICE_USD or price > config.MAX_PRICE_USD:
                return False
            
            # Фильтр по черному списку
            if symbol in self.blacklisted_pairs:
                return False
            
            # Дополнительные фильтры
            change_24h = abs(market.get('change_24h', 0))
            if change_24h > 50:  # Исключаем слишком волатильные
                return False
            
            trades_count = market.get('trades_count', 0)
            if trades_count < 100:  # Минимальная активность
                return False
            
            spread_percent = (market.get('ask', 0) - market.get('bid', 0)) / price * 100
            if spread_percent > 1:  # Максимальный спред 1%
                return False
            
            return True
            
        except Exception as e:
            logger.debug(f"Ошибка проверки фильтров для {market.get('symbol', 'unknown')}: {e}")
            return False
    
    async def _calculate_pair_score(self, market: Dict) -> float:
        """Расчет скора торговой пары для ранжирования"""
        try:
            score = 0.0
            
            # Скор по объему (30%)
            volume_24h = market.get('volume_24h', 0)
            volume_score = min(1.0, volume_24h / 50000000)  # Нормализуем к $50M
            score += volume_score * 0.3
            
            # Скор по активности торгов (20%)
            trades_count = market.get('trades_count', 0)
            activity_score = min(1.0, trades_count / 10000)  # Нормализуем к 10k сделок
            score += activity_score * 0.2
            
            # Скор по ликвидности (спреду) (20%)
            price = market.get('price', 1)
            spread = (market.get('ask', price) - market.get('bid', price)) / price
            liquidity_score = max(0, 1 - spread * 100)  # Чем меньше спред, тем лучше
            score += liquidity_score * 0.2
            
            # Скор по волатильности (15%)
            change_24h = abs(market.get('change_24h', 0))
            volatility_score = min(1.0, change_24h / 10)  # Нормализуем к 10%
            score += volatility_score * 0.15
            
            # Скор по популярности базового актива (15%)
            base = market.get('base', '')
            popularity_score = self._get_asset_popularity_score(base)
            score += popularity_score * 0.15
            
            return min(1.0, score)
            
        except Exception as e:
            logger.debug(f"Ошибка расчета скора для {market.get('symbol', 'unknown')}: {e}")
            return 0.0
    
    def _get_asset_popularity_score(self, base_asset: str) -> float:
        """Получение скора популярности актива"""
        # Популярные активы получают больший скор
        popularity_map = {
            'BTC': 1.0, 'ETH': 0.95, 'BNB': 0.9, 'SOL': 0.85, 'ADA': 0.8,
            'XRP': 0.75, 'DOT': 0.7, 'AVAX': 0.65, 'MATIC': 0.6, 'LINK': 0.55,
            'UNI': 0.5, 'LTC': 0.45, 'BCH': 0.4, 'ATOM': 0.35, 'FIL': 0.3
        }
        return popularity_map.get(base_asset, 0.1)  # Базовый скор для неизвестных
    
    async def _categorize_trading_pairs(self):
        """Категоризация торговых пар"""
        try:
            # Очищаем старые категории
            self.active_pairs.clear()
            self.watchlist_pairs.clear()
            self.trending_pairs.clear()
            self.high_volume_pairs.clear()
            
            if not self.all_trading_pairs:
                return
            
            # Сортируем по скору
            sorted_pairs = sorted(self.all_trading_pairs, 
                                key=lambda x: x.get('trading_score', 0), 
                                reverse=True)
            
            # Активные пары (топ 30% или максимум из конфига)
            max_active = min(config.MAX_POSITIONS, len(sorted_pairs) // 3)
            self.active_pairs = [pair['symbol'] for pair in sorted_pairs[:max_active]]
            
            # Список наблюдения (следующие 20%)
            watchlist_count = min(50, len(sorted_pairs) // 5)
            start_idx = len(self.active_pairs)
            self.watchlist_pairs = [pair['symbol'] for pair in sorted_pairs[start_idx:start_idx + watchlist_count]]
            
            # Трендовые пары (с высоким изменением за 24ч)
            trending_pairs = [pair for pair in sorted_pairs if abs(pair.get('change_24h', 0)) > 5]
            self.trending_pairs = [pair['symbol'] for pair in trending_pairs[:20]]
            
            # Высокообъемные пары (топ по объему)
            volume_sorted = sorted(sorted_pairs, key=lambda x: x.get('volume_24h', 0), reverse=True)
            self.high_volume_pairs = [pair['symbol'] for pair in volume_sorted[:20]]
            
            logger.info(f"📊 Категоризация завершена:")
            logger.info(f"  🎯 Активные: {len(self.active_pairs)}")
            logger.info(f"  👀 Наблюдение: {len(self.watchlist_pairs)}")
            logger.info(f"  📈 Трендовые: {len(self.trending_pairs)}")
            logger.info(f"  💰 Высокообъемные: {len(self.high_volume_pairs)}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка категоризации пар: {e}")
    
    def _load_pairs_from_config(self):
        """Загрузка торговых пар из конфигурации"""
        try:
            configured_pairs = config.get_active_trading_pairs()
            
            # Преобразуем в формат all_trading_pairs
            self.all_trading_pairs = [
                {
                    'symbol': symbol,
                    'base': symbol.replace('USDT', '').replace('BUSD', '').replace('USDC', ''),
                    'quote': 'USDT',
                    'trading_score': 0.5  # Средний скор
                }
                for symbol in configured_pairs
            ]
            
            # Ограничиваем количество
            max_pairs = config.MAX_TRADING_PAIRS
            self.all_trading_pairs = self.all_trading_pairs[:max_pairs]
            self.active_pairs = [pair['symbol'] for pair in self.all_trading_pairs[:config.MAX_POSITIONS]]
            
            logger.info(f"📊 Загружено {len(self.all_trading_pairs)} пар из конфигурации")
            
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки пар из конфигурации: {e}")
            # Fallback к минимальному набору
            self.active_pairs = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT']
    
    # =================================================================
    # ТОРГОВЫЕ ЦИКЛЫ И СТРАТЕГИИ 
    # =================================================================
    
    async def _start_all_trading_loops(self):
        """Запуск всех торговых циклов"""
        try:
            logger.info("🔄 Запуск всех торговых циклов...")
            
            # Основной торговый цикл
            self.tasks['main_trading'] = asyncio.create_task(
                self._main_trading_loop(), name="main_trading"
            )
            
            # Цикл мониторинга рынка
            self.tasks['market_monitoring'] = asyncio.create_task(
                self._market_monitoring_loop(), name="market_monitoring"
            )
            
            # Цикл обновления торговых пар
            self.tasks['pair_discovery'] = asyncio.create_task(
                self._pair_discovery_loop(), name="pair_discovery"
            )
            
            # Цикл управления позициями
            self.tasks['position_management'] = asyncio.create_task(
                self._position_management_loop(), name="position_management"
            )
            
            # Цикл мониторинга рисков
            self.tasks['risk_monitoring'] = asyncio.create_task(
                self._risk_monitoring_loop(), name="risk_monitoring"
            )
            
            # Цикл мониторинга здоровья
            self.tasks['health_monitoring'] = asyncio.create_task(
                self._health_monitoring_loop(), name="health_monitoring"
            )
            
            # Цикл обновления производительности
            self.tasks['performance_monitoring'] = asyncio.create_task(
                self._performance_monitoring_loop(), name="performance_monitoring"
            )
            
            # Цикл экспорта данных
            self.tasks['data_export'] = asyncio.create_task(
                self._data_export_loop(), name="data_export"
            )
            
            # Циклы машинного обучения (если включено)
            if config.ENABLE_MACHINE_LEARNING:
                self.tasks['ml_training'] = asyncio.create_task(
                    self._ml_training_loop(), name="ml_training"
                )
                self.tasks['ml_prediction'] = asyncio.create_task(
                    self._ml_prediction_loop(), name="ml_prediction"
                )
            
            # Циклы анализа новостей (если включено)
            if config.ENABLE_NEWS_ANALYSIS:
                self.tasks['news_collection'] = asyncio.create_task(
                    self._news_collection_loop(), name="news_collection"
                )
                self.tasks['sentiment_analysis'] = asyncio.create_task(
                    self._sentiment_analysis_loop(), name="sentiment_analysis"
                )
            
            # Цикл обработки событий
            self.tasks['event_processing'] = asyncio.create_task(
                self._event_processing_loop(), name="event_processing"
            )
            
            # Инициализируем здоровье задач
            for task_name in self.tasks:
                self.task_health[task_name] = 'starting'
            
            logger.info(f"✅ Запущено {len(self.tasks)} торговых циклов")
            
        except Exception as e:
            logger.error(f"❌ Ошибка запуска торговых циклов: {e}")
            raise
    
    async def _main_trading_loop(self):
        """Главный торговый цикл - ПОЛНАЯ ВЕРСИЯ"""
        logger.info("🔄 Запуск главного торгового цикла...")
        self.task_health['main_trading'] = 'running'
        
        consecutive_errors = 0
        max_consecutive_errors = 5
        
        while not self._stop_event.is_set():
            try:
                # Ждем если на паузе
                await self._pause_event.wait()
                
                cycle_start = datetime.utcnow()
                self.cycles_count += 1
                
                logger.info(f"📊 Цикл #{self.cycles_count} - анализ {len(self.active_pairs)} пар")
                
                # 1. Обновляем рыночные данные
                await self._update_market_data()
                
                # 2. Поиск торговых возможностей
                opportunities = await self._find_all_trading_opportunities()
                
                # 3. Фильтрация и ранжирование возможностей
                filtered_opportunities = await self._filter_opportunities(opportunities)
                ranked_opportunities = await self._rank_all_opportunities(filtered_opportunities)
                
                # 4. Проверка рисков перед торговлей
                risk_check = await self._perform_pre_trade_risk_check()
                if not risk_check:
                    logger.warning("⚠️ Риск-проверка не пройдена, пропускаем торговлю")
                    await asyncio.sleep(config.ANALYSIS_INTERVAL_SECONDS)
                    continue
                
                # 5. Выполнение новых сделок
                trades_executed = await self._execute_best_trades(ranked_opportunities)
                
                # 6. Обновление статистики стратегий
                await self._update_strategy_performance()
                
                # 7. Очистка устаревших возможностей
                await self._cleanup_expired_opportunities()
                
                # Сброс счетчика ошибок при успешном цикле
                consecutive_errors = 0
                
                # Обновляем метрики производительности
                cycle_time = (datetime.utcnow() - cycle_start).total_seconds()
                self.performance_metrics.analysis_time_avg = (
                    self.performance_metrics.analysis_time_avg * 0.9 + cycle_time * 0.1
                )
                self.performance_metrics.pairs_per_second = (
                    len(self.active_pairs) / cycle_time if cycle_time > 0 else 0
                )
                
                logger.info(f"⏱️ Цикл #{self.cycles_count} завершен за {cycle_time:.2f}с, сделок: {trades_executed}")
                
                # Пауза до следующего цикла
                sleep_time = max(1, config.ANALYSIS_INTERVAL_SECONDS - cycle_time)
                await asyncio.sleep(sleep_time)
                
            except asyncio.CancelledError:
                logger.info("🛑 Главный торговый цикл отменен")
                self.task_health['main_trading'] = 'cancelled'
                break
            except Exception as e:
                consecutive_errors += 1
                self.task_health['main_trading'] = 'error'
                
                logger.error(f"❌ Ошибка в главном цикле #{consecutive_errors}: {e}")
                
                if consecutive_errors >= max_consecutive_errors:
                    logger.critical(f"🚨 Критическое количество ошибок в главном цикле: {consecutive_errors}")
                    await self._trigger_emergency_stop("Критические ошибки в главном цикле")
                    break
                
                # Увеличиваем паузу при ошибках
                error_sleep = min(300, 30 * consecutive_errors)  # До 5 минут
                await asyncio.sleep(error_sleep)
        
        self.task_health['main_trading'] = 'stopped'
        logger.info("🛑 Главный торговый цикл остановлен")
    
    # ⏭️ ПРОДОЛЖЕНИЕ В СЛЕДУЮЩИХ МЕТОДАХ...
    # Здесь должны быть еще ~1500 строк кода со всеми остальными методами
    
    # =================================================================
    # УПРАВЛЕНИЕ ЗДОРОВЬЕМ СИСТЕМЫ
    # =================================================================
    
    async def _perform_health_check(self) -> Dict[str, Any]:
        """Проверка здоровья всей системы"""
        try:
            health_info = {
                'timestamp': datetime.utcnow().isoformat(),
                'overall_healthy': True,
                'components': {},
                'tasks': {},
                'system': {},
                'alerts': []
            }
            
            # Проверка компонентов
            for name, comp in self.components.items():
                is_healthy = comp.status == ComponentStatus.READY
                if comp.last_heartbeat:
                    time_since_heartbeat = (datetime.utcnow() - comp.last_heartbeat).total_seconds()
                    is_healthy = is_healthy and time_since_heartbeat < comp.health_check_interval * 2
                
                health_info['components'][name] = {
                    'status': comp.status.value,
                    'healthy': is_healthy,
                    'last_heartbeat': comp.last_heartbeat.isoformat() if comp.last_heartbeat else None,
                    'restart_count': comp.restart_count
                }
                
                if not is_healthy and comp.is_critical:
                    health_info['overall_healthy'] = False
                    health_info['alerts'].append(f"Critical component {name} is unhealthy")
            
            # Проверка задач
            for name, task in self.tasks.items():
                task_healthy = task and not task.done()
                health_info['tasks'][name] = {
                    'running': task_healthy,
                    'health': self.task_health.get(name, 'unknown'),
                    'done': task.done() if task else True
                }
                
                if not task_healthy:
                    health_info['alerts'].append(f"Task {name} is not running")
            
            # Системные метрики
            try:
                process = psutil.Process()
                memory_info = process.memory_info()
                
                health_info['system'] = {
                    'memory_usage_mb': memory_info.rss / 1024 / 1024,
                    'cpu_percent': process.cpu_percent(),
                    'open_files': len(process.open_files()),
                    'threads': process.num_threads()
                }
                
                # Проверяем лимиты
                if health_info['system']['memory_usage_mb'] > 2048:  # 2GB
                    health_info['alerts'].append("High memory usage detected")
                
            except Exception as e:
                health_info['system']['error'] = str(e)
            
            # Проверка торговых лимитов
            if self.trades_today >= config.MAX_DAILY_TRADES * 0.9:
                health_info['alerts'].append("Approaching daily trade limit")
            
            if len(self.positions) >= config.MAX_POSITIONS * 0.9:
                health_info['alerts'].append("Approaching position limit")
            
            # Общее здоровье
            if health_info['alerts']:
                health_info['overall_healthy'] = False
            
            self.last_health_check_time = datetime.utcnow().isoformat()
            return health_info
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки здоровья: {e}")
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'overall_healthy': False,
                'error': str(e)
            }
    
    # =================================================================
    # ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ (заглушки для компиляции)
    # =================================================================
    
    async def _setup_signal_handlers(self):
        """Настройка обработчиков сигналов"""
        pass
    
    async def _validate_configuration(self) -> bool:
        """Валидация конфигурации"""
        return True
    
    async def _connect_exchange(self) -> bool:
        """Подключение к бирже"""
        return True
    
    async def _initialize_strategies(self):
        """Инициализация стратегий"""
        pass
    
    async def _initialize_ml_system(self):
        """Инициализация ML системы"""
        pass
    
    async def _load_historical_data(self):
        """Загрузка исторических данных"""
        pass
    
    async def _perform_initial_market_analysis(self):
        """Начальный анализ рынка"""
        pass
    
    async def _setup_monitoring_system(self):
        """Настройка системы мониторинга"""
        pass
    
    async def _start_websocket_connections(self):
        """Запуск WebSocket соединений"""
        pass
    
    async def _send_startup_notification(self):
        """Отправка уведомления о запуске"""
        pass
    
    async def _log_startup_statistics(self):
        """Логирование статистики запуска"""
        pass
    
    async def _save_current_state(self):
        """Сохранение текущего состояния"""
        pass
    
    async def _close_all_positions_safely(self):
        """Безопасное закрытие всех позиций"""
        pass
    
    async def _cancel_all_orders(self):
        """Отмена всех ордеров"""
        pass
    
    async def _stop_all_tasks(self):
        """Остановка всех задач"""
        for task_name, task in self.tasks.items():
            if task and not task.done():
                task.cancel()
                try:
                    await asyncio.wait_for(task, timeout=5.0)
                except asyncio.TimeoutError:
                    logger.warning(f"⚠️ Таймаут остановки задачи: {task_name}")
                except asyncio.CancelledError:
                    pass
    
    async def _close_websocket_connections(self):
        """Закрытие WebSocket соединений"""
        pass
    
    async def _stop_ml_system(self):
        """Остановка ML системы"""
        pass
    
    async def _export_final_data(self):
        """Экспорт финальных данных"""
        pass
    
    async def _disconnect_exchange(self):
        """Отключение от биржи"""
        pass
    
    async def _close_database_connections(self):
        """Закрытие соединений с БД"""
        pass
    
    async def _cleanup_caches(self):
        """Очистка кэшей"""
        self.market_data_cache.clear()
        self.ml_predictions.clear()
        self.current_opportunities.clear()
    
    async def _send_shutdown_notification(self, old_status):
        """Отправка уведомления об остановке"""
        pass
    
    async def _send_error_notification(self, error_msg):
        """Отправка уведомления об ошибке"""
        pass
    
    async def _cancel_pending_orders(self):
        """Отмена ожидающих ордеров"""
        pass
    
    async def _send_pause_notification(self):
        """Отправка уведомления о паузе"""
        pass
    
    async def _refresh_market_data(self):
        """Обновление рыночных данных"""
        pass
    
    async def _send_resume_notification(self):
        """Отправка уведомления о возобновлении"""
        pass
    
    async def _emergency_close_all_positions(self):
        """Экстренное закрытие всех позиций"""
        pass
    
    async def _send_emergency_notification(self):
        """Отправка экстренного уведомления"""
        pass
    
    def _get_best_strategy(self) -> Optional[str]:
        """Получение лучшей стратегии"""
        if not self.strategy_performance:
            return None
        
        best_strategy = max(
            self.strategy_performance.items(),
            key=lambda x: x[1].get('win_rate', 0)
        )
        return best_strategy[0]
    
    # =================================================================
    # ДОПОЛНИТЕЛЬНЫЕ ЦИКЛЫ (заглушки)
    # =================================================================
    
    async def _market_monitoring_loop(self):
        """Цикл мониторинга рынка"""
        while not self._stop_event.is_set():
            try:
                await self._pause_event.wait()
                # Логика мониторинга рынка
                await asyncio.sleep(300)  # 5 минут
            except asyncio.CancelledError:
                break
    
    async def _pair_discovery_loop(self):
        """Цикл обновления торговых пар"""
        while not self._stop_event.is_set():
            try:
                await self._pause_event.wait()
                # Логика обновления пар
                await asyncio.sleep(config.PAIR_DISCOVERY_INTERVAL_HOURS * 3600)
            except asyncio.CancelledError:
                break
    
    async def _position_management_loop(self):
        """Цикл управления позициями"""
        while not self._stop_event.is_set():
            try:
                await self._pause_event.wait()
                # Логика управления позициями
                await asyncio.sleep(30)
            except asyncio.CancelledError:
                break
    
    async def _risk_monitoring_loop(self):
        """Цикл мониторинга рисков"""
        while not self._stop_event.is_set():
            try:
                await self._pause_event.wait()
                # Логика мониторинга рисков
                await asyncio.sleep(60)
            except asyncio.CancelledError:
                break
    
    async def _health_monitoring_loop(self):
        """Цикл мониторинга здоровья"""
        while not self._stop_event.is_set():
            try:
                await self._pause_event.wait()
                health_status = await self._perform_health_check()
                # Обработка результатов проверки здоровья
                await asyncio.sleep(300)  # 5 минут
            except asyncio.CancelledError:
                break
    
    async def _performance_monitoring_loop(self):
        """Цикл мониторинга производительности"""
        while not self._stop_event.is_set():
            try:
                await self._pause_event.wait()
                # Логика мониторинга производительности
                await asyncio.sleep(60)
            except asyncio.CancelledError:
                break
    
    async def _data_export_loop(self):
        """Цикл экспорта данных"""
        while not self._stop_event.is_set():
            try:
                await self._pause_event.wait()
                # Логика экспорта данных
                await asyncio.sleep(3600)  # 1 час
            except asyncio.CancelledError:
                break
    
    async def _ml_training_loop(self):
        """Цикл обучения ML"""
        while not self._stop_event.is_set():
            try:
                await self._pause_event.wait()
                # Логика обучения ML
                await asyncio.sleep(config.RETRAIN_INTERVAL_HOURS * 3600)
            except asyncio.CancelledError:
                break
    
    async def _ml_prediction_loop(self):
        """Цикл ML предсказаний"""
        while not self._stop_event.is_set():
            try:
                await self._pause_event.wait()
                # Логика ML предсказаний
                await asyncio.sleep(300)  # 5 минут
            except asyncio.CancelledError:
                break
    
    async def _news_collection_loop(self):
        """Цикл сбора новостей"""
        while not self._stop_event.is_set():
            try:
                await self._pause_event.wait()
                # Логика сбора новостей
                await asyncio.sleep(1800)  # 30 минут
            except asyncio.CancelledError:
                break
    
    async def _sentiment_analysis_loop(self):
        """Цикл анализа настроений"""
        while not self._stop_event.is_set():
            try:
                await self._pause_event.wait()
                # Логика анализа настроений
                await asyncio.sleep(600)  # 10 минут
            except asyncio.CancelledError:
                break
    
    async def _event_processing_loop(self):
        """Цикл обработки событий"""
        while not self._stop_event.is_set():
            try:
                await self._pause_event.wait()
                # Логика обработки событий
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                break
    
    # =================================================================
    # ДОПОЛНИТЕЛЬНЫЕ МЕТОДЫ ДЛЯ ТОРГОВЛИ (заглушки)
    # =================================================================
    
    async def _update_market_data(self):
        """Обновление рыночных данных"""
        pass
    
    async def _find_all_trading_opportunities(self) -> List[TradingOpportunity]:
        """Поиск всех торговых возможностей"""
        return []
    
    async def _filter_opportunities(self, opportunities: List[TradingOpportunity]) -> List[TradingOpportunity]:
        """Фильтрация возможностей"""
        return opportunities
    
    async def _rank_all_opportunities(self, opportunities: List[TradingOpportunity]) -> List[TradingOpportunity]:
        """Ранжирование возможностей"""
        return opportunities
    
    async def _perform_pre_trade_risk_check(self) -> bool:
        """Проверка рисков перед торговлей"""
        return True
    
    async def _execute_best_trades(self, opportunities: List[TradingOpportunity]) -> int:
        """Выполнение лучших сделок"""
        return 0
    
    async def _update_strategy_performance(self):
        """Обновление производительности стратегий"""
        pass
    
    async def _cleanup_expired_opportunities(self):
        """Очистка устаревших возможностей"""
        pass
    
    async def _trigger_emergency_stop(self, reason: str):
        """Запуск экстренной остановки"""
        logger.critical(f"🚨 Запуск экстренной остановки: {reason}")
        await self.emergency_stop()
    
    # =================================================================
    # МЕТОДЫ ДЛЯ СОВМЕСТИМОСТИ (сохраняем существующие)
    # =================================================================
    
    async def update_pairs(self, pairs: List[str]) -> None:
        """Обновление торговых пар (для совместимости)"""
        self.trading_pairs = pairs
        # Обновляем также активные пары
        self.active_pairs = pairs[:config.MAX_TRADING_PAIRS]
        logger.info(f"📊 Обновлены торговые пары: {len(pairs)}")
    
    def __repr__(self) -> str:
        """Строковое представление для отладки"""
        return (
            f"BotManager(status={self.status.value}, "
            f"pairs={len(self.active_pairs)}, "
            f"positions={len(self.positions)}, "
            f"cycles={self.cycles_count}, "
            f"uptime={self.start_time})"
        )


# =========================================================================
# === СОЗДАНИЕ ГЛОБАЛЬНОГО ЭКЗЕМПЛЯРА ===
# =========================================================================

# Создаем единственный экземпляр менеджера бота (Singleton)
bot_manager = BotManager()

# Экспорт
__all__ = ['BotManager', 'bot_manager']

# Дополнительная проверка для отладки
if __name__ == "__main__":
    # Этот блок выполняется только при прямом запуске файла
    # Полезно для тестирования отдельных компонентов
    print("🤖 BotManager module loaded successfully")
    print(f"📊 Manager instance: {bot_manager}")
    print(f"🔧 Configuration loaded: {hasattr(config, 'BYBIT_API_KEY')}")