"""
Адаптер конфигурации для совместимости с разными форматами .env
Файл: src/core/config.py
"""
import os
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

# Пытаемся загрузить из разных мест
env_paths = [
    Path("/etc/crypto/config/.env"),
    Path(".env"),
    Path("../.env")
]

for env_path in env_paths:
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Загружена конфигурация из {env_path}")
        break


class Config:
    """Унифицированная конфигурация"""
    
    # База данных - используем ваши переменные
    DATABASE_URL = os.getenv('DATABASE_URL') or os.getenv('ASYNC_DATABASE_URL')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    DB_NAME = os.getenv('DB_NAME', 'crypto_top_bd_mysql')
    DB_USER = os.getenv('DB_USER', 'crypto_top_admin')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    
    # API биржи - адаптируем под Bybit
    EXCHANGE_NAME = 'bybit'  # Фиксируем Bybit
    EXCHANGE_API_KEY = os.getenv('BYBIT_API_KEY') or os.getenv('EXCHANGE_API_KEY', '')
    EXCHANGE_API_SECRET = os.getenv('BYBIT_API_SECRET') or os.getenv('EXCHANGE_API_SECRET', '')
    EXCHANGE_TESTNET = os.getenv('BYBIT_TESTNET', 'true').lower() == 'true'
    
    # Приложение
    APP_SECRET_KEY = os.getenv('SECRET_KEY') or os.getenv('APP_SECRET_KEY', 'default-secret-key')
    APP_ENV = os.getenv('APP_ENV', 'production')
    APP_DEBUG = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
    
    # Торговля
    DEFAULT_SYMBOL = os.getenv('TRADING_SYMBOL', 'BTCUSDT')
    DEFAULT_TRADE_AMOUNT = float(os.getenv('INITIAL_CAPITAL', 100))
    MAX_POSITIONS = int(os.getenv('MAX_POSITIONS', 5))
    RISK_PERCENTAGE = float(os.getenv('MAX_POSITION_SIZE_PERCENT', 2))
    
    # ML настройки
    ML_MODEL_UPDATE_HOURS = int(os.getenv('ML_MODEL_UPDATE_HOURS', 24))
    ML_MIN_ACCURACY = float(os.getenv('ML_MIN_ACCURACY', 0.65))
    ML_CONFIDENCE_THRESHOLD = float(os.getenv('ML_CONFIDENCE_THRESHOLD', 0.7))
    
    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
    TELEGRAM_ENABLED = os.getenv('TELEGRAM_ENABLED', 'false').lower() == 'true'
    
    # Новости и соцсети
    TWITTER_API_KEY = os.getenv('TWITTER_API_KEY', '')
    TWITTER_API_SECRET = os.getenv('TWITTER_API_SECRET', '')
    REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID', '')
    REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET', '')
    NEWS_API_KEY = os.getenv('NEWS_API_KEY', '')
    
    # Логирование
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE_PATH = os.getenv('LOG_FILE_PATH', './logs/crypto_bot.log')
    
    # Web
    WEB_HOST = os.getenv('WEB_HOST', '0.0.0.0')
    WEB_PORT = int(os.getenv('WEB_PORT', 5000))
    
    @classmethod
    def validate(cls) -> tuple[bool, list[str]]:
        """Проверяет наличие обязательных настроек"""
        errors = []
        
        if not cls.DATABASE_URL:
            errors.append("DATABASE_URL не установлена")
        
        if not cls.EXCHANGE_API_KEY:
            errors.append("API ключ биржи не установлен (BYBIT_API_KEY)")
            
        if not cls.EXCHANGE_API_SECRET:
            errors.append("API секрет биржи не установлен (BYBIT_API_SECRET)")
        
        return len(errors) == 0, errors
    
    @classmethod
    def get_exchange_params(cls) -> dict:
        """Возвращает параметры для подключения к бирже"""
        return {
            'apiKey': cls.EXCHANGE_API_KEY,
            'secret': cls.EXCHANGE_API_SECRET,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'future',  # Для фьючерсов
                'testnet': cls.EXCHANGE_TESTNET
            }
        }


# Экспортируем экземпляр
config = Config()