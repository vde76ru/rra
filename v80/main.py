#!/usr/bin/env python3
"""
Главная точка входа в приложение Crypto Trading Bot - ОБНОВЛЕННАЯ ВЕРСИЯ
Файл: main.py
"""
import os
import sys
import asyncio
import argparse
import logging
from pathlib import Path

# Подавляем предупреждения ПЕРЕД всеми импортами
import warnings
warnings.filterwarnings('ignore', message='pkg_resources is deprecated')
warnings.filterwarnings('ignore', category=DeprecationWarning)

# Отключаем предупреждения TensorFlow
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'  # Отключаем GPU если не нужен

# Добавляем путь к модулям
sys.path.insert(0, str(Path(__file__).parent))

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_environment():
    """Настройка окружения"""
    # Проверяем наличие .env файла
    env_path = Path('/etc/crypto/config/.env')
    if not env_path.exists():
        logger.warning(f"⚠️ Файл конфигурации не найден: {env_path}")
        logger.info("Используем переменные окружения по умолчанию")
    
    # Создаем необходимые директории
    dirs = ['logs', 'data', 'data/cache', 'data/backups', 'models', 'static', 'templates']
    for dir_name in dirs:
        Path(dir_name).mkdir(parents=True, exist_ok=True)
    
    logger.info("✅ Окружение настроено")

def create_database():
    """Создание таблиц БД"""
    try:
        from src.core.database import db
        db.create_tables()
        logger.info("✅ База данных инициализирована")
    except Exception as e:
        logger.error(f"❌ Ошибка создания БД: {e}")
        sys.exit(1)

async def run_bot():
    """Запуск торгового бота"""
    try:
        from src.bot.manager import bot_manager
        
        logger.info("🚀 Запуск торгового бота...")
        
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
        sys.exit(1)

def run_web():
    """Запуск веб-интерфейса"""
    try:
        # Подавляем вывод при импорте
        import io
        import contextlib
        
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            from src.web.app import app, socketio
        
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
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Ошибка запуска веб-интерфейса: {e}")
        sys.exit(1)

async def run_both():
    """Запуск бота и веб-интерфейса одновременно"""
    try:
        # Импортируем необходимые модули
        from src.bot.manager import bot_manager
        from src.web.app import app, socketio
        import threading
        
        logger.info("🚀 Запуск бота и веб-интерфейса...")
        
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
    logger.info("Теперь можно запустить бота: python main.py bot")
    logger.info("Или веб-интерфейс: python main.py web")

def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(
        description='Crypto Trading Bot - Professional Trading System'
    )
    parser.add_argument(
        'mode',
        choices=['bot', 'web', 'both', 'setup'],
        help='Режим запуска: bot (только бот), web (только веб), both (оба), setup (настройка)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Включить режим отладки'
    )
    
    args = parser.parse_args()
    
    # Настройка уровня логирования
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("🐛 Режим отладки включен")
    
    # Всегда настраиваем окружение
    setup_environment()
    
    # Всегда проверяем БД
    create_database()
    
    logger.info(f"🚀 Запуск в режиме: {args.mode}")
    
    if args.mode == 'bot':
        asyncio.run(run_bot())
    elif args.mode == 'web':
        run_web()
    elif args.mode == 'both':
        asyncio.run(run_both())
    elif args.mode == 'setup':
        setup_mode()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n⏹️ Программа остановлена пользователем")
        sys.exit(0)
    except Exception as e:
        logger.error(f"\n❌ Критическая ошибка: {e}")
        sys.exit(1)