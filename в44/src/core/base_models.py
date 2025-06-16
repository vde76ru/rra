"""
Базовые модели для избежания циклических импортов
"""
from sqlalchemy import Column, Integer, Boolean, Float, DateTime, String, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class BotState(Base):
    """Состояние торгового бота"""
    __tablename__ = 'bot_state'
    
    id = Column(Integer, primary_key=True)
    is_running = Column(Boolean, default=False)
    start_time = Column(DateTime)
    stop_time = Column(DateTime)
    total_trades = Column(Integer, default=0)
    profitable_trades = Column(Integer, default=0)
    total_profit = Column(Float, default=0.0)
    current_balance = Column(Float, default=0.0)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def to_dict(self):
        """Преобразование в словарь для API"""
        return {
            'id': self.id,
            'is_running': self.is_running,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'stop_time': self.stop_time.isoformat() if self.stop_time else None,
            'total_trades': self.total_trades,
            'profitable_trades': self.profitable_trades,
            'total_profit': self.total_profit,
            'current_balance': self.current_balance,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
