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

# Импортируем ML компоненты если они существуют
try:
    from .classifier import DirectionClassifier
except ImportError:
    DirectionClassifier = None

try:
    from .regressor import PriceLevelRegressor  
except ImportError:
    PriceLevelRegressor = None

try:
    from .reinforcement import TradingRLAgent
except ImportError:
    TradingRLAgent = None

# Экспортируем все
__all__ = [
    'MLModel',
    'MLPrediction', 
    'TradeMLPrediction',
    'TradingLog',
    'BotState',  # ← Добавить эту строку
    'DirectionClassifier',
    'PriceLevelRegressor',
    'TradingRLAgent'
]
