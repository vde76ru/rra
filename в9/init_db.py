#!/usr/bin/env python3
# init_db.py - Инициализация базы данных через SQLAlchemy

from src.core.database import engine
from src.core.models import Base

print("🔨 Создание таблиц через SQLAlchemy...")

try:
    # Создаем все таблицы
    Base.metadata.create_all(bind=engine)
    print("✅ Таблицы созданы успешно!")
    
    # Показываем созданные таблицы
    print("\n📊 Созданные таблицы:")
    for table in Base.metadata.tables:
        print(f"   - {table}")
        
except Exception as e:
    print(f"❌ Ошибка при создании таблиц: {e}")
    print("\nВозможно, таблицы уже существуют или есть проблема с подключением.")