#!/bin/bash
# final_refactoring.sh - Финальные шаги рефакторинга

cd /var/www/www-root/data/www/systemetech.ru

echo "🚀 ФИНАЛЬНЫЙ РЕФАКТОРИНГ CRYPTO TRADING BOT"
echo "==========================================="

# 1. Останавливаем все процессы
echo -e "\n🛑 Остановка всех процессов..."
pkill -f "python.*main" || true
pkill -f "python.*app" || true
systemctl stop cryptobot 2>/dev/null || true

# 2. Создаем бэкап текущего состояния
echo -e "\n💾 Создание полного бэкапа..."
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Копируем важные файлы
cp -r src "$BACKUP_DIR/" 2>/dev/null || true
cp *.py "$BACKUP_DIR/" 2>/dev/null || true
cp -r logs "$BACKUP_DIR/" 2>/dev/null || true

echo "✅ Бэкап создан в $BACKUP_DIR"

# 3. Применяем новую структуру
echo -e "\n📁 Применение новой структуры..."

# Создаем все необходимые директории
mkdir -p src/{core,bot,exchange,strategies,analysis,notifications,web}
mkdir -p scripts tests docs
mkdir -p data/{cache,backups}
mkdir -p logs

# 4. Создаем новые файлы ядра
echo -e "\n🔧 Создание файлов ядра системы..."

# Создаем __init__.py везде
find src -type d -exec touch {}/__init__.py \;

# Создаем исключения
cat > src/core/exceptions.py << 'EOF'
"""Кастомные исключения"""

class BotException(Exception):
    """Базовое исключение бота"""
    pass

class ConfigurationError(BotException):
    """Ошибка конфигурации"""
    pass

class ExchangeError(BotException):
    """Ошибка работы с биржей"""
    pass

class StrategyError(BotException):
    """Ошибка стратегии"""
    pass

class InsufficientBalanceError(BotException):
    """Недостаточно средств"""
    pass
EOF

# 5. Создаем базовый класс стратегии
echo -e "\n📊 Создание базовых классов..."

cat > src/strategies/base.py << 'EOF'
"""Базовый класс для всех стратегий"""
from abc import ABC, abstractmethod
from typing import Dict, Any
import pandas as pd
from dataclasses import dataclass

@dataclass
class Signal:
    """Торговый сигнал"""
    symbol: str
    action: str  # BUY, SELL, WAIT
    confidence: float
    price: float
    stop_loss: float = None
    take_profit: float = None
    reason: str = ""
    strategy: str = ""

class BaseStrategy(ABC):
    """Базовый класс стратегии"""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    async def analyze(self, df: pd.DataFrame, symbol: str) -> Signal:
        """Анализ данных и генерация сигнала"""
        pass
    
    def validate_dataframe(self, df: pd.DataFrame) -> bool:
        """Валидация входных данных"""
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        return all(col in df.columns for col in required_columns)
EOF

# 6. Создаем фабрику стратегий
cat > src/strategies/__init__.py << 'EOF'
"""Фабрика стратегий"""
from typing import Dict, Type
from .base import BaseStrategy
from .momentum import MomentumStrategy
from .multi_indicator import MultiIndicatorStrategy
from .scalping import ScalpingStrategy

class StrategyFactory:
    """Фабрика для создания стратегий"""
    
    _strategies: Dict[str, Type[BaseStrategy]] = {
        'momentum': MomentumStrategy,
        'multi_indicator': MultiIndicatorStrategy,
        'scalping': ScalpingStrategy
    }
    
    @classmethod
    def create(cls, name: str) -> BaseStrategy:
        """Создать стратегию по имени"""
        strategy_class = cls._strategies.get(name)
        if not strategy_class:
            raise ValueError(f"Неизвестная стратегия: {name}")
        return strategy_class()
    
    @classmethod
    def list_strategies(cls) -> list:
        """Список доступных стратегий"""
        return list(cls._strategies.keys())
EOF

# 7. Создаем анализатор рынка
echo -e "\n📈 Создание анализатора рынка..."

mkdir -p src/analysis
cat > src/analysis/market_analyzer.py << 'EOF'
"""Анализатор рынка"""
import logging
from typing import Dict, List
import pandas as pd
from ..exchange.client import exchange_client

logger = logging.getLogger(__name__)

class MarketAnalyzer:
    """Анализ рыночных данных"""
    
    def __init__(self):
        self.exchange = exchange_client
    
    async def analyze_market(self, symbols: List[str]) -> Dict[str, pd.DataFrame]:
        """Анализ рынка для списка символов"""
        market_data = {}
        
        for symbol in symbols:
            try:
                # Получаем исторические данные
                ohlcv = await self.exchange.fetch_ohlcv(symbol, '5m', 200)
                
                # Преобразуем в DataFrame
                df = pd.DataFrame(
                    ohlcv,
                    columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
                )
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('timestamp', inplace=True)
                
                market_data[symbol] = df
                
            except Exception as e:
                logger.error(f"Ошибка анализа {symbol}: {e}")
        
        return market_data
    
    def calculate_volatility(self, df: pd.DataFrame) -> float:
        """Расчет волатильности"""
        returns = df['close'].pct_change().dropna()
        return returns.std() * (252 ** 0.5)  # Годовая волатильность
    
    def detect_trend(self, df: pd.DataFrame) -> str:
        """Определение тренда"""
        sma_short = df['close'].rolling(window=20).mean()
        sma_long = df['close'].rolling(window=50).mean()
        
        if sma_short.iloc[-1] > sma_long.iloc[-1]:
            return 'UPTREND'
        elif sma_short.iloc[-1] < sma_long.iloc[-1]:
            return 'DOWNTREND'
        else:
            return 'SIDEWAYS'
EOF

# 8. Обновляем уведомления
echo -e "\n📢 Обновление системы уведомлений..."

cat > src/notifications/telegram.py << 'EOF'
"""Telegram уведомления"""
import os
import asyncio
import logging
from datetime import datetime
from telegram import Bot
from telegram.error import TelegramError
from typing import Optional, List

from ..core.config import config

logger = logging.getLogger(__name__)

class TelegramNotifier:
    """Отправка уведомлений в Telegram"""
    
    def __init__(self):
        self.bot = Bot(token=config.TELEGRAM_BOT_TOKEN) if config.TELEGRAM_BOT_TOKEN else None
        self.chat_id = config.TELEGRAM_CHAT_ID
        self.enabled = bool(self.bot and self.chat_id)
        
        if not self.enabled:
            logger.warning("Telegram уведомления отключены")
    
    async def send_message(self, text: str, parse_mode: str = 'HTML'):
        """Отправка сообщения"""
        if not self.enabled:
            return
        
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=text,
                parse_mode=parse_mode
            )
        except TelegramError as e:
            logger.error(f"Ошибка отправки в Telegram: {e}")
    
    async def send_startup_message(self, pairs: List[str], mode: str):
        """Уведомление о запуске"""
        text = f"""🚀 <b>Бот запущен</b>
        
📊 Режим: {mode}
💱 Пары: {', '.join(pairs)}
⏰ Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        await self.send_message(text)
    
    async def send_trade_opened(self, symbol: str, side: str, amount: float, price: float):
        """Уведомление об открытии сделки"""
        emoji = "🟢" if side == "BUY" else "🔴"
        text = f"""{emoji} <b>Открыта позиция</b>
        
💱 {symbol}
📊 {side} {amount:.4f}
💵 Цена: ${price:.2f}
        """
        await self.send_message(text)
    
    async def send_error(self, error: str):
        """Уведомление об ошибке"""
        text = f"""🚨 <b>Ошибка</b>
        
{error[:500]}
        """
        await self.send_message(text)
EOF

# 9. Создаем новый web app
echo -e "\n🌐 Создание нового веб-приложения..."

cat > src/web/app.py << 'EOF'
"""Веб-интерфейс"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import router as api_router
from .websocket import websocket_endpoint

def create_app() -> FastAPI:
    """Создание FastAPI приложения"""
    app = FastAPI(
        title="Crypto Trading Bot",
        version="3.0",
        description="Professional Crypto Trading Bot"
    )
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Роуты
    app.include_router(api_router, prefix="/api")
    app.websocket("/ws")(websocket_endpoint)
    
    return app

app = create_app()
EOF

# 10. Создаем единый main.py
echo -e "\n🎯 Создание единого main.py..."

cat > main.py << 'EOF'
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
EOF

chmod +x main.py

# 11. Обновляем скрипты
echo -e "\n📜 Создание управляющих скриптов..."

cat > scripts/start.sh << 'EOF'
#!/bin/bash
cd /var/www/www-root/data/www/systemetech.ru
source venv/bin/activate
python main.py "$@"
EOF

cat > scripts/stop.sh << 'EOF'
#!/bin/bash
pkill -f "python.*main.py" || true
echo "✅ Бот остановлен"
EOF

cat > scripts/status.sh << 'EOF'
#!/bin/bash
if pgrep -f "python.*main.py" > /dev/null; then
    echo "✅ Бот запущен"
    ps aux | grep "python.*main.py" | grep -v grep
else
    echo "❌ Бот не запущен"
fi
EOF

chmod +x scripts/*.sh

# 12. Финальная проверка
echo -e "\n🔍 Финальная проверка..."

# Проверяем структуру
echo -e "\n📁 Структура проекта:"
tree -d -L 3 src/ 2>/dev/null || find src -type d | sort

# Проверяем Python модули
echo -e "\n🐍 Проверка импортов:"
python -c "
try:
    from src.core.config import config
    from src.bot.manager import bot_manager
    from src.exchange.client import exchange_client
    print('✅ Основные модули импортируются успешно')
except Exception as e:
    print(f'❌ Ошибка импорта: {e}')
"

echo -e "\n✨ РЕФАКТОРИНГ ЗАВЕРШЕН!"
echo ""
echo "📝 Дальнейшие действия:"
echo "1. Перенесите логику из старых файлов в новые модули"
echo "2. Обновите импорты во всех файлах"
echo "3. Протестируйте систему: python main.py --mode bot"
echo "4. Запустите полную систему: python main.py"
echo ""
echo "🚀 Команды:"
echo "   ./scripts/start.sh       # Запуск всей системы"
echo "   ./scripts/start.sh bot   # Только бот"
echo "   ./scripts/start.sh web   # Только веб"
echo "   ./scripts/status.sh      # Проверка статуса"
echo "   ./scripts/stop.sh        # Остановка"