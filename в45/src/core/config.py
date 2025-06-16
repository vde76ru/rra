"""Конфигурация приложения"""
import os
from pathlib import Path
from dotenv import load_dotenv

class Config:
    """Класс конфигурации с поддержкой всех необходимых параметров"""
    
    def __init__(self):
        # Загружаем .env файл из /etc/crypto/config/
        env_path = Path('/etc/crypto/config/.env')
        if env_path.exists():
            load_dotenv(env_path)
            print(f"✅ Конфигурация загружена из {env_path}")
        else:
            # Fallback на локальный .env
            load_dotenv()
            print("⚠️ Используется локальный .env файл")
        
        # База данных - ВАЖНО: добавляем ASYNC_DATABASE_URL
        self.DATABASE_URL = os.getenv('DATABASE_URL')
        self.ASYNC_DATABASE_URL = os.getenv('ASYNC_DATABASE_URL')
        
        # Параметры БД
        self.DB_HOST = os.getenv('DB_HOST', 'localhost')
        self.DB_NAME = os.getenv('DB_NAME')
        self.DB_USER = os.getenv('DB_USER')
        self.DB_PASSWORD = os.getenv('DB_PASSWORD')
        self.DB_PORT = int(os.getenv('DB_PORT', '3306'))
        
        # Bybit API
        self.BYBIT_API_KEY = os.getenv('BYBIT_API_KEY')
        self.BYBIT_API_SECRET = os.getenv('BYBIT_API_SECRET')
        self.BYBIT_TESTNET = os.getenv('BYBIT_TESTNET', 'true').lower() == 'true'
        
        # Торговые параметры
        self.TRADING_SYMBOL = os.getenv('TRADING_SYMBOL', 'BTCUSDT')
        self.INITIAL_CAPITAL = float(os.getenv('INITIAL_CAPITAL', '1000'))
        self.MAX_POSITION_SIZE_PERCENT = float(os.getenv('MAX_POSITION_SIZE_PERCENT', '5'))
        self.STOP_LOSS_PERCENT = float(os.getenv('STOP_LOSS_PERCENT', '2'))
        self.TAKE_PROFIT_PERCENT = float(os.getenv('TAKE_PROFIT_PERCENT', '4'))
        
        # Режимы работы
        self.PAPER_TRADING = os.getenv('PAPER_TRADING', 'true').lower() == 'true'
        self.LIVE_TRADING = os.getenv('LIVE_TRADING', 'false').lower() == 'true'
        self.DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
        
        # Веб-интерфейс
        self.WEB_HOST = os.getenv('WEB_HOST', '0.0.0.0')
        self.WEB_PORT = int(os.getenv('WEB_PORT', '8000'))
        
        # Безопасность
        self.SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key')
        self.JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'default-jwt-key')
        
        # Telegram
        self.TELEGRAM_ENABLED = os.getenv('TELEGRAM_ENABLED', 'false').lower() == 'true'
        self.TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
        self.TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
        
        # Логирование
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
        self.LOG_FILE_PATH = os.getenv('LOG_FILE_PATH', './logs/crypto_bot.log')
    
    def validate(self):
        """Валидация конфигурации"""
        errors = []
        
        if self.LIVE_TRADING and self.PAPER_TRADING:
            errors.append("Нельзя включать LIVE_TRADING и PAPER_TRADING одновременно")
        
        if not self.DATABASE_URL:
            errors.append("DATABASE_URL не указан")
        
        if not self.ASYNC_DATABASE_URL:
            errors.append("ASYNC_DATABASE_URL не указан")
        
        if self.TELEGRAM_ENABLED and (not self.TELEGRAM_BOT_TOKEN or not self.TELEGRAM_CHAT_ID):
            errors.append("Telegram включен, но не указаны токен или chat_id")
        
        if errors:
            raise ValueError(f"Ошибки конфигурации: {'; '.join(errors)}")
        
        return True

# Создаем глобальный экземпляр
config = Config()
