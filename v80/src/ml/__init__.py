"""
ML модули для торгового бота - ИСПРАВЛЕННАЯ ВЕРСИЯ
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
    'StrategySelector',  # Алиас
    'FeatureEngineering',
    'FeatureEngineer',
    'DirectionClassifier',
    'PriceLevelRegressor',
    'TradingRLAgent'
]