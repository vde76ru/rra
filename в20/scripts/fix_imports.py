#!/usr/bin/env python3
"""
fix_imports.py - Исправление оставшихся импортов
"""
import os
import sys

def fix_file_imports(filepath, fixes):
    """Исправляет импорты в файле"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        for old, new in fixes.items():
            content = content.replace(old, new)
        
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Исправлен: {filepath}")
            return True
        return False
    except Exception as e:
        print(f"❌ Ошибка в {filepath}: {e}")
        return False

def main():
    """Основная функция"""
    print("🔧 Исправление импортов...")
    
    # Исправления для разных файлов
    fixes = {
        # Общие исправления
        "from typing import ": "from typing import Dict, List, Optional, Tuple, ",
        "import asyncio\n": "import asyncio\nimport sys\n",
        
        # Исправления для auth.py
        "return asyncio.run(": "import asyncio\n    return asyncio.run(",
        
        # Исправления для exchange/client.py  
        "from typing import Dict": "from typing import Dict, Optional, List",
        
        # Исправления для strategies
        "from typing import Dict": "from typing import Dict, Any",
    }
    
    # Файлы для проверки
    files_to_fix = [
        "src/bot/manager.py",
        "src/bot/trader.py", 
        "src/bot/risk_manager.py",
        "src/web/auth.py",
        "src/web/api.py",
        "src/web/websocket.py",
        "src/exchange/client.py",
        "src/exchange/humanizer.py",
        "src/strategies/base.py",
        "src/strategies/momentum.py",
        "src/strategies/multi_indicator.py",
        "src/strategies/scalping.py",
        "src/analysis/market_analyzer.py",
        "src/notifications/telegram.py"
    ]
    
    fixed_count = 0
    for filepath in files_to_fix:
        if os.path.exists(filepath):
            if fix_file_imports(filepath, fixes):
                fixed_count += 1
        else:
            print(f"⚠️ Файл не найден: {filepath}")
    
    print(f"\n✅ Исправлено файлов: {fixed_count}")
    
    # Дополнительные специфичные исправления
    print("\n🔧 Дополнительные исправления...")
    
    # Исправляем auth.py - добавляем импорт asyncio
    auth_file = "src/web/auth.py"
    if os.path.exists(auth_file):
        with open(auth_file, 'r') as f:
            content = f.read()
        
        if "import asyncio" not in content:
            # Добавляем импорт после других импортов
            content = content.replace(
                "from sqlalchemy.orm import Session\n",
                "from sqlalchemy.orm import Session\nimport asyncio\n"
            )
            
            with open(auth_file, 'w') as f:
                f.write(content)
            print(f"✅ Добавлен import asyncio в {auth_file}")
    
    # Исправляем exchange/humanizer.py
    humanizer_file = "src/exchange/humanizer.py"
    if os.path.exists(humanizer_file):
        with open(humanizer_file, 'r') as f:
            content = f.read()
        
        # Добавляем недостающие импорты
        if "from typing import" not in content:
            content = "from typing import Optional, Tuple\n" + content
        
        if "micro_delay" in content and "async def micro_delay" not in content:
            # Добавляем метод micro_delay
            content = content.replace(
                "    async def human_delay(",
                """    async def micro_delay(self):
        \"\"\"Микро-задержка для быстрых операций\"\"\"
        if self.enable_human_mode:
            await asyncio.sleep(random.uniform(0.1, 0.5))
    
    async def human_delay("""
            )
        
        with open(humanizer_file, 'w') as f:
            f.write(content)
        print(f"✅ Исправлен {humanizer_file}")
    
    print("\n✅ Все исправления применены!")

if __name__ == "__main__":
    main()