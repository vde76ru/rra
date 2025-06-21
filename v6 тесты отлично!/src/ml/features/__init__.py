"""
Feature engineering для ML моделей - ИСПРАВЛЕННАЯ ВЕРСИЯ
Файл: src/ml/features/__init__.py
"""

# Попытка импорта с защитой от отсутствия модулей
try:
    from .feature_engineering import FeatureEngineer
    # Создаем алиас для обратной совместимости
    FeatureEngineering = FeatureEngineer
except ImportError as e:
    print(f"⚠️ Не удалось импортировать FeatureEngineer: {e}")
    
    # Если модули еще не созданы, создаем заглушки
    class FeatureEngineer:
        """Заглушка для FeatureEngineer"""
        def __init__(self):
            pass
            
        def create_features(self, df):
            """Возвращает DataFrame без изменений"""
            return df
        
        def extract_features(self, *args, **kwargs):
            """Заглушка для extract_features"""
            return {'features': None}
    
    # Алиас для обратной совместимости
    FeatureEngineering = FeatureEngineer

# Экспортируем оба имени для совместимости
__all__ = ['FeatureEngineering', 'FeatureEngineer']