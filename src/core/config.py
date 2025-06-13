"""Единая конфигурация системы"""
import os
from dataclasses import dataclass
from typing import List
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv('/etc/crypto/config/.env')

@dataclass
class Config:
    """Централизованная конфигурация"""
    
    # API
    BYBIT_API_KEY: str = os.getenv('BYBIT_API_KEY')
    BYBIT_API_SECRET: str = os.getenv('BYBIT_API_SECRET')
    BYBIT_TESTNET: bool = os.getenv('BYBIT_TESTNET', 'true').lower() == 'true'
    
    # База данных
    DB_HOST: str = os.getenv('DB_HOST', 'localhost')
    DB_NAME: str = os.getenv('DB_NAME', 'crypto_top_bd_mysql')
    DB_USER: str = os.getenv('DB_USER', 'crypto_top_admin')
    DB_PASSWORD: str = os.getenv('DB_PASSWORD')
    DATABASE_URL: str = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
    
    # Торговля
    TRADING_PAIRS: List[str] = os.getenv('TRADING_PAIRS', 'BTCUSDT').split(',')
    MAX_POSITIONS: int = int(os.getenv('MAX_POSITIONS', '1'))
    MAX_POSITION_SIZE_PERCENT: float = float(os.getenv('MAX_POSITION_SIZE_PERCENT', '5'))
    STOP_LOSS_PERCENT: float = float(os.getenv('STOP_LOSS_PERCENT', '2'))
    TAKE_PROFIT_PERCENT: float = float(os.getenv('TAKE_PROFIT_PERCENT', '4'))
    
    # Human behavior
    ENABLE_HUMAN_MODE: bool = os.getenv('ENABLE_HUMAN_MODE', 'true').lower() == 'true'
    MIN_DELAY_SECONDS: float = float(os.getenv('MIN_DELAY_SECONDS', '0.5'))
    MAX_DELAY_SECONDS: float = float(os.getenv('MAX_DELAY_SECONDS', '3.0'))
    
    # Telegram
    TELEGRAM_BOT_TOKEN: str = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID: str = os.getenv('TELEGRAM_CHAT_ID')
    
    # Web
    WEB_HOST: str = os.getenv('WEB_HOST', '0.0.0.0')
    WEB_PORT: int = int(os.getenv('WEB_PORT', '8000'))
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'change-this-in-production')
    
    # Стратегии
    ENABLE_MULTI_INDICATOR: bool = os.getenv('ENABLE_MULTI_INDICATOR', 'true').lower() == 'true'
    ENABLE_SCALPING: bool = os.getenv('ENABLE_SCALPING', 'true').lower() == 'true'
    MIN_RISK_REWARD_RATIO: float = float(os.getenv('MIN_RISK_REWARD_RATIO', '2.0'))
    MAX_DAILY_TRADES: int = int(os.getenv('MAX_DAILY_TRADES', '10'))

config = Config()
