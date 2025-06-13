#!/usr/bin/env python3
"""
Crypto Trading Bot - Main Entry Point
Использует единый менеджер бота для управления торговлей
"""

import asyncio
import os
import logging
import signal
import sys
from dotenv import load_dotenv

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

# Загружаем конфигурацию
load_dotenv()

# Импортируем менеджер бота
from src.core.bot_manager import bot_manager

class CryptoTradingBot:
    """Главный класс торгового бота"""
    
    def __init__(self):
        self.bot_manager = bot_manager
        self.shutdown_event = asyncio.Event()
        
    async def run(self):
        """Запуск бота"""
        logger.info("=" * 50)
        logger.info("🤖 Crypto Trading Bot v3.0")
        logger.info("=" * 50)
        
        # Настройка обработчиков сигналов
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, self._signal_handler)
        
        try:
            # Запускаем менеджер бота
            logger.info("🚀 Запуск торгового бота...")
            await self.bot_manager.start()
            
            # Ждем сигнала остановки
            await self.shutdown_event.wait()
            
        except Exception as e:
            logger.error(f"❌ Критическая ошибка: {e}")
        finally:
            # Останавливаем бота
            logger.info("🛑 Остановка бота...")
            await self.bot_manager.stop()
            logger.info("👋 Бот остановлен")
    
    def _signal_handler(self, signum, frame):
        """Обработчик сигналов для graceful shutdown"""
        logger.info(f"Получен сигнал {signum}, инициируем остановку...")
        self.shutdown_event.set()

async def main():
    """Точка входа"""
    # Проверяем необходимые директории
    os.makedirs('logs', exist_ok=True)
    os.makedirs('data/cache', exist_ok=True)
    os.makedirs('data/backups', exist_ok=True)
    
    # Проверяем конфигурацию
    if not os.getenv('BYBIT_API_KEY') or os.getenv('BYBIT_API_KEY') == 'your_testnet_api_key_here':
        logger.error("❌ API ключи не настроены!")
        logger.error("Используйте: sudo python add_api_keys.py")
        sys.exit(1)
    
    # Создаем и запускаем бота
    bot = CryptoTradingBot()
    await bot.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Программа прервана пользователем")
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
        sys.exit(1)