"""
Подключение к базе данных
Путь: /var/www/www-root/data/www/systemetech.ru/src/core/database.py
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import config

# Создаем engine с pool_pre_ping для автоматического переподключения
engine = create_engine(
    config.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Генератор сессии БД для FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()