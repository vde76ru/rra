"""
ML классификатор для предсказания направления движения цены
Файл: src/ml/models/classifier.py
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
import joblib
import json
from datetime import datetime
from pathlib import Path

from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from sklearn.feature_selection import SelectKBest, f_classif, RFE
import xgboost as xgb
import optuna

from sqlalchemy.orm import Session
from ...core.database import SessionLocal
from ...logging.smart_logger import SmartLogger


class DirectionClassifier:
    """
    Классификатор для предсказания направления движения цены
    """
    
    def __init__(self, model_type: str = 'xgboost', name: str = 'direction_classifier'):
        self.model_type = model_type
        self.name = name
        self.model = None
        self.scaler = None
        self.feature_selector = None
        self.selected_features = None
        self.model_params = {}
        self.performance_metrics = {}
        self.logger = SmartLogger(f"ml.{name}")
        
        # Директория для сохранения моделей
        self.models_dir = Path("models") / name
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        # Инициализация модели
        self._initialize_model()
    
    def _initialize_model(self):
        """Инициализирует модель согласно типу"""
        if self.model_type == 'random_forest':
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                min_samples_split=20,
                min_samples_leaf=10,
                random_state=42,
                n_jobs=-1
            )
        
        elif self.model_type == 'xgboost':
            self.model = xgb.XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                objective='multi:softprob',
                use_label_encoder=False,
                random_state=42,
                n_jobs=-1
            )
        
        elif self.model_type == 'gradient_boosting':
            self.model = GradientBoostingClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42
            )
        
        elif self.model_type == 'neural_network':
            self.model = MLPClassifier(
                hidden_layer_sizes=(100, 50, 25),
                activation='relu',
                solver='adam',
                learning_rate_init=0.001,
                max_iter=500,
                random_state=42
            )
        
        # Инициализация препроцессоров
        self.scaler = RobustScaler()  # Более устойчив к выбросам
    
    def optimize_hyperparameters(self, X_train: pd.DataFrame, y_train: pd.Series, 
                               n_trials: int = 50) -> Dict[str, Any]:
        """
        Оптимизация гиперпараметров с помощью Optuna
        """
        self.logger.info(
            f"Начинаем оптимизацию гиперпараметров для {self.model_type}",
            category='ml',
            model_type=self.model_type,
            n_trials=n_trials
        )
        
        def objective(trial):
            # Параметры для разных типов моделей
            if self.model_type == 'xgboost':
                params = {
                    'n_estimators': trial.suggest_int('n_estimators', 50, 300),
                    'max_depth': trial.suggest_int('max_depth', 3, 10),
                    'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
                    'subsample': trial.suggest_float('subsample', 0.6, 1.0),
                    'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
                    'gamma': trial.suggest_float('gamma', 0, 5),
                    'reg_alpha': trial.suggest_float('reg_alpha', 0, 2),
                    'reg_lambda': trial.suggest_float('reg_lambda', 0, 2),
                    'min_child_weight': trial.suggest_int('min_child_weight', 1, 10)
                }
                model = xgb.XGBClassifier(**params, objective='multi:softprob', 
                                        use_label_encoder=False, random_state=42)
            
            elif self.model_type == 'random_forest':
                params = {
                    'n_estimators': trial.suggest_int('n_estimators', 50, 300),
                    'max_depth': trial.suggest_int('max_depth', 5, 30),
                    'min_samples_split': trial.suggest_int('min_samples_split', 2, 50),
                    'min_samples_leaf': trial.suggest_int('min_samples_leaf', 1, 20),
                    'max_features': trial.suggest_categorical('max_features', ['sqrt', 'log2', None])
                }
                model = RandomForestClassifier(**params, random_state=42, n_jobs=-1)
            
            elif self.model_type == 'neural_network':
                n_layers = trial.suggest_int('n_layers', 1, 4)
                layers = []
                for i in range(n_layers):
                    layers.append(trial.suggest_int(f'n_units_{i}', 10, 200))
                
                params = {
                    'hidden_layer_sizes': tuple(layers),
                    'learning_rate_init': trial.suggest_float('learning_rate_init', 0.0001, 0.1, log=True),
                    'alpha': trial.suggest_float('alpha', 0.0001, 0.1, log=True),
                    'batch_size': trial.suggest_categorical('batch_size', ['auto', 32, 64, 128])
                }
                model = MLPClassifier(**params, activation='relu', solver='adam', 
                                    max_iter=500, random_state=42)
            
            # Cross-validation
            cv_scores = cross_val_score(
                model, X_train, y_train, 
                cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=42),
                scoring='f1_macro'
            )
            
            return cv_scores.mean()
        
        # Запуск оптимизации
        study = optuna.create_study(direction='maximize')
        study.optimize(objective, n_trials=n_trials, n_jobs=1)
        
        # Сохраняем лучшие параметры
        self.model_params = study.best_params
        
        self.logger.info(
            f"Оптимизация завершена. Лучший score: {study.best_value:.4f}",
            category='ml',
            best_params=self.model_params,
            best_score=study.best_value
        )
        
        return self.model_params
    
    def select_features(self, X: pd.DataFrame, y: pd.Series, 
                       method: str = 'mutual_info', k: int = 50) -> List[str]:
        """
        Выбор наиболее важных признаков
        """
        self.logger.info(
            f"Выбор {k} лучших признаков методом {method}",
            category='ml',
            total_features=len(X.columns),
            method=method
        )
        
        if method == 'mutual_info':
            # Mutual Information
            selector = SelectKBest(score_func=f_classif, k=min(k, len(X.columns)))
            selector.fit(X, y)
            
            # Получаем индексы лучших признаков
            feature_scores = pd.DataFrame({
                'feature': X.columns,
                'score': selector.scores_
            }).sort_values('score', ascending=False)
            
            self.selected_features = feature_scores.head(k)['feature'].tolist()
            self.feature_selector = selector
        
        elif method == 'rfe':
            # Recursive Feature Elimination
            if self.model_type in ['random_forest', 'xgboost']:
                estimator = self.model
            else:
                estimator = RandomForestClassifier(n_estimators=50, random_state=42)
            
            selector = RFE(estimator, n_features_to_select=k, step=5)
            selector.fit(X, y)
            
            self.selected_features = X.columns[selector.support_].tolist()
            self.feature_selector = selector
        
        elif method == 'importance':
            # Feature importance из модели
            if hasattr(self.model, 'feature_importances_'):
                importances = pd.DataFrame({
                    'feature': X.columns,
                    'importance': self.model.feature_importances_
                }).sort_values('importance', ascending=False)
                
                self.selected_features = importances.head(k)['feature'].tolist()
            else:
                # Fallback на mutual info
                return self.select_features(X, y, method='mutual_info', k=k)
        
        self.logger.info(
            f"Выбрано {len(self.selected_features)} признаков",
            category='ml',
            selected_features=self.selected_features[:10]  # Топ-10 для логов
        )
        
        return self.selected_features
    
    def train(self, X_train: pd.DataFrame, y_train: pd.Series,
              X_val: Optional[pd.DataFrame] = None, y_val: Optional[pd.Series] = None,
              optimize_params: bool = True, select_features: bool = True) -> Dict[str, float]:
        """
        Обучение модели
        """
        self.logger.info(
            f"Начинаем обучение модели {self.name}",
            category='ml',
            model_type=self.model_type,
            train_size=len(X_train),
            val_size=len(X_val) if X_val is not None else 0
        )
        
        # Оптимизация гиперпараметров
        if optimize_params:
            self.optimize_hyperparameters(X_train, y_train)
            self._initialize_model()  # Переинициализация с новыми параметрами
            
            # Применяем оптимальные параметры
            if self.model_type == 'xgboost':
                self.model = xgb.XGBClassifier(
                    **self.model_params,
                    objective='multi:softprob',
                    use_label_encoder=False,
                    random_state=42
                )
            elif self.model_type == 'random_forest':
                self.model = RandomForestClassifier(**self.model_params, random_state=42, n_jobs=-1)
            elif self.model_type == 'neural_network':
                self.model = MLPClassifier(**self.model_params, activation='relu', 
                                         solver='adam', max_iter=500, random_state=42)
        
        # Выбор признаков
        if select_features:
            self.select_features(X_train, y_train)
            X_train = X_train[self.selected_features]
            if X_val is not None:
                X_val = X_val[self.selected_features]
        
        # Масштабирование
        X_train_scaled = self.scaler.fit_transform(X_train)
        if X_val is not None:
            X_val_scaled = self.scaler.transform(X_val)
        
        # Обучение
        with self.logger.timer("model_training", category="ml"):
            if self.model_type == 'xgboost' and X_val is not None:
                # XGBoost с early stopping
                self.model.fit(
                    X_train_scaled, y_train,
                    eval_set=[(X_val_scaled, y_val)],
                    early_stopping_rounds=20,
                    verbose=False
                )
            else:
                self.model.fit(X_train_scaled, y_train)
        
        # Оценка производительности
        train_metrics = self.evaluate(X_train, y_train)
        self.performance_metrics['train'] = train_metrics
        
        if X_val is not None:
            val_metrics = self.evaluate(X_val, y_val)
            self.performance_metrics['validation'] = val_metrics
            
            self.logger.info(
                f"Обучение завершено. Val accuracy: {val_metrics['accuracy']:.4f}",
                category='ml',
                train_metrics=train_metrics,
                val_metrics=val_metrics
            )
        else:
            self.logger.info(
                f"Обучение завершено. Train accuracy: {train_metrics['accuracy']:.4f}",
                category='ml',
                train_metrics=train_metrics
            )
        
        # Сохраняем модель
        self.save_model()
        
        return self.performance_metrics
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Предсказание классов"""
        if self.model is None:
            raise ValueError("Модель не обучена")
        
        # Применяем выбор признаков
        if self.selected_features:
            X = X[self.selected_features]
        
        # Масштабирование
        X_scaled = self.scaler.transform(X)
        
        # Предсказание
        predictions = self.model.predict(X_scaled)
        
        return predictions
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Предсказание вероятностей классов"""
        if self.model is None:
            raise ValueError("Модель не обучена")
        
        # Применяем выбор признаков
        if self.selected_features:
            X = X[self.selected_features]
        
        # Масштабирование
        X_scaled = self.scaler.transform(X)
        
        # Предсказание вероятностей
        probabilities = self.model.predict_proba(X_scaled)
        
        return probabilities
    
    def evaluate(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, float]:
        """Оценка модели"""
        predictions = self.predict(X)
        
        # Базовые метрики
        metrics = {
            'accuracy': accuracy_score(y, predictions),
            'precision': precision_score(y, predictions, average='macro', zero_division=0),
            'recall': recall_score(y, predictions, average='macro', zero_division=0),
            'f1_score': f1_score(y, predictions, average='macro', zero_division=0)
        }
        
        # Метрики по классам
        if len(np.unique(y)) == 3:  # UP, DOWN, SIDEWAYS
            class_names = ['DOWN', 'SIDEWAYS', 'UP']
            for i, class_name in enumerate(class_names):
                class_mask = y == (i - 1)  # -1, 0, 1
                if class_mask.sum() > 0:
                    metrics[f'precision_{class_name}'] = precision_score(
                        y == (i - 1), predictions == (i - 1), zero_division=0
                    )
                    metrics[f'recall_{class_name}'] = recall_score(
                        y == (i - 1), predictions == (i - 1), zero_division=0
                    )
        
        return metrics
    
    def get_feature_importance(self) -> pd.DataFrame:
        """Получает важность признаков"""
        if hasattr(self.model, 'feature_importances_'):
            importances = pd.DataFrame({
                'feature': self.selected_features if self.selected_features else [],
                'importance': self.model.feature_importances_
            }).sort_values('importance', ascending=False)
            
            return importances
        else:
            return pd.DataFrame()
    
    def save_model(self, version: Optional[str] = None):
        """Сохраняет модель и метаданные"""
        if version is None:
            version = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        model_path = self.models_dir / f"model_{version}.pkl"
        scaler_path = self.models_dir / f"scaler_{version}.pkl"
        metadata_path = self.models_dir / f"metadata_{version}.json"
        
        # Сохраняем модель и препроцессоры
        joblib.dump(self.model, model_path)
        joblib.dump(self.scaler, scaler_path)
        if self.feature_selector:
            selector_path = self.models_dir / f"selector_{version}.pkl"
            joblib.dump(self.feature_selector, selector_path)
        
        # Сохраняем метаданные
        metadata = {
            'name': self.name,
            'model_type': self.model_type,
            'version': version,
            'created_at': datetime.now().isoformat(),
            'model_params': self.model_params,
            'selected_features': self.selected_features,
            'performance_metrics': self.performance_metrics,
            'feature_importance': self.get_feature_importance().to_dict() if hasattr(self.model, 'feature_importances_') else {}
        }
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Сохраняем в БД
        self._save_to_database(version, metadata)
        
        self.logger.info(
            f"Модель сохранена: {model_path}",
            category='ml',
            version=version,
            metrics=self.performance_metrics
        )
    
    def load_model(self, version: Optional[str] = None):
        """Загружает модель"""
        if version is None:
            # Загружаем последнюю версию
            model_files = list(self.models_dir.glob("model_*.pkl"))
            if not model_files:
                raise ValueError("Нет сохраненных моделей")
            
            latest_model = max(model_files, key=lambda x: x.stat().st_mtime)
            version = latest_model.stem.replace('model_', '')
        
        model_path = self.models_dir / f"model_{version}.pkl"
        scaler_path = self.models_dir / f"scaler_{version}.pkl"
        metadata_path = self.models_dir / f"metadata_{version}.json"
        
        # Загружаем модель и препроцессоры
        self.model = joblib.load(model_path)
        self.scaler = joblib.load(scaler_path)
        
        selector_path = self.models_dir / f"selector_{version}.pkl"
        if selector_path.exists():
            self.feature_selector = joblib.load(selector_path)
        
        # Загружаем метаданные
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        self.model_params = metadata.get('model_params', {})
        self.selected_features = metadata.get('selected_features', [])
        self.performance_metrics = metadata.get('performance_metrics', {})
        
        self.logger.info(
            f"Модель загружена: версия {version}",
            category='ml',
            version=version,
            metrics=self.performance_metrics
        )
    
    def _save_to_database(self, version: str, metadata: Dict):
        """Сохраняет информацию о модели в БД"""
        from ...core.models import Base
        from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Boolean
        
        # Модель для БД (если еще не создана)
        class MLModel(Base):
            __tablename__ = "ml_models"
            
            id = Column(Integer, primary_key=True, index=True)
            name = Column(String(100), nullable=False)
            model_type = Column(String(50), nullable=False)
            version = Column(String(50), nullable=False)
            accuracy = Column(Float)
            precision_score = Column(Float)
            recall_score = Column(Float)
            f1_score = Column(Float)
            created_at = Column(DateTime, default=datetime.utcnow)
            updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
            parameters = Column(JSON)
            feature_importance = Column(JSON)
            training_history = Column(JSON)
            is_active = Column(Boolean, default=True)
        
        db = SessionLocal()
        try:
            # Деактивируем предыдущие версии
            db.query(MLModel).filter(
                MLModel.name == self.name,
                MLModel.is_active == True
            ).update({'is_active': False})
            
            # Создаем новую запись
            val_metrics = metadata['performance_metrics'].get('validation', 
                                                             metadata['performance_metrics'].get('train', {}))
            
            db_model = MLModel(
                name=self.name,
                model_type=self.model_type,
                version=version,
                accuracy=val_metrics.get('accuracy'),
                precision_score=val_metrics.get('precision'),
                recall_score=val_metrics.get('recall'),
                f1_score=val_metrics.get('f1_score'),
                parameters=self.model_params,
                feature_importance=metadata.get('feature_importance', {}),
                training_history=self.performance_metrics,
                is_active=True
            )
            
            db.add(db_model)
            db.commit()
            
        except Exception as e:
            db.rollback()
            self.logger.error(
                f"Ошибка сохранения модели в БД: {e}",
                category='ml',
                error=str(e)
            )
        finally:
            db.close()