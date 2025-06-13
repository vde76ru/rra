#!/usr/bin/env python3
# test_installation.py - Проверка что всё установлено правильно

import sys
import os
from dotenv import load_dotenv

print("🔍 Проверка установки Crypto Trading Bot")
print("=" * 50)

# Загружаем переменные окружения
load_dotenv()

errors = []
warnings = []

# 1. Проверка импортов
print("\n1️⃣ Проверка Python пакетов...")
try:
    import fastapi
    print("   ✅ FastAPI")
except ImportError:
    errors.append("FastAPI не установлен")

try:
    import ccxt
    print("   ✅ CCXT")
except ImportError:
    errors.append("CCXT не установлен")

try:
    import pandas
    print("   ✅ Pandas")
except ImportError:
    errors.append("Pandas не установлен")

try:
    import redis
    print("   ✅ Redis")
except ImportError:
    errors.append("Redis не установлен")

try:
    import pymysql
    print("   ✅ PyMySQL")
except ImportError:
    errors.append("PyMySQL не установлен")

# 2. Проверка структуры проекта
print("\n2️⃣ Проверка структуры проекта...")
required_dirs = ['src', 'src/core', 'src/exchange', 'src/strategies', 'logs', 'data']
for dir_path in required_dirs:
    if os.path.exists(dir_path):
        print(f"   ✅ {dir_path}")
    else:
        errors.append(f"Директория {dir_path} не найдена")

# 3. Проверка конфигурации
print("\n3️⃣ Проверка конфигурации...")
if os.path.exists('.env'):
    print("   ✅ Файл .env найден")
    
    # Проверяем ключевые переменные
    required_vars = ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD', 'BYBIT_TESTNET']
    for var in required_vars:
        if os.getenv(var):
            print(f"   ✅ {var} установлен")
        else:
            warnings.append(f"{var} не установлен в .env")
    
    # Проверка API ключей
    if not os.getenv('BYBIT_API_KEY') or os.getenv('BYBIT_API_KEY') == 'your_testnet_api_key_here':
        warnings.append("BYBIT_API_KEY не настроен! Получите ключи на https://testnet.bybit.com")
else:
    errors.append("Файл .env не найден")

# 4. Проверка подключения к БД
print("\n4️⃣ Проверка подключения к БД...")
try:
    import pymysql
    connection = pymysql.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )
    connection.close()
    print("   ✅ Подключение к MySQL успешно")
except Exception as e:
    errors.append(f"Ошибка подключения к БД: {e}")

# 5. Проверка Redis
print("\n5️⃣ Проверка Redis...")
try:
    import redis
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    r.ping()
    print("   ✅ Redis работает")
except Exception as e:
    warnings.append(f"Redis недоступен: {e}")

# 6. Проверка прав на запись логов
print("\n6️⃣ Проверка прав на запись...")
try:
    test_file = 'logs/test.tmp'
    with open(test_file, 'w') as f:
        f.write('test')
    os.remove(test_file)
    print("   ✅ Права на запись в logs есть")
except Exception as e:
    errors.append(f"Нет прав на запись в logs: {e}")

# Результаты
print("\n" + "=" * 50)
print("📊 РЕЗУЛЬТАТЫ ПРОВЕРКИ:")
print("=" * 50)

if not errors and not warnings:
    print("\n✅ Всё отлично! Система готова к запуску.")
    print("\n🚀 Следующие шаги:")
    print("1. Добавьте API ключи Bybit в .env файл")
    print("2. Запустите бота: python main.py")
    print("3. Откройте веб-интерфейс: http://systemetech.ru:8001")
else:
    if errors:
        print(f"\n❌ Найдено критических ошибок: {len(errors)}")
        for error in errors:
            print(f"   • {error}")
    
    if warnings:
        print(f"\n⚠️  Предупреждений: {len(warnings)}")
        for warning in warnings:
            print(f"   • {warning}")
    
    print("\n❗ Исправьте ошибки перед запуском бота!")

print("\n" + "=" * 50)