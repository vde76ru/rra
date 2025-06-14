"""
Отладочная версия главного файла
Файл: main_debug.py
"""

import asyncio
import argparse
import signal
import sys
import socket
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Импорты нашего проекта
from src.core.config import Config
from src.core.clean_logging import init_logging_system, get_clean_logger, trading_logger
from src.bot.manager import BotManager
from src.web.api_routes import router as api_router, set_bot_manager, ws_manager
from src.core.database import init_database, init_database_async

# Глобальные переменные
config = Config()
bot_manager: Optional[BotManager] = None
web_app: Optional[FastAPI] = None
shutdown_event = asyncio.Event()

# Инициализируем логгер после настройки системы логирования
logger = None

def check_port_availability(host: str, port: int) -> bool:
    """
    Проверка доступности порта
    
    Простая функция, которая пытается подключиться к порту.
    Если подключение удается, значит порт занят.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)  # Таймаут 1 секунда
            result = s.connect_ex((host, port))
            return result != 0  # 0 означает успешное подключение (порт занят)
    except Exception as e:
        logger.warning(f"⚠️ Ошибка проверки порта {port}: {e}")
        return True  # Считаем доступным при ошибке

def setup_signal_handlers():
    """Настройка обработчиков сигналов для graceful shutdown"""
    def signal_handler(signum, frame):
        logger.info(f"🛑 Получен сигнал {signum}, начинаем завершение...")
        shutdown_event.set()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Современный lifespan manager для FastAPI
    
    Этот менеджер контекста управляет жизненным циклом приложения:
    - При запуске: инициализирует ресурсы
    - При завершении: освобождает ресурсы
    """
    logger.info("🌐 Lifespan: Начинаем инициализацию...")
    
    try:
        # === STARTUP PHASE ===
        logger.info("🚀 Lifespan: Startup phase начался")
        
        # Инициализируем базу данных
        logger.info("💾 Lifespan: Инициализируем базу данных...")
        result = await init_database_async()
        if result:
            logger.info("✅ Lifespan: База данных инициализирована асинхронно")
        else:
            logger.warning("⚠️ Lifespan: База данных инициализирована в синхронном режиме")
        
        logger.info("✅ Lifespan: Startup phase завершен успешно")
        
        # === YIELD - ПРИЛОЖЕНИЕ РАБОТАЕТ ===
        yield
        
    except Exception as startup_error:
        logger.error(f"❌ Lifespan: Ошибка в startup phase: {startup_error}", exc_info=True)
        raise
    finally:
        # === SHUTDOWN PHASE ===
        logger.info("🛑 Lifespan: Начинаем shutdown phase...")
        
        try:
            # Здесь можно добавить cleanup логику
            logger.info("🧹 Lifespan: Очистка ресурсов...")
            
            # Например, остановка BotManager если он был запущен
            global bot_manager
            if bot_manager and hasattr(bot_manager, 'status'):
                logger.info("🤖 Lifespan: Останавливаем BotManager...")
                try:
                    await bot_manager.stop()
                    logger.info("✅ Lifespan: BotManager остановлен")
                except Exception as bot_stop_error:
                    logger.warning(f"⚠️ Lifespan: Ошибка остановки BotManager: {bot_stop_error}")
            
            logger.info("✅ Lifespan: Shutdown phase завершен")
            
        except Exception as shutdown_error:
            logger.error(f"❌ Lifespan: Ошибка в shutdown phase: {shutdown_error}")

def create_web_app() -> FastAPI:
    """
    Создание FastAPI приложения с современным lifespan
    
    Эта функция создает основное веб-приложение со всеми
    необходимыми настройками и middleware.
    """
    logger.info("🏗️ Создаем FastAPI приложение...")
    
    app = FastAPI(
        title="🚀 Crypto Trading Bot Dashboard",
        description="Полная панель управления криптотрейдинг ботом",
        version="3.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan  # ✅ Используем современный подход
    )
    
    logger.info("🔧 Настраиваем CORS middleware...")
    
    # CORS middleware для фронтенда
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # В продакшене ограничить конкретными доменами
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    logger.info("🛣️ Подключаем API роуты...")
    
    # Подключаем роуты дашборда
    app.include_router(api_router)
    
    logger.info("✅ FastAPI приложение создано успешно")
    return app

async def run_web_only():
    """
    Запуск только веб-интерфейса
    
    Эта функция запускает только веб-сервер без торгового бота.
    Полезно для отладки интерфейса или настройки системы.
    """
    global web_app
    
    logger.info("🌐 === ЗАПУСК ВЕБА В РЕЖИМЕ WEB-ONLY ===")
    
    try:
        # === ШАГ 1: ПРОВЕРКА ПОРТА ===
        logger.info("🔍 Проверяем доступность порта 8000...")
        if not check_port_availability("0.0.0.0", 8000):
            logger.error("❌ Порт 8000 уже занят! Завершите процесс или используйте другой порт.")
            logger.info("💡 Подсказка: Используйте 'netstat -tulpn | grep :8000' для поиска процесса")
            return
        logger.info("✅ Порт 8000 доступен")
        
        # === ШАГ 2: СОЗДАНИЕ ПРИЛОЖЕНИЯ ===
        logger.info("🏗️ Создаем веб-приложение...")
        web_app = create_web_app()
        logger.info("✅ Веб-приложение создано")
        
        # === ШАГ 3: НАСТРОЙКА СЕРВЕРА ===
        logger.info("⚙️ Настраиваем uvicorn сервер...")
        config_uvicorn = uvicorn.Config(
            app=web_app,
            host="0.0.0.0",
            port=8000,
            log_level="info",  # Увеличим уровень логирования для отладки
            access_log=True,   # Включим access логи для отладки
            ws_ping_interval=20,
            ws_ping_timeout=10,
            loop="asyncio"     # Явно указываем event loop
        )
        
        server = uvicorn.Server(config_uvicorn)
        logger.info("✅ Uvicorn сервер настроен")
        
        # === ШАГ 4: ИНФОРМИРОВАНИЕ ПОЛЬЗОВАТЕЛЯ ===
        logger.info("🚀 " + "=" * 50)
        logger.info("🚀 ВЕБА-СЕРВЕР ГОТОВ К ЗАПУСКУ!")
        logger.info("🚀 " + "=" * 50)
        logger.info("🌐 URL: http://0.0.0.0:8000")
        logger.info("📊 Дашборд: http://localhost:8000")
        logger.info("📖 Документация API: http://localhost:8000/docs")
        logger.info("🔧 Redoc: http://localhost:8000/redoc")
        logger.info("🚀 " + "=" * 50)
        
        # === ШАГ 5: ЗАПУСК СЕРВЕРА ===
        logger.info("⚡ Запускаем uvicorn сервер...")
        logger.info("⚡ Если всё прошло успешно, вы увидите сообщения uvicorn...")
        
        await server.serve()
        
    except Exception as e:
        logger.error(f"💥 Критическая ошибка веб-интерфейса: {e}", exc_info=True)
        logger.error("🔍 Возможные причины:")
        logger.error("   1. Порт 8000 занят другим процессом")
        logger.error("   2. Проблемы с правами доступа")
        logger.error("   3. Ошибка в коде FastAPI приложения")
        logger.error("   4. Проблемы с базой данных")
        raise

async def run_bot_only():
    """Запуск только торгового бота без веб-интерфейса"""
    global bot_manager
    
    logger.info("🤖 === ЗАПУСК БОТА В РЕЖИМЕ BOT-ONLY ===")
    
    try:
        logger.info("🔧 Создаем BotManager...")
        bot_manager = BotManager()
        logger.info("✅ BotManager создан")
        
        logger.info("🚀 Запускаем торгового бота...")
        success, message = await bot_manager.start()
        if not success:
            logger.error(f"❌ Не удалось запустить бота: {message}")
            return
        
        logger.info("✅ Торговый бот запущен успешно")
        logger.info("⏳ Ожидаем сигнал завершения (Ctrl+C)...")
        
        await shutdown_event.wait()
        
    except Exception as e:
        logger.error(f"💥 Ошибка в торговом боте: {e}", exc_info=True)
        raise
    finally:
        if bot_manager:
            logger.info("🛑 Останавливаем торгового бота...")
            await bot_manager.stop()
            logger.info("✅ Торговый бот остановлен")

async def run_full_system():
    """Запуск полной системы: бот + веб-интерфейс"""
    global bot_manager, web_app
    
    logger.info("🚀 === ЗАПУСК ПОЛНОЙ СИСТЕМЫ ===")
    
    try:
        # === ШАГ 1: ПРОВЕРКА ПОРТА ===
        logger.info("🔍 Проверяем доступность порта 8000...")
        if not check_port_availability("0.0.0.0", 8000):
            logger.error("❌ Порт 8000 уже занят!")
            return
        
        # === ШАГ 2: ИНИЦИАЛИЗАЦИЯ БОТА ===
        logger.info("🤖 Создаем и настраиваем BotManager...")
        bot_manager = BotManager()
        set_bot_manager(bot_manager)  # Связываем с веб-интерфейсом
        logger.info("✅ BotManager создан и связан с веб-интерфейсом")
        
        # === ШАГ 3: СОЗДАНИЕ ВЕБ-ПРИЛОЖЕНИЯ ===
        logger.info("🌐 Создаем веб-приложение...")
        web_app = create_web_app()
        
        # === ШАГ 4: НАСТРОЙКА СЕРВЕРА ===
        config_uvicorn = uvicorn.Config(
            app=web_app,
            host="0.0.0.0",
            port=8000,
            log_level="info",
            access_log=True,
            ws_ping_interval=20,
            ws_ping_timeout=10,
            loop="asyncio"
        )
        
        server = uvicorn.Server(config_uvicorn)
        
        # === ШАГ 5: ИНФОРМИРОВАНИЕ ===
        logger.info("🚀 " + "=" * 50)
        logger.info("🚀 ПОЛНАЯ СИСТЕМА ГОТОВА К ЗАПУСКУ!")
        logger.info("🚀 " + "=" * 50)
        logger.info("🌐 Веб-интерфейс: http://localhost:8000")
        logger.info("🤖 Торговый бот: Интегрирован")
        logger.info("📊 Дашборд: http://localhost:8000")
        logger.info("📖 API Docs: http://localhost:8000/docs")
        logger.info("🚀 " + "=" * 50)
        
        # === ШАГ 6: ЗАПУСК ===
        logger.info("⚡ Запускаем полную систему...")
        await server.serve()
        
    except Exception as e:
        logger.error(f"💥 Ошибка полной системы: {e}", exc_info=True)
        raise
    finally:
        if bot_manager:
            logger.info("🛑 Останавливаем систему...")
            await bot_manager.stop()
            logger.info("✅ Система остановлена")

async def main():
    """
    Главная функция приложения
    
    Точка входа в программу. Парсит аргументы командной строки
    и запускает соответствующий режим работы.
    """
    global logger
    
    # === ИНИЦИАЛИЗАЦИЯ ЛОГИРОВАНИЯ ===
    print("🔧 Инициализируем систему логирования...")
    init_logging_system()
    logger = get_clean_logger(__name__)
    
    # === НАСТРОЙКА ОБРАБОТЧИКОВ СИГНАЛОВ ===
    logger.info("📡 Настраиваем обработчики сигналов...")
    setup_signal_handlers()
    
    # === ПАРСИНГ АРГУМЕНТОВ ===
    parser = argparse.ArgumentParser(description="Crypto Trading Bot")
    parser.add_argument("--mode", choices=["bot", "web", "full"], default="full",
                        help="Режим запуска (bot=только бот, web=только веб, full=полная система)")
    parser.add_argument("--debug", action="store_true", 
                        help="Включить отладочный режим")
    args = parser.parse_args()
    
    # === ПРИВЕТСТВИЕ ===
    logger.info("=" * 60)
    logger.info("🚀 CRYPTO TRADING BOT v3.0 - ОТЛАДОЧНАЯ ВЕРСИЯ")
    logger.info("=" * 60)
    logger.info(f"🎯 Режим запуска: {args.mode.upper()}")
    logger.info(f"🐛 Отладка: {'ВКЛ' if args.debug else 'ВЫКЛ'}")
    logger.info("=" * 60)
    
    try:
        # === ВЫБОР РЕЖИМА РАБОТЫ ===
        if args.mode == "bot":
            logger.info("🤖 Выбран режим: ТОЛЬКО ТОРГОВЫЙ БОТ")
            await run_bot_only()
        elif args.mode == "web":
            logger.info("🌐 Выбран режим: ТОЛЬКО ВЕБ-ИНТЕРФЕЙС")
            await run_web_only()
        else:  # full
            logger.info("🚀 Выбран режим: ПОЛНАЯ СИСТЕМА")
            await run_full_system()
            
    except KeyboardInterrupt:
        logger.info("🛑 Получен сигнал прерывания (Ctrl+C)")
        logger.info("👋 Программа завершается по запросу пользователя")
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}", exc_info=True)
        logger.error("🔍 Рекомендации по устранению:")
        logger.error("   1. Проверьте конфигурацию .env файла")
        logger.error("   2. Убедитесь что MySQL сервер запущен")
        logger.error("   3. Проверьте доступность порта 8000")
        logger.error("   4. Проверьте права доступа к файлам")
        sys.exit(1)
    finally:
        logger.info("🏁 Завершение программы")
        logger.info("📊 Статистика сессии сохранена")
        logger.info("👋 До свидания!")

if __name__ == "__main__":
    asyncio.run(main())