# Добавьте эти импорты в начало файла (после существующих)
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
import pandas as pd


from src.core.db_models import MLModel
from src.core.db_models import TradingPair
from src.core.db_models import Balance
from src.core.db_models import Signal
from src.core.db_models import Trade
from src.core.db_models import User
from src.core.db_models import BotState
from src.core.db_models import Base, TradingLog
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

# ===== ENUMS =====
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