#!/usr/bin/env python3
"""
Crypto Trading Bot - Main Entry Point
Исправленная версия с правильной обработкой остановки
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
    """Главный класс торгового бота с улучшенной обработкой остановки"""
    
    def __init__(self):
        self.bot_manager = bot_manager
        self.shutdown_event = asyncio.Event()
        self._shutdown_requested = False  # ✅ Добавляем флаг
        
    async def run(self):
        """Запуск бота с правильной обработкой остановки"""
        logger.info("=" * 50)
        logger.info("🤖 Crypto Trading Bot v3.0")
        logger.info("=" * 50)
        
        # Настройка обработчиков сигналов
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, self._signal_handler)
        
        try:
            # ✅ ИСПРАВЛЕНИЕ: Запускаем бота и мониторинг параллельно
            logger.info("🚀 Запуск торгового бота...")
            
            # Создаем задачи
            bot_task = asyncio.create_task(self._run_bot_safely())
            monitor_task = asyncio.create_task(self._monitor_shutdown())
            
            # Ждем завершения любой из задач
            done, pending = await asyncio.wait(
                [bot_task, monitor_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Отменяем оставшиеся задачи
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
        except KeyboardInterrupt:
            logger.info("⚠️ Получен KeyboardInterrupt")
        except Exception as e:
            logger.error(f"❌ Критическая ошибка: {e}")
        finally:
            # ✅ ИСПРАВЛЕНИЕ: Быстрая остановка с таймаутом
            await self._shutdown_with_timeout()
    
    async def _run_bot_safely(self):
        """Безопасный запуск бота с обработкой ошибок"""
        try:
            await self.bot_manager.start()
            
            # Ждем сигнала остановки через короткие интервалы
            while not self._shutdown_requested:
                await asyncio.sleep(1)  # ✅ Проверяем каждую секунду
                
        except Exception as e:
            logger.error(f"❌ Ошибка в боте: {e}")
            self._shutdown_requested = True
    
    async def _monitor_shutdown(self):
        """Мониторинг сигнала остановки"""
        await self.shutdown_event.wait()
        logger.info("🛑 Получен сигнал остановки, инициируем shutdown...")
        self._shutdown_requested = True
    
    async def _shutdown_with_timeout(self):
        """Остановка бота с таймаутом"""
        logger.info("🛑 Остановка бота...")
        
        try:
            # ✅ Устанавливаем таймаут на остановку (максимум 10 секунд)
            await asyncio.wait_for(
                self.bot_manager.stop(),
                timeout=10.0
            )
            logger.info("✅ Бот остановлен корректно")
            
        except asyncio.TimeoutError:
            logger.warning("⚠️ Таймаут остановки бота (10 секунд)")
            logger.info("🔧 Принудительное завершение...")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при остановке: {e}")
        
        finally:
            logger.info("👋 Завершение программы")
    
    def _signal_handler(self, signum, frame):
        """Улучшенный обработчик сигналов"""
        if self._shutdown_requested:
            # ✅ Если уже получили сигнал, принудительно завершаем
            logger.warning(f"⚠️ Повторный сигнал {signum}, принудительное завершение!")
            sys.exit(1)
        
        logger.info(f"📡 Получен сигнал {signum}, инициируем graceful shutdown...")
        self._shutdown_requested = True
        self.shutdown_event.set()

async def main():
    """Точка входа с улучшенной инициализацией"""
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
        # ✅ Устанавливаем политику событий для Windows
        if sys.platform.startswith('win'):
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            
        asyncio.run(main())
        
    except KeyboardInterrupt:
        logger.info("👋 Программа прервана пользователем")
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
        sys.exit(1)