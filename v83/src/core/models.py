"""
Модели базы данных для криптовалютного торгового бота
"""
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, JSON, Index, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from passlib.context import CryptContext
from flask_login import UserMixin

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

Base = declarative_base()


# Enums
class TradeStatus(str, Enum):
    """Статусы сделок"""
    NEW = "NEW"
    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class OrderSide(str, Enum):
    """Направление сделки"""
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    """Тип ордера"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"


class SignalAction(str, Enum):
    """Действия сигнала"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class User(Base):
    """
    Модель пользователя - ИСПРАВЛЕННАЯ ВЕРСИЯ
    Включает все необходимые поля и методы безопасности
    """
    __tablename__ = 'users'
    
    
    
    # Основные поля (соответствуют структуре БД)
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), nullable=True)  # nullable=True как в БД
    hashed_password = Column(String(128), nullable=False)  # Размер как в БД
    
    # Статусы пользователя (соответствуют БД)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    is_blocked = Column(Boolean, default=False)         # 🆕 Из БД
    
    # Безопасность (соответствуют БД)
    failed_login_attempts = Column(Integer, default=0)  # 🆕 Из БД
    
    # Временные метки (соответствуют БД)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)        # 🆕 Вместо updated_at
    blocked_at = Column(DateTime, nullable=True)        # 🆕 Из БД
    
    # Отношения (как в оригинале)
    bot_settings = relationship("BotSettings", back_populates="user", cascade="all, delete-orphan")
    trades = relationship("Trade", back_populates="user", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        """Конструктор с безопасными значениями по умолчанию"""
        super().__init__(**kwargs)
        # Устанавливаем значения по умолчанию, если не заданы
        if not hasattr(self, 'is_active') or self.is_active is None:
            self.is_active = True
        if not hasattr(self, 'is_admin') or self.is_admin is None:
            self.is_admin = False
        if not hasattr(self, 'is_blocked') or self.is_blocked is None:
            self.is_blocked = False
        if not hasattr(self, 'failed_login_attempts') or self.failed_login_attempts is None:
            self.failed_login_attempts = 0

    def check_password(self, password: str) -> bool:
        """
        Проверяем пароль пользователя
        
        Args:
            password (str): Пароль для проверки
            
        Returns:
            bool: True если пароль верный, False если неверный
        """
        if not password:
            return False
            
        try:
            return pwd_context.verify(password, self.hashed_password)
        except Exception as e:
            print(f"⚠️ Ошибка проверки пароля для пользователя {self.username}: {e}")
            return False

    def set_password(self, password: str) -> None:
        """
        Устанавливаем новый пароль (с хешированием)
        
        Args:
            password (str): Новый пароль
            
        Raises:
            ValueError: Если пароль пустой или слишком короткий
        """
        if not password:
            raise ValueError("Пароль не может быть пустым")
        
        if len(password) < 6:
            raise ValueError("Пароль должен содержать минимум 6 символов")
        
        try:
            self.hashed_password = pwd_context.hash(password)
        except Exception as e:
            raise ValueError(f"Ошибка хеширования пароля: {e}")

    def record_failed_login(self) -> None:
        """
        Записываем неудачную попытку входа
        Блокируем пользователя после 5 неудачных попыток
        """
        self.failed_login_attempts = (self.failed_login_attempts or 0) + 1
        
        # Блокируем после 5 неудачных попыток
        if self.failed_login_attempts >= 5:
            self.is_blocked = True
            self.blocked_at = datetime.utcnow()

    def reset_failed_logins(self) -> None:
        """
        Сбрасываем счётчик неудачных попыток при успешном входе
        Также записываем время последнего входа
        """
        self.failed_login_attempts = 0
        self.last_login = datetime.utcnow()
        
        # Если пользователь был заблокирован, разблокируем
        if self.is_blocked:
            self.is_blocked = False
            self.blocked_at = None

    def is_account_locked(self) -> bool:
        """
        Проверяем, заблокирован ли аккаунт
        
        Returns:
            bool: True если заблокирован, False если нет
        """
        return bool(self.is_blocked) or not bool(self.is_active)

    def can_login(self) -> tuple[bool, str]:
        """
        Проверяем, может ли пользователь войти в систему
        
        Returns:
            tuple[bool, str]: (можно_ли_войти, причина_запрета_или_OK)
        """
        if not self.is_active:
            return False, "Аккаунт деактивирован администратором"
        
        if self.is_blocked:
            return False, "Аккаунт заблокирован из-за превышения попыток входа"
        
        attempts = self.failed_login_attempts or 0
        if attempts >= 5:
            return False, "Слишком много неудачных попыток входа"
        
        return True, "OK"

    def get_remaining_attempts(self) -> int:
        """
        Получаем количество оставшихся попыток входа
        
        Returns:
            int: Количество оставшихся попыток (0-5)
        """
        attempts = self.failed_login_attempts or 0
        return max(0, 5 - attempts)

    def to_dict(self, include_sensitive: bool = False) -> dict:
        """
        Преобразуем объект в словарь для JSON ответов
        
        Args:
            include_sensitive (bool): Включать ли чувствительные данные
            
        Returns:
            dict: Словарь с данными пользователя
        """
        result = {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_active': bool(self.is_active),
            'is_admin': bool(self.is_admin),
            'is_blocked': bool(self.is_blocked),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
        }
        
        # Добавляем чувствительные данные только при необходимости
        if include_sensitive:
            result.update({
                'failed_login_attempts': self.failed_login_attempts or 0,
                'blocked_at': self.blocked_at.isoformat() if self.blocked_at else None,
                'remaining_attempts': self.get_remaining_attempts()
            })
        
        return result

    def __repr__(self) -> str:
        """Строковое представление объекта для отладки"""
        return f"<User(id={self.id}, username='{self.username}', active={self.is_active})>"

    def __str__(self) -> str:
        """Человекочитаемое представление"""
        status = "активен" if self.is_active else "неактивен"
        if self.is_blocked:
            status = "заблокирован"
        return f"Пользователь: {self.username} ({status})"
        
    def get_id(self):
        """Возвращает ID пользователя как строку для Flask-Login"""
        return str(self.id)
    
    @property
    def is_authenticated(self):
        """Проверка, аутентифицирован ли пользователь"""
        return True  # Всегда True для залогиненных пользователей
    
    @property
    def is_anonymous(self):
        """Проверка, анонимный ли пользователь"""
        return False  # Всегда False для реальных пользователей
    
    # is_active уже есть в вашей модели, но убедитесь что это свойство:
    @property
    def is_active(self):
        """Активен ли пользователь"""
        return bool(self._is_active if hasattr(self, '_is_active') else True)


class BotSettings(Base):
    """Настройки бота для каждого пользователя"""
    __tablename__ = 'bot_settings'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    strategy = Column(String(50), default='multi_indicator')
    risk_level = Column(Float, default=0.02)
    max_positions = Column(Integer, default=1)
    position_size = Column(Float, default=100.0)
    stop_loss_percent = Column(Float, default=2.0)
    take_profit_percent = Column(Float, default=4.0)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Отношения
    user = relationship("User", back_populates="bot_settings")


class BotState(Base):
    """Состояние бота"""
    __tablename__ = 'bot_state'
    
    id = Column(Integer, primary_key=True)
    is_running = Column(Boolean, default=False)
    last_heartbeat = Column(DateTime)
    current_strategy = Column(String(50))
    total_trades = Column(Integer, default=0)
    successful_trades = Column(Integer, default=0)
    failed_trades = Column(Integer, default=0)
    total_profit = Column(Float, default=0.0)
    start_time = Column(DateTime)
    stop_time = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Balance(Base):
    """Балансы пользователей"""
    __tablename__ = 'balances'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    asset = Column(String(20), nullable=False)
    free = Column(Float, default=0.0)
    locked = Column(Float, default=0.0)
    total = Column(Float, default=0.0)
    usd_value = Column(Float, default=0.0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_user_asset', 'user_id', 'asset', unique=True),
    )


class TradingPair(Base):
    """Торговые пары"""
    __tablename__ = 'trading_pairs'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), unique=True, nullable=False)
    base_asset = Column(String(10), nullable=False)
    quote_asset = Column(String(10), nullable=False)
    is_active = Column(Boolean, default=True)
    min_order_size = Column(Float)
    max_order_size = Column(Float)
    price_precision = Column(Integer)
    quantity_precision = Column(Integer)
    status = Column(String(20), default='TRADING')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Signal(Base):
    """Торговые сигналы"""
    __tablename__ = 'signals'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False)
    strategy = Column(String(50), nullable=False)
    action = Column(String(10), nullable=False)  # BUY, SELL, HOLD
    price = Column(Float, nullable=False)
    confidence = Column(Float, default=0.0)
    indicators = Column(JSON)  # Значения индикаторов
    reason = Column(Text)
    is_executed = Column(Boolean, default=False)
    executed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Отношения
    trades = relationship("Trade", back_populates="signal")
    
    __table_args__ = (
        Index('idx_signal_symbol_created', 'symbol', 'created_at'),
        Index('idx_signal_strategy', 'strategy'),
    )


class Trade(Base):
    """История сделок"""
    __tablename__ = 'trades'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    signal_id = Column(Integer, ForeignKey('signals.id'))
    symbol = Column(String(20), nullable=False)
    side = Column(String(10), nullable=False)  # BUY, SELL
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    total = Column(Float, nullable=False)
    fee = Column(Float, default=0.0)
    fee_asset = Column(String(10))
    status = Column(String(20), default='NEW')  # NEW, FILLED, CANCELLED
    order_id = Column(String(100))
    strategy = Column(String(50))
    stop_loss = Column(Float)
    take_profit = Column(Float)
    profit_loss = Column(Float)
    profit_loss_percent = Column(Float)
    close_price = Column(Float)
    close_time = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Отношения
    user = relationship("User", back_populates="trades")
    signal = relationship("Signal", back_populates="trades")
    ml_predictions = relationship("TradeMLPrediction", back_populates="trade")
    
    __table_args__ = (
        Index('idx_trade_user_created', 'user_id', 'created_at'),
        Index('idx_trade_symbol', 'symbol'),
    )


class Order(Base):
    """Активные ордера"""
    __tablename__ = 'orders'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    exchange_order_id = Column(String(100), unique=True)
    symbol = Column(String(20), nullable=False)
    side = Column(String(10), nullable=False)
    type = Column(String(20), nullable=False)
    quantity = Column(Float, nullable=False)
    price = Column(Float)
    stop_price = Column(Float)
    status = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Candle(Base):
    """Свечи для анализа"""
    __tablename__ = 'candles'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False)
    interval = Column(String(10), nullable=False)
    open_time = Column(DateTime, nullable=False)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    close_time = Column(DateTime, nullable=False)
    
    __table_args__ = (
        Index('idx_candle_symbol_time', 'symbol', 'interval', 'open_time', unique=True),
    )


class MarketCondition(Base):
    """Рыночные условия"""
    __tablename__ = 'market_conditions'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False)
    trend = Column(String(20))  # BULLISH, BEARISH, SIDEWAYS
    volatility = Column(String(20))  # LOW, MEDIUM, HIGH
    volume_trend = Column(String(20))  # INCREASING, DECREASING, STABLE
    support_level = Column(Float)
    resistance_level = Column(Float)
    rsi = Column(Float)
    macd_signal = Column(String(20))
    market_phase = Column(String(30))  # ACCUMULATION, MARKUP, DISTRIBUTION, MARKDOWN
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_market_symbol_created', 'symbol', 'created_at'),
    )


class StrategyPerformance(Base):
    """Производительность стратегий"""
    __tablename__ = 'strategy_performance'
    
    id = Column(Integer, primary_key=True)
    strategy_name = Column(String(50), nullable=False)
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    win_rate = Column(Float, default=0.0)
    total_profit = Column(Float, default=0.0)
    total_loss = Column(Float, default=0.0)
    net_profit = Column(Float, default=0.0)
    avg_profit = Column(Float, default=0.0)
    avg_loss = Column(Float, default=0.0)
    profit_factor = Column(Float, default=0.0)
    sharpe_ratio = Column(Float, default=0.0)
    max_drawdown = Column(Float, default=0.0)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_strategy_performance', 'strategy_name'),
    )


class MLModel(Base):
    """Модели машинного обучения"""
    __tablename__ = 'ml_models'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    model_type = Column(String(50), nullable=False)  # LSTM, GRU, TRANSFORMER, etc.
    version = Column(String(20))
    accuracy = Column(Float)
    precision = Column(Float)
    recall = Column(Float)
    f1_score = Column(Float)
    parameters = Column(JSON)
    feature_importance = Column(JSON)
    training_data_size = Column(Integer)
    is_active = Column(Boolean, default=False)
    model_path = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MLPrediction(Base):
    """Предсказания ML моделей"""
    __tablename__ = 'ml_predictions'
    
    id = Column(Integer, primary_key=True)
    model_id = Column(Integer, ForeignKey('ml_models.id'))
    symbol = Column(String(20), nullable=False)
    prediction = Column(String(20), nullable=False)  # BUY, SELL, HOLD
    confidence = Column(Float, nullable=False)
    predicted_price = Column(Float)
    actual_price = Column(Float)
    features = Column(JSON)
    is_correct = Column(Boolean)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_ml_prediction_symbol', 'symbol'),
        Index('idx_ml_prediction_created', 'created_at'),
    )


class TradeMLPrediction(Base):
    """ML предсказания для конкретных сделок"""
    __tablename__ = 'trade_ml_predictions'
    
    id = Column(Integer, primary_key=True)
    trade_id = Column(Integer, ForeignKey('trades.id'), nullable=False)
    model_name = Column(String(50), nullable=False)
    prediction = Column(String(20), nullable=False)
    confidence = Column(Float, nullable=False)
    predicted_profit = Column(Float)
    actual_profit = Column(Float)
    features_used = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Отношения
    trade = relationship("Trade", back_populates="ml_predictions")


class NewsAnalysis(Base):
    """Анализ новостей"""
    __tablename__ = 'news_analysis'
    
    id = Column(Integer, primary_key=True)
    source = Column(String(50), nullable=False)
    title = Column(Text, nullable=False)
    content = Column(Text)
    url = Column(String(500))
    sentiment = Column(String(20))  # POSITIVE, NEGATIVE, NEUTRAL
    sentiment_score = Column(Float)
    impact_score = Column(Float)
    related_symbols = Column(JSON)
    keywords = Column(JSON)
    published_at = Column(DateTime)
    analyzed_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_news_published', 'published_at'),
        Index('idx_news_sentiment', 'sentiment'),
    )


class SocialSignal(Base):
    """Социальные сигналы"""
    __tablename__ = 'social_signals'
    
    id = Column(Integer, primary_key=True)
    platform = Column(String(30), nullable=False)  # TWITTER, REDDIT, TELEGRAM
    symbol = Column(String(20))
    content = Column(Text)
    author = Column(String(100))
    sentiment = Column(String(20))
    sentiment_score = Column(Float)
    engagement_score = Column(Float)
    followers_count = Column(Integer)
    is_influencer = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_social_symbol', 'symbol'),
        Index('idx_social_platform', 'platform'),
    )


class TradingLog(Base):
    """Логи торговых операций"""
    __tablename__ = 'trading_logs'
    
    id = Column(Integer, primary_key=True)
    level = Column(String(10), nullable=False)  # INFO, WARNING, ERROR
    category = Column(String(50))  # TRADE, SIGNAL, API, SYSTEM
    message = Column(Text, nullable=False)
    details = Column(JSON)
    error_traceback = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_log_level', 'level'),
        Index('idx_log_category', 'category'),
        Index('idx_log_created', 'created_at'),
    )


# Экспорт всех моделей
__all__ = [
    'Base',
    # Enums
    'TradeStatus',
    'OrderSide',
    'OrderType',
    'SignalAction',
    # Models
    'User',
    'BotSettings',
    'BotState',
    'Balance',
    'TradingPair',
    'Signal',
    'Trade',
    'Order',
    'Candle',
    'MarketCondition',
    'StrategyPerformance',
    'MLModel',
    'MLPrediction',
    'TradeMLPrediction',
    'NewsAnalysis',
    'SocialSignal',
    'TradingLog'
]