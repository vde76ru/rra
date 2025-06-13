
"""Единый скрипт проверки системы"""
import sys
import os
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from src.core.config import config
from src.core.database import engine

def check_system():
    """Полная проверка системы"""
    print("🔍 ПРОВЕРКА СИСТЕМЫ")
    print("=" * 50)
    
    errors = []
    warnings = []
    
    # 1. Проверка конфигурации
    print("\n1️⃣ Конфигурация:")
    if config.BYBIT_API_KEY and config.BYBIT_API_KEY != 'your_testnet_api_key_here':
        print("   ✅ API ключи настроены")
    else:
        errors.append("API ключи не настроены")
    
    print(f"   📊 Режим: {'TESTNET' if config.BYBIT_TESTNET else 'MAINNET'}")
    print(f"   💱 Торговые пары: {', '.join(config.TRADING_PAIRS)}")
    
    # 2. Проверка БД
    print("\n2️⃣ База данных:")
    try:
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            print("   ✅ Подключение успешно")
    except Exception as e:
        errors.append(f"Ошибка подключения к БД: {e}")
    
    # 3. Проверка зависимостей
    print("\n3️⃣ Зависимости:")
    required_packages = [
        'fastapi', 'uvicorn', 'ccxt', 'pandas', 
        'sqlalchemy', 'redis', 'telegram'
    ]
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"   ✅ {package}")
        except ImportError:
            errors.append(f"{package} не установлен")
    
    # Результаты
    print("\n" + "=" * 50)
    if errors:
        print(f"❌ Найдено ошибок: {len(errors)}")
        for error in errors:
            print(f"   • {error}")
        return False
    else:
        print("✅ Система готова к запуску!")
        return True

if __name__ == "__main__":
    if not check_system():
        sys.exit(1)