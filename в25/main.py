"""
Обновленный главный файл с интеграцией полного дашборда
Файл: main.py
"""

import asyncio
import argparse
import signal
import sys
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Импорты нашего проекта
from src.core.config import Config
from src.core.clean_logging import init_logging_system, get_clean_logger, trading_logger
from src.bot.manager import BotManager  # ✅ ИСПРАВЛЕНО: используем правильное имя класса
from src.web.api_routes import router as api_router, set_bot_manager, ws_manager
from src.core.database import init_database

# Глобальные переменные
config = Config()
bot_manager: Optional[BotManager] = None  # ✅ ИСПРАВЛЕНО: BotManager вместо TradingBotManager
web_app: Optional[FastAPI] = None
shutdown_event = asyncio.Event()

# Инициализируем логгер после настройки системы логирования
logger = None

def setup_signal_handlers():
    """Настройка обработчиков сигналов для graceful shutdown"""
    def signal_handler(signum, frame):
        logger.info(f"🛑 Получен сигнал {signum}, начинаем завершение...")
        shutdown_event.set()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

def create_web_app() -> FastAPI:
    """Создание FastAPI приложения"""
    app = FastAPI(
        title="🚀 Crypto Trading Bot Dashboard",
        description="Полная панель управления криптотрейдинг ботом",
        version="3.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # CORS middleware для фронтенда
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Подключаем роуты дашборда
    app.include_router(api_router)
    
    @app.on_event("startup")
    async def startup_event():
        logger.info("🌐 Веб-приложение запускается...")
        
        # Инициализируем базу данных
        try:
            await init_database()
            logger.info("✅ База данных инициализирована")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации БД: {e}")
    
    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("🌐 Веб-приложение завершается...")
    
    return app

async def run_bot_only():
    """Запуск только торгового бота без веб-интерфейса"""
    global bot_manager
    
    logger.info("🤖 Запуск торгового бота...")
    
    try:
        # Создаем менеджера бота
        bot_manager = BotManager()  # ✅ ИСПРАВЛЕНО: BotManager без параметров
        
        # Запускаем бота с базовой стратегией
        success, message = await bot_manager.start()
        if not success:
            logger.error(f"❌ Не удалось запустить бота: {message}")
            return
        
        logger.info("✅ Торговый бот запущен успешно")
        
        # Ждем сигнала завершения
        await shutdown_event.wait()
        
    except Exception as e:
        logger.error(f"💥 Ошибка в торговом боте: {e}", exc_info=True)
        raise
    finally:
        if bot_manager:
            await bot_manager.stop()
            logger.info("✅ Торговый бот остановлен")

async def run_web_only():
    """Запуск только веб-интерфейса"""
    global web_app
    
    logger.info("🌐 Запуск веб-интерфейса...")
    
    try:
        # Создаем FastAPI приложение
        web_app = create_web_app()
        
        # Настройки сервера
        config_uvicorn = uvicorn.Config(
            app=web_app,
            host="0.0.0.0",
            port=8000,
            log_level="warning",  # Убираем лишние логи uvicorn
            access_log=False,     # Отключаем access логи
            ws_ping_interval=20,
            ws_ping_timeout=10
        )
        
        server = uvicorn.Server(config_uvicorn)
        
        logger.info("🚀 Веб-интерфейс запущен на http://0.0.0.0:8000")
        logger.info("📊 Дашборд доступен по адресу: http://0.0.0.0:8000")
        
        # Запускаем сервер
        await server.serve()
        
    except Exception as e:
        logger.error(f"💥 Ошибка веб-интерфейса: {e}", exc_info=True)
        raise

async def run_full_system():
    """Запуск полной системы: бот + веб-интерфейс"""
    global bot_manager, web_app
    
    logger.info("🚀 Запуск полной системы...")
    
    try:
        # Создаем менеджера бота
        bot_manager = BotManager()
        
        # Устанавливаем ссылку на менеджера в API роутах
        set_bot_manager(bot_manager)
        
        # Создаем веб-приложение
        web_app = create_web_app()
        
        # Настройки сервера
        config_uvicorn = uvicorn.Config(
            app=web_app,
            host="0.0.0.0",
            port=8000,
            log_level="warning",
            access_log=False,
            ws_ping_interval=20,
            ws_ping_timeout=10
        )
        
        server = uvicorn.Server(config_uvicorn)
        
        logger.info("🚀 Полная система запущена на http://0.0.0.0:8000")
        logger.info("📊 Дашборд: http://0.0.0.0:8000")
        logger.info("📖 Документация API: http://0.0.0.0:8000/docs")
        
        # Запускаем сервер
        await server.serve()
        
    except Exception as e:
        logger.error(f"💥 Ошибка полной системы: {e}", exc_info=True)
        raise
    finally:
        if bot_manager:
            await bot_manager.stop()
            logger.info("✅ Система остановлена")

async def main():
    """Главная функция приложения"""
    global logger
    
    # Инициализируем систему логирования
    init_logging_system()
    logger = get_clean_logger(__name__)
    
    # Настройка обработчиков сигналов
    setup_signal_handlers()
    
    # Парсинг аргументов командной строки
    parser = argparse.ArgumentParser(description="Crypto Trading Bot")
    parser.add_argument("--mode", choices=["bot", "web", "full"], default="full",
                        help="Режим запуска (bot=только бот, web=только веб, full=полная система)")
    args = parser.parse_args()
    
    logger.info("=" * 50)
    logger.info("🚀 Crypto Trading Bot v3.0 - Полная система")
    logger.info("=" * 50)
    
    try:
        if args.mode == "bot":
            await run_bot_only()
        elif args.mode == "web":
            await run_web_only()
        else:  # full
            await run_full_system()
            
    except KeyboardInterrupt:
        logger.info("🛑 Получен сигнал прерывания")
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("🏁 Завершение программы")
        logger.info("📈 Программа завершена")

if __name__ == "__main__":
    asyncio.run(main())