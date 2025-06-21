"""
Торговые стратегии
"""

# Безопасный импорт стратегий
try:
    from .base import BaseStrategy, TradingSignal
except ImportError:
    BaseStrategy = None
    TradingSignal = None

try:
    from .multi_indicator import MultiIndicatorStrategy
except ImportError:
    MultiIndicatorStrategy = None

try:
    from .momentum import MomentumStrategy
except ImportError:
    MomentumStrategy = None

try:
    from .mean_reversion import MeanReversionStrategy
except ImportError:
    MeanReversionStrategy = None

try:
    from .scalping import ScalpingStrategy
except ImportError:
    ScalpingStrategy = None

try:
    from .breakout import BreakoutStrategy
except ImportError:
    BreakoutStrategy = None

try:
    from .swing import SwingStrategy
except ImportError:
    SwingStrategy = None

try:
    from .strategy_selector import get_strategy_selector
except ImportError:
    get_strategy_selector = None

__all__ = [
    'BaseStrategy',
    'TradingSignal',
    'MultiIndicatorStrategy',
    'MomentumStrategy',
    'MeanReversionStrategy',
    'ScalpingStrategy',
    'BreakoutStrategy',
    'SwingStrategy',
    'get_strategy_selector'
]