#!/usr/bin/env python3
"""
Скрипт для проверки всех исправлений - УЛУЧШЕННАЯ ВЕРСИЯ
Файл: verify_fixes.py
"""
import sys
import os
import warnings
import importlib
from pathlib import Path

# Подавляем предупреждения перед импортами
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
warnings.filterwarnings('ignore', message='pkg_resources is deprecated')
warnings.filterwarnings('ignore', category=DeprecationWarning)

# Цвета для вывода
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def check_import(module_path, class_name=None):
    """Проверяет возможность импорта модуля и класса"""
    try:
        # Подавляем вывод при импорте
        import io
        import contextlib
        
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            module = importlib.import_module(module_path)
        
        if class_name:
            if hasattr(module, class_name):
                return True, f"✅ {module_path}.{class_name}"
            else:
                return False, f"❌ Класс {class_name} не найден в {module_path}"
        return True, f"✅ {module_path}"
    except ImportError as e:
        return False, f"❌ Ошибка импорта {module_path}: {e}"

def check_file_contains(filepath, search_string):
    """Проверяет наличие строки в файле"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            if search_string in content:
                return True, f"✅ Найдено '{search_string}' в {filepath}"
            else:
                return False, f"❌ Не найдено '{search_string}' в {filepath}"
    except FileNotFoundError:
        return False, f"❌ Файл не найден: {filepath}"
    except Exception as e:
        return False, f"❌ Ошибка чтения {filepath}: {e}"

def main():
    print(f"{BLUE}🔍 ПРОВЕРКА ИСПРАВЛЕНИЙ CRYPTO BOT{RESET}")
    print("=" * 50)
    
    errors = 0
    warnings = 0
    
    # 1. Проверка основных импортов
    print(f"\n{BLUE}📦 Проверка основных импортов:{RESET}")
    
    imports_to_check = [
        ('src.core.models', 'StrategyPerformance'),
        ('src.core.models', 'User'),
        ('src.core.models', 'Trade'),
        ('src.core.database', 'SessionLocal'),
        ('src.bot.manager', 'BotManager'),
    ]
    
    for module, cls in imports_to_check:
        success, msg = check_import(module, cls)
        print(f"  {msg}")
        if not success:
            errors += 1
    
    # 2. Проверка ML импортов с алиасами
    print(f"\n{BLUE}🤖 Проверка ML импортов:{RESET}")
    
    # Проверка FeatureEngineering
    try:
        import io
        import contextlib
        
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            from src.ml.features import FeatureEngineering, FeatureEngineer
        print(f"  ✅ FeatureEngineering и FeatureEngineer доступны")
    except ImportError as e:
        print(f"  ❌ Ошибка импорта feature engineering: {e}")
        errors += 1
    
    # Проверка StrategySelector
    try:
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            from src.ml import StrategySelector, MLStrategySelector
        print(f"  ✅ StrategySelector и MLStrategySelector доступны")
    except ImportError as e:
        print(f"  {YELLOW}⚠️  ML strategy selector недоступен: {e}{RESET}")
        warnings += 1
    
    # 3. Проверка файлов на исправления
    print(f"\n{BLUE}📄 Проверка файлов на исправления:{RESET}")
    
    files_to_check = [
        ('src/web/app.py', 'StrategyPerformance'),
        ('src/ml/features/__init__.py', 'FeatureEngineering = FeatureEngineer'),
        ('src/risk/enhanced_risk_manager.py', 'from ..ml.features import FeatureEngineer'),
    ]
    
    for filepath, search_str in files_to_check:
        success, msg = check_file_contains(filepath, search_str)
        print(f"  {msg}")
        if not success and 'Не найдено' in msg:
            errors += 1
    
    # 4. Проверка запуска модулей
    print(f"\n{BLUE}🚀 Проверка инициализации модулей:{RESET}")
    
    # Проверка стратегий
    try:
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            from src.strategies import strategy_factory
        count = strategy_factory.get_strategy_count()
        print(f"  ✅ Фабрика стратегий: загружено {count} стратегий")
    except Exception as e:
        print(f"  ❌ Ошибка фабрики стратегий: {e}")
        errors += 1
    
    # Проверка БД
    try:
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            from src.core.database import db
        
        # Проверяем наличие метода test_connection
        if hasattr(db, 'test_connection'):
            if db.test_connection():
                print(f"  ✅ Подключение к БД работает")
            else:
                print(f"  {YELLOW}⚠️  БД доступна, но тест подключения не прошел{RESET}")
                warnings += 1
        else:
            # Альтернативная проверка
            try:
                from src.core.database import engine
                with engine.connect() as conn:
                    conn.execute("SELECT 1")
                print(f"  ✅ Подключение к БД работает (альтернативная проверка)")
            except Exception as e:
                print(f"  ❌ Ошибка подключения к БД: {e}")
                errors += 1
    except Exception as e:
        print(f"  ❌ Ошибка импорта БД: {e}")
        errors += 1
    
    # 5. Проверка TA-Lib
    print(f"\n{BLUE}📊 Проверка дополнительных библиотек:{RESET}")
    
    try:
        import talib
        print(f"  ✅ TA-Lib установлен (версия {talib.__version__})")
    except ImportError:
        print(f"  {YELLOW}⚠️  TA-Lib не установлен (используется pandas_ta){RESET}")
        warnings += 1
    
    # 6. Итоговый отчет
    print("\n" + "=" * 50)
    print(f"{BLUE}📊 ИТОГОВЫЙ ОТЧЕТ:{RESET}")
    
    if errors == 0 and warnings == 0:
        print(f"{GREEN}✅ Все проверки пройдены успешно!{RESET}")
        print("Можно запускать: python main.py web")
        return 0
    else:
        if errors > 0:
            print(f"{RED}❌ Обнаружено критических ошибок: {errors}{RESET}")
        if warnings > 0:
            print(f"{YELLOW}⚠️  Обнаружено предупреждений: {warnings}{RESET}")
        
        if errors == 0:
            print(f"\n{GREEN}✅ Критических ошибок нет, можно запускать с предупреждениями{RESET}")
            print("Запуск: python main.py web")
        else:
            print("\nНеобходимо исправить критические ошибки перед запуском!")
        return 1 if errors > 0 else 0

if __name__ == "__main__":
    sys.exit(main())