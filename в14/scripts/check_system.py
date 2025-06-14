#!/usr/bin/env python3
"""Проверка системы"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_system_check():
    print("🔍 ПРОВЕРКА СИСТЕМЫ")
    print("=" * 50)
    
    # 1. Проверка конфигурации
    try:
        from src.core.config import config
        valid, errors = config.validate()
        if valid:
            print("✅ Конфигурация валидна")
        else:
            print("❌ Ошибки конфигурации:")
            for error in errors:
                print(f"   - {error}")
            return 1
    except Exception as e:
        print(f"❌ Не удалось загрузить конфигурацию: {e}")
        return 1
    
    # 2. Проверка импортов
    modules = [
        ('src.bot.manager', 'BotManager'),
        ('src.exchange.client', 'ExchangeClient'),
        ('src.web.app', 'app'),
        ('src.notifications.telegram', 'TelegramNotifier')
    ]
    
    for module_name, class_name in modules:
        try:
            module = __import__(module_name, fromlist=[class_name])
            getattr(module, class_name)
            print(f"✅ {module_name} - OK")
        except Exception as e:
            print(f"❌ {module_name} - {e}")
            return 1
    
    # 3. Проверка базы данных
    try:
        from src.core.database import engine
        engine.connect()
        print("✅ Подключение к БД - OK")
    except Exception as e:
        print(f"❌ Ошибка БД: {e}")
        return 1
    
    print("\n✅ Все проверки пройдены!")
    return 0

if __name__ == "__main__":
    sys.exit(run_system_check())
EOF