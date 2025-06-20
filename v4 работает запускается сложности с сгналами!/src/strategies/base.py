"""
Базовый класс для всех торговых стратегий
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime
import pandas as pd

@dataclass
class TradingSignal:
    """Торговый сигнал от стратегии"""
    action: str  # BUY, SELL, HOLD
    confidence: float  # 0-1
    price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class BaseStrategy(ABC):
    """Базовый класс для всех стратегий"""
    
    # Метаданные стратегии (переопределить в наследниках)
    NAME = "BaseStrategy"
    DESCRIPTION = "Base strategy class"
    TYPE = "base"  # momentum, mean_reversion, ml_based, etc.
    RISK_LEVEL = "medium"  # low, medium, high
    TIMEFRAMES = ["5m", "15m", "1h"]  # Поддерживаемые таймфреймы
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.last_signal = None
        self.initialized = False
        
    @abstractmethod
    async def analyze(self, df: pd.DataFrame, symbol: str) -> Optional[TradingSignal]:
        """
        Анализирует данные и генерирует сигнал
        
        Args:
            df: DataFrame с OHLCV данными
            symbol: Торговая пара
            
        Returns:
            TradingSignal или None
        """
        pass
    
    def validate_dataframe(self, df: pd.DataFrame) -> bool:
        """Проверка корректности данных"""
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        return all(col in df.columns for col in required_columns)
    
    def get_info(self) -> Dict[str, Any]:
        """Получение информации о стратегии"""
        return {
            'name': self.NAME,
            'description': self.DESCRIPTION,
            'type': self.TYPE,
            'risk_level': self.RISK_LEVEL,
            'timeframes': self.TIMEFRAMES,
            'config': self.config
        }