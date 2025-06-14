"""
Инициализация модуля стратегий
Путь: src/strategies/__init__.py
"""
from .factory import StrategyFactory, strategy_factory
from .base import BaseStrategy, TradingSignal

# Экспортируем основные классы
__all__ = [
    'StrategyFactory',
    'strategy_factory', 
    'BaseStrategy',
    'TradingSignal'
]

# Информация о модуле
__version__ = '1.0.0'
__author__ = 'Crypto Trading Bot'

print(f"📦 Модуль стратегий инициализирован (версия {__version__})")
