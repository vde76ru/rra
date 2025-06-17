from sqlalchemy.ext.declarative import declarative_base
from typing import Optional, List, Dict, Any

# Добавьте эти импорты в начало файла (после существующих)
"""
Модели базы данных для Crypto Trading Bot
Путь: src/core/models.py

ВАЖНО: Этот файл содержит ТОЛЬКО модели SQLAlchemy без импортов других модулей проекта
для избежания циклических зависимостей
"""
from datetime import datetime
from enum import Enum
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, JSON, 
    ForeignKey, Enum as SQLEnum, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

# Создаем базовый класс для всех моделей
Base = declarative_base()

# ===== ENUMS =====


class Balance(Base):
    """Модель баланса пользователя"""
    __tablename__ = 'balances'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    currency = Column(String(10), nullable=False)
    amount = Column(Float, default=0.0)
    locked = Column(Float, default=0.0)
    exchange = Column(String(50), default='bybit')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship('User', back_populates='balances')
    
    def __repr__(self):
        return f'<Balance {self.currency}: {self.amount}>'

class TradeStatus(str, Enum):
    """Статусы сделок"""
    PENDING = "PENDING"
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"
    ERROR = "ERROR"

class OrderSide(str, Enum):
    """Направление сделки"""
    BUY = "BUY"
    SELL = "SELL"

class OrderType(str, Enum):
    """Тип ордера"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "STOP_LOSS"
    TAKE_PROFIT = "TAKE_PROFIT"

class SignalAction(str, Enum):
    """Действие сигнала"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

# ===== МОДЕЛИ =====

class MarketCondition(Base):
    """Состояние рынка"""
    __tablename__ = 'market_conditions'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False)
    timeframe = Column(String(20), nullable=False)
    condition_type = Column(String(50), nullable=False)
    condition_value = Column(String(50), nullable=False)
    strength = Column(Float)
    indicators = Column(JSON)
    timestamp = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=func.current_timestamp())
    
    __table_args__ = (
        Index('idx_symbol_timestamp', 'symbol', 'timestamp'),
        Index('idx_condition_type', 'condition_type'),
    )


class BotState(Base):
    """Состояние торгового бота"""
    __tablename__ = 'bot_state'
    
    id = Column(Integer, primary_key=True)
    bot_name = Column(String(50), nullable=False, default='main')
    status = Column(String(20), nullable=False, default='stopped')
    is_running = Column(Boolean, default=False)
    last_heartbeat = Column(DateTime, default=func.now())
    started_at = Column(DateTime)
    stopped_at = Column(DateTime)
    
    # Статистика
    total_trades = Column(Integer, default=0)
    successful_trades = Column(Integer, default=0)
    failed_trades = Column(Integer, default=0)
    total_profit = Column(Float, default=0.0)
    
    # Конфигурация
    active_strategy = Column(String(50))
    trading_pairs = Column(JSON)
    config = Column(JSON)
    
    # Состояние
    error_message = Column(Text)
    last_error_at = Column(DateTime)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<BotState(bot_name='{self.bot_name}', status='{self.status}', is_running={self.is_running})>"

class MLPrediction(Base):
    """ML предсказания"""
    __tablename__ = 'ml_predictions'
    
    id = Column(Integer, primary_key=True)
    model_id = Column(Integer, ForeignKey('ml_models.id'), nullable=False)
    symbol = Column(String(20), nullable=False)
    prediction_type = Column(String(50), nullable=False)
    prediction_value = Column(JSON, nullable=False)
    confidence = Column(Float, nullable=False)
    features_snapshot = Column(JSON)
    actual_outcome = Column(JSON)
    created_at = Column(DateTime, default=func.current_timestamp())
    
    __table_args__ = (
        Index('idx_model_symbol', 'model_id', 'symbol'),
        Index('idx_created_at', 'created_at'),
    )

# Дополнительные модели для полноты

class Order(Base):
    """Ордера на бирже"""
    __tablename__ = 'orders'
    
    id = Column(Integer, primary_key=True)
    exchange_order_id = Column(String(100), unique=True)
    symbol = Column(String(20), nullable=False)
    side = Column(String(10), nullable=False)
    order_type = Column(String(20), nullable=False)
    price = Column(Float)
    quantity = Column(Float, nullable=False)
    filled_quantity = Column(Float, default=0)
    status = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())
    trade_id = Column(Integer, ForeignKey('trades.id'))

class BotSettings(Base):
    """Настройки бота"""
    __tablename__ = 'bot_settings'
    
    id = Column(Integer, primary_key=True)
    key = Column(String(50), nullable=False, unique=True)
    value = Column(Text)
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())
    description = Column(Text)
    
    __table_args__ = (
        Index('idx_key', 'key'),
    )


class Strategy(Base):
    """Торговые стратегии"""
    __tablename__ = 'strategies'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    parameters = Column(JSON)
    min_confidence = Column(Float, default=0.6)
    max_positions = Column(Integer, default=1)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    __table_args__ = {'extend_existing': True}
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'is_active': self.is_active,
            'parameters': self.parameters,
            'min_confidence': self.min_confidence
        }
        
        
        
class TradingPair(Base):
    """Модель торговой пары"""
    __tablename__ = 'trading_pairs'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), unique=True, nullable=False, index=True)
    base_asset = Column(String(10), nullable=False)
    quote_asset = Column(String(10), nullable=False)
    is_active = Column(Boolean, default=True)
    min_order_size = Column(Float, default=10.0)
    max_order_size = Column(Float, default=10000.0)
    price_precision = Column(Integer, default=2)
    quantity_precision = Column(Integer, default=3)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    trades = relationship("Trade", back_populates="trading_pair", lazy='dynamic')
    signals = relationship("Signal", back_populates="trading_pair", lazy='dynamic')
    
    def __repr__(self):
        return f"<TradingPair {self.symbol}>"


class Trade(Base):
    """Модель сделки"""
    __tablename__ = 'trades'
    
    id = Column(Integer, primary_key=True)
    trading_pair_id = Column(Integer, ForeignKey('trading_pairs.id'), nullable=False)
    order_id = Column(String(100), unique=True, nullable=False)
    side = Column(String(10), nullable=False)  # BUY или SELL
    order_type = Column(String(20), nullable=False)  # MARKET, LIMIT и т.д.
    status = Column(String(20), nullable=False)  # PENDING, FILLED, CANCELLED
    
    # Цены и объемы
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    executed_quantity = Column(Float, default=0)
    executed_price = Column(Float)
    commission = Column(Float, default=0)
    commission_asset = Column(String(10))
    
    # Стратегия и сигналы
    strategy_name = Column(String(50))
    signal_id = Column(Integer, ForeignKey('signals.id'))
    
    # P&L
    realized_pnl = Column(Float, default=0)
    unrealized_pnl = Column(Float, default=0)
    pnl_percentage = Column(Float, default=0)
    
    # Stop Loss и Take Profit
    stop_loss = Column(Float)
    take_profit = Column(Float)
    
    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow)
    executed_at = Column(DateTime)
    closed_at = Column(DateTime)
    
    # ML предсказания
    ml_confidence = Column(Float)
    ml_prediction = Column(String(10))  # UP, DOWN, NEUTRAL
    
    # Связи
    trading_pair = relationship("TradingPair", back_populates="trades")
    signal = relationship("Signal", back_populates="trades")
    ml_predictions = relationship("TradeMLPrediction", back_populates="trade", lazy='dynamic')
    
    def __repr__(self):
        return f"<Trade {self.order_id} {self.side} {self.quantity} @ {self.price}>"
    
    @property
    def is_profitable(self):
        return self.realized_pnl > 0 if self.realized_pnl else False


class MLModel(Base):
    """Модель машинного обучения"""
    __tablename__ = 'ml_models'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    model_type = Column(String(50), nullable=False)  # neural_network, random_forest, etc.
    version = Column(String(20), nullable=False)
    
    # Параметры модели
    parameters = Column(JSON)
    features = Column(JSON)  # список используемых признаков
    
    # Метрики производительности
    accuracy = Column(Float)
    precision = Column(Float)
    recall = Column(Float)
    f1_score = Column(Float)
    
    # Данные обучения
    training_start = Column(DateTime)
    training_end = Column(DateTime)
    training_samples = Column(Integer)
    validation_samples = Column(Integer)
    
    # Статус
    status = Column(String(20), default='training')  # training, active, inactive, failed
    is_active = Column(Boolean, default=False)
    
    # Путь к файлу модели
    model_path = Column(String(255))
    
    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used_at = Column(DateTime)
    
    # Связи
    predictions = relationship("MLPrediction", back_populates="model", lazy='dynamic')
    
    def __repr__(self):
        return f"<MLModel {self.name} v{self.version}>"


class Candle:
    """
    Класс для представления торговой свечи (OHLCV данных)
    
    Этот класс НЕ является моделью БД - это обычный Python класс
    для работы с рыночными данными в памяти.
    
    Attributes:
        timestamp: Время свечи (Unix timestamp)
        open: Цена открытия
        high: Максимальная цена  
        low: Минимальная цена
        close: Цена закрытия
        volume: Объем торгов
        symbol: Торговая пара (например, 'BTC/USDT')
    """
    timestamp: int  # Unix timestamp в миллисекундах
    open: float
    high: float
    low: float
    close: float
    volume: float
    symbol: Optional[str] = None
    
    def __post_init__(self):
        """
        Проверка корректности данных свечи после создания
        
        Эта функция автоматически вызывается после __init__
        и помогает избежать некорректных данных
        """
        # Проверяем логику цен
        if self.high < max(self.open, self.close, self.low):
            raise ValueError(f"High ({self.high}) должен быть >= max(open, close, low)")
        
        if self.low > min(self.open, self.close, self.high):
            raise ValueError(f"Low ({self.low}) должен быть <= min(open, close, high)")
        
        # Проверяем положительность объема
        if self.volume < 0:
            raise ValueError(f"Volume ({self.volume}) не может быть отрицательным")
        
        # Проверяем положительность цен
        if any(price <= 0 for price in [self.open, self.high, self.low, self.close]):
            raise ValueError("Все цены должны быть положительными")
    
    @classmethod
    def from_ccxt(cls, ohlcv_data: List[float], symbol: Optional[str] = None) -> 'Candle':
        """
        Создание свечи из данных CCXT библиотеки
        
        Args:
            ohlcv_data: Список [timestamp, open, high, low, close, volume]
            symbol: Символ торговой пары
            
        Returns:
            Объект Candle
            
        Example:
            # Данные от биржи через CCXT
            ccxt_data = [1640995200000, 47000.0, 47500.0, 46800.0, 47200.0, 123.45]
            candle = Candle.from_ccxt(ccxt_data, "BTC/USDT")
        """
        if len(ohlcv_data) < 6:
            raise ValueError(f"CCXT данные должны содержать 6 элементов, получено: {len(ohlcv_data)}")
        
        return cls(
            timestamp=int(ohlcv_data[0]),
            open=float(ohlcv_data[1]),
            high=float(ohlcv_data[2]),
            low=float(ohlcv_data[3]),
            close=float(ohlcv_data[4]),
            volume=float(ohlcv_data[5]),
            symbol=symbol
        )
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], symbol: Optional[str] = None) -> 'Candle':
        """
        Создание свечи из словаря
        
        Args:
            data: Словарь с ключами: timestamp, open, high, low, close, volume
            symbol: Символ торговой пары
            
        Returns:
            Объект Candle
        """
        required_keys = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        missing_keys = [key for key in required_keys if key not in data]
        
        if missing_keys:
            raise ValueError(f"Отсутствуют обязательные ключи: {missing_keys}")
        
        return cls(
            timestamp=int(data['timestamp']),
            open=float(data['open']),
            high=float(data['high']),
            low=float(data['low']),
            close=float(data['close']),
            volume=float(data['volume']),
            symbol=symbol or data.get('symbol')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Преобразование свечи в словарь
        
        Returns:
            Словарь с данными свечи
        """
        return {
            'timestamp': self.timestamp,
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume,
            'symbol': self.symbol
        }
    
    def to_pandas_row(self) -> Dict[str, Any]:
        """
        Преобразование в формат для pandas DataFrame
        
        Returns:
            Словарь для добавления в DataFrame
        """
        return {
            'timestamp': pd.to_datetime(self.timestamp, unit='ms'),
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume
        }
    
    @property
    def datetime(self) -> datetime:
        """
        Получение объекта datetime из timestamp
        
        Returns:
            Объект datetime
        """
        return datetime.fromtimestamp(self.timestamp / 1000)
    
    @property
    def body_size(self) -> float:
        """
        Размер тела свечи (разница между open и close)
        
        Returns:
            Абсолютный размер тела свечи
        """
        return abs(self.close - self.open)
    
    @property
    def upper_shadow(self) -> float:
        """
        Размер верхней тени свечи
        
        Returns:
            Размер верхней тени
        """
        return self.high - max(self.open, self.close)
    
    @property
    def lower_shadow(self) -> float:
        """
        Размер нижней тени свечи
        
        Returns:
            Размер нижней тени
        """
        return min(self.open, self.close) - self.low
    
    @property
    def is_bullish(self) -> bool:
        """
        Проверка, является ли свеча бычьей (растущей)
        
        Returns:
            True если close > open
        """
        return self.close > self.open
    
    @property
    def is_bearish(self) -> bool:
        """
        Проверка, является ли свеча медвежьей (падающей)
        
        Returns:
            True если close < open
        """
        return self.close < self.open
    
    @property
    def is_doji(self) -> bool:
        """
        Проверка, является ли свеча доджи (open ≈ close)
        
        Returns:
            True если разница между open и close < 0.1% от цены
        """
        return self.body_size / max(self.open, self.close) < 0.001
    
    def __str__(self) -> str:
        """Строковое представление свечи"""
        direction = "📈" if self.is_bullish else "📉" if self.is_bearish else "🔄"
        return (f"Candle {direction} {self.symbol or 'Unknown'} "
                f"[O:{self.open:.2f} H:{self.high:.2f} L:{self.low:.2f} C:{self.close:.2f} V:{self.volume:.2f}]")
    
    def __repr__(self) -> str:
        """Техническое представление свечи"""
        return (f"Candle(timestamp={self.timestamp}, open={self.open}, "
                f"high={self.high}, low={self.low}, close={self.close}, "
                f"volume={self.volume}, symbol='{self.symbol}')")

# Экспорт всех моделей
# Обновите список экспорта в конце файла
__all__ = [
    'Base',
    'Candle',  # ← Добавьте эту строку
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
    'Strategy',
    'TradeStatus',
    'OrderSide',
    'OrderType',
    'SignalAction'
]

class TradingLog(Base):
    """Логи торговых операций"""
    __tablename__ = 'trading_logs'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=func.now())
    level = Column(String(20))  # INFO, WARNING, ERROR
    category = Column(String(50))  # trade, signal, risk, etc
    message = Column(Text)
    
    # Связанные данные
    trade_id = Column(Integer, ForeignKey('trades.id'))
    signal_id = Column(Integer, ForeignKey('signals.id'))
    symbol = Column(String(20))
    
    # Дополнительная информация
    details = Column(JSON)
    
    # Отношения
    trade = relationship("Trade", back_populates="logs")
    signal = relationship("Signal", back_populates="logs")
    
    def __repr__(self):
        return f"<TradingLog(timestamp={self.timestamp}, level='{self.level}', category='{self.category}')>"
