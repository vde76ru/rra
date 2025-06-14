#!/usr/bin/env python3
"""
Crypto Trading Bot v3.0 - Единая точка входа
Объединяет все компоненты в единую систему
"""
import asyncio
import argparse
import logging
import signal
import sys
import multiprocessing
from pathlib import Path
from datetime import datetime

# Добавляем корневую директорию в путь
sys.path.append(str(Path(__file__).parent))

from src.core.config import config
from src.bot.manager import bot_manager

# Настройка логирования остается той же...
def setup_logging(log_level='INFO'):
    """Настройка системы логирования"""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    Path('logs').mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, log_level),
        format=log_format,
        handlers=[
            logging.FileHandler('logs/trading.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logging.getLogger('ccxt').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('telegram').setLevel(logging.WARNING)
    
    return logging.getLogger(__name__)

# Глобальная переменная для сигналов
shutdown_event = asyncio.Event()

def signal_handler(signum, frame):
    """Обработчик сигналов для graceful shutdown"""
    logger = logging.getLogger(__name__)
    logger.info(f"📡 Получен сигнал {signum}, инициируем graceful shutdown...")
    shutdown_event.set()

async def run_bot():
    """Запуск торгового бота"""
    logger = logging.getLogger(__name__)
    
    logger.info("==================================================")
    logger.info("🤖 Crypto Trading Bot v3.0")
    logger.info("==================================================")
    logger.info("🚀 Запуск торгового бота...")
    
    try:
        success, message = await bot_manager.start()
        if not success:
            logger.error(f"❌ Не удалось запустить бота: {message}")
            return
        
        logger.info("✅ Бот запущен. Нажмите Ctrl+C для остановки")
        await shutdown_event.wait()
        
        logger.info("🛑 Получен сигнал остановки, инициируем shutdown...")
        
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}", exc_info=True)
    finally:
        logger.info("🛑 Остановка бота...")
        await bot_manager.stop()
        logger.info("✅ Бот остановлен корректно")

# ✅ ИСПРАВЛЕНИЕ: Новая функция для запуска веб-сервера с правильным event loop
async def run_web_async():
    """Асинхронный запуск веб-интерфейса"""
    logger = logging.getLogger(__name__)
    
    try:
        import uvicorn
        from src.web.app import app
        from src.web.websocket import ws_manager
        
        # ✅ ИСПРАВЛЕНИЕ: Создаем WebSocket broadcast в уже запущенном event loop
        broadcast_task = asyncio.create_task(ws_manager.start_broadcast_loop())
        
        # Настройка uvicorn config
        uvicorn_config = uvicorn.Config(
            app,
            host=config.WEB_HOST,
            port=config.WEB_PORT,
            log_level="info",
            access_log=False  # Отключаем access логи для чистоты
        )
        
        server = uvicorn.Server(uvicorn_config)
        
        # Запускаем сервер
        await server.serve()
        
    except Exception as e:
        logger.error(f"💥 Ошибка веб-сервера: {e}", exc_info=True)
    finally:
        # Останавливаем broadcast task
        if 'broadcast_task' in locals():
            broadcast_task.cancel()
            try:
                await broadcast_task
            except asyncio.CancelledError:
                pass

def run_web():
    """Обёртка для запуска веб-интерфейса в отдельном процессе"""
    logger = logging.getLogger(__name__)
    
    logger.info("==================================================")
    logger.info("🌐 Crypto Trading Bot Web Interface")
    logger.info("==================================================")
    logger.info(f"🌐 Запуск веб-интерфейса на {config.WEB_HOST}:{config.WEB_PORT}...")
    
    # ✅ ИСПРАВЛЕНИЕ: Запускаем асинхронную функцию правильно
    asyncio.run(run_web_async())

async def run_all():
    """Запуск всей системы"""
    logger = logging.getLogger(__name__)
    
    logger.info("==================================================")
    logger.info("🚀 Crypto Trading Bot v3.0 - Full System")
    logger.info("==================================================")
    
    # Запускаем веб в отдельном процессе
    web_process = multiprocessing.Process(target=run_web)
    web_process.start()
    
    # Небольшая задержка чтобы веб успел запуститься
    await asyncio.sleep(2)
    
    try:
        await run_bot()
    finally:
        logger.info("🛑 Остановка веб-интерфейса...")
        web_process.terminate()
        web_process.join(timeout=5)
        if web_process.is_alive():
            web_process.kill()
        logger.info("✅ Веб-интерфейс остановлен")
        
    logger.info("👋 Завершение программы")

# Остальной код main() остается тем же...
def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(
        description='Crypto Trading Bot v3.0',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python main.py              # Запуск всей системы (бот + веб)
  python main.py --bot        # Только торговый бот
  python main.py --web        # Только веб-интерфейс
  python main.py --check      # Проверка системы
        """
    )
    
    parser.add_argument('--bot', action='store_true', help='Запустить только торгового бота')
    parser.add_argument('--web', action='store_true', help='Запустить только веб-интерфейс')
    parser.add_argument('--check', action='store_true', help='Проверить настройки системы')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], default='INFO', help='Уровень логирования')
    
    args = parser.parse_args()
    
    logger = setup_logging(args.log_level)
    
    for directory in ['logs', 'data/cache', 'data/backups']:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    if args.check:
        from scripts.check_system import run_system_check
        sys.exit(run_system_check())
    
    if not config.BYBIT_API_KEY or config.BYBIT_API_KEY == 'your_testnet_api_key_here':
        logger.error("❌ API ключи не настроены!")
        logger.info("📝 Настройте их в /etc/crypto/config/.env")
        sys.exit(1)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    if args.bot and args.web:
        logger.error("❌ Нельзя использовать --bot и --web одновременно")
        sys.exit(1)
    
    try:
        if args.bot:
            asyncio.run(run_bot())
        elif args.web:
            run_web()
        else:
            asyncio.run(run_all())
    except KeyboardInterrupt:
        logger.info("⌨️ Получен KeyboardInterrupt")
    except Exception as e:
        logger.error(f"💥 Неожиданная ошибка: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("🏁 Программа завершена")

if __name__ == "__main__":
    main()