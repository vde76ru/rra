#!/usr/bin/env python3
"""
Главная точка входа в приложение Crypto Trading Bot
Поддерживает различные режимы запуска
"""
import asyncio
import argparse
import sys
import os
from pathlib import Path
from dotenv import load_dotenv
import logging

# Добавляем корневую директорию в path
sys.path.insert(0, str(Path(__file__).parent))

# Загружаем переменные окружения
load_dotenv()

# Импорты после настройки путей
from src.web.app import create_app
from src.bot.manager import BotManager
from src.core.database import init_db, SessionLocal
from src.logging.smart_logger import SmartLogger
from src.logging.log_manager import cleanup_scheduler
from src.web.websocket_server import WebSocketServer
from src.ml.data_pipeline import DataPipeline

# Настройка логирования
smart_logger = SmartLogger("main")
logger = smart_logger


class CryptoTradingApp:
    """Главный класс приложения"""
    
    def __init__(self):
        self.web_app = None
        self.bot_manager = None
        self.websocket_server = None
        self.data_pipeline = None
        self.is_running = False
    
    async def init_database(self):
        """Инициализация базы данных"""
        logger.info("Инициализация базы данных...", category='system')
        try:
            # Создаем таблицы если их нет
            init_db()
            
            # Проверяем подключение
            db = SessionLocal()
            db.execute("SELECT 1")
            db.close()
            
            logger.info("База данных успешно инициализирована", category='system')
            return True
        except Exception as e:
            logger.error(f"Ошибка инициализации БД: {e}", category='error')
            return False
    
    async def start_web_interface(self, host='0.0.0.0', port=5000):
        """Запуск веб-интерфейса"""
        logger.info(f"Запуск веб-интерфейса на {host}:{port}", category='system')
        
        try:
            # Создаем Flask приложение
            self.web_app = create_app()
            
            # Инициализируем WebSocket сервер
            self.websocket_server = WebSocketServer(self.web_app)
            await self.websocket_server.start()
            
            # Запускаем Flask в отдельном потоке
            import threading
            from werkzeug.serving import run_simple
            
            def run_flask():
                run_simple(host, port, self.web_app, use_reloader=False, use_debugger=False)
            
            flask_thread = threading.Thread(target=run_flask)
            flask_thread.daemon = True
            flask_thread.start()
            
            logger.info(f"✅ Веб-интерфейс запущен: http://{host}:{port}", category='system')
            logger.info("📊 Дашборд доступен по адресу: http://localhost:5000/dashboard", category='system')
            return True
            
        except Exception as e:
            logger.error(f"Ошибка запуска веб-интерфейса: {e}", category='error')
            return False
    
    async def start_trading_bot(self):
        """Запуск торгового бота"""
        logger.info("Запуск торгового бота...", category='system')
        
        try:
            # Создаем менеджер бота
            self.bot_manager = BotManager()
            
            # Инициализируем ML pipeline
            self.data_pipeline = DataPipeline()
            await self.data_pipeline.initialize()
            
            # Запускаем бота
            await self.bot_manager.start()
            
            logger.info("✅ Торговый бот успешно запущен", category='system')
            return True
            
        except Exception as e:
            logger.error(f"Ошибка запуска бота: {e}", category='error')
            return False
    
    async def start_full_app(self, host='0.0.0.0', port=5000):
        """Полный запуск приложения (веб + бот)"""
        logger.info("🚀 Запуск полного приложения...", category='system')
        
        # Инициализация БД
        if not await self.init_database():
            return False
        
        # Запуск логирования
        await smart_logger.start_db_writer()
        await cleanup_scheduler.start()
        
        # Запуск веб-интерфейса
        if not await self.start_web_interface(host, port):
            return False
        
        # Запуск бота
        if not await self.start_trading_bot():
            return False
        
        self.is_running = True
        logger.info("✅ Приложение полностью запущено!", category='system')
        
        # Держим приложение запущенным
        try:
            while self.is_running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Получен сигнал остановки", category='system')
        
        await self.shutdown()
    
    async def start_web_only(self, host='0.0.0.0', port=5000):
        """Запуск только веб-интерфейса"""
        logger.info("🌐 Запуск только веб-интерфейса...", category='system')
        
        # Инициализация БД
        if not await self.init_database():
            return False
        
        # Запуск логирования
        await smart_logger.start_db_writer()
        await cleanup_scheduler.start()
        
        # Запуск веб-интерфейса
        if not await self.start_web_interface(host, port):
            return False
        
        self.is_running = True
        logger.info("✅ Веб-интерфейс запущен! Бот можно запустить из дашборда", category='system')
        
        # Держим приложение запущенным
        try:
            while self.is_running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Получен сигнал остановки", category='system')
        
        await self.shutdown()
    
    async def shutdown(self):
        """Корректное завершение работы"""
        logger.info("Завершение работы приложения...", category='system')
        
        self.is_running = False
        
        # Останавливаем бота
        if self.bot_manager:
            await self.bot_manager.stop()
        
        # Останавливаем WebSocket
        if self.websocket_server:
            await self.websocket_server.stop()
        
        # Останавливаем логирование
        await smart_logger.stop_db_writer()
        await cleanup_scheduler.stop()
        
        logger.info("✅ Приложение остановлено", category='system')


def parse_arguments():
    """Парсинг аргументов командной строки"""
    parser = argparse.ArgumentParser(
        description='Crypto Trading Bot - Интеллектуальная система криптотрейдинга'
    )
    
    parser.add_argument(
        '--mode',
        choices=['full', 'web', 'bot'],
        default='web',
        help='Режим запуска: full (веб+бот), web (только веб), bot (только бот)'
    )
    
    parser.add_argument(
        '--host',
        default='0.0.0.0',
        help='Хост для веб-сервера (default: 0.0.0.0)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=5000,
        help='Порт для веб-сервера (default: 5000)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Включить режим отладки'
    )
    
    return parser.parse_args()


async def main():
    """Главная функция"""
    args = parse_arguments()
    
    # Настройка логирования
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    # Проверка переменных окружения
    required_env = ['EXCHANGE_API_KEY', 'EXCHANGE_API_SECRET', 'DATABASE_URL']
    missing_env = [var for var in required_env if not os.getenv(var)]
    
    if missing_env:
        logger.error(f"Отсутствуют переменные окружения: {', '.join(missing_env)}", category='error')
        logger.info("Создайте файл .env на основе .env.example", category='system')
        return
    
    # Создаем приложение
    app = CryptoTradingApp()
    
    try:
        if args.mode == 'full':
            await app.start_full_app(args.host, args.port)
        elif args.mode == 'web':
            await app.start_web_only(args.host, args.port)
        elif args.mode == 'bot':
            # Только бот (без веб-интерфейса)
            if await app.init_database():
                await smart_logger.start_db_writer()
                await cleanup_scheduler.start()
                await app.start_trading_bot()
                
                # Держим бота запущенным
                try:
                    while True:
                        await asyncio.sleep(1)
                except KeyboardInterrupt:
                    pass
                
                await app.shutdown()
    except Exception as e:
        logger.critical(f"Критическая ошибка: {e}", category='error')
        await app.shutdown()


if __name__ == '__main__':
    print("""
╔═══════════════════════════════════════════════════════════╗
║            CRYPTO TRADING BOT v2.0                        ║
║    Интеллектуальная система криптотрейдинга с ML         ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 До свидания!")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        sys.exit(1)