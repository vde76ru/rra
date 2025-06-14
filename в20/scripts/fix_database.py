#!/usr/bin/env python3
"""
Скрипт для исправления структуры базы данных
"""
import sys
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.append(str(Path(__file__).parent.parent))

from src.core.database import engine
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_database():
    """Исправляем структуру базы данных"""
    
    with engine.connect() as conn:
        try:
            # ✅ ИСПРАВЛЕНИЕ: Проверяем существует ли колонка user_id
            result = conn.execute(text("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'trades' 
                AND COLUMN_NAME = 'user_id'
            """))
            
            if not result.fetchone():
                logger.info("🔧 Добавляем колонку user_id в таблицу trades...")
                
                # Добавляем колонку user_id (nullable, чтобы не сломать существующие записи)
                conn.execute(text("""
                    ALTER TABLE trades 
                    ADD COLUMN user_id INTEGER NULL 
                    COMMENT 'ID пользователя (может быть NULL для старых записей)'
                """))
                
                # Делаем commit
                conn.commit()
                logger.info("✅ Колонка user_id добавлена успешно")
            else:
                logger.info("✅ Колонка user_id уже существует")
                
        except Exception as e:
            logger.error(f"❌ Ошибка при исправлении БД: {e}")
            conn.rollback()
            raise

if __name__ == "__main__":
    print("🔧 ИСПРАВЛЕНИЕ СТРУКТУРЫ БАЗЫ ДАННЫХ")
    print("=" * 50)
    
    try:
        fix_database()
        print("✅ База данных исправлена успешно!")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        sys.exit(1)