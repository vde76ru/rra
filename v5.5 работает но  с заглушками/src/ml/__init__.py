"""
ML модули для торгового бота - ПОЛНОСТЬЮ ИСПРАВЛЕННАЯ ВЕРСИЯ
Файл: src/ml/__init__.py
"""

# Безопасный импорт компонентов
try:
    from .strategy_selector import MLStrategySelector
    # Создаем алиас для обратной совместимости
    StrategySelector = MLStrategySelector
except ImportError as e:
    print(f"⚠️ Не удалось импортировать MLStrategySelector: {e}")
    MLStrategySelector = None
    StrategySelector = None

try:
    from .features import FeatureEngineering, FeatureEngineer
except ImportError as e:
    print(f"⚠️ Не удалось импортировать feature engineering: {e}")
    FeatureEngineering = None
    FeatureEngineer = None

try:
    from .models import (
        DirectionClassifier,
        PriceLevelRegressor,
        TradingRLAgent
    )
except ImportError as e:
    print(f"⚠️ Не удалось импортировать ML модели: {e}")
    DirectionClassifier = None
    PriceLevelRegressor = None
    TradingRLAgent = None

# Экспортируем все доступные компоненты
__all__ = [
    'MLStrategySelector',
    'StrategySelector',  # Алиас для обратной совместимости
    'FeatureEngineering',
    'FeatureEngineer',
    'DirectionClassifier',
    'PriceLevelRegressor',
    'TradingRLAgent'
]

# Создаем прямые алиасы на уровне модуля для обратной совместимости
if MLStrategySelector:
    strategy_selector = MLStrategySelector
else:
    strategy_selector = None