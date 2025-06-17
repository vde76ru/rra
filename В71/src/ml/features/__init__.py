"""
Feature engineering для ML моделей
"""
# Попытка импорта с защитой от отсутствия модулей
try:
    from .feature_engineering import FeatureEngineering, FeatureEngineer
except ImportError:
    # Если модули еще не созданы, создаем заглушки
    class FeatureEngineering:
        """Заглушка для FeatureEngineering"""
        def __init__(self):
            pass
            
        def create_features(self, df):
            """Возвращает DataFrame без изменений"""
            return df
    
    class FeatureEngineer:
        """Заглушка для FeatureEngineer (алиас)"""
        def __init__(self):
            self.fe = FeatureEngineering()
        
        def create_features(self, df):
            return self.fe.create_features(df)

__all__ = ['FeatureEngineering', 'FeatureEngineer']