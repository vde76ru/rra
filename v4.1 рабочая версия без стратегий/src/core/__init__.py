"""
Core модуль - центральное место для всех базовых компонентов
Путь: src/core/__init__.py
"""

# Импортируем все модели из models.py (ЕДИНСТВЕННЫЙ ИСТОЧНИК МОДЕЛЕЙ)
from .models import (
    Base,
    # Enums
    TradeStatus,
    OrderSide,
    OrderType,
    SignalAction,
    # Models
    User,
    BotSettings,
    BotState,
    Balance,
    TradingPair,
    Signal,
    Trade,
    Order,
    Candle,
    MarketCondition,
    StrategyPerformance,
    MLModel,
    MLPrediction,
    TradeMLPrediction,
    NewsAnalysis,
    SocialSignal,
    TradingLog
)

# Импортируем компоненты базы данных
from .database import (
    Database,
    db,
    engine,
    SessionLocal,
    get_db,
    get_session,
    create_session,
    transaction
)

# Импортируем конфигурацию
from .config import config, settings

# Экспортируем все
__all__ = [
    # База
    'Base',
    # Enums
    'TradeStatus',
    'OrderSide', 
    'OrderType',
    'SignalAction',
    # Models
    'User',
    'BotSettings',
    'BotState',
    'Balance',
    'TradingPair',
    'Signal',
    'Trade',
    'Order',
    'Candle',
    'MarketCondition',
    'StrategyPerformance',
    'MLModel',
    'MLPrediction',
    'TradeMLPrediction',
    'NewsAnalysis',
    'SocialSignal',
    'TradingLog',
    # Database
    'Database',
    'db',
    'engine',
    'SessionLocal',
    'get_db',
    'get_session',
    'create_session',
    'transaction',
    # Config
    'config',
    'settings'
]

# Добавляем алиас для обратной совместимости
settings = config