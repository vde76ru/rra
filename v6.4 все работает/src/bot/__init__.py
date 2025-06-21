"""
Bot модули для торгового бота
"""

# Безопасный импорт основных компонентов
try:
    from .manager import BotManager
except ImportError:
    BotManager = None

try:
    from .trader import Trader
except ImportError:
    Trader = None

try:
    from .trading_integration import TradingBotWithRealTrading
except ImportError:
    TradingBotWithRealTrading = None

try:
    from .signal_processor import SignalProcessor
except ImportError:
    SignalProcessor = None

__all__ = [
    'BotManager',
    'Trader', 
    'TradingBotWithRealTrading',
    'SignalProcessor'
]