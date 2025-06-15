"""
Единая конфигурация системы
Загружает все настройки из .env файла
"""
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# Загружаем .env файл - приоритет системному пути
if os.path.exists('/etc/crypto/config/.env'):
    load_dotenv('/etc/crypto/config/.env')
    print("✅ Загружена конфигурация из /etc/crypto/config/.env")
elif os.path.exists('.env'):
    load_dotenv('.env')
    print("✅ Загружена конфигурация из .env")
else:
    print("⚠️ Файл .env не найден!")

@dataclass
class Config:
    """Конфигурация приложения"""
    
    # API настройки
    BYBIT_API_KEY: str = field(default_factory=lambda: os.getenv('BYBIT_API_KEY', ''))
    BYBIT_API_SECRET: str = field(default_factory=lambda: os.getenv('BYBIT_API_SECRET', ''))
    BYBIT_TESTNET: bool = field(default_factory=lambda: os.getenv('BYBIT_TESTNET', 'true').lower() == 'true')
    
    # База данных
    DB_HOST: str = field(default_factory=lambda: os.getenv('DB_HOST', 'localhost'))
    DB_NAME: str = field(default_factory=lambda: os.getenv('DB_NAME', 'crypto_top_bd_mysql'))
    DB_USER: str = field(default_factory=lambda: os.getenv('DB_USER', 'crypto_top_admin'))
    DB_PASSWORD: str = field(default_factory=lambda: os.getenv('DB_PASSWORD', ''))
    
    @property
    def DATABASE_URL(self) -> str:
        """Синхронная версия URL для подключения к MySQL"""
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}/{self.DB_NAME}"
    
    @property
    def ASYNC_DATABASE_URL(self) -> str:
        """Асинхронная версия URL для подключения к MySQL"""
        return f"mysql+aiomysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}/{self.DB_NAME}"
    
    # Redis
    REDIS_HOST: str = field(default_factory=lambda: os.getenv('REDIS_HOST', 'localhost'))
    REDIS_PORT: int = field(default_factory=lambda: int(os.getenv('REDIS_PORT', '6379')))
    
    # Торговые параметры
    TRADING_SYMBOL: str = field(default_factory=lambda: os.getenv('TRADING_SYMBOL', 'BTCUSDT'))
    TRADING_PAIRS: List[str] = field(default_factory=lambda: os.getenv('TRADING_PAIRS', 'BTCUSDT,ETHUSDT,BNBUSDT,SOLUSDT').split(','))
    INITIAL_CAPITAL: float = field(default_factory=lambda: float(os.getenv('INITIAL_CAPITAL', '1000')))
    MAX_POSITIONS: int = field(default_factory=lambda: int(os.getenv('MAX_POSITIONS', '1')))
    MAX_POSITION_SIZE_PERCENT: float = field(default_factory=lambda: float(os.getenv('MAX_POSITION_SIZE_PERCENT', '5')))
    STOP_LOSS_PERCENT: float = field(default_factory=lambda: float(os.getenv('STOP_LOSS_PERCENT', '2')))
    TAKE_PROFIT_PERCENT: float = field(default_factory=lambda: float(os.getenv('TAKE_PROFIT_PERCENT', '4')))
    
    # Human behavior
    ENABLE_HUMAN_MODE: bool = field(default_factory=lambda: os.getenv('ENABLE_HUMAN_MODE', 'true').lower() == 'true')
    MIN_DELAY_SECONDS: float = field(default_factory=lambda: float(os.getenv('MIN_DELAY_SECONDS', '0.5')))
    MAX_DELAY_SECONDS: float = field(default_factory=lambda: float(os.getenv('MAX_DELAY_SECONDS', '3.0')))
    
    # Веб-интерфейс
    WEB_HOST: str = field(default_factory=lambda: os.getenv('WEB_HOST', '0.0.0.0'))
    WEB_PORT: int = field(default_factory=lambda: int(os.getenv('WEB_PORT', '8000')))
    
    # Telegram
    TELEGRAM_BOT_TOKEN: str = field(default_factory=lambda: os.getenv('TELEGRAM_BOT_TOKEN', ''))
    TELEGRAM_CHAT_ID: str = field(default_factory=lambda: os.getenv('TELEGRAM_CHAT_ID', ''))
    
    # Безопасность
    SECRET_KEY: str = field(default_factory=lambda: os.getenv('SECRET_KEY', 'your-very-long-random-secret-key-change-this-in-production'))
    
    # Стратегии
    ENABLE_MULTI_INDICATOR: bool = field(default_factory=lambda: os.getenv('ENABLE_MULTI_INDICATOR', 'true').lower() == 'true')
    ENABLE_SCALPING: bool = field(default_factory=lambda: os.getenv('ENABLE_SCALPING', 'true').lower() == 'true')
    
    # Риск менеджмент
    MIN_RISK_REWARD_RATIO: float = field(default_factory=lambda: float(os.getenv('MIN_RISK_REWARD_RATIO', '2.0')))
    MAX_DAILY_TRADES: int = field(default_factory=lambda: int(os.getenv('MAX_DAILY_TRADES', '10')))
    
    def validate(self) -> tuple[bool, list[str]]:
        """Валидация конфигурации"""
        errors = []
        
        if not self.BYBIT_API_KEY:
            errors.append("BYBIT_API_KEY не установлен")
        if not self.BYBIT_API_SECRET:
            errors.append("BYBIT_API_SECRET не установлен")
        if not self.DB_PASSWORD:
            errors.append("DB_PASSWORD не установлен")
        
        return len(errors) == 0, errors

# Глобальный экземпляр конфигурации
config = Config()