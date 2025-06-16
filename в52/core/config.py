"""
Конфигурация приложения
Путь: src/core/config.py
"""
import os
from dotenv import load_dotenv
from typing import Optional

# Загружаем переменные окружения
load_dotenv('/etc/crypto/config/.env')

class Config:
    """Класс конфигурации с всеми необходимыми параметрами"""
    
    # API настройки
    BYBIT_API_KEY = os.getenv('BYBIT_API_KEY')
    BYBIT_API_SECRET = os.getenv('BYBIT_API_SECRET')
    BYBIT_TESTNET = os.getenv('BYBIT_TESTNET', 'true').lower() == 'true'
    
    # База данных
    DATABASE_URL = os.getenv('DATABASE_URL')
    ASYNC_DATABASE_URL = os.getenv('ASYNC_DATABASE_URL', DATABASE_URL)
    
    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    TELEGRAM_ENABLED = os.getenv('TELEGRAM_ENABLED', 'true').lower() == 'true'
    
    # Человекоподобное поведение
    ENABLE_HUMAN_MODE = os.getenv('ENABLE_HUMAN_MODE', 'true').lower() == 'true'
    MIN_DELAY_SECONDS = float(os.getenv('MIN_DELAY_SECONDS', '0.5'))
    MAX_DELAY_SECONDS = float(os.getenv('MAX_DELAY_SECONDS', '3.0'))
    RANDOM_DELAY_ENABLED = os.getenv('RANDOM_DELAY_ENABLED', 'true').lower() == 'true'
    
    # Торговые параметры
    TRADING_SYMBOL = os.getenv('TRADING_SYMBOL', 'BTCUSDT')
    INITIAL_CAPITAL = float(os.getenv('INITIAL_CAPITAL', '1000'))
    MAX_POSITION_SIZE_PERCENT = float(os.getenv('MAX_POSITION_SIZE_PERCENT', '5'))
    STOP_LOSS_PERCENT = float(os.getenv('STOP_LOSS_PERCENT', '2'))
    TAKE_PROFIT_PERCENT = float(os.getenv('TAKE_PROFIT_PERCENT', '4'))
    MIN_ORDER_SIZE = float(os.getenv('MIN_ORDER_SIZE', '10.0'))
    MAX_LEVERAGE = int(os.getenv('MAX_LEVERAGE', '1'))
    SLIPPAGE_TOLERANCE = float(os.getenv('SLIPPAGE_TOLERANCE', '0.1'))
    
    # Веб-интерфейс
    WEB_HOST = os.getenv('WEB_HOST', '0.0.0.0')
    WEB_PORT = int(os.getenv('WEB_PORT', '8000'))
    DEBUG_MODE = os.getenv('DEBUG_MODE', 'true').lower() == 'true'
    RELOAD_ON_CHANGE = os.getenv('RELOAD_ON_CHANGE', 'true').lower() == 'true'
    
    # Безопасность
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-jwt-secret-key')
    JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
    JWT_EXPIRE_MINUTES = int(os.getenv('JWT_EXPIRE_MINUTES', '60'))
    
    # Администратор
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
    ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@example.com')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'SecurePassword123!')
    
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
    
    # Режимы работы
    PAPER_TRADING = os.getenv('PAPER_TRADING', 'true').lower() == 'true'
    BACKTEST_MODE = os.getenv('BACKTEST_MODE', 'false').lower() == 'true'
    LIVE_TRADING = os.getenv('LIVE_TRADING', 'false').lower() == 'true'
    
    # Временные рамки
    DEFAULT_TIMEFRAME = os.getenv('DEFAULT_TIMEFRAME', '1m')
    ANALYSIS_TIMEFRAMES = os.getenv('ANALYSIS_TIMEFRAMES', '1m,5m,15m,1h').split(',')
    DATA_HISTORY_DAYS = int(os.getenv('DATA_HISTORY_DAYS', '30'))
    
    # Индикаторы
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
    
    # Redis (опционально)
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')
    ENABLE_REDIS = os.getenv('ENABLE_REDIS', 'false').lower() == 'true'
    
    def __repr__(self):
        return f"<Config {self.TRADING_SYMBOL} testnet={self.BYBIT_TESTNET}>"

# Создаем экземпляры для экспорта
config = Config()
settings = config

# Экспорт
__all__ = ['Config', 'config', 'settings']
