"""
Редирект для обратной совместимости
Все модели находятся в core.models
"""
from ..core.models import *

# Для явного указания что импортировать
__all__ = [
    'Trade', 'Signal', 'BotState', 'TradingPair',
    'Balance', 'User', 'TradingLog', 'MLModel'
]
