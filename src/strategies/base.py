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
