"""
Core модуль - центральное место для всех базовых компонентов
Путь: src/core/__init__.py

Этот файл экспортирует все основные компоненты для использования
в других модулях проекта, избегая циклических импортов.
"""

# Импортируем модели
from .models import (
    Base,
    BotState,
    User,
    Trade,
    Signal,
    Balance,
    TradingPair,
    MarketCondition,
    MLModel,
    MLPrediction,
    TradingLog,
    Order,
    BotSettings,
    TradeStatus,
    OrderSide,
    OrderType,
    SignalAction
)

# Импортируем компоненты базы данных
from .database import (
    Database,
    db,
    engine,
    SessionLocal,
    get_db,
    get_session,
    transaction
)

# Импортируем конфигурацию
try:
    from .config import config, settings
except ImportError:
    # Если config.py еще не создан, используем заглушку
    class Config:
        BYBIT_API_KEY = None
        BYBIT_API_SECRET = None
        BYBIT_TESTNET = True
        DATABASE_URL = None
        TELEGRAM_BOT_TOKEN = None
        TELEGRAM_CHAT_ID = None
    
    config = Config()
    settings = config

# Экспортируем все компоненты
__all__ = [
    # Модели
    'Base',
    'BotState',
    'User',
    'Trade',
    'Signal',
    'Balance',
    'TradingPair',
    'MarketCondition',
    'MLModel',
    'MLPrediction',
    'TradingLog',
    'Order',
    'BotSettings',
    
    # Enums
    'TradeStatus',
    'OrderSide',
    'OrderType',
    'SignalAction',
    
    # База данных
    'Database',
    'db',
    'engine',
    'SessionLocal',
    'get_db',
    'get_session',
    'transaction',
    
    # Конфигурация
    'config',
    'settings'
]