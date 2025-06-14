"""
Гибридное подключение к базе данных MySQL
Поддерживает как синхронный, так и асинхронный доступ
"""
from typing import AsyncGenerator, Generator
from contextlib import asynccontextmanager, contextmanager

# ✅ Импорты для обоих подходов
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# ✅ Асинхронные импорты (опционально)
try:
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    ASYNC_AVAILABLE = True
except ImportError:
    ASYNC_AVAILABLE = False
    print("⚠️ Асинхронная поддержка недоступна, используем синхронный режим")

from .config import config

# ✅ СИНХРОННАЯ версия (основная, всегда работает)
engine = create_engine(
    config.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ✅ АСИНХРОННАЯ версия (если доступна)
if ASYNC_AVAILABLE:
    try:
        async_engine = create_async_engine(
            config.ASYNC_DATABASE_URL,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
            pool_recycle=3600,
            echo=False
        )
        AsyncSessionLocal = async_sessionmaker(
            async_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    except Exception as e:
        print(f"⚠️ Не удалось создать асинхронный engine: {e}")
        ASYNC_AVAILABLE = False

# ✅ Функции для FastAPI и веб-интерфейса

def get_db() -> Generator[Session, None, None]:
    """
    🎯 СИНХРОННАЯ версия для FastAPI
    Всегда работает, простая и надежная
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    🎯 АСИНХРОННАЯ версия для FastAPI
    Работает только если установлен aiomysql
    """
    if not ASYNC_AVAILABLE:
        raise RuntimeError("Асинхронная поддержка недоступна. Используйте get_db() вместо get_db_session()")
    
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# ✅ Прямое использование в коде

@contextmanager
def get_sync_db():
    """
    🔧 Синхронный контекстный менеджер
    
    Пример:
    with get_sync_db() as db:
        users = db.query(User).all()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

@asynccontextmanager
async def get_async_db():
    """
    🔧 Асинхронный контекстный менеджер
    
    Пример:
    async with get_async_db() as db:
        result = await db.execute(text("SELECT * FROM users"))
    """
    if not ASYNC_AVAILABLE:
        raise RuntimeError("Асинхронная поддержка недоступна")
    
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

# ✅ Функция инициализации
def init_database():
    """
    🚀 Синхронная инициализация базы данных
    """
    try:
        # Создаем таблицы если нужно
        Base.metadata.create_all(bind=engine)
        
        # Тестируем соединение
        with SessionLocal() as session:
            result = session.execute(text("SELECT 1")).scalar()
            if result == 1:
                print("✅ База данных MySQL подключена успешно (синхронно)")
                return True
    except Exception as e:
        print(f"❌ Ошибка подключения к MySQL: {e}")
        return False

async def init_database_async():
    """
    🚀 Асинхронная инициализация (если доступна)
    """
    if not ASYNC_AVAILABLE:
        return init_database()
    
    try:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1"))
            if result.scalar() == 1:
                print("✅ База данных MySQL подключена успешно (асинхронно)")
                return True
    except Exception as e:
        print(f"❌ Ошибка асинхронного подключения: {e}")
        return init_database()  # Fallback к синхронной версии

# ✅ Экспорт всех функций
__all__ = [
    'get_db',           # ✅ Основная функция для FastAPI
    'get_db_session',   # ✅ Асинхронная для FastAPI (если доступна)
    'get_sync_db',      # ✅ Синхронный контекстный менеджер
    'get_async_db',     # ✅ Асинхронный контекстный менеджер
    'init_database',    # ✅ Синхронная инициализация
    'init_database_async', # ✅ Асинхронная инициализация
    'SessionLocal',     # ✅ Для прямого использования
    'engine',          # ✅ Engine
    'Base'             # ✅ Базовый класс
]