"""
Database module с поддержкой SessionLocal для обратной совместимости
"""
import os
from contextlib import contextmanager
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
from dotenv import load_dotenv
import logging

# Загружаем переменные окружения
for env_path in ['/etc/crypto/config/.env', '.env']:
    if os.path.exists(env_path):
        load_dotenv(env_path)
        break

logger = logging.getLogger(__name__)

class Database:
    """Singleton класс для работы с базой данных"""
    
    _instance = None
    _engine = None
    _metadata = None
    _SessionLocal = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Инициализация подключения к БД"""
        if self._engine is None:
            self.database_url = os.getenv('DATABASE_URL')
            if not self.database_url:
                # Формируем URL из отдельных параметров
                db_host = os.getenv('DB_HOST', 'localhost')
                db_port = os.getenv('DB_PORT', '3306')
                db_user = os.getenv('DB_USER')
                db_pass = os.getenv('DB_PASSWORD')
                db_name = os.getenv('DB_NAME')
                
                if db_user and db_pass and db_name:
                    self.database_url = f"mysql+pymysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}?charset=utf8mb4"
                else:
                    # Fallback на SQLite
                    self.database_url = "sqlite:///./crypto_bot.db"
                    logger.warning("Используется SQLite база данных")
            
            # Создаем engine
            self._engine = create_engine(
                self.database_url,
                pool_pre_ping=True,
                echo=False
            )
            
            # Единый metadata для всех таблиц
            self._metadata = MetaData()
            
            # Создаем SessionLocal для обратной совместимости
            self._SessionLocal = sessionmaker(
                bind=self._engine,
                autocommit=False,
                autoflush=False
            )
            
            # Scoped session
            self.Session = scoped_session(self._SessionLocal)
            
            logger.info("✅ Database инициализирована")
    
    @property
    def engine(self):
        """Получить engine"""
        return self._engine
    
    @property
    def metadata(self):
        """Получить metadata"""
        return self._metadata
    
    @contextmanager
    def get_session(self):
        """Контекстный менеджер для сессии"""
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Ошибка в сессии БД: {e}")
            raise
        finally:
            session.close()
    
    def create_session(self):
        """Создать новую сессию"""
        return self.Session()
    
    def close(self):
        """Закрыть все соединения"""
        self.Session.remove()
        if self._engine:
            self._engine.dispose()

# Создаем глобальный экземпляр
db = Database()

# Экспортируем для обратной совместимости
engine = db.engine
metadata = db.metadata
get_session = db.get_session
create_session = db.create_session
SessionLocal = db._SessionLocal  # ВАЖНО: экспортируем SessionLocal!

# Дополнительные функции для совместимости
def get_db():
    """Генератор сессий для FastAPI"""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        
# Декоратор для транзакций
def transaction(func):
    """Декоратор для выполнения функции в транзакции"""
    def wrapper(*args, **kwargs):
        session = SessionLocal()
        try:
            result = func(session, *args, **kwargs)
            session.commit()
            return result
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()
    return wrapper

__all__ = [
    'Database',
    'db',
    'engine',
    'metadata',
    'get_session',
    'create_session',
    'SessionLocal',  # Добавляем в экспорт
    'get_db'
]
