from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from datetime import datetime
from .database import Base

class Trade(Base):
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), index=True)
    side = Column(String(10))  # BUY/SELL
    entry_price = Column(Float)
    exit_price = Column(Float, nullable=True)
    quantity = Column(Float)
    profit = Column(Float, nullable=True)
    status = Column(String(20))  # OPEN/CLOSED
    strategy = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)

class Signal(Base):
    __tablename__ = "signals"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20))
    action = Column(String(10))  # BUY/SELL
    confidence = Column(Float)
    price = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    executed = Column(Boolean, default=False)