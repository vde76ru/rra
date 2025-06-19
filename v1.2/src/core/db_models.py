"""
Единый модуль со всеми моделями БД
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, JSON, create_engine
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import os

# Создаем Base
Base = declarative_base()

class TradingLog(Base):
    """Логи торговых операций"""
    __tablename__ = 'trading_logs'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    action = Column(String(50))
    symbol = Column(String(20))
    price = Column(Float)
    amount = Column(Float)
    side = Column(String(10))
    order_id = Column(String(100))
    status = Column(String(50))
    profit_loss = Column(Float, default=0)
    balance_after = Column(Float)
    details = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class BotState(Base):
    """Состояние бота"""
    __tablename__ = 'bot_state'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    is_running = Column(Boolean, default=False)
    current_strategy = Column(String(100))
    last_update = Column(DateTime, default=datetime.utcnow)
    total_profit = Column(Float, default=0)
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    config = Column(JSON)

class Trade(Base):
    """История сделок"""
    __tablename__ = 'trades'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20))
    side = Column(String(10))
    entry_price = Column(Float)
    exit_price = Column(Float)
    quantity = Column(Float)
    profit = Column(Float, default=0)
    profit_percent = Column(Float, default=0)
    strategy = Column(String(100))
    entry_time = Column(DateTime)
    exit_time = Column(DateTime)
    status = Column(String(20), default='open')
    stop_loss = Column(Float)
    take_profit = Column(Float)
    fees = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class Signal(Base):
    """Торговые сигналы"""
    __tablename__ = 'signals'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20))
    signal_type = Column(String(10))
    strategy = Column(String(100))
    strength = Column(Float, default=0)
    price = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    indicators = Column(JSON)
    executed = Column(Boolean, default=False)

class Balance(Base):
    """История баланса"""
    __tablename__ = 'balances'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    total_balance = Column(Float)
    free_balance = Column(Float)
    locked_balance = Column(Float, default=0)
    profit_loss = Column(Float, default=0)
    currency = Column(String(10), default='USDT')

class TradingPair(Base):
    """Торговые пары"""
    __tablename__ = 'trading_pairs'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), unique=True)
    base_asset = Column(String(10))
    quote_asset = Column(String(10))
    is_active = Column(Boolean, default=True)
    min_order_size = Column(Float)
    price_precision = Column(Integer)
    quantity_precision = Column(Integer)
    last_price = Column(Float)
    volume_24h = Column(Float)
    updated_at = Column(DateTime, default=datetime.utcnow)

class MLModel(Base):
    """ML модели"""
    __tablename__ = 'ml_models'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100))
    model_type = Column(String(50))
    accuracy = Column(Float)
    parameters = Column(JSON)
    training_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

class User(Base):
    """Пользователи системы"""
    __tablename__ = 'users'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True)
    email = Column(String(200), unique=True)
    password_hash = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)

# Функции для работы с БД
def get_engine():
    """Получить engine базы данных"""
    from src.core.database import engine
    return engine

def get_session():
    """Получить сессию базы данных"""
    from src.core.database import create_session
    return create_session()

def create_all_tables():
    """Создать все таблицы в БД"""
    try:
        engine = get_engine()
        Base.metadata.create_all(engine)
        print("✅ Все таблицы созданы успешно")
        return True
    except Exception as e:
        print(f"❌ Ошибка создания таблиц: {e}")
        return False

# Экспортируем все модели и функции
__all__ = [
    'Base',
    'TradingLog',
    'BotState',
    'Trade',
    'Signal',
    'Balance',
    'TradingPair',
    'MLModel',
    'User',
    'get_engine',
    'get_session',
    'create_all_tables'
]
