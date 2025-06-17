"""
Core модуль - центральное место для всех базовых компонентов
Путь: src/core/__init__.py

Этот файл экспортирует все основные компоненты для использования
в других модулях проекта, избегая циклических импортов.
"""

# Импортируем модели
from .models import (
    Base,
    Candle,        # ← ДОБАВЛЯЕМ ЭТУ СТРОКУ!
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
    Strategy,      # ← Добавьте эту модель тоже
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
except ImportError as e:
    # Логируем предупреждение для отладки
    import logging
    logging.warning(f"Config не найден: {e}. Используется заглушка.")
    
    # Если config.py еще не создан, используем заглушку
    class Config:
        """Заглушка конфигурации для разработки"""
        BYBIT_API_KEY = None
        BYBIT_API_SECRET = None
        BYBIT_TESTNET = True
        DATABASE_URL = None
        TELEGRAM_BOT_TOKEN = None
        TELEGRAM_CHAT_ID = None
        
        def __repr__(self):
            return "Config(stub=True)"
    
    config = Config()
    settings = config

# Экспортируем все компоненты
__all__ = [
    # Основные модели данных
    'Base',
    'Candle',          # ← ДОБАВЛЯЕМ В ЭКСПОРТ!
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
    'Strategy',        # ← И эту модель тоже
    
    # Enums для типобезопасности
    'TradeStatus',
    'OrderSide',
    'OrderType',
    'SignalAction',
    
    # Компоненты базы данных
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

# Версия модуля для отслеживания изменений
__version__ = "1.0.0"

# Базовые компоненты для быстрого доступа
CORE_MODELS = [
    'Base', 'Candle', 'BotState', 'User', 'Trade', 
    'Signal', 'Balance', 'TradingPair'
]

ENUMS = [
    'TradeStatus', 'OrderSide', 'OrderType', 'SignalAction'
]

def get_all_models():
    """
    Возвращает список всех доступных моделей
    
    Полезно для автоматической генерации документации
    или динамического анализа системы
    """
    return [model for model in __all__ if model in CORE_MODELS]

def validate_imports():
    """
    Проверяет, что все критические импорты доступны
    
    Returns:
        bool: True если все импорты успешны
    """
    try:
        # Проверяем основные модели
        assert Candle is not None
        assert Database is not None
        assert Base is not None
        
        # Проверяем enums
        assert TradeStatus is not None
        
        return True
    except (AssertionError, NameError) as e:
        logging.error(f"Ошибка валидации импортов: {e}")
        return False

# Автоматическая проверка при импорте модуля
if __name__ != "__main__":  # Только при импорте, не при прямом запуске
    import logging
    if not validate_imports():
        logging.warning("Некоторые импорты core модуля недоступны!")