"""
Конфигурация приложения
Путь: src/core/config.py
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Загружаем переменные окружения
for env_path in ['/etc/crypto/config/.env', '.env']:
    if os.path.exists(env_path):
        load_dotenv(env_path)
        break

class Config:
    """Конфигурация приложения"""
    
    # API ключи Bybit
    BYBIT_API_KEY = os.getenv('BYBIT_API_KEY', '')
    BYBIT_API_SECRET = os.getenv('BYBIT_API_SECRET', '')
    BYBIT_TESTNET = os.getenv('BYBIT_TESTNET', 'true').lower() == 'true'
    
    # База данных
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./trading_bot.db')
    ASYNC_DATABASE_URL = os.getenv('ASYNC_DATABASE_URL', DATABASE_URL.replace('sqlite:///', 'sqlite+aiosqlite:///'))
    
    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
    TELEGRAM_ENABLED = os.getenv('TELEGRAM_ENABLED', 'true').lower() == 'true'
    
    # Web интерфейс
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-jwt-secret-key')
    JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '1440'))
    
    # Торговые параметры
    TRADING_SYMBOL = os.getenv('TRADING_SYMBOL', 'BTCUSDT')
    POSITION_SIZE = float(os.getenv('POSITION_SIZE', '100'))
    MAX_POSITION_SIZE = float(os.getenv('MAX_POSITION_SIZE', '1000'))
    MAX_POSITION_SIZE_PERCENT = float(os.getenv('MAX_POSITION_SIZE_PERCENT', '5'))
    STOP_LOSS_PERCENT = float(os.getenv('STOP_LOSS_PERCENT', '2'))
    TAKE_PROFIT_PERCENT = float(os.getenv('TAKE_PROFIT_PERCENT', '4'))
    MIN_ORDER_SIZE = float(os.getenv('MIN_ORDER_SIZE', '10.0'))
    MAX_LEVERAGE = int(os.getenv('MAX_LEVERAGE', '1'))
    SLIPPAGE_TOLERANCE = float(os.getenv('SLIPPAGE_TOLERANCE', '0.1'))
    
    # Человекоподобное поведение
    ENABLE_HUMAN_MODE = os.getenv('ENABLE_HUMAN_MODE', 'true').lower() == 'true'
    MIN_DELAY_SECONDS = float(os.getenv('MIN_DELAY_SECONDS', '0.5'))
    MAX_DELAY_SECONDS = float(os.getenv('MAX_DELAY_SECONDS', '3.0'))
    RANDOM_DELAY_ENABLED = os.getenv('RANDOM_DELAY_ENABLED', 'true').lower() == 'true'
    
    # Торговые пары и стратегии
    TRADING_PAIRS = os.getenv('TRADING_PAIRS', 'BTCUSDT,ETHUSDT,BNBUSDT,SOLUSDT').split(',')
    MAX_POSITIONS = int(os.getenv('MAX_POSITIONS', '1'))
    MAX_CONCURRENT_TRADES = int(os.getenv('MAX_CONCURRENT_TRADES', '3'))
    
    # Активные стратегии
    ENABLE_MULTI_INDICATOR = os.getenv('ENABLE_MULTI_INDICATOR', 'true').lower() == 'true'
    ENABLE_SCALPING = os.getenv('ENABLE_SCALPING', 'true').lower() == 'true'
    ENABLE_MOMENTUM = os.getenv('ENABLE_MOMENTUM', 'true').lower() == 'true'
    ENABLE_CONSERVATIVE = os.getenv('ENABLE_CONSERVATIVE', 'false').lower() == 'true'
    DEFAULT_STRATEGY = os.getenv('DEFAULT_STRATEGY', 'multi_indicator')
    
    # Риск-менеджмент
    MIN_RISK_REWARD_RATIO = float(os.getenv('MIN_RISK_REWARD_RATIO', '2.0'))
    MAX_DAILY_TRADES = int(os.getenv('MAX_DAILY_TRADES', '10'))
    MAX_DAILY_LOSS_PERCENT = float(os.getenv('MAX_DAILY_LOSS_PERCENT', '10'))
    MAX_DRAWDOWN_PERCENT = float(os.getenv('MAX_DRAWDOWN_PERCENT', '15'))
    MAX_CONSECUTIVE_LOSSES = int(os.getenv('MAX_CONSECUTIVE_LOSSES', '3'))
    COOLING_OFF_PERIOD_MINUTES = int(os.getenv('COOLING_OFF_PERIOD_MINUTES', '30'))
    EMERGENCY_STOP_LOSS_PERCENT = float(os.getenv('EMERGENCY_STOP_LOSS_PERCENT', '5'))
    
    # Логирование
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE_PATH = os.getenv('LOG_FILE_PATH', './logs/crypto_bot.log')
    LOG_MAX_SIZE_MB = int(os.getenv('LOG_MAX_SIZE_MB', '50'))
    LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', '5'))
    LOG_TRADES = os.getenv('LOG_TRADES', 'true').lower() == 'true'
    LOG_SIGNALS = os.getenv('LOG_SIGNALS', 'true').lower() == 'true'
    LOG_ERRORS = os.getenv('LOG_ERRORS', 'true').lower() == 'true'
    LOG_API_CALLS = os.getenv('LOG_API_CALLS', 'false').lower() == 'true'
    ENABLE_DB_LOGGING = os.getenv('ENABLE_DB_LOGGING', 'true').lower() == 'true'
    
    # Технические настройки
    CONNECTION_TIMEOUT = int(os.getenv('CONNECTION_TIMEOUT', '30'))
    READ_TIMEOUT = int(os.getenv('READ_TIMEOUT', '60'))
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
    RETRY_DELAY = int(os.getenv('RETRY_DELAY', '1'))
    API_TIMEOUT = int(os.getenv('API_TIMEOUT', '30'))
    
    # Производительность
    THREAD_POOL_SIZE = int(os.getenv('THREAD_POOL_SIZE', '4'))
    ASYNC_WORKERS = int(os.getenv('ASYNC_WORKERS', '2'))
    ENABLE_CACHING = os.getenv('ENABLE_CACHING', 'true').lower() == 'true'
    CACHE_TTL_SECONDS = int(os.getenv('CACHE_TTL_SECONDS', '300'))
    UPDATE_INTERVAL = int(os.getenv('UPDATE_INTERVAL', '60'))
    
    # Режимы работы
    PAPER_TRADING = os.getenv('PAPER_TRADING', 'true').lower() == 'true'
    BACKTEST_MODE = os.getenv('BACKTEST_MODE', 'false').lower() == 'true'
    LIVE_TRADING = os.getenv('LIVE_TRADING', 'false').lower() == 'true'
    DRY_RUN = os.getenv('DRY_RUN', 'true').lower() == 'true'
    
    # Временные рамки
    DEFAULT_TIMEFRAME = os.getenv('DEFAULT_TIMEFRAME', '1m')
    ANALYSIS_TIMEFRAMES = os.getenv('ANALYSIS_TIMEFRAMES', '1m,5m,15m,1h').split(',')
    DATA_HISTORY_DAYS = int(os.getenv('DATA_HISTORY_DAYS', '30'))
    
    # Технические индикаторы
    RSI_PERIOD = int(os.getenv('RSI_PERIOD', '14'))
    RSI_OVERSOLD = int(os.getenv('RSI_OVERSOLD', '30'))
    RSI_OVERBOUGHT = int(os.getenv('RSI_OVERBOUGHT', '70'))
    SMA_FAST_PERIOD = int(os.getenv('SMA_FAST_PERIOD', '10'))
    SMA_SLOW_PERIOD = int(os.getenv('SMA_SLOW_PERIOD', '20'))
    EMA_PERIOD = int(os.getenv('EMA_PERIOD', '12'))
    MACD_FAST = int(os.getenv('MACD_FAST', '12'))
    MACD_SLOW = int(os.getenv('MACD_SLOW', '26'))
    MACD_SIGNAL = int(os.getenv('MACD_SIGNAL', '9'))
    BOLLINGER_PERIOD = int(os.getenv('BOLLINGER_PERIOD', '20'))
    BOLLINGER_DEVIATION = int(os.getenv('BOLLINGER_DEVIATION', '2'))
    
    # Машинное обучение
    ENABLE_ML = os.getenv('ENABLE_ML', 'true').lower() == 'true'
    ML_MIN_TRAINING_DATA = int(os.getenv('ML_MIN_TRAINING_DATA', '1000'))
    ML_RETRAIN_HOURS = int(os.getenv('ML_RETRAIN_HOURS', '24'))
    
    # Анализ новостей
    ENABLE_NEWS_ANALYSIS = os.getenv('ENABLE_NEWS_ANALYSIS', 'true').lower() == 'true'
    NEWS_API_KEY = os.getenv('NEWS_API_KEY', '')
    CRYPTOCOMPARE_API_KEY = os.getenv('CRYPTOCOMPARE_API_KEY', '')
    
    # Веб-интерфейс
    WEB_HOST = os.getenv('WEB_HOST', '0.0.0.0')
    WEB_PORT = int(os.getenv('WEB_PORT', '8000'))
    DEBUG_MODE = os.getenv('DEBUG_MODE', 'true').lower() == 'true'
    RELOAD_ON_CHANGE = os.getenv('RELOAD_ON_CHANGE', 'true').lower() == 'true'
    
    # CORS настройки
    ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 'http://localhost:8000,http://127.0.0.1:8000').split(',')
    ALLOWED_METHODS = os.getenv('ALLOWED_METHODS', 'GET,POST,PUT,DELETE,OPTIONS').split(',')
    ALLOWED_HEADERS = os.getenv('ALLOWED_HEADERS', '*').split(',')
    
    # Административные настройки
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
    ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@example.com')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')
    
    # Redis (опционально)
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')
    ENABLE_REDIS = os.getenv('ENABLE_REDIS', 'false').lower() == 'true'
    
    # Разработка и отладка
    DEVELOPMENT_MODE = os.getenv('DEVELOPMENT_MODE', 'true').lower() == 'true'
    DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
    ENABLE_PROFILING = os.getenv('ENABLE_PROFILING', 'false').lower() == 'true'
    ENABLE_METRICS = os.getenv('ENABLE_METRICS', 'true').lower() == 'true'
    METRICS_PORT = int(os.getenv('METRICS_PORT', '9090'))
    
    # Тестирование
    MOCK_TRADING = os.getenv('MOCK_TRADING', 'false').lower() == 'true'
    SIMULATE_LATENCY = os.getenv('SIMULATE_LATENCY', 'false').lower() == 'true'
    TEST_MODE = os.getenv('TEST_MODE', 'false').lower() == 'true'
    
    def __repr__(self):
        return f"<Config {self.TRADING_SYMBOL} testnet={self.BYBIT_TESTNET}>"

# Создаем экземпляры для экспорта
config = Config()
settings = config

# Экспорт
__all__ = ['Config', 'config', 'settings']