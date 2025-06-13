#!/usr/bin/env python3
# check_install.py - Проверка установки пакетов

print("🔍 Проверка установленных пакетов...\n")

packages = [
    ('fastapi', 'FastAPI'),
    ('uvicorn', 'Uvicorn'),
    ('ccxt', 'CCXT'),
    ('pandas', 'Pandas'),
    ('sqlalchemy', 'SQLAlchemy'),
    ('redis', 'Redis'),
    ('dotenv', 'python-dotenv'),
]

all_ok = True

for module_name, display_name in packages:
    try:
        __import__(module_name)
        print(f"✅ {display_name} установлен")
    except ImportError:
        print(f"❌ {display_name} НЕ установлен")
        all_ok = False

print("\n" + "="*40)
if all_ok:
    print("✅ Все базовые пакеты установлены!")
else:
    print("❌ Некоторые пакеты отсутствуют. Установите их через pip.")