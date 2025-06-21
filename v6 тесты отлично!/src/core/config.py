#!/usr/bin/env python3
"""
ПОЛНЫЙ ИСПРАВЛЕННЫЙ CONFIG.PY С РАСШИРЕННЫМИ ТОРГОВЫМИ НАСТРОЙКАМИ
==================================================================

⚠️ ВАЖНО: Этот файл ПОЛНОСТЬЮ ЗАМЕНЯЕТ существующий src/core/config.py

Включает:
- Все предыдущие настройки
- Расширенные режимы торговли
- Улучшенную валидацию
- Дополнительные лимиты безопасности

Путь: src/core/config.py
"""

import os
from typing import List, Dict, Any
import logging

class Config:
    """
    Конфигурация торгового бота - ПОЛНАЯ ИСПРАВЛЕННАЯ ВЕРСИЯ
    
    Включает ВСЕ настройки из .env файла + недостающие атрибуты
    + расширенные торговые настройки
    """
    
    # =================================================================
    # БАЗОВЫЕ НАСТРОЙКИ
    # =================================================================
    
    # Среда выполнения
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'production')
    DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
    TEST_MODE = os.getenv('TEST_MODE', 'false').lower() == 'true'
    DEVELOPMENT_MODE = os.getenv('DEVELOPMENT_MODE', 'false').lower() == 'true'
    
    # База данных
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./crypto_bot.db')
    ASYNC_DATABASE_URL = os.getenv('ASYNC_DATABASE_URL', '')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_NAME = os.getenv('DB_NAME', 'crypto_bot')
    DB_USER = os.getenv('DB_USER', '')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_PORT = int(os.getenv('DB_PORT', '3306'))
    DATABASE_POOL_SIZE = int(os.getenv('DATABASE_POOL_SIZE', '20'))
    DATABASE_MAX_OVERFLOW = int(os.getenv('DATABASE_MAX_OVERFLOW', '30'))
    
    # =================================================================
    # БИРЖЕВЫЕ НАСТРОЙКИ
    # =================================================================
    
    # Bybit API
    BYBIT_API_KEY = os.getenv('BYBIT_API_KEY', '')
    BYBIT_API_SECRET = os.getenv('BYBIT_API_SECRET', '')
    BYBIT_TESTNET = os.getenv('BYBIT_TESTNET', 'true').lower() == 'true'
    BYBIT_RECV_WINDOW = int(os.getenv('BYBIT_RECV_WINDOW', '5000'))
    
    # Binance API (дополнительно)
    BINANCE_API_KEY = os.getenv('BINANCE_API_KEY', '')
    BINANCE_API_SECRET = os.getenv('BINANCE_API_SECRET', '')
    BINANCE_TESTNET = os.getenv('BINANCE_TESTNET', 'true').lower() == 'true'
    
    # =================================================================
    # РЕЖИМЫ ТОРГОВЛИ - РАСШИРЕННЫЕ НАСТРОЙКИ
    # =================================================================
    
    # Основные режимы торговли
    PAPER_TRADING = os.getenv('PAPER_TRADING', 'true').lower() == 'true'
    LIVE_TRADING = os.getenv('LIVE_TRADING', 'false').lower() == 'true'
    BACKTEST_MODE = os.getenv('BACKTEST_MODE', 'false').lower() == 'true'
    DRY_RUN = os.getenv('DRY_RUN', 'false').lower() == 'true'
    
    # Дополнительные режимы
    ENABLE_BACKTESTING = os.getenv('ENABLE_BACKTESTING', 'true').lower() == 'true'
    BACKTEST_START_DATE = os.getenv('BACKTEST_START_DATE', '2024-01-01')
    BACKTEST_END_DATE = os.getenv('BACKTEST_END_DATE', '2024-12-31')
    BACKTEST_INITIAL_CAPITAL = float(os.getenv('BACKTEST_INITIAL_CAPITAL', '10000'))
    
    # =================================================================
    # ЛИМИТЫ ДЛЯ РЕАЛЬНОЙ ТОРГОВЛИ - БЕЗОПАСНОСТЬ
    # =================================================================
    
    # Основные торговые лимиты
    MAX_DAILY_TRADES = int(os.getenv('MAX_DAILY_TRADES', '20'))  # Переопределено с более консервативным значением
    MAX_HOURLY_TRADES = int(os.getenv('MAX_HOURLY_TRADES', '10'))
    MAX_TRADES_PER_PAIR_DAILY = int(os.getenv('MAX_TRADES_PER_PAIR_DAILY', '5'))
    MAX_CONCURRENT_TRADES = int(os.getenv('MAX_CONCURRENT_TRADES', '3'))
    
    # Размеры позиций - расширенные лимиты
    MAX_POSITION_SIZE_USD = float(os.getenv('MAX_POSITION_SIZE_USD', '1000'))  # Новый лимит в USD
    MAX_POSITION_SIZE = float(os.getenv('MAX_POSITION_SIZE', '500'))
    MAX_POSITION_SIZE_PERCENT = float(os.getenv('MAX_POSITION_SIZE_PERCENT', '5'))
    POSITION_SIZE_PERCENT = float(os.getenv('POSITION_SIZE_PERCENT', '2.0'))
    MIN_POSITION_SIZE_PERCENT = float(os.getenv('MIN_POSITION_SIZE_PERCENT', '0.5'))
    
    # Экстренные лимиты безопасности
    EMERGENCY_STOP_LOSS_PERCENT = float(os.getenv('EMERGENCY_STOP_LOSS_PERCENT', '10'))  # Новый экстренный стоп-лосс
    MAX_DAILY_LOSS_PERCENT = float(os.getenv('MAX_DAILY_LOSS_PERCENT', '10'))
    MAX_WEEKLY_LOSS_PERCENT = float(os.getenv('MAX_WEEKLY_LOSS_PERCENT', '15'))
    MAX_DRAWDOWN_PERCENT = float(os.getenv('MAX_DRAWDOWN_PERCENT', '15'))
    
    # Лимиты позиций
    MAX_POSITIONS = int(os.getenv('MAX_POSITIONS', '20'))
    MAX_POSITIONS_PER_STRATEGY = int(os.getenv('MAX_POSITIONS_PER_STRATEGY', '5'))
    MAX_CORRELATED_POSITIONS = int(os.getenv('MAX_CORRELATED_POSITIONS', '3'))
    
    # =================================================================
    # НАСТРОЙКИ ИСПОЛНЕНИЯ ОРДЕРОВ
    # =================================================================
    
    # Таймауты и исполнение
    ORDER_TIMEOUT_SECONDS = int(os.getenv('ORDER_TIMEOUT_SECONDS', '30'))  # Новый таймаут ордеров
    CONNECTION_TIMEOUT_SECONDS = int(os.getenv('CONNECTION_TIMEOUT_SECONDS', '30'))
    CONNECTION_TIMEOUT = int(os.getenv('CONNECTION_TIMEOUT', '30'))
    READ_TIMEOUT = int(os.getenv('READ_TIMEOUT', '60'))
    
    # Настройки проскальзывания
    SLIPPAGE_TOLERANCE_PERCENT = float(os.getenv('SLIPPAGE_TOLERANCE_PERCENT', '0.1'))  # Новая настройка проскальзывания
    MAX_SLIPPAGE_PERCENT = float(os.getenv('MAX_SLIPPAGE_PERCENT', '0.5'))
    
    # Повторные попытки
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
    RETRY_DELAY_SECONDS = float(os.getenv('RETRY_DELAY_SECONDS', '1.0'))
    
    # =================================================================
    # ТОРГОВЫЕ ПАРЫ - РАСШИРЕННЫЕ НАСТРОЙКИ
    # =================================================================
    
    # Автопоиск торговых пар
    ENABLE_AUTO_PAIR_DISCOVERY = os.getenv('ENABLE_AUTO_PAIR_DISCOVERY', 'true').lower() == 'true'
    MAX_TRADING_PAIRS = int(os.getenv('MAX_TRADING_PAIRS', '200'))
    MIN_VOLUME_24H_USD = float(os.getenv('MIN_VOLUME_24H_USD', '1000000'))
    MIN_MARKET_CAP_USD = float(os.getenv('MIN_MARKET_CAP_USD', '10000000'))
    MIN_PRICE_USD = float(os.getenv('MIN_PRICE_USD', '0.001'))
    MAX_PRICE_USD = float(os.getenv('MAX_PRICE_USD', '100000'))
    
    # Базовые пары
    TRADING_SYMBOL = os.getenv('TRADING_SYMBOL', 'BTCUSDT')
    TRADING_PAIRS = os.getenv('TRADING_PAIRS', 'BTCUSDT,ETHUSDT,BNBUSDT').split(',')
    
    # Фильтры валют
    ALLOWED_QUOTE_ASSETS = os.getenv('ALLOWED_QUOTE_ASSETS', 'USDT,BUSD,USDC').split(',')
    EXCLUDED_BASE_ASSETS = os.getenv('EXCLUDED_BASE_ASSETS', 'USDT,BUSD,USDC,DAI,TUSD').split(',')
    
    # Интервалы обновления
    PAIR_DISCOVERY_INTERVAL_HOURS = int(os.getenv('PAIR_DISCOVERY_INTERVAL_HOURS', '6'))
    MARKET_DATA_UPDATE_INTERVAL_SECONDS = int(os.getenv('MARKET_DATA_UPDATE_INTERVAL_SECONDS', '30'))
    ANALYSIS_INTERVAL_SECONDS = int(os.getenv('ANALYSIS_INTERVAL_SECONDS', '60'))
    POSITION_CHECK_INTERVAL_SECONDS = int(os.getenv('POSITION_CHECK_INTERVAL_SECONDS', '30'))
    UPDATE_INTERVAL = int(os.getenv('UPDATE_INTERVAL', '60'))
    
    # =================================================================
    # КАПИТАЛ И УПРАВЛЕНИЕ СРЕДСТВАМИ
    # =================================================================
    
    # Начальный капитал
    INITIAL_CAPITAL = float(os.getenv('INITIAL_CAPITAL', '1000'))
    POSITION_SIZE = float(os.getenv('POSITION_SIZE', '100'))
    DYNAMIC_POSITION_SIZING = os.getenv('DYNAMIC_POSITION_SIZING', 'true').lower() == 'true'
    
    # =================================================================
    # МНОЖЕСТВЕННЫЕ СТРАТЕГИИ
    # =================================================================
    
    # Активные стратегии
    ENABLED_STRATEGIES = os.getenv(
        'ENABLED_STRATEGIES',
        'multi_indicator,momentum,mean_reversion,breakout,scalping,swing,ml_prediction'
    ).split(',')
    DEFAULT_STRATEGY = os.getenv('DEFAULT_STRATEGY', 'multi_indicator')
    
    # Настройки стратегий
    STRATEGY_SELECTION_METHOD = os.getenv('STRATEGY_SELECTION_METHOD', 'adaptive')
    MIN_STRATEGY_CONFIDENCE = float(os.getenv('MIN_STRATEGY_CONFIDENCE', '0.65'))
    ENSEMBLE_MIN_STRATEGIES = int(os.getenv('ENSEMBLE_MIN_STRATEGIES', '3'))
    STRATEGY_PERFORMANCE_WINDOW_DAYS = int(os.getenv('STRATEGY_PERFORMANCE_WINDOW_DAYS', '30'))
    
    # Включение стратегий
    ENABLE_MULTI_INDICATOR = os.getenv('ENABLE_MULTI_INDICATOR', 'true').lower() == 'true'
    ENABLE_SCALPING = os.getenv('ENABLE_SCALPING', 'false').lower() == 'true'
    ENABLE_MOMENTUM = os.getenv('ENABLE_MOMENTUM', 'true').lower() == 'true'
    ENABLE_CONSERVATIVE = os.getenv('ENABLE_CONSERVATIVE', 'false').lower() == 'true'
    
    # Веса стратегий
    WEIGHT_MULTI_INDICATOR = float(os.getenv('WEIGHT_MULTI_INDICATOR', '0.25'))
    WEIGHT_MOMENTUM = float(os.getenv('WEIGHT_MOMENTUM', '0.20'))
    WEIGHT_MEAN_REVERSION = float(os.getenv('WEIGHT_MEAN_REVERSION', '0.15'))
    WEIGHT_BREAKOUT = float(os.getenv('WEIGHT_BREAKOUT', '0.15'))
    WEIGHT_SCALPING = float(os.getenv('WEIGHT_SCALPING', '0.10'))
    WEIGHT_SWING = float(os.getenv('WEIGHT_SWING', '0.15'))
    WEIGHT_ML_PREDICTION = float(os.getenv('WEIGHT_ML_PREDICTION', '0.05'))
    
    # =================================================================
    # РИСК-МЕНЕДЖМЕНТ
    # =================================================================
    
    # Базовые риски
    STOP_LOSS_PERCENT = float(os.getenv('STOP_LOSS_PERCENT', '2'))
    TAKE_PROFIT_PERCENT = float(os.getenv('TAKE_PROFIT_PERCENT', '4'))
    MAX_RISK_PER_TRADE_PERCENT = float(os.getenv('MAX_RISK_PER_TRADE_PERCENT', '1.0'))
    MAX_PORTFOLIO_RISK_PERCENT = float(os.getenv('MAX_PORTFOLIO_RISK_PERCENT', '10.0'))
    
    # Корреляционный риск
    MAX_CORRELATION_THRESHOLD = float(os.getenv('MAX_CORRELATION_THRESHOLD', '0.7'))
    CORRELATION_LOOKBACK_DAYS = int(os.getenv('CORRELATION_LOOKBACK_DAYS', '30'))
    
    # ATR-based stops
    STOP_LOSS_ATR_MULTIPLIER = float(os.getenv('STOP_LOSS_ATR_MULTIPLIER', '2.0'))
    TAKE_PROFIT_ATR_MULTIPLIER = float(os.getenv('TAKE_PROFIT_ATR_MULTIPLIER', '4.0'))
    MIN_RISK_REWARD_RATIO = float(os.getenv('MIN_RISK_REWARD_RATIO', '2.0'))
    
    # Трейлинг стопы
    ENABLE_TRAILING_STOPS = os.getenv('ENABLE_TRAILING_STOPS', 'true').lower() == 'true'
    TRAILING_STOP_DISTANCE_PERCENT = float(os.getenv('TRAILING_STOP_DISTANCE_PERCENT', '1.0'))
    TRAILING_STOP_ACTIVATION_PERCENT = float(os.getenv('TRAILING_STOP_ACTIVATION_PERCENT', '2.0'))
    
    # Защитные механизмы
    ENABLE_CIRCUIT_BREAKER = os.getenv('ENABLE_CIRCUIT_BREAKER', 'true').lower() == 'true'
    CIRCUIT_BREAKER_LOSS_PERCENT = float(os.getenv('CIRCUIT_BREAKER_LOSS_PERCENT', '10.0'))
    COOLING_OFF_PERIOD_MINUTES = int(os.getenv('COOLING_OFF_PERIOD_MINUTES', '30'))
    MAX_CONSECUTIVE_LOSSES = int(os.getenv('MAX_CONSECUTIVE_LOSSES', '5'))
    
    # =================================================================
    # МАШИННОЕ ОБУЧЕНИЕ
    # =================================================================
    
    # Основные настройки ML
    ENABLE_MACHINE_LEARNING = os.getenv('ENABLE_MACHINE_LEARNING', 'true').lower() == 'true'
    ENABLE_ML = os.getenv('ENABLE_ML', 'true').lower() == 'true'
    ML_PREDICTION_WEIGHT = float(os.getenv('ML_PREDICTION_WEIGHT', '0.3'))
    MIN_TRAINING_SAMPLES = int(os.getenv('MIN_TRAINING_SAMPLES', '1000'))
    ML_MIN_TRAINING_DATA = int(os.getenv('ML_MIN_TRAINING_DATA', '1000'))
    RETRAIN_INTERVAL_HOURS = int(os.getenv('RETRAIN_INTERVAL_HOURS', '24'))
    ML_RETRAIN_HOURS = int(os.getenv('ML_RETRAIN_HOURS', '24'))
    
    # Модели
    ENABLE_PRICE_PREDICTION = os.getenv('ENABLE_PRICE_PREDICTION', 'true').lower() == 'true'
    ENABLE_DIRECTION_CLASSIFICATION = os.getenv('ENABLE_DIRECTION_CLASSIFICATION', 'true').lower() == 'true'
    ENABLE_VOLATILITY_PREDICTION = os.getenv('ENABLE_VOLATILITY_PREDICTION', 'true').lower() == 'true'
    ENABLE_REGIME_CLASSIFICATION = os.getenv('ENABLE_REGIME_CLASSIFICATION', 'true').lower() == 'true'
    
    # Параметры обучения
    ML_LOOKBACK_HOURS = int(os.getenv('ML_LOOKBACK_HOURS', '720'))
    ML_PREDICTION_HORIZON_HOURS = int(os.getenv('ML_PREDICTION_HORIZON_HOURS', '4'))
    ML_VALIDATION_SPLIT = float(os.getenv('ML_VALIDATION_SPLIT', '0.2'))
    
    # =================================================================
    # АНАЛИЗ НОВОСТЕЙ И СОЦИАЛЬНЫХ СЕТЕЙ
    # =================================================================
    
    # Новостной анализ
    ENABLE_NEWS_ANALYSIS = os.getenv('ENABLE_NEWS_ANALYSIS', 'true').lower() == 'true'
    NEWS_IMPACT_WEIGHT = float(os.getenv('NEWS_IMPACT_WEIGHT', '0.2'))
    NEWS_SENTIMENT_THRESHOLD = float(os.getenv('NEWS_SENTIMENT_THRESHOLD', '0.1'))
    NEWS_UPDATE_INTERVAL_MINUTES = int(os.getenv('NEWS_UPDATE_INTERVAL_MINUTES', '30'))
    
    # API ключи для новостей
    NEWS_API_KEY = os.getenv('NEWS_API_KEY', '')
    CRYPTOCOMPARE_API_KEY = os.getenv('CRYPTOCOMPARE_API_KEY', '')
    COINAPI_KEY = os.getenv('COINAPI_KEY', '')
    
    # Социальные сети
    ENABLE_SOCIAL_ANALYSIS = os.getenv('ENABLE_SOCIAL_ANALYSIS', 'true').lower() == 'true'
    SOCIAL_SENTIMENT_WEIGHT = float(os.getenv('SOCIAL_SENTIMENT_WEIGHT', '0.1'))
    
    # Twitter API
    TWITTER_API_KEY = os.getenv('TWITTER_API_KEY', '')
    TWITTER_API_SECRET = os.getenv('TWITTER_API_SECRET', '')
    TWITTER_ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN', '')
    TWITTER_ACCESS_TOKEN_SECRET = os.getenv('TWITTER_ACCESS_TOKEN_SECRET', '')
    
    # =================================================================
    # ПРОИЗВОДИТЕЛЬНОСТЬ
    # =================================================================
    
    # Кэширование
    ENABLE_REDIS_CACHE = os.getenv('ENABLE_REDIS_CACHE', 'false').lower() == 'true'
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')
    CACHE_TTL_SECONDS = int(os.getenv('CACHE_TTL_SECONDS', '300'))
    
    # Многопоточность
    MAX_CONCURRENT_ANALYSIS = int(os.getenv('MAX_CONCURRENT_ANALYSIS', '10'))
    ENABLE_ASYNC_PROCESSING = os.getenv('ENABLE_ASYNC_PROCESSING', 'true').lower() == 'true'
    
    # API настройки
    API_RATE_LIMIT_PER_MINUTE = int(os.getenv('API_RATE_LIMIT_PER_MINUTE', '1200'))
    
    # =================================================================
    # ЛОГИРОВАНИЕ И МОНИТОРИНГ
    # =================================================================
    
    # Уровни логирования
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    DB_LOG_LEVEL = os.getenv('DB_LOG_LEVEL', 'WARNING')
    API_LOG_LEVEL = os.getenv('API_LOG_LEVEL', 'ERROR')
    
    # Файлы логов
    LOG_FILE_PATH = os.getenv('LOG_FILE_PATH', './logs/crypto_bot.log')
    LOG_FILE = os.getenv('LOG_FILE', 'crypto_bot.log')  # Обратная совместимость
    ERROR_LOG_FILE = os.getenv('ERROR_LOG_FILE', './logs/errors.log')
    TRADE_LOG_FILE = os.getenv('TRADE_LOG_FILE', './logs/trades.log')
    
    # Размеры и ротация логов
    LOG_MAX_SIZE_MB = int(os.getenv('LOG_MAX_SIZE_MB', '50'))
    LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', '5'))
    LOG_COMPRESSION = os.getenv('LOG_COMPRESSION', 'gzip')
    
    # Детализация логирования
    LOG_TRADES = os.getenv('LOG_TRADES', 'true').lower() == 'true'
    LOG_SIGNALS = os.getenv('LOG_SIGNALS', 'true').lower() == 'true'
    LOG_ML_PREDICTIONS = os.getenv('LOG_ML_PREDICTIONS', 'true').lower() == 'true'
    LOG_NEWS_ANALYSIS = os.getenv('LOG_NEWS_ANALYSIS', 'false').lower() == 'true'
    LOG_PERFORMANCE_METRICS = os.getenv('LOG_PERFORMANCE_METRICS', 'true').lower() == 'true'
    
    # =================================================================
    # УВЕДОМЛЕНИЯ
    # =================================================================
    
    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
    TELEGRAM_ENABLED = os.getenv('TELEGRAM_ENABLED', 'true').lower() == 'true'
    TELEGRAM_ENABLE_TRADE_ALERTS = os.getenv('TELEGRAM_ENABLE_TRADE_ALERTS', 'true').lower() == 'true'
    TELEGRAM_ENABLE_ERROR_ALERTS = os.getenv('TELEGRAM_ENABLE_ERROR_ALERTS', 'true').lower() == 'true'
    TELEGRAM_ENABLE_DAILY_SUMMARY = os.getenv('TELEGRAM_ENABLE_DAILY_SUMMARY', 'true').lower() == 'true'
    
    # Email
    EMAIL_SMTP_SERVER = os.getenv('EMAIL_SMTP_SERVER', 'smtp.gmail.com')
    EMAIL_SMTP_PORT = int(os.getenv('EMAIL_SMTP_PORT', '587'))
    EMAIL_USERNAME = os.getenv('EMAIL_USERNAME', '')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', '')
    EMAIL_FROM = os.getenv('EMAIL_FROM', '')
    EMAIL_TO = os.getenv('EMAIL_TO', '')
    
    # =================================================================
    # ВЕБ-ИНТЕРФЕЙС
    # =================================================================
    
    # Веб-сервер
    WEB_HOST = os.getenv('WEB_HOST', '0.0.0.0')
    WEB_PORT = int(os.getenv('WEB_PORT', '8000'))
    WEB_WORKERS = int(os.getenv('WEB_WORKERS', '1'))
    DEBUG_MODE = os.getenv('DEBUG_MODE', 'true').lower() == 'true'
    RELOAD_ON_CHANGE = os.getenv('RELOAD_ON_CHANGE', 'false').lower() == 'true'
    
    # Безопасность
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', '')
    JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
    JWT_EXPIRE_MINUTES = int(os.getenv('JWT_EXPIRE_MINUTES', '60'))
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '60'))
    
    # CORS
    ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', '*').split(',')
    ALLOWED_METHODS = os.getenv('ALLOWED_METHODS', 'GET,POST,PUT,DELETE,OPTIONS').split(',')
    ALLOWED_HEADERS = os.getenv('ALLOWED_HEADERS', '*').split(',')
    
    # =================================================================
    # АДМИНИСТРАТИВНЫЕ НАСТРОЙКИ
    # =================================================================
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
    ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@example.com')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')
    
    # =================================================================
    # ОПТИМИЗАЦИЯ ПАРАМЕТРОВ
    # =================================================================
    ENABLE_PARAMETER_OPTIMIZATION = os.getenv('ENABLE_PARAMETER_OPTIMIZATION', 'true').lower() == 'true'
    OPTIMIZATION_INTERVAL_DAYS = int(os.getenv('OPTIMIZATION_INTERVAL_DAYS', '7'))
    OPTIMIZATION_LOOKBACK_DAYS = int(os.getenv('OPTIMIZATION_LOOKBACK_DAYS', '90'))
    
    # Экспорт данных
    ENABLE_DATA_EXPORT = os.getenv('ENABLE_DATA_EXPORT', 'true').lower() == 'true'
    EXPORT_FORMAT = os.getenv('EXPORT_FORMAT', 'csv')
    AUTO_EXPORT_INTERVAL_HOURS = int(os.getenv('AUTO_EXPORT_INTERVAL_HOURS', '24'))
    
    # =================================================================
    # ⚠️ РЕЖИМ ИМИТАЦИИ ЧЕЛОВЕКА - КРИТИЧНО ВАЖНО! ⚠️
    # =================================================================
    
    # Основные настройки human behavior
    ENABLE_HUMAN_MODE = os.getenv('ENABLE_HUMAN_MODE', 'true').lower() == 'true'
    HUMAN_BEHAVIOR_ENABLED = os.getenv('HUMAN_BEHAVIOR_ENABLED', 'true').lower() == 'true'
    
    # Задержки для имитации человека
    MIN_DELAY_SECONDS = float(os.getenv('MIN_DELAY_SECONDS', '1.0'))
    MAX_DELAY_SECONDS = float(os.getenv('MAX_DELAY_SECONDS', '5.0'))
    HUMAN_MIN_DELAY = float(os.getenv('HUMAN_MIN_DELAY', '1.0'))
    HUMAN_MAX_DELAY = float(os.getenv('HUMAN_MAX_DELAY', '5.0'))
    
    # Вариативность поведения
    HUMAN_ERROR_RATE = float(os.getenv('HUMAN_ERROR_RATE', '0.02'))
    HUMAN_HESITATION_RATE = float(os.getenv('HUMAN_HESITATION_RATE', '0.05'))
    HUMAN_BREAK_PROBABILITY = float(os.getenv('HUMAN_BREAK_PROBABILITY', '0.02'))
    
    # Паттерны активности
    HUMAN_ACTIVITY_MORNING_START = int(os.getenv('HUMAN_ACTIVITY_MORNING_START', '6'))
    HUMAN_ACTIVITY_MORNING_END = int(os.getenv('HUMAN_ACTIVITY_MORNING_END', '12'))
    HUMAN_ACTIVITY_AFTERNOON_START = int(os.getenv('HUMAN_ACTIVITY_AFTERNOON_START', '12'))
    HUMAN_ACTIVITY_AFTERNOON_END = int(os.getenv('HUMAN_ACTIVITY_AFTERNOON_END', '18'))
    HUMAN_ACTIVITY_EVENING_START = int(os.getenv('HUMAN_ACTIVITY_EVENING_START', '18'))
    HUMAN_ACTIVITY_EVENING_END = int(os.getenv('HUMAN_ACTIVITY_EVENING_END', '23'))
    
    # Скорость "набора" и "чтения"
    HUMAN_TYPING_SPEED_MIN = float(os.getenv('HUMAN_TYPING_SPEED_MIN', '200'))
    HUMAN_TYPING_SPEED_MAX = float(os.getenv('HUMAN_TYPING_SPEED_MAX', '300'))
    HUMAN_READING_SPEED_MIN = float(os.getenv('HUMAN_READING_SPEED_MIN', '200'))
    HUMAN_READING_SPEED_MAX = float(os.getenv('HUMAN_READING_SPEED_MAX', '250'))
    
    # =================================================================
    # ДОПОЛНИТЕЛЬНЫЕ НЕДОСТАЮЩИЕ АТРИБУТЫ
    # =================================================================
    
    # WebSocket настройки
    ENABLE_WEBSOCKET = os.getenv('ENABLE_WEBSOCKET', 'true').lower() == 'true'
    WEBSOCKET_RECONNECT_DELAY = int(os.getenv('WEBSOCKET_RECONNECT_DELAY', '5'))
    WEBSOCKET_MAX_RETRIES = int(os.getenv('WEBSOCKET_MAX_RETRIES', '10'))
    
    # Real-time данные
    ENABLE_REAL_TIME_DATA = os.getenv('ENABLE_REAL_TIME_DATA', 'true').lower() == 'true'
    REAL_TIME_UPDATE_INTERVAL = int(os.getenv('REAL_TIME_UPDATE_INTERVAL', '1'))
    
    # Confidence scores
    MIN_CONFIDENCE_SCORE = float(os.getenv('MIN_CONFIDENCE_SCORE', '0.6'))
    CONFIDENCE_THRESHOLD = float(os.getenv('CONFIDENCE_THRESHOLD', '0.65'))
    
    # Расширенные торговые пары
    EXTENDED_TRADING_PAIRS = os.getenv(
        'EXTENDED_TRADING_PAIRS',
        'BTCUSDT,ETHUSDT,BNBUSDT,SOLUSDT,ADAUSDT,XRPUSDT,DOTUSDT,AVAXUSDT,MATICUSDT,LINKUSDT,'
        'UNIUSDT,LTCUSDT,BCHUSDT,ATOMUSDT,FILUSDT,XLMUSDT,VETUSDT,EOSUSDT,TRXUSDT,THETAUSDT,'
        'MKRUSDT,AAVEUSDT,COMPUSDT,SUSHIUSDT,YFIUSDT,SNXUSDT,CRVUSDT,BALREUSDT,UMAUSDT,RENUSDT,'
        'KNCUSDT,LRCUSDT,BANDUSDT,STORJUSDT,MANAUSDT,ENJUSDT,CHZUSDT,SANDUSDT,AXSUSDT,GALAUSDT,'
        'FTMUSDT,NEARUSDT,ONEUSDT,ZILUSDT,ICXUSDT,IOTAUSDT,ONTUSDT,QTUMUSDT,BATUSDT,ZECUSDT'
    ).split(',')
    
    # Новостные источники
    NEWS_SOURCES = os.getenv('NEWS_SOURCES', 'coindesk,cointelegraph,cryptonews').split(',')
    SENTIMENT_ANALYSIS_PROVIDER = os.getenv('SENTIMENT_ANALYSIS_PROVIDER', 'textblob')
    
    # Мониторинг системы
    SYSTEM_MONITORING_ENABLED = os.getenv('SYSTEM_MONITORING_ENABLED', 'true').lower() == 'true'
    MEMORY_MONITORING_INTERVAL = int(os.getenv('MEMORY_MONITORING_INTERVAL', '60'))
    CPU_MONITORING_INTERVAL = int(os.getenv('CPU_MONITORING_INTERVAL', '60'))
    
    # =================================================================
    # РАЗРАБОТКА И ОТЛАДКА
    # =================================================================
    ENABLE_PROFILING = os.getenv('ENABLE_PROFILING', 'false').lower() == 'true'
    ENABLE_METRICS = os.getenv('ENABLE_METRICS', 'true').lower() == 'true'
    METRICS_PORT = int(os.getenv('METRICS_PORT', '9090'))
    
    # Тестирование
    MOCK_TRADING = os.getenv('MOCK_TRADING', 'false').lower() == 'true'
    SIMULATE_LATENCY = os.getenv('SIMULATE_LATENCY', 'false').lower() == 'true'
    
    # Отладочные эндпоинты
    ENABLE_DEBUG_ENDPOINTS = os.getenv('ENABLE_DEBUG_ENDPOINTS', 'true').lower() == 'true'
    ENABLE_TEST_DATA = os.getenv('ENABLE_TEST_DATA', 'true').lower() == 'true'
    
    # Моковые данные
    USE_MOCK_EXCHANGE_DATA = os.getenv('USE_MOCK_EXCHANGE_DATA', 'false').lower() == 'true'
    USE_MOCK_ML_PREDICTIONS = os.getenv('USE_MOCK_ML_PREDICTIONS', 'false').lower() == 'true'
    USE_MOCK_NEWS_DATA = os.getenv('USE_MOCK_NEWS_DATA', 'false').lower() == 'true'
    
    # Ускорение для тестирования
    FAST_MODE_ENABLED = os.getenv('FAST_MODE_ENABLED', 'false').lower() == 'true'
    ANALYSIS_INTERVAL_FAST = int(os.getenv('ANALYSIS_INTERVAL_FAST', '10'))
    UPDATE_INTERVAL_FAST = int(os.getenv('UPDATE_INTERVAL_FAST', '5'))
    
    # =================================================================
    # ТЕХНИЧЕСКИЕ ИНДИКАТОРЫ
    # =================================================================
    
    # Глубина анализа
    TIMEFRAME = os.getenv('TIMEFRAME', '1h')
    ANALYSIS_DEPTH = int(os.getenv('ANALYSIS_DEPTH', '100'))
    
    # RSI
    RSI_PERIOD = int(os.getenv('RSI_PERIOD', '14'))
    RSI_OVERSOLD = int(os.getenv('RSI_OVERSOLD', '30'))
    RSI_OVERBOUGHT = int(os.getenv('RSI_OVERBOUGHT', '70'))
    
    # MACD
    MACD_FAST = int(os.getenv('MACD_FAST', '12'))
    MACD_SLOW = int(os.getenv('MACD_SLOW', '26'))
    MACD_SIGNAL = int(os.getenv('MACD_SIGNAL', '9'))
    
    # Bollinger Bands
    BB_PERIOD = int(os.getenv('BB_PERIOD', '20'))
    BB_STD = float(os.getenv('BB_STD', '2.0'))
    
    # Moving Averages
    SMA_PERIOD = int(os.getenv('SMA_PERIOD', '20'))
    EMA_FAST = int(os.getenv('EMA_FAST', '12'))
    EMA_SLOW = int(os.getenv('EMA_SLOW', '26'))
    
    # ATR
    ATR_PERIOD = int(os.getenv('ATR_PERIOD', '14'))
    
    # =================================================================
    # СПЕЦИФИЧНЫЕ НАСТРОЙКИ СТРАТЕГИЙ
    # =================================================================
    
    # Multi Indicator Strategy
    MULTI_INDICATOR_RSI_WEIGHT = float(os.getenv('MULTI_INDICATOR_RSI_WEIGHT', '0.3'))
    MULTI_INDICATOR_MACD_WEIGHT = float(os.getenv('MULTI_INDICATOR_MACD_WEIGHT', '0.3'))
    MULTI_INDICATOR_BB_WEIGHT = float(os.getenv('MULTI_INDICATOR_BB_WEIGHT', '0.2'))
    MULTI_INDICATOR_VOLUME_WEIGHT = float(os.getenv('MULTI_INDICATOR_VOLUME_WEIGHT', '0.2'))
    
    # Momentum Strategy
    MOMENTUM_LOOKBACK_PERIOD = int(os.getenv('MOMENTUM_LOOKBACK_PERIOD', '20'))
    MOMENTUM_THRESHOLD = float(os.getenv('MOMENTUM_THRESHOLD', '0.02'))
    
    # Mean Reversion Strategy
    MEAN_REVERSION_BOLLINGER_PERIOD = int(os.getenv('MEAN_REVERSION_BOLLINGER_PERIOD', '20'))
    MEAN_REVERSION_BOLLINGER_STD = float(os.getenv('MEAN_REVERSION_BOLLINGER_STD', '2.0'))
    MEAN_REVERSION_RSI_OVERSOLD = int(os.getenv('MEAN_REVERSION_RSI_OVERSOLD', '30'))
    MEAN_REVERSION_RSI_OVERBOUGHT = int(os.getenv('MEAN_REVERSION_RSI_OVERBOUGHT', '70'))
    
    # Breakout Strategy
    BREAKOUT_LOOKBACK_PERIOD = int(os.getenv('BREAKOUT_LOOKBACK_PERIOD', '20'))
    BREAKOUT_VOLUME_THRESHOLD = float(os.getenv('BREAKOUT_VOLUME_THRESHOLD', '1.5'))
    BREAKOUT_PRICE_THRESHOLD = float(os.getenv('BREAKOUT_PRICE_THRESHOLD', '0.02'))
    
    # Scalping Strategy
    SCALPING_TIMEFRAME = os.getenv('SCALPING_TIMEFRAME', '5m')
    SCALPING_PROFIT_TARGET = float(os.getenv('SCALPING_PROFIT_TARGET', '0.005'))
    SCALPING_STOP_LOSS = float(os.getenv('SCALPING_STOP_LOSS', '0.003'))
    
    # Swing Strategy
    SWING_TIMEFRAME = os.getenv('SWING_TIMEFRAME', '1h')
    SWING_PROFIT_TARGET = float(os.getenv('SWING_PROFIT_TARGET', '0.03'))
    SWING_STOP_LOSS = float(os.getenv('SWING_STOP_LOSS', '0.015'))
    
    # =================================================================
    # ДОПОЛНИТЕЛЬНЫЕ НАСТРОЙКИ
    # =================================================================
    
    # Интервалы мониторинга
    HEALTH_CHECK_INTERVAL = int(os.getenv('HEALTH_CHECK_INTERVAL', '300'))
    PERFORMANCE_LOG_INTERVAL = int(os.getenv('PERFORMANCE_LOG_INTERVAL', '3600'))
    STATS_UPDATE_INTERVAL = int(os.getenv('STATS_UPDATE_INTERVAL', '60'))
    
    # Лимиты памяти и производительности
    MAX_MEMORY_USAGE_MB = int(os.getenv('MAX_MEMORY_USAGE_MB', '2048'))
    MAX_CPU_USAGE_PERCENT = int(os.getenv('MAX_CPU_USAGE_PERCENT', '80'))
    
    # =================================================================
    # ОБРАТНАЯ СОВМЕСТИМОСТЬ
    # =================================================================
    
    # Алиасы для старых имен
    API_RATE_LIMIT = API_RATE_LIMIT_PER_MINUTE  
    
    # =================================================================
    # МЕТОДЫ ВАЛИДАЦИИ - РАСШИРЕННЫЕ
    # =================================================================
    
    @classmethod
    def get_active_trading_pairs(cls) -> List[str]:
        """Получение списка активных торговых пар"""
        return cls.TRADING_PAIRS[:cls.MAX_TRADING_PAIRS]
    
    @classmethod
    def validate_trading_config(cls):
        """
        Валидация конфигурации перед запуском торговли
        
        Raises:
            ValueError: При неверной конфигурации
        """
        errors = []
        
        # Проверяем взаимоисключающие режимы
        if cls.LIVE_TRADING and cls.PAPER_TRADING:
            errors.append("Нельзя включить одновременно LIVE_TRADING и PAPER_TRADING")
        
        if cls.LIVE_TRADING and cls.BACKTEST_MODE:
            errors.append("Нельзя включить одновременно LIVE_TRADING и BACKTEST_MODE")
        
        if cls.LIVE_TRADING and cls.DRY_RUN:
            errors.append("Нельзя включить одновременно LIVE_TRADING и DRY_RUN")
        
        # Для реальной торговли проверяем обязательные параметры
        if cls.LIVE_TRADING:
            required_env_vars = ['BYBIT_API_KEY', 'BYBIT_API_SECRET']
            missing = [key for key in required_env_vars if not os.getenv(key)]
            if missing:
                errors.append(f"Для реальной торговли нужны переменные окружения: {', '.join(missing)}")
        
        # Проверяем торговые лимиты
        if cls.MAX_POSITION_SIZE_USD <= 0:
            errors.append("MAX_POSITION_SIZE_USD должно быть больше 0")
        
        if cls.MAX_DAILY_TRADES <= 0:
            errors.append("MAX_DAILY_TRADES должно быть больше 0")
        
        if cls.ORDER_TIMEOUT_SECONDS <= 0:
            errors.append("ORDER_TIMEOUT_SECONDS должно быть больше 0")
        
        if cls.SLIPPAGE_TOLERANCE_PERCENT < 0:
            errors.append("SLIPPAGE_TOLERANCE_PERCENT не может быть отрицательным")
        
        # Проверяем стоп-лоссы
        if cls.EMERGENCY_STOP_LOSS_PERCENT <= 0:
            errors.append("EMERGENCY_STOP_LOSS_PERCENT должно быть больше 0")
        
        if cls.STOP_LOSS_PERCENT <= 0:
            errors.append("STOP_LOSS_PERCENT должно быть больше 0")
        
        # Проверяем риск-менеджмент
        if cls.MAX_RISK_PER_TRADE_PERCENT <= 0:
            errors.append("MAX_RISK_PER_TRADE_PERCENT должно быть больше 0")
        
        if cls.MAX_PORTFOLIO_RISK_PERCENT <= 0:
            errors.append("MAX_PORTFOLIO_RISK_PERCENT должно быть больше 0")
        
        # Выбрасываем исключение при наличии ошибок
        if errors:
            error_message = "❌ Ошибки конфигурации торговли:\n" + "\n".join(f"  - {error}" for error in errors)
            raise ValueError(error_message)
        
        # Логируем успешную валидацию
        mode = "LIVE TRADING" if cls.LIVE_TRADING else "PAPER TRADING" if cls.PAPER_TRADING else "BACKTEST MODE"
        logging.info(f"✅ Конфигурация торговли валидна для режима: {mode}")
        
        # Логируем важные лимиты безопасности
        if cls.LIVE_TRADING:
            logging.warning(f"🚨 РЕАЛЬНАЯ ТОРГОВЛЯ ВКЛЮЧЕНА!")
            logging.warning(f"💰 Максимальный размер позиции: ${cls.MAX_POSITION_SIZE_USD}")
            logging.warning(f"📊 Максимально сделок в день: {cls.MAX_DAILY_TRADES}")
            logging.warning(f"⏰ Таймаут ордеров: {cls.ORDER_TIMEOUT_SECONDS}с")
            logging.warning(f"🛑 Экстренный стоп-лосс: {cls.EMERGENCY_STOP_LOSS_PERCENT}%")
    
    @classmethod
    def validate_config(cls) -> bool:
        """
        Базовая валидация конфигурации
        
        Returns:
            bool: True если конфигурация валидна
        """
        errors = []
        
        # Проверяем обязательные параметры
        if not cls.BYBIT_API_KEY and not cls.TEST_MODE and not cls.PAPER_TRADING:
            errors.append("BYBIT_API_KEY не задан")
        
        if cls.MAX_POSITIONS <= 0:
            errors.append("MAX_POSITIONS должно быть больше 0")
        
        if cls.MAX_DAILY_TRADES <= 0:
            errors.append("MAX_DAILY_TRADES должно быть больше 0")
        
        # Проверяем логику стратегий
        if not cls.ENABLED_STRATEGIES:
            errors.append("Должна быть включена хотя бы одна стратегия")
        
        # Проверяем настройки ML
        if cls.ENABLE_MACHINE_LEARNING and cls.MIN_TRAINING_SAMPLES <= 0:
            errors.append("MIN_TRAINING_SAMPLES должно быть больше 0 при включенном ML")
        
        if errors:
            for error in errors:
                logging.error(f"❌ Ошибка конфигурации: {error}")
            return False
        
        logging.info("✅ Базовая конфигурация валидна")
        return True
    
    @classmethod
    def get_trading_mode_info(cls) -> Dict[str, Any]:
        """
        Получение информации о текущем режиме торговли
        
        Returns:
            Dict[str, Any]: Информация о режиме торговли
        """
        return {
            'live_trading': cls.LIVE_TRADING,
            'paper_trading': cls.PAPER_TRADING,
            'backtest_mode': cls.BACKTEST_MODE,
            'dry_run': cls.DRY_RUN,
            'test_mode': cls.TEST_MODE,
            'testnet': cls.BYBIT_TESTNET,
            'max_position_size_usd': cls.MAX_POSITION_SIZE_USD,
            'max_daily_trades': cls.MAX_DAILY_TRADES,
            'emergency_stop_loss_percent': cls.EMERGENCY_STOP_LOSS_PERCENT,
            'order_timeout_seconds': cls.ORDER_TIMEOUT_SECONDS,
            'slippage_tolerance_percent': cls.SLIPPAGE_TOLERANCE_PERCENT
        }
    
    @classmethod
    def is_safe_mode(cls) -> bool:
        """
        Проверяем, работает ли бот в безопасном режиме
        
        Returns:
            bool: True если в безопасном режиме (не реальная торговля)
        """
        return not cls.LIVE_TRADING
    
    def __repr__(self):
        mode = "LIVE" if self.LIVE_TRADING else "PAPER" if self.PAPER_TRADING else "BACKTEST"
        return f"<Config mode={mode} pairs={len(self.get_active_trading_pairs())} strategies={len(self.ENABLED_STRATEGIES)} testnet={self.BYBIT_TESTNET}>"

# Создаем экземпляры для экспорта
config = Config()
settings = config

# Экспорт
__all__ = ['Config', 'config', 'settings']