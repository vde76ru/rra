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

# Экспорт всех моделей
__all__ = [
    'Base',
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
    'Strategy',
    'TradeStatus',
    'OrderSide',
    'OrderType',
    'SignalAction'
]