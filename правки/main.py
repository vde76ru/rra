#!/usr/bin/env python3
"""
Главная точка входа в приложение Crypto Trading Bot
Файл: main.py
"""
import os
import sys
import asyncio
import argparse
import logging
from pathlib import Path

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
    dirs = ['logs', 'data', 'data/cache', 'data/backups']
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
        from src.web.app import app, socketio
        
        logger.info("🌐 Запуск веб-интерфейса...")
        
        # Запускаем Flask с SocketIO
        socketio.run(
            app,
            host='0.0.0.0',
            port=5000,
            debug=False,
            use_reloader=False
        )
    except Exception as e:
        logger.error(f"❌ Ошибка запуска веб-интерфейса: {e}")
        sys.exit(1)

def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(description='Crypto Trading Bot')
    parser.add_argument(
        'mode',
        choices=['bot', 'web', 'both', 'setup'],
        help='Режим запуска: bot (только бот), web (только веб), both (всё), setup (настройка)'
    )
    
    args = parser.parse_args()
    
    # Настройка окружения
    setup_environment()
    
    if args.mode == 'setup':
        # Только создаем БД и выходим
        create_database()
        logger.info("✅ Настройка завершена")
        
    elif args.mode == 'bot':
        # Запуск только бота
        create_database()
        asyncio.run(run_bot())
        
    elif args.mode == 'web':
        # Запуск только веб-интерфейса
        create_database()
        run_web()
        
    elif args.mode == 'both':
        # Запуск всего
        create_database()
        
        # В будущем здесь можно запустить оба процесса параллельно
        logger.info("ℹ️ Для запуска бота и веб-интерфейса одновременно:")
        logger.info("  1. Запустите в одном терминале: python main.py bot")
        logger.info("  2. Запустите в другом терминале: python main.py web")

if __name__ == '__main__':
    main()
