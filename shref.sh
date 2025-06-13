#!/bin/bash
# Скрипт рефакторинга Crypto Trading Bot

cd /var/www/www-root/data/www/systemetech.ru

echo "🔧 НАЧИНАЕМ РЕФАКТОРИНГ ПРОЕКТА"
echo "================================"

# 1. Создаем правильную структуру
echo -e "\n📁 Создание новой структуры..."

mkdir -p src/{core,bot,exchange,strategies,analysis,notifications,web}
mkdir -p scripts
mkdir -p tests
mkdir -p docs
mkdir -p data/{cache,backups}

# 2. Перемещаем основные файлы
echo -e "\n📦 Перемещение основных файлов..."

# Core
mv src/core/database.py src/core/database_backup.py 2>/dev/null || true
mv src/core/models.py src/core/models_backup.py 2>/dev/null || true

# 3. Создаем единую конфигурацию
echo -e "\n⚙️ Создание единой конфигурации..."

cat > src/core/config.py << 'EOF'
"""Единая конфигурация системы"""
import os
from dataclasses import dataclass
from typing import List
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv('/etc/crypto/config/.env')

@dataclass
class Config:
    """Централизованная конфигурация"""
    
    # API
    BYBIT_API_KEY: str = os.getenv('BYBIT_API_KEY')
    BYBIT_API_SECRET: str = os.getenv('BYBIT_API_SECRET')
    BYBIT_TESTNET: bool = os.getenv('BYBIT_TESTNET', 'true').lower() == 'true'
    
    # База данных
    DB_HOST: str = os.getenv('DB_HOST', 'localhost')
    DB_NAME: str = os.getenv('DB_NAME', 'crypto_top_bd_mysql')
    DB_USER: str = os.getenv('DB_USER', 'crypto_top_admin')
    DB_PASSWORD: str = os.getenv('DB_PASSWORD')
    DATABASE_URL: str = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
    
    # Торговля
    TRADING_PAIRS: List[str] = os.getenv('TRADING_PAIRS', 'BTCUSDT').split(',')
    MAX_POSITIONS: int = int(os.getenv('MAX_POSITIONS', '1'))
    MAX_POSITION_SIZE_PERCENT: float = float(os.getenv('MAX_POSITION_SIZE_PERCENT', '5'))
    STOP_LOSS_PERCENT: float = float(os.getenv('STOP_LOSS_PERCENT', '2'))
    TAKE_PROFIT_PERCENT: float = float(os.getenv('TAKE_PROFIT_PERCENT', '4'))
    
    # Human behavior
    ENABLE_HUMAN_MODE: bool = os.getenv('ENABLE_HUMAN_MODE', 'true').lower() == 'true'
    MIN_DELAY_SECONDS: float = float(os.getenv('MIN_DELAY_SECONDS', '0.5'))
    MAX_DELAY_SECONDS: float = float(os.getenv('MAX_DELAY_SECONDS', '3.0'))
    
    # Telegram
    TELEGRAM_BOT_TOKEN: str = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID: str = os.getenv('TELEGRAM_CHAT_ID')
    
    # Web
    WEB_HOST: str = os.getenv('WEB_HOST', '0.0.0.0')
    WEB_PORT: int = int(os.getenv('WEB_PORT', '8000'))
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'change-this-in-production')
    
    # Стратегии
    ENABLE_MULTI_INDICATOR: bool = os.getenv('ENABLE_MULTI_INDICATOR', 'true').lower() == 'true'
    ENABLE_SCALPING: bool = os.getenv('ENABLE_SCALPING', 'true').lower() == 'true'
    MIN_RISK_REWARD_RATIO: float = float(os.getenv('MIN_RISK_REWARD_RATIO', '2.0'))
    MAX_DAILY_TRADES: int = int(os.getenv('MAX_DAILY_TRADES', '10'))

config = Config()
EOF

# 4. Восстанавливаем database.py с использованием config
echo -e "\n📊 Обновление database.py..."

cat > src/core/database.py << 'EOF'
"""Подключение к базе данных"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import config

engine = create_engine(config.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
EOF

# 5. Копируем models.py
cp src/core/models_backup.py src/core/models.py 2>/dev/null || true

# 6. Создаем __init__.py файлы
echo -e "\n📝 Создание __init__.py файлов..."

touch src/__init__.py
touch src/core/__init__.py
touch src/bot/__init__.py
touch src/exchange/__init__.py
touch src/strategies/__init__.py
touch src/analysis/__init__.py
touch src/notifications/__init__.py
touch src/web/__init__.py

# 7. Объединяем менеджеры в один
echo -e "\n🔧 Создание единого менеджера бота..."

# Сначала делаем бэкапы
mkdir -p backups/managers
cp src/core/bot_manager.py backups/managers/bot_manager_old.py 2>/dev/null || true
cp src/core/process_bot_manager.py backups/managers/process_bot_manager_old.py 2>/dev/null || true
cp src/core/unified_bot_manager.py backups/managers/unified_bot_manager_old.py 2>/dev/null || true
cp src/core/state_manager.py backups/managers/state_manager_old.py 2>/dev/null || true

# 8. Перемещаем файлы в правильные места
echo -e "\n📁 Организация файлов..."

# Exchange
mv src/exchange/bybit_client.py backups/bybit_client_old.py 2>/dev/null || true

# Strategies
mv src/strategies/*.py src/strategies/ 2>/dev/null || true

# Notifications
mv src/notifications/telegram_notifier.py src/notifications/telegram.py 2>/dev/null || true

# Web
mv src/web/auth.py src/web/ 2>/dev/null || true
mv app.py src/web/app_old.py 2>/dev/null || true

# 9. Удаляем дублирующие файлы
echo -e "\n🗑️ Удаление дублирующих файлов..."

mkdir -p backups/duplicates
mv main_simple.py backups/duplicates/ 2>/dev/null || true
mv main_advanced.py backups/duplicates/ 2>/dev/null || true
mv test_installation.py backups/duplicates/ 2>/dev/null || true
mv test_installation_fixed.py backups/duplicates/ 2>/dev/null || true
mv check_install.py backups/duplicates/ 2>/dev/null || true
mv check_database.py backups/duplicates/ 2>/dev/null || true
mv test_setup.py backups/duplicates/ 2>/dev/null || true

# 10. Создаем новый единый main.py
echo -e "\n🚀 Создание единого main.py..."

# (Код main.py будет создан отдельно)

# 11. Создаем requirements.txt
echo -e "\n📋 Обновление requirements.txt..."

cat > requirements.txt << 'EOF'
# Core
fastapi==0.104.1
uvicorn==0.24.0
aiohttp==3.10.11
websockets==12.0

# Trading
ccxt==4.4.89
pandas==2.1.3
numpy==1.26.2
ta==0.10.2

# Database
PyMySQL==1.1.0
sqlalchemy==2.0.23
redis==5.0.1

# Auth
passlib[bcrypt]==1.7.4
python-jose[cryptography]==3.3.0

# Notifications
python-telegram-bot==20.7

# Utils
python-dotenv==1.0.0
psutil==5.9.6
structlog==23.2.0
APScheduler==3.10.4

# ML (optional)
scikit-learn==1.3.2
EOF

# 12. Создаем .gitignore
echo -e "\n📝 Создание .gitignore..."

cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/

# Logs
logs/
*.log

# Database
*.db
*.sqlite

# Environment
.env
.env.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# Data
data/cache/
data/backups/

# Temporary
*.tmp
*.bak
backups/

# OS
.DS_Store
Thumbs.db
EOF

# 13. Создаем документацию
echo -e "\n📚 Создание документации..."

cat > docs/README.md << 'EOF'
# Crypto Trading Bot v3.0

## Структура проекта

```
src/
├── core/          # Ядро системы
├── bot/           # Торговый бот
├── exchange/      # Работа с биржей
├── strategies/    # Торговые стратегии
├── analysis/      # Анализ рынка
├── notifications/ # Уведомления
└── web/           # Веб-интерфейс
```

## Запуск

```bash
# Полная система
python main.py

# Только бот
python main.py --mode bot

# Только веб
python main.py --mode web
```
EOF

echo -e "\n✅ РЕФАКТОРИНГ ЗАВЕРШЕН!"
echo ""
echo "📝 Следующие шаги:"
echo "1. Проверьте структуру: tree -d src/"
echo "2. Создайте единый main.py"
echo "3. Объедините логику менеджеров в src/bot/manager.py"
echo "4. Запустите проверку: python scripts/check_system.py"