"""
Trainer для обучения и оценки ML моделей
Файл: src/ml/training/trainer.py
"""
import asyncio
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
from sklearn.model_selection import train_test_split, TimeSeriesSplit
from sklearn.metrics import classification_report
import json
from pathlib import Path

from sqlalchemy.orm import Session
from ...core.database import SessionLocal
from ...core.models import Trade, Signal
from ...logging.smart_logger import SmartLogger
from ..features.feature_engineering import FeatureEngineer
from ..models.classifier import DirectionClassifier


class MLTrainer:
    """
    Координатор обучения ML моделей
    """
    
    def __init__(self):
        self.logger = SmartLogger("ml.trainer")
        self.feature_engineer = FeatureEngineer()
        self.models = {}
        
        # Директория для отчетов
        self.reports_dir = Path("reports/ml")
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Параметры обучения
        self.training_config = {
            'min_samples': 1000,  # Минимум образцов для обучения
            'val_split': 0.2,     # Размер валидационной выборки
            'test_split': 0.1,    # Размер тестовой выборки
            'retrain_interval_hours': 24,  # Интервал переобучения
            'model_types': ['xgboost', 'random_forest'],  # Типы моделей для ансамбля
            'symbols': [],  # Заполняется из БД
            'timeframes': ['5m', '15m', '1h']  # Таймфреймы для анализа
        }
        
        # История обучения
        self.training_history = []
    
    async def initialize(self):
        """Инициализация тренера"""
        # Загружаем активные символы из БД
        db = SessionLocal()
        try:
            # Получаем уникальные символы из недавних сделок
            recent_trades = db.query(Trade.symbol).distinct().all()
            self.training_config['symbols'] = [t[0] for t in recent_trades]
            
            if not self.training_config['symbols']:
                # Если нет сделок, используем популярные пары
                self.training_config['symbols'] = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
            
            self.logger.info(
                "ML Trainer инициализирован",
                category='ml',
                symbols=self.training_config['symbols'],
                model_types=self.training_config['model_types']
            )
            
        finally:
            db.close()
    
    async def train_all_models(self):
        """Обучает все модели для всех символов"""
        self.logger.info("Начинаем обучение всех моделей", category='ml')
        
        results = {}
        
        for symbol in self.training_config['symbols']:
            self.logger.info(f"Обучение моделей для {symbol}", category='ml', symbol=symbol)
            
            try:
                # Готовим данные
                X_train, X_val, X_test, y_train, y_val, y_test = await self.prepare_data(symbol)
                
                if X_train is None or len(X_train) < self.training_config['min_samples']:
                    self.logger.warning(
                        f"Недостаточно данных для {symbol}",
                        category='ml',
                        symbol=symbol,
                        samples=len(X_train) if X_train is not None else 0
                    )
                    continue
                
                symbol_results = {}
                
                # Обучаем разные типы моделей
                for model_type in self.training_config['model_types']:
                    model_name = f"{symbol}_{model_type}"
                    
                    # Создаем и обучаем модель
                    model = DirectionClassifier(model_type=model_type, name=model_name)
                    
                    # Обучение
                    metrics = model.train(
                        X_train, y_train,
                        X_val, y_val,
                        optimize_params=True,
                        select_features=True
                    )
                    
                    # Тестирование
                    test_metrics = model.evaluate(X_test, y_test)
                    metrics['test'] = test_metrics
                    
                    # Сохраняем модель
                    self.models[model_name] = model
                    symbol_results[model_type] = metrics
                    
                    # Генерируем отчет
                    await self.generate_model_report(model, X_test, y_test, symbol, model_type)
                
                # Создаем ансамбль
                ensemble_model = await self.create_ensemble(symbol, X_train, y_train, X_val, y_val)
                if ensemble_model:
                    ensemble_metrics = ensemble_model.evaluate(X_test, y_test)
                    symbol_results['ensemble'] = {'test': ensemble_metrics}
                    self.models[f"{symbol}_ensemble"] = ensemble_model
                
                results[symbol] = symbol_results
                
            except Exception as e:
                self.logger.error(
                    f"Ошибка обучения для {symbol}: {e}",
                    category='ml',
                    symbol=symbol,
                    error=str(e)
                )
        
        # Сохраняем историю обучения
        self.training_history.append({
            'timestamp': datetime.utcnow().isoformat(),
            'results': results
        })
        
        # Генерируем общий отчет
        await self.generate_training_report(results)
        
        return results
    
    async def prepare_data(self, symbol: str, 
                          timeframe: str = '5m') -> Tuple[pd.DataFrame, ...]:
        """
        Подготавливает данные для обучения
        
        Returns:
            X_train, X_val, X_test, y_train, y_val, y_test
        """
        self.logger.info(
            f"Подготовка данных для {symbol}",
            category='ml',
            symbol=symbol,
            timeframe=timeframe
        )
        
        # Извлекаем признаки
        df = await self.feature_engineer.extract_features(
            symbol=symbol,
            timeframe=timeframe,
            lookback_periods=2000  # ~1 неделя для 5m
        )
        
        if df.empty:
            return None, None, None, None, None, None
        
        # Подготавливаем обучающие данные
        X, y = self.feature_engineer.prepare_training_data(
            df,
            target_type='direction',
            target_periods=5  # Предсказываем на 5 свечей вперед
        )
        
        if len(X) < self.training_config['min_samples']:
            return None, None, None, None, None, None
        
        # Временное разделение (важно для временных рядов!)
        # Сначала отделяем тестовую выборку
        test_size = int(len(X) * self.training_config['test_split'])
        X_temp, X_test = X[:-test_size], X[-test_size:]
        y_temp, y_test = y[:-test_size], y[-test_size:]
        
        # Затем валидационную
        val_size = int(len(X_temp) * self.training_config['val_split'])
        X_train, X_val = X_temp[:-val_size], X_temp[-val_size:]
        y_train, y_val = y_temp[:-val_size], y_temp[-val_size:]
        
        self.logger.info(
            f"Данные подготовлены для {symbol}",
            category='ml',
            train_size=len(X_train),
            val_size=len(X_val),
            test_size=len(X_test),
            class_distribution=y_train.value_counts().to_dict()
        )
        
        return X_train, X_val, X_test, y_train, y_val, y_test
    
    async def create_ensemble(self, symbol: str, X_train: pd.DataFrame, y_train: pd.Series,
                            X_val: pd.DataFrame, y_val: pd.Series) -> Optional[DirectionClassifier]:
        """
        Создает ансамбль моделей
        """
        self.logger.info(f"Создаем ансамбль для {symbol}", category='ml', symbol=symbol)
        
        # Собираем предсказания от всех моделей
        predictions = []
        weights = []
        
        for model_type in self.training_config['model_types']:
            model_name = f"{symbol}_{model_type}"
            if model_name in self.models:
                model = self.models[model_name]
                
                # Получаем предсказания вероятностей
                val_proba = model.predict_proba(X_val)
                predictions.append(val_proba)
                
                # Вес основан на F1-score
                val_metrics = model.evaluate(X_val, y_val)
                weights.append(val_metrics['f1_score'])
        
        if len(predictions) < 2:
            return None
        
        # Нормализуем веса
        weights = np.array(weights)
        weights = weights / weights.sum()
        
        # Взвешенное усреднение вероятностей
        ensemble_proba = np.zeros_like(predictions[0])
        for i, (pred, weight) in enumerate(zip(predictions, weights)):
            ensemble_proba += pred * weight
        
        # Создаем ensemble модель (обертка)
        class EnsembleModel:
            def __init__(self, models, weights):
                self.models = models
                self.weights = weights
                self.name = f"{symbol}_ensemble"
                self.selected_features = models[0].selected_features
            
            def predict(self, X):
                predictions = []
                for model in self.models:
                    predictions.append(model.predict_proba(X))
                
                ensemble_proba = np.zeros_like(predictions[0])
                for pred, weight in zip(predictions, self.weights):
                    ensemble_proba += pred * weight
                
                return np.argmax(ensemble_proba, axis=1) - 1  # Возвращаем -1, 0, 1
            
            def predict_proba(self, X):
                predictions = []
                for model in self.models:
                    predictions.append(model.predict_proba(X))
                
                ensemble_proba = np.zeros_like(predictions[0])
                for pred, weight in zip(predictions, self.weights):
                    ensemble_proba += pred * weight
                
                return ensemble_proba
            
            def evaluate(self, X, y):
                from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
                
                predictions = self.predict(X)
                return {
                    'accuracy': accuracy_score(y, predictions),
                    'precision': precision_score(y, predictions, average='macro', zero_division=0),
                    'recall': recall_score(y, predictions, average='macro', zero_division=0),
                    'f1_score': f1_score(y, predictions, average='macro', zero_division=0)
                }
        
        # Создаем ансамбль
        ensemble_models = [self.models[f"{symbol}_{mt}"] for mt in self.training_config['model_types'] 
                          if f"{symbol}_{mt}" in self.models]
        
        ensemble = EnsembleModel(ensemble_models, weights)
        
        self.logger.info(
            f"Ансамбль создан для {symbol}",
            category='ml',
            symbol=symbol,
            model_count=len(ensemble_models),
            weights=weights.tolist()
        )
        
        return ensemble
    
    async def predict_direction(self, symbol: str, features: pd.DataFrame,
                              use_ensemble: bool = True) -> Dict[str, Any]:
        """
        Предсказывает направление движения цены
        """
        model_name = f"{symbol}_ensemble" if use_ensemble else f"{symbol}_xgboost"
        
        if model_name not in self.models:
            # Пробуем загрузить модель
            try:
                model = DirectionClassifier(name=model_name)
                model.load_model()
                self.models[model_name] = model
            except:
                self.logger.warning(
                    f"Модель {model_name} не найдена",
                    category='ml',
                    model_name=model_name
                )
                return None
        
        model = self.models[model_name]
        
        # Предсказание
        prediction = model.predict(features)[-1]  # Последнее предсказание
        probabilities = model.predict_proba(features)[-1]
        
        # Интерпретация
        direction_map = {-1: 'DOWN', 0: 'SIDEWAYS', 1: 'UP'}
        
        result = {
            'direction': direction_map[prediction],
            'confidence': float(probabilities.max()),
            'probabilities': {
                'DOWN': float(probabilities[0]),
                'SIDEWAYS': float(probabilities[1]),
                'UP': float(probabilities[2])
            },
            'model': model_name,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Сохраняем предсказание в БД
        await self._save_prediction(symbol, result, features)
        
        return result
    
    async def _save_prediction(self, symbol: str, prediction: Dict, features: pd.DataFrame):
        """Сохраняет предсказание в БД"""
        from ...core.models import Base
        from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
        
        class MLPrediction(Base):
            __tablename__ = "ml_predictions"
            
            id = Column(Integer, primary_key=True, index=True)
            model_id = Column(Integer, nullable=False)
            symbol = Column(String(20), nullable=False)
            prediction_type = Column(String(50), nullable=False)
            prediction_value = Column(JSON, nullable=False)
            confidence = Column(Float, nullable=False)
            features_snapshot = Column(JSON)
            actual_outcome = Column(JSON)
            created_at = Column(DateTime, default=datetime.utcnow)
        
        db = SessionLocal()
        try:
            # Получаем ID модели
            model_name = prediction['model']
            # Здесь нужно получить ID из таблицы ml_models
            
            # Сохраняем топ признаки
            top_features = {}
            if hasattr(self.models[model_name], 'selected_features'):
                selected_features = self.models[model_name].selected_features[:10]
                top_features = features[selected_features].iloc[-1].to_dict()
            
            db_prediction = MLPrediction(
                model_id=1,  # Заглушка, нужно получить реальный ID
                symbol=symbol,
                prediction_type='direction',
                prediction_value=prediction,
                confidence=prediction['confidence'],
                features_snapshot=top_features
            )
            
            db.add(db_prediction)
            db.commit()
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"Ошибка сохранения предсказания: {e}", category='ml')
        finally:
            db.close()
    
    async def evaluate_predictions(self, hours_back: int = 24) -> Dict[str, Any]:
        """Оценивает точность предсказаний за период"""
        db = SessionLocal()
        try:
            # Получаем предсказания за период
            cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
            
            # Здесь нужно сравнить предсказания с реальными движениями цены
            # и обновить actual_outcome в БД
            
            evaluation_results = {
                'period_hours': hours_back,
                'total_predictions': 0,
                'accuracy_by_symbol': {},
                'accuracy_by_confidence': {}
            }
            
            return evaluation_results
            
        finally:
            db.close()
    
    async def generate_model_report(self, model: DirectionClassifier, 
                                  X_test: pd.DataFrame, y_test: pd.Series,
                                  symbol: str, model_type: str):
        """Генерирует детальный отчет по модели"""
        predictions = model.predict(X_test)
        probabilities = model.predict_proba(X_test)
        
        # Classification report
        report = classification_report(
            y_test, predictions,
            target_names=['DOWN', 'SIDEWAYS', 'UP'],
            output_dict=True
        )
        
        # Feature importance
        feature_importance = model.get_feature_importance()
        
        # Confidence analysis
        max_probs = probabilities.max(axis=1)
        confidence_analysis = {
            'mean_confidence': float(max_probs.mean()),
            'confidence_distribution': {
                'low (<0.4)': float((max_probs < 0.4).sum() / len(max_probs)),
                'medium (0.4-0.6)': float(((max_probs >= 0.4) & (max_probs < 0.6)).sum() / len(max_probs)),
                'high (0.6-0.8)': float(((max_probs >= 0.6) & (max_probs < 0.8)).sum() / len(max_probs)),
                'very_high (>0.8)': float((max_probs >= 0.8).sum() / len(max_probs))
            }
        }
        
        # Полный отчет
        full_report = {
            'symbol': symbol,
            'model_type': model_type,
            'timestamp': datetime.utcnow().isoformat(),
            'performance_metrics': model.performance_metrics,
            'classification_report': report,
            'confidence_analysis': confidence_analysis,
            'feature_importance': feature_importance.head(20).to_dict() if not feature_importance.empty else {},
            'model_parameters': model.model_params
        }
        
        # Сохраняем отчет
        report_path = self.reports_dir / f"{symbol}_{model_type}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w') as f:
            json.dump(full_report, f, indent=2)
        
        self.logger.info(
            f"Отчет по модели сохранен: {report_path}",
            category='ml',
            symbol=symbol,
            model_type=model_type
        )
    
    async def generate_training_report(self, results: Dict[str, Any]):
        """Генерирует общий отчет по обучению"""
        summary = {
            'timestamp': datetime.utcnow().isoformat(),
            'symbols_trained': list(results.keys()),
            'overall_performance': {}
        }
        
        # Собираем среднюю производительность
        all_accuracies = []
        all_f1_scores = []
        
        for symbol, symbol_results in results.items():
            for model_type, metrics in symbol_results.items():
                if 'test' in metrics:
                    all_accuracies.append(metrics['test']['accuracy'])
                    all_f1_scores.append(metrics['test']['f1_score'])
        
        if all_accuracies:
            summary['overall_performance'] = {
                'mean_accuracy': float(np.mean(all_accuracies)),
                'mean_f1_score': float(np.mean(all_f1_scores)),
                'best_accuracy': float(max(all_accuracies)),
                'worst_accuracy': float(min(all_accuracies))
            }
        
        # Детальные результаты
        summary['detailed_results'] = results
        
        # Сохраняем отчет
        report_path = self.reports_dir / f"training_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        self.logger.info(
            "Общий отчет по обучению сохранен",
            category='ml',
            report_path=str(report_path),
            overall_performance=summary['overall_performance']
        )
    
    async def auto_retrain_loop(self):
        """Автоматический цикл переобучения"""
        while True:
            try:
                self.logger.info("Запуск автоматического переобучения", category='ml')
                
                # Обучаем все модели
                await self.train_all_models()
                
                # Оцениваем предсказания
                evaluation = await self.evaluate_predictions()
                
                self.logger.info(
                    "Автоматическое переобучение завершено",
                    category='ml',
                    evaluation=evaluation
                )
                
                # Ждем до следующего переобучения
                await asyncio.sleep(self.training_config['retrain_interval_hours'] * 3600)
                
            except Exception as e:
                self.logger.error(
                    f"Ошибка в цикле переобучения: {e}",
                    category='ml',
                    error=str(e)
                )
                await asyncio.sleep(3600)  # Повтор через час при ошибке