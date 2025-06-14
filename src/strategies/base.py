"""
Базовый класс для всех стратегий
Путь: /var/www/www-root/data/www/systemetech.ru/src/strategies/base.py
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple, Dict, Any, Optional
import pandas as pd
from dataclasses import dataclass

@dataclass
class TradingSignal:
    """Результат анализа стратегии"""
    action: str  # BUY, SELL, WAIT
    confidence: float  # 0.0-1.0
    price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    reason: str = ""
    risk_reward_ratio: float = 0.0
    indicators: Dict[str, float] = None

class BaseStrategy(ABC):
    """Базовый класс стратегии"""
    
    def __init__(self, name: str):
        self.name = name
        self.min_confidence = 0.6
    
    @abstractmethod
    async def analyze(self, df: pd.DataFrame, symbol: str) -> TradingSignal:
        """Анализ данных и генерация сигнала"""
        pass
    
    def validate_dataframe(self, df: pd.DataFrame) -> bool:
        """Валидация входных данных"""
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        
        if not all(col in df.columns for col in required_columns):
            return False
            
        if len(df) < 50:  # Минимум данных для анализа
            return False
            
        if df.isnull().any().any():
            return False
            
        return True
    
    def calculate_stop_loss(self, price: float, side: str, atr: float, multiplier: float = 2.0) -> float:
        """Расчет стоп-лосса на основе ATR"""
        if side == 'BUY':
            return price - (atr * multiplier)
        else:
            return price + (atr * multiplier)
    
    def calculate_take_profit(self, price: float, side: str, atr: float, multiplier: float = 3.0) -> float:
        """Расчет тейк-профита на основе ATR"""
        if side == 'BUY':
            return price + (atr * multiplier)
        else:
            return price - (atr * multiplier)
    
    def calculate_risk_reward(self, entry: float, stop_loss: float, take_profit: float) -> float:
        """Расчет соотношения риск/прибыль"""
        risk = abs(entry - stop_loss)
        reward = abs(take_profit - entry)
        
        if risk == 0:
            return 0
            
        return reward / risk