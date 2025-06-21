"""
ML модели для торгового бота
"""

# Импортируем модели из core
from ...core.models import (
    MLModel,
    MLPrediction,
    TradeMLPrediction,
    TradingLog
)

# Импортируем ML компоненты с проверкой
__all__ = [
    'MLModel',
    'MLPrediction', 
    'TradeMLPrediction',
    'TradingLog'
]

# Условный импорт ML классов
try:
    from .classifier import DirectionClassifier
    __all__.append('DirectionClassifier')
except ImportError:
    DirectionClassifier = None

try:
    from .regressor import PriceLevelRegressor
    __all__.append('PriceLevelRegressor')
except ImportError:
    PriceLevelRegressor = None

try:
    from .reinforcement import TradingRLAgent
    __all__.append('TradingRLAgent')
except ImportError:
    TradingRLAgent = None