"""
Чистая конфигурация логирования для криптобота
Убирает избыточные логи, оставляет только важные события
Файл: src/core/clean_logging.py
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

class ColoredFormatter(logging.Formatter):
    """Форматтер с цветами для консоли"""
    
    # Цветовые коды ANSI
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }
    
    def format(self, record):
        # Добавляем цвет к уровню логирования
        if record.levelname in self.COLORS:
            colored_levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
            # Создаем копию записи чтобы не изменять оригинал
            record = logging.makeLogRecord(record.__dict__)
            record.levelname = colored_levelname
        
        return super().format(record)


class TradingLogFilter(logging.Filter):
    """Фильтр для торговых логов - показывает только важные события"""
    
    IMPORTANT_KEYWORDS = [
        'trade', 'сделка', 'позиция', 'прибыль', 'убыток',
        'buy', 'sell', 'покупка', 'продажа',
        'stop', 'loss', 'profit', 'стоп', 'лосс',
        'signal', 'сигнал', 'strategy', 'стратегия',
        'error', 'ошибка', 'warning', 'предупреждение',
        'start', 'stop', 'запуск', 'остановка',
        'balance', 'баланс', 'portfolio', 'портфель',
        'инициализ', 'загруж', 'подключ'
    ]
    
    EXCLUDE_PATTERNS = [
        'heartbeat', 'ping', 'pong',
        'websocket keep-alive', 'ws ping',
        'checking connection', 'проверка соединения',
        'fetching ticker', 'получение тикера',
        'updating cache', 'обновление кэша'
    ]
    
    def filter(self, record):
        message = record.getMessage().lower()
        
        # Всегда показываем ERROR и CRITICAL
        if record.levelno >= logging.ERROR:
            return True
        
        # Исключаем DEBUG сообщения в продакшене
        if record.levelno == logging.DEBUG and not os.getenv('DEBUG', 'false').lower() == 'true':
            return False
        
        # Проверяем исключения
        for pattern in self.EXCLUDE_PATTERNS:
            if pattern in message:
                return False
        
        # Проверяем важные ключевые слова
        for keyword in self.IMPORTANT_KEYWORDS:
            if keyword in message:
                return True
        
        # Для INFO уровня пропускаем если нет важных ключевых слов
        if record.levelno == logging.INFO:
            return False
        
        # Остальные пропускаем
        return True


class CleanLoggingManager:
    """Менеджер для настройки чистого логирования"""
    
    def __init__(self):
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        self.initialized = False
    
    def setup_logging(self, log_level: str = "INFO"):
        """Настройка системы логирования"""
        if self.initialized:
            return
        
        # Получаем числовой уровень
        numeric_level = getattr(logging, log_level.upper(), logging.INFO)
        
        # Очищаем существующие обработчики
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Базовый форматтер для файлов
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Цветной форматтер для консоли
        console_formatter = ColoredFormatter(
            '%(levelname)s - %(message)s'
        )
        
        # Консольный обработчик
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(console_formatter)
        console_handler.addFilter(TradingLogFilter())
        
        # Файловый обработчик для всех логов
        file_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "trading_bot.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(file_formatter)
        
        # Файловый обработчик только для ошибок
        error_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "errors.log",
            maxBytes=5*1024*1024,   # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        
        # Настраиваем корневой логгер
        root_logger.setLevel(logging.DEBUG)
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(error_handler)
        
        # Отключаем избыточные логи от внешних библиотек
        self._configure_external_loggers()
        
        self.initialized = True
    
    def _configure_external_loggers(self):
        """Настройка логгеров внешних библиотек"""
        external_loggers = [
            'ccxt',
            'urllib3',
            'requests',
            'aiohttp',
            'websockets',
            'sqlalchemy.engine',
            'sqlalchemy.pool',
            'uvicorn.access',
            'uvicorn.error'
        ]
        
        for logger_name in external_loggers:
            logger = logging.getLogger(logger_name)
            logger.setLevel(logging.WARNING)
    
    def get_logger(self, name: str) -> logging.Logger:
        """Получить настроенный логгер"""
        if not self.initialized:
            self.setup_logging()
        
        return logging.getLogger(name)


# Глобальный экземпляр менеджера
_logging_manager = CleanLoggingManager()

def init_logging_system(log_level: str = "INFO"):
    """Инициализация системы логирования"""
    _logging_manager.setup_logging(log_level)

def get_clean_logger(name: str) -> logging.Logger:
    """Получить чистый логгер для модуля"""
    return _logging_manager.get_logger(name)

# Специальный логгер для торговых операций
trading_logger = get_clean_logger('trading')

# Экспортируем важные функции
__all__ = [
    'init_logging_system',
    'get_clean_logger',
    'trading_logger',
    'TradingLogFilter',
    'ColoredFormatter'
]


# Автоматическая инициализация при импорте
if not _logging_manager.initialized:
    init_logging_system()