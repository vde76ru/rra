#!/usr/bin/env python3
import sys

print("🔍 Полная проверка установки...")
print("=" * 50)

errors = []

# 1. Проверка импортов
print("\n1️⃣ Проверка пакетов...")
packages = [
    'fastapi', 'uvicorn', 'aiohttp', 'websockets',
    'ccxt', 'pandas', 'numpy', 'ta',
    'pymysql', 'sqlalchemy', 'redis',
    'passlib', 'jose', 'telegram',
    'dotenv', 'pydantic', 'sklearn'
]

for package in packages:
    try:
        __import__(package)
        print(f"   ✅ {package}")
    except ImportError:
        print(f"   ❌ {package}")
        errors.append(f"{package} не установлен")

# 2. Проверка БД
print("\n2️⃣ Проверка таблиц БД...")
try:
    from src.core.database import engine
    from sqlalchemy import text
    
    with engine.connect() as conn:
        result = conn.execute(text("SHOW TABLES"))
        tables = [row[0] for row in result]
        
        required_tables = ['trades', 'signals', 'balances', 'users', 'bot_settings', 'trading_pairs']
        
        for table in required_tables:
            if table in tables:
                print(f"   ✅ {table}")
            else:
                print(f"   ❌ {table}")
                errors.append(f"Таблица {table} отсутствует")
                
except Exception as e:
    print(f"   ❌ Ошибка БД: {e}")
    errors.append(str(e))

# Результат
print("\n" + "=" * 50)
if errors:
    print(f"❌ Найдено ошибок: {len(errors)}")
    for error in errors:
        print(f"   • {error}")
else:
    print("✅ Все компоненты установлены!")
    print("\n🎉 Система готова к запуску!")
    print("\nСледующие шаги:")
    print("1. Создайте пользователя: python create_user.py")
    print("2. Запустите бота: python main_advanced.py")
    print("3. Запустите веб-интерфейс: python app.py")