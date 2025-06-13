#!/usr/bin/env python3
"""
Crypto Trading Bot v3.0 - Единая точка входа
"""
import asyncio
import argparse
import logging
import signal
import sys
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.append(str(Path(__file__).parent))

from src.core.config import config
from src.bot.manager import bot_manager

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/trading.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def run_bot():
    """Запуск торгового бота"""
    logger.info("🚀 Запуск торгового бота...")
    
    # Обработка сигналов
    stop_event = asyncio.Event()
    
    def signal_handler(sig, frame):
        logger.info(f"📡 Получен сигнал {sig}")
        stop_event.set()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Запускаем бота
        success, message = await bot_manager.start()
        if not success:
            logger.error(f"❌ Не удалось запустить бота: {message}")
            return
        
        # Ждем сигнала остановки
        await stop_event.wait()
        
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
    finally:
        # Останавливаем бота
        logger.info("🛑 Остановка бота...")
        await bot_manager.stop()

def run_web():
    """Запуск веб-интерфейса"""
    logger.info("🌐 Запуск веб-интерфейса...")
    
    import uvicorn
    from src.web.app import app
    
    uvicorn.run(
        app,
        host=config.WEB_HOST,
        port=config.WEB_PORT,
        log_level="info"
    )

async def run_all():
    """Запуск всей системы"""
    logger.info("🚀 Запуск полной системы...")
    
    # Запускаем бота в фоне
    bot_task = asyncio.create_task(run_bot())
    
    # Запускаем веб в отдельном процессе
    import multiprocessing
    web_process = multiprocessing.Process(target=run_web)
    web_process.start()
    
    try:
        await bot_task
    finally:
        web_process.terminate()
        web_process.join()

def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(description='Crypto Trading Bot v3.0')
    parser.add_argument(
        '--mode',
        choices=['bot', 'web', 'all'],
        default='all',
        help='Режим запуска: bot (только бот), web (только веб), all (всё)'
    )
    
    args = parser.parse_args()
    
    # Создаем директории
    Path('logs').mkdir(exist_ok=True)
    Path('data/cache').mkdir(parents=True, exist_ok=True)
    Path('data/backups').mkdir(parents=True, exist_ok=True)
    
    # Проверяем конфигурацию
    if not config.BYBIT_API_KEY or config.BYBIT_API_KEY == 'your_testnet_api_key_here':
        logger.error("❌ API ключи не настроены!")
        logger.info("📝 Настройте их в /etc/crypto/config/.env")
        sys.exit(1)
    
    # Запускаем
    if args.mode == 'bot':
        asyncio.run(run_bot())
    elif args.mode == 'web':
        run_web()
    else:
        asyncio.run(run_all())

if __name__ == "__main__":
    main()
