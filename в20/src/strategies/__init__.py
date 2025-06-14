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
