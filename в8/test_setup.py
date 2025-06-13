#!/usr/bin/env python3
# test_setup.py - Проверка настройки системы

import sys
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

print("🔍 Проверка настройки Crypto Trading Bot\n")

# 1. Проверка переменных окружения
print("1️⃣ Проверка переменных окружения:")
required_env = [
    'BYBIT_API_KEY',
    'BYBIT_API_SECRET', 
    'DB_HOST',
    'DB_NAME',
    'DB_USER',
    'DB_PASSWORD'
]

env_ok = True
for var in required_env:
    value = os.getenv(var)
    if value:
        if 'PASSWORD' in var or 'SECRET' in var:
            print(f"   ✅ {var}: ***hidden***")
        else:
            print(f"   ✅ {var}: {value}")
    else:
        print(f"   ❌ {var}: НЕ УСТАНОВЛЕНО")
        env_ok = False

# 2. Проверка подключения к БД
print("\n2️⃣ Проверка подключения к базе данных:")
try:
    from src.core.database import engine
    from sqlalchemy import text
    
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("   ✅ Подключение к MySQL успешно")
        
        # Проверяем таблицы
        result = conn.execute(text("SHOW TABLES"))
        tables = [row[0] for row in result]
        if tables:
            print(f"   ✅ Найдено таблиц: {len(tables)}")
            for table in tables:
                print(f"      - {table}")
        else:
            print("   ⚠️  Таблицы не созданы. Запустите: python init_db.py")
except Exception as e:
    print(f"   ❌ Ошибка подключения к БД: {e}")

# 3. Проверка Redis
print("\n3️⃣ Проверка Redis:")
try:
    import redis
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    r.ping()
    print("   ✅ Redis работает")
except Exception as e:
    print(f"   ❌ Redis не доступен: {e}")

# 4. Проверка Bybit API
print("\n4️⃣ Проверка Bybit API:")
try:
    from src.exchange.bybit_client import HumanizedBybitClient
    client = HumanizedBybitClient()
    
    if client.testnet:
        print("   ✅ Режим: TESTNET (безопасный режим)")
    else:
        print("   ⚠️  Режим: MAINNET (реальные деньги!)")
        
    # Проверяем подключение
    import asyncio
    async def check_connection():
        try:
            balance = await client.fetch_balance()
            if balance:
                print("   ✅ Подключение к Bybit API успешно")
                return True
        except Exception as e:
            print(f"   ❌ Ошибка API: {e}")
            return False
    
    asyncio.run(check_connection())
    
except Exception as e:
    print(f"   ❌ Ошибка импорта Bybit клиента: {e}")

# 5. Проверка стратегий
print("\n5️⃣ Проверка торговых стратегий:")
try:
    from src.strategies.simple_momentum import SimpleMomentumStrategy
    strategy = SimpleMomentumStrategy()
    print("   ✅ Momentum стратегия загружена")
except Exception as e:
    print(f"   ❌ Ошибка загрузки стратегии: {e}")

# Итог
print("\n" + "="*50)
if env_ok:
    print("✅ Базовая настройка завершена!")
    print("\n📝 Следующие шаги:")
    print("1. Получите API ключи на https://testnet.bybit.com")
    print("2. Обновите .env файл с вашими ключами")
    print("3. Запустите: python init_db.py")
    print("4. Запустите: ./start_bot.sh")
else:
    print("❌ Есть проблемы с настройкой. Исправьте ошибки выше.")