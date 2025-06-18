#!/usr/bin/env python3
"""
Главный файл запуска Crypto Trading Bot - ИСПРАВЛЕННАЯ ВЕРСИЯ
Файл: main.py
"""
import sys
import os
import asyncio
import logging
from pathlib import Path

# Добавляем корневую директорию в PYTHONPATH
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

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
    dirs = ['logs', 'data', 'models', 'static', 'templates']
    for dir_name in dirs:
        dir_path = ROOT_DIR / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True)
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
    else:
        logger.info("✅ Все необходимые переменные окружения установлены")

def create_database():
    """Создание таблиц БД"""
    try:
        from src.core.database import Database
        db = Database()
        db.create_tables()
        logger.info("✅ База данных инициализирована")
    except Exception as e:
        logger.error(f"❌ Ошибка создания БД: {e}")
        sys.exit(1)

async def run_bot():
    """Запуск торгового бота"""
    try:
        from src.bot.manager import BotManager
        
        logger.info("🚀 Запуск торгового бота...")
        
        # Создаем экземпляр менеджера
        bot_manager = BotManager()
        
        # Запускаем бота
        success, message = await bot_manager.start()
        
        if success:
            logger.info(f"✅ {message}")
            
            # Держим бота запущенным
            while bot_manager.is_running:
                await asyncio.sleep(1)
        else:
            logger.error(f"❌ {message}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("⏹️ Получен сигнал остановки...")
        await bot_manager.stop()
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def run_web():
    """Запуск веб-интерфейса"""
    try:
        # ИСПРАВЛЕНИЕ: Правильный импорт и создание приложения
        from src.web.app import create_app
        
        logger.info("🌐 Создание веб-приложения...")
        app, socketio = create_app()
        
        logger.info("🌐 Запуск веб-интерфейса...")
        
        # Запускаем Flask с SocketIO
        socketio.run(
            app,
            host='0.0.0.0',
            port=5000,
            debug=False,
            use_reloader=False,
            log_output=True
        )
    except ImportError as e:
        logger.error(f"❌ Ошибка импорта веб-модуля: {e}")
        logger.info("Попробуйте запустить: pip install -r requirements.txt")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Ошибка запуска веб-интерфейса: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

async def run_both():
    """Запуск бота и веб-интерфейса одновременно"""
    try:
        # Импортируем необходимые модули
        from src.bot.manager import BotManager
        from src.web.app import create_app
        import threading
        
        logger.info("🚀 Запуск бота и веб-интерфейса...")
        
        # Создаем веб-приложение
        app, socketio = create_app()
        
        # Запускаем веб-сервер в отдельном потоке
        web_thread = threading.Thread(
            target=socketio.run,
            args=(app,),
            kwargs={
                'host': '0.0.0.0',
                'port': 5000,
                'debug': False,
                'use_reloader': False
            }
        )
        web_thread.daemon = True
        web_thread.start()
        
        logger.info("✅ Веб-интерфейс запущен на http://0.0.0.0:5000")
        
        # Небольшая задержка
        await asyncio.sleep(2)
        
        # Запускаем бота
        await run_bot()
        
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def setup_mode():
    """Режим первоначальной настройки"""
    logger.info("🔧 Режим настройки...")
    
    # Настройка окружения
    setup_environment()
    
    # Создание БД
    create_database()
    
    # Проверка подключения к бирже
    try:
        from src.exchange.client import ExchangeClient
        client = ExchangeClient()
        logger.info("✅ Подключение к бирже успешно")
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к бирже: {e}")
    
    logger.info("✅ Настройка завершена!")

def main():
    """Главная функция"""
    logger.info("=== CRYPTO TRADING BOT v3.0 ===")
    
    # Настройка окружения
    setup_environment()
    
    # Создание БД
    create_database()
    
    # Определяем режим работы
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        
        if mode == 'bot':
            # Только бот
            asyncio.run(run_bot())
        elif mode == 'web':
            # Только веб-интерфейс
            run_web()
        elif mode == 'both':
            # Бот + веб
            asyncio.run(run_both())
        elif mode == 'setup':
            # Режим настройки
            setup_mode()
        else:
            logger.error(f"❌ Неизвестный режим: {mode}")
            print("\nИспользование:")
            print("  python main.py bot    - запуск только бота")
            print("  python main.py web    - запуск только веб-интерфейса")
            print("  python main.py both   - запуск бота и веб-интерфейса")
            print("  python main.py setup  - режим настройки")
            sys.exit(1)
    else:
        # По умолчанию - запуск веб-интерфейса
        logger.info("💡 Режим не указан, запускаем веб-интерфейс")
        run_web()

if __name__ == "__main__":
    main()