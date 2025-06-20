#!/usr/bin/env python3
"""
Главный файл запуска Crypto Trading Bot - ПОЛНОСТЬЮ ИСПРАВЛЕННАЯ ВЕРСИЯ
Файл: main.py
"""
import sys
import os
import asyncio
import logging
from pathlib import Path
import threading
import time
from dotenv import load_dotenv

# Добавляем корневую директорию в PYTHONPATH
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

# Загружаем переменные окружения
env_path = ROOT_DIR / '.env'
if not env_path.exists():
    # Ищем в других местах
    possible_paths = [
        Path('/etc/crypto/config/.env'),
        ROOT_DIR / 'config' / '.env',
        ROOT_DIR / '.env.example'
    ]
    for path in possible_paths:
        if path.exists():
            env_path = path
            break

load_dotenv(env_path)

# Подавляем предупреждения TensorFlow
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_environment():
    """Настройка окружения"""
    # Создаем необходимые директории
    dirs = ['logs', 'data', 'models', 'static', 'templates', 'data/cache', 'logs/archive']
    for dir_name in dirs:
        dir_path = ROOT_DIR / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ Создана директория: {dir_path}")
    
    # Проверяем переменные окружения
    required_env = [
        'BYBIT_API_KEY',
        'BYBIT_API_SECRET',
        'DATABASE_URL',
        'TELEGRAM_BOT_TOKEN',
        'TELEGRAM_CHAT_ID'
    ]
    
    missing = []
    for var in required_env:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        logger.warning(f"⚠️ Отсутствуют переменные окружения: {', '.join(missing)}")
        logger.info("💡 Проверьте файл .env")
    else:
        logger.info("✅ Все необходимые переменные окружения установлены")

def create_database():
    """Создание таблиц БД"""
    try:
        from src.core.database import Database, engine
        from src.core.models import Base
        
        # Создаем таблицы
        Base.metadata.create_all(bind=engine)
        logger.info("✅ База данных инициализирована")
        
        # Создаем тестовые данные если БД пустая
        from src.core.database import SessionLocal
        from src.core.models import User, BotSettings
        from passlib.context import CryptContext
        
        db = SessionLocal()
        try:
            # Проверяем есть ли пользователи
            if db.query(User).count() == 0:
                pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
                
                # Создаем админа
                admin = User(
                    username="admin",
                    email=os.getenv("ADMIN_EMAIL", "admin@systemetech.ru"),
                    password_hash=pwd_context.hash(os.getenv("ADMIN_PASSWORD", "SecurePassword123!")),
                    is_admin=True,
                    is_active=True
                )
                db.add(admin)
                
                # Создаем дефолтные настройки бота
                settings = BotSettings(
                    user_id=1,
                    max_position_size=float(os.getenv("MAX_POSITION_SIZE", "1000")),
                    stop_loss_percent=float(os.getenv("STOP_LOSS_PERCENT", "2")),
                    take_profit_percent=float(os.getenv("TAKE_PROFIT_PERCENT", "4")),
                    max_daily_trades=int(os.getenv("MAX_DAILY_TRADES", "10"))
                )
                db.add(settings)
                
                db.commit()
                logger.info("✅ Создан пользователь admin")
                logger.info(f"📧 Email: {admin.email}")
                logger.info("🔑 Пароль: из переменной ADMIN_PASSWORD в .env")
                
        except Exception as e:
            logger.error(f"Ошибка создания тестовых данных: {e}")
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"❌ Ошибка создания БД: {e}")
        import traceback
        traceback.print_exc()

async def run_bot():
    """Запуск торгового бота"""
    try:
        from src.bot.manager import BotManager
        
        logger.info("🤖 Запуск торгового бота...")
        
        # Создаем экземпляр менеджера
        bot = BotManager()
        
        # Запускаем бота
        await bot.start()
        
        logger.info("✅ Бот успешно запущен!")
        
        # Держим бота работающим
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("⏹️ Получен сигнал остановки...")
            await bot.stop()
            
    except Exception as e:
        logger.error(f"❌ Ошибка запуска бота: {e}")
        import traceback
        traceback.print_exc()

def run_web():
    """Запуск веб-интерфейса"""
    try:
        from src.web.app import create_app
        
        logger.info("🌐 Запуск веб-интерфейса...")
        
        # Создаем приложение
        app, socketio = create_app()
        
        # Получаем настройки из .env
        host = os.getenv('WEB_HOST', '0.0.0.0')
        port = int(os.getenv('WEB_PORT', '8000'))
        debug = os.getenv('DEBUG_MODE', 'true').lower() == 'true'
        
        logger.info(f"✅ Веб-интерфейс доступен на http://{host}:{port}")
        logger.info("📊 Дашборд: http://localhost:{}/".format(port))
        logger.info("🔐 Логин: admin")
        logger.info("🔑 Пароль: из ADMIN_PASSWORD в .env")
        
        # Запускаем сервер
        socketio.run(
            app,
            host=host,
            port=port,
            debug=debug,
            use_reloader=False
        )
        
    except Exception as e:
        logger.error(f"❌ Ошибка запуска веб-интерфейса: {e}")
        import traceback
        traceback.print_exc()

async def run_both():
    """Запуск бота и веб-интерфейса одновременно"""
    try:
        from src.bot.manager import BotManager
        from src.web.app import create_app
        
        logger.info("🚀 Запуск бота и веб-интерфейса...")
        
        # Создаем веб-приложение
        app, socketio = create_app()
        
        # Получаем настройки
        host = os.getenv('WEB_HOST', '0.0.0.0')
        port = int(os.getenv('WEB_PORT', '8000'))
        
        # Запускаем веб-сервер в отдельном потоке
        web_thread = threading.Thread(
            target=socketio.run,
            args=(app,),
            kwargs={
                'host': host,
                'port': port,
                'debug': False,
                'use_reloader': False
            }
        )
        web_thread.daemon = True
        web_thread.start()
        
        logger.info(f"✅ Веб-интерфейс запущен на http://{host}:{port}")
        
        # Небольшая задержка для запуска веб-сервера
        await asyncio.sleep(2)
        
        # Запускаем бота
        bot = BotManager()
        await bot.start()
        
        logger.info("✅ Система полностью запущена!")
        logger.info(f"📊 Дашборд доступен: http://localhost:{port}/")
        
        # Держим систему работающей
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("⏹️ Остановка системы...")
            await bot.stop()
            
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

def check_system():
    """Проверка системы"""
    logger.info("🔍 Проверка системы...")
    
    # Проверка Python версии
    logger.info(f"Python версия: {sys.version}")
    
    # Проверка окружения
    setup_environment()
    
    # Проверка БД
    try:
        from src.core.database import SessionLocal
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        logger.info("✅ Подключение к БД успешно")
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к БД: {e}")
    
    # Проверка биржи
    try:
        from src.exchange.client import ExchangeClient
        client = ExchangeClient()
        logger.info("✅ Подключение к бирже настроено")
    except Exception as e:
        logger.error(f"❌ Ошибка настройки биржи: {e}")
    
    # Проверка Telegram
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    telegram_chat = os.getenv('TELEGRAM_CHAT_ID')
    if telegram_token and telegram_chat:
        logger.info("✅ Telegram настроен")
    else:
        logger.warning("⚠️ Telegram не настроен")
    
    logger.info("✅ Проверка завершена!")

def main():
    """Главная функция"""
    print("""
    ╔══════════════════════════════════════╗
    ║     CRYPTO TRADING BOT v3.0          ║
    ║     Professional Trading System      ║
    ╚══════════════════════════════════════╝
    """)
    
    # Определяем режим работы
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        
        if mode == 'bot':
            # Только бот
            setup_environment()
            create_database()
            asyncio.run(run_bot())
            
        elif mode == 'web':
            # Только веб-интерфейс
            setup_environment()
            create_database()
            run_web()
            
        elif mode == 'both':
            # Бот + веб
            setup_environment()
            create_database()
            asyncio.run(run_both())
            
        elif mode == 'check':
            # Проверка системы
            check_system()
            
        elif mode == 'setup':
            # Настройка
            setup_environment()
            create_database()
            logger.info("✅ Настройка завершена!")
            
        else:
            logger.error(f"❌ Неизвестный режим: {mode}")
            print("\n📖 Использование:")
            print("  python main.py web    - запуск веб-интерфейса (рекомендуется)")
            print("  python main.py bot    - запуск только бота")
            print("  python main.py both   - запуск бота и веб-интерфейса")
            print("  python main.py check  - проверка системы")
            print("  python main.py setup  - первоначальная настройка")
            sys.exit(1)
    else:
        # По умолчанию - запуск веб-интерфейса
        logger.info("💡 Запуск в режиме веб-интерфейса")
        setup_environment()
        create_database()
        run_web()

if __name__ == "__main__":
    main()