#!/usr/bin/env python3
# main_simple.py - Упрощенная версия для начального тестирования

import asyncio
import os
import logging
from datetime import datetime
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

class SimpleCryptoBot:
    """Упрощенная версия бота для тестирования"""
    
    def __init__(self):
        self.symbol = os.getenv('TRADING_SYMBOL', 'BTCUSDT')
        self.testnet = os.getenv('BYBIT_TESTNET', 'true').lower() == 'true'
        self.is_running = True
        
        logger.info(f"🤖 Инициализация бота")
        logger.info(f"📊 Торговая пара: {self.symbol}")
        logger.info(f"🔧 Режим: {'TESTNET' if self.testnet else 'MAINNET'}")
    
    async def check_connection(self):
        """Проверка подключения к бирже"""
        try:
            import ccxt
            
            # Проверяем наличие API ключей
            api_key = os.getenv('BYBIT_API_KEY')
            api_secret = os.getenv('BYBIT_API_SECRET')
            
            if not api_key or api_key == 'your_testnet_api_key_here':
                logger.error("❌ API ключи не настроены! Добавьте их в .env файл")
                return False
            
            # Создаем подключение
            exchange = ccxt.bybit({
                'apiKey': api_key,
                'secret': api_secret,
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'swap',
                    'testnet': self.testnet
                }
            })
            
            if self.testnet:
                exchange.set_sandbox_mode(True)
            
            # Проверяем баланс
            logger.info("🔍 Проверка подключения к Bybit...")
            balance = exchange.fetch_balance()
            
            # Выводим баланс USDT
            usdt_balance = balance.get('USDT', {})
            total_usdt = usdt_balance.get('total', 0)
            free_usdt = usdt_balance.get('free', 0)
            
            logger.info(f"✅ Подключение успешно!")
            logger.info(f"💰 Баланс USDT: {total_usdt:.2f} (доступно: {free_usdt:.2f})")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка подключения: {e}")
            return False
    
    async def monitor_price(self):
        """Простой мониторинг цены"""
        try:
            import ccxt
            
            exchange = ccxt.bybit({
                'apiKey': os.getenv('BYBIT_API_KEY'),
                'secret': os.getenv('BYBIT_API_SECRET'),
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'swap',
                    'testnet': self.testnet
                }
            })
            
            if self.testnet:
                exchange.set_sandbox_mode(True)
            
            while self.is_running:
                try:
                    # Получаем текущую цену
                    ticker = exchange.fetch_ticker(self.symbol)
                    current_price = ticker['last']
                    volume_24h = ticker['quoteVolume']
                    
                    logger.info(f"📈 {self.symbol}: ${current_price:.2f} | Объем 24ч: ${volume_24h:,.0f}")
                    
                    # Пауза между проверками
                    await asyncio.sleep(30)  # Проверяем каждые 30 секунд
                    
                except Exception as e:
                    logger.error(f"Ошибка получения цены: {e}")
                    await asyncio.sleep(60)
                    
        except KeyboardInterrupt:
            logger.info("🛑 Остановка бота...")
            self.is_running = False
    
    async def run(self):
        """Основной цикл бота"""
        logger.info("🚀 Запуск Crypto Trading Bot (упрощенная версия)")
        
        # Проверяем подключение
        if not await self.check_connection():
            logger.error("❌ Не удалось подключиться к бирже. Проверьте настройки!")
            return
        
        # Запускаем мониторинг
        logger.info("📊 Начинаем мониторинг рынка...")
        await self.monitor_price()

async def main():
    """Точка входа"""
    bot = SimpleCryptoBot()
    
    try:
        await bot.run()
    except KeyboardInterrupt:
        logger.info("🛑 Получен сигнал остановки")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
    finally:
        logger.info("👋 Бот остановлен")

if __name__ == "__main__":
    # Проверяем что директория logs существует
    os.makedirs('logs', exist_ok=True)
    
    # Запускаем бота
    asyncio.run(main())