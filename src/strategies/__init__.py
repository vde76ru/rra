"""
Модуль стратегий
"""
from .factory import strategy_factory, StrategyFactory
from .base import BaseStrategy, TradingSignal

__all__ = [
    'strategy_factory',
    'StrategyFactory', 
    'BaseStrategy',
    'TradingSignal'
]