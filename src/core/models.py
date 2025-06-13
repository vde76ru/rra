"""
Модели базы данных
Путь: /var/www/www-root/data/www/systemetech.ru/src/core/models.py
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, Enum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base
import enum

class TradeStatus(enum.Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"

class OrderSide(enum.Enum):
    BUY = "BUY"
    SELL = "SELL"

class Trade(Base):
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), index=True, nullable=False)
    side = Column(Enum(OrderSide), nullable=False)
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=True)
    quantity = Column(Float, nullable=False)
    profit = Column(Float, nullable=True)
    profit_percent = Column(Float, nullable=True)
    status = Column(Enum(TradeStatus), default=TradeStatus.OPEN, nullable=False)
    strategy = Column(String(50), nullable=False)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    trailing_stop = Column(Boolean, default=False)
    commission = Column(Float, default=0)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    def calculate_profit(self):
        """Расчет прибыли"""
        if self.exit_price and self.entry_price:
            if self.side == OrderSide.BUY:
                self.profit = (self.exit_price - self.entry_price) * self.quantity - self.commission
            else:
                self.profit = (self.entry_price - self.exit_price) * self.quantity - self.commission
            
            self.profit_percent = (self.profit / (self.entry_price * self.quantity)) * 100
        return self.profit

class Signal(Base):
    __tablename__ = "signals"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    action = Column(String(10), nullable=False)
    confidence = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    strategy = Column(String(50), nullable=False)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    executed = Column(Boolean, default=False)
    executed_at = Column(DateTime, nullable=True)
    trade_id = Column(Integer, ForeignKey('trades.id'), nullable=True)

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(128), nullable=False)
    email = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    is_blocked = Column(Boolean, default=False)
    failed_login_attempts = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    blocked_at = Column(DateTime, nullable=True)
    
    trades = relationship("Trade", back_populates="user")

class TradingPair(Base):
    __tablename__ = "trading_pairs"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True)
    min_position_size = Column(Float, nullable=True)
    max_position_size = Column(Float, nullable=True)
    stop_loss_percent = Column(Float, default=2.0)
    take_profit_percent = Column(Float, default=4.0)
    strategy = Column(String(50), default='multi_indicator')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class BotState(Base):
    __tablename__ = "bot_state"
    
    id = Column(Integer, primary_key=True, index=True)
    is_running = Column(Boolean, default=False)
    start_time = Column(DateTime, nullable=True)
    stop_time = Column(DateTime, nullable=True)
    total_trades = Column(Integer, default=0)
    profitable_trades = Column(Integer, default=0)
    total_profit = Column(Float, default=0)
    current_balance = Column(Float, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Balance(Base):
    __tablename__ = "balances"
    
    id = Column(Integer, primary_key=True, index=True)
    currency = Column(String(10), nullable=False)
    total = Column(Float, nullable=False)
    free = Column(Float, nullable=False)
    used = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

class BotSettings(Base):
    __tablename__ = "bot_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(50), unique=True, index=True, nullable=False)
    value = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)