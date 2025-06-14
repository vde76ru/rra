#!/usr/bin/env python3
"""
Скрипт для исправления всех проблем с импортами в проекте
"""
import os
import re
import shutil
from pathlib import Path

def fix_imports_in_file(filepath):
    """Исправляет импорты в файле"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Исправляем дублирующиеся импорты в одной строке
        # Находим все строки с from typing import
        typing_pattern = r'from typing import (.+)'
        
        def fix_typing_imports(match):
            imports = match.group(1)
            # Разбиваем по запятым и убираем дубликаты
            import_list = [imp.strip() for imp in imports.split(',')]
            unique_imports = []
            seen = set()
            for imp in import_list:
                if imp and imp not in seen:
                    seen.add(imp)
                    unique_imports.append(imp)
            return f"from typing import {', '.join(unique_imports)}"
        
        content = re.sub(typing_pattern, fix_typing_imports, content)
        
        # Удаляем полностью дублирующиеся строки импорта
        lines = content.split('\n')
        seen_imports = set()
        new_lines = []
        
        for line in lines:
            if line.strip().startswith(('import ', 'from ')):
                if line.strip() not in seen_imports:
                    seen_imports.add(line.strip())
                    new_lines.append(line)
            else:
                new_lines.append(line)
        
        content = '\n'.join(new_lines)
        
        # Сохраняем только если были изменения
        if content != original_content:
            # Создаем резервную копию
            backup_path = filepath + '.backup'
            shutil.copy2(filepath, backup_path)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ Исправлен: {filepath}")
            return True
        
        return False
        
    except Exception as e:
        print(f"❌ Ошибка в {filepath}: {e}")
        return False

def remove_unused_files():
    """Удаляет неиспользуемые файлы"""
    unused_files = [
        'src/strategies/improved_multi_indicator.py',
        'src/strategies/simple_momentum.py',
        'src/strategies/advanced_strategies.py',
    ]
    
    for filepath in unused_files:
        if os.path.exists(filepath):
            # Создаем резервную копию в папке backup
            backup_dir = 'backup_unused'
            os.makedirs(backup_dir, exist_ok=True)
            backup_path = os.path.join(backup_dir, os.path.basename(filepath))
            shutil.move(filepath, backup_path)
            print(f"🗑️ Перемещен в backup: {filepath} -> {backup_path}")

def fix_strategies_init():
    """Исправляет __init__.py в strategies"""
    init_file = 'src/strategies/__init__.py'
    
    correct_content = '''"""Торговые стратегии"""
from .factory import StrategyFactory

__all__ = ['StrategyFactory']
'''
    
    with open(init_file, 'w', encoding='utf-8') as f:
        f.write(correct_content)
    
    print(f"✅ Исправлен: {init_file}")

def main():
    """Основная функция"""
    print("🔧 Исправление импортов и структуры проекта...")
    print("=" * 50)
    
    # 1. Удаляем неиспользуемые файлы
    print("\n📁 Удаление неиспользуемых файлов...")
    remove_unused_files()
    
    # 2. Исправляем __init__.py в strategies
    print("\n📝 Исправление __init__.py...")
    fix_strategies_init()
    
    # 3. Исправляем импорты во всех Python файлах
    print("\n🔍 Поиск и исправление дублирующихся импортов...")
    
    fixed_count = 0
    total_count = 0
    
    for root, dirs, files in os.walk('src'):
        # Пропускаем __pycache__
        if '__pycache__' in root:
            continue
            
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                total_count += 1
                
                if fix_imports_in_file(filepath):
                    fixed_count += 1
    
    print(f"\n📊 Результаты:")
    print(f"   Всего файлов проверено: {total_count}")
    print(f"   Файлов исправлено: {fixed_count}")
    print(f"\n✅ Исправление завершено!")
    
    # 4. Проверяем, что все импорты корректны
    print("\n🔍 Проверка корректности импортов...")
    
    try:
        # Пытаемся импортировать основные модули
        import src.bot.manager
        import src.exchange.client
        import src.strategies.factory
        import src.web.app
        print("✅ Все основные модули импортируются корректно!")
    except Exception as e:
        print(f"❌ Ошибка импорта: {e}")

if __name__ == "__main__":
    main()