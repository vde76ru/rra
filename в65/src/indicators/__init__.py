"""
Модуль технических индикаторов
"""
from .technical_indicators import TechnicalIndicators, indicators
from .ta_wrapper import *

__all__ = ['TechnicalIndicators', 'indicators']

# Экспортируем все функции из ta_wrapper для обратной совместимости
from .ta_wrapper import __all__ as ta_all
__all__.extend(ta_all)
