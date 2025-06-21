#!/usr/bin/env python3
"""
SIGNAL PROCESSOR - Центральный обработчик торговых сигналов
Файл: src/bot/signal_processor.py

🎯 ФУНКЦИИ:
✅ Валидация входящих торговых сигналов
✅ Фильтрация слабых и противоречивых сигналов  
✅ Агрегация сигналов от нескольких стратегий
✅ Приоритизация сигналов по качеству
✅ Интеграция с риск-менеджментом
"""

import asyncio
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import logging

from ..strategies.base import TradingSignal
from ..core.database import SessionLocal
from ..core.models import Signal, SignalType, Trade
from ..core.config import config

logger = logging.getLogger(__name__)

class SignalQuality(Enum):
    """Качество торгового сигнала"""
    EXCELLENT = "excellent"    # >0.8 уверенности
    GOOD = "good"             # 0.6-0.8 уверенности
    AVERAGE = "average"       # 0.4-0.6 уверенности
    POOR = "poor"             # 0.2-0.4 уверенности
    INVALID = "invalid"       # <0.2 уверенности

class SignalStatus(Enum):
    """Статус обработки сигнала"""
    PENDING = "pending"
    VALIDATED = "validated"
    FILTERED = "filtered"
    AGGREGATED = "aggregated"
    PROCESSED = "processed"
    REJECTED = "rejected"

@dataclass
class ProcessedSignal:
    """Обработанный торговый сигнал"""
    original_signal: TradingSignal
    strategy_name: str
    symbol: str
    quality: SignalQuality
    confidence_adjusted: float     # Скорректированная уверенность
    priority: int                  # Приоритет 1-10 (10 - наивысший)
    risk_score: float             # Оценка риска 0-1
    timestamp: datetime
    validation_results: Dict[str, Any] = field(default_factory=dict)
    status: SignalStatus = SignalStatus.PENDING

@dataclass 
class AggregatedSignal:
    """Агрегированный сигнал от нескольких стратегий"""
    symbol: str
    action: str                   # BUY, SELL, WAIT
    confidence: float            # Консенсус уверенности
    strategies_count: int        # Количество стратегий
    strategy_names: List[str]    # Имена стратегий
    individual_signals: List[ProcessedSignal]
    consensus_strength: float    # Сила консенсуса 0-1
    conflicting_signals: int     # Количество противоречивых
    avg_stop_loss: float
    avg_take_profit: float
    recommended_position_size: float
    timestamp: datetime

class SignalProcessor:
    """
    Центральный процессор торговых сигналов
    
    🧠 ОБРАБОТКА СИГНАЛОВ:
    
    ┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
    │   ВХОДЯЩИЕ      │───▶│   ВАЛИДАЦИЯ      │───▶│   ФИЛЬТРАЦИЯ    │
    │   СИГНАЛЫ       │    │   - Качество     │    │   - Дубликаты   │
    │   - Стратегии   │    │   - Полнота      │    │   - Слабые       │
    │   - ML модели   │    │   - Логичность   │    │   - Устаревшие   │
    └─────────────────┘    └──────────────────┘    └─────────────────┘
             │                        │                        │
             ▼                        ▼                        ▼
    ┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
    │   АГРЕГАЦИЯ     │    │   ПРИОРИТИЗАЦИЯ  │    │   ИСПОЛНЕНИЕ    │
    │   - Консенсус   │    │   - Качество     │    │   - Лучшие      │
    │   - Противоречия│    │   - Срочность    │    │   - Вовремя     │
    │   - Веса        │    │   - Риски        │    │   - Корректно   │
    └─────────────────┘    └──────────────────┘    └─────────────────┘
    """
    
    def __init__(self, max_signal_age_minutes: int = 5):
        """
        Инициализация процессора сигналов
        
        Args:
            max_signal_age_minutes: Максимальный возраст сигнала в минутах
        """
        self.max_signal_age = timedelta(minutes=max_signal_age_minutes)
        self.processed_signals = deque(maxlen=1000)
        self.signal_cache = {}
        self.last_signals_by_strategy = defaultdict(lambda: None)
        
        # Настройки фильтрации
        self.min_confidence = config.MIN_STRATEGY_CONFIDENCE
        self.consensus_threshold = 0.6  # Минимальный консенсус для агрегации
        self.max_conflicting_ratio = 0.3  # Максимум противоречий
        
        # Веса стратегий
        self.strategy_weights = {
            'multi_indicator': config.WEIGHT_MULTI_INDICATOR,
            'momentum': config.WEIGHT_MOMENTUM,
            'mean_reversion': config.WEIGHT_MEAN_REVERSION,
            'breakout': config.WEIGHT_BREAKOUT,
            'scalping': config.WEIGHT_SCALPING,
            'swing': config.WEIGHT_SWING,
            'ml_prediction': config.WEIGHT_ML_PREDICTION
        }
        
        logger.info("✅ SignalProcessor инициализирован")
    
    async def process_signal(self, signal: TradingSignal, strategy_name: str,
                           symbol: str) -> Optional[ProcessedSignal]:
        """
        Основная функция обработки одиночного сигнала
        
        Args:
            signal: Торговый сигнал от стратегии
            strategy_name: Имя стратегии
            symbol: Торговая пара
            
        Returns:
            ProcessedSignal или None если сигнал отклонен
        """
        try:
            logger.debug(
                f"🔄 Обработка сигнала {strategy_name}: {signal.action} "
                f"для {symbol} (confidence: {signal.confidence:.2f})"
            )
            
            # Шаг 1: Валидация сигнала
            validation_results = await self._validate_signal(signal, strategy_name, symbol)
            if not validation_results['is_valid']:
                logger.debug(f"❌ Сигнал отклонен: {validation_results['reason']}")
                return None
            
            # Шаг 2: Определение качества
            quality = self._determine_signal_quality(signal, validation_results)
            
            # Шаг 3: Корректировка уверенности
            adjusted_confidence = self._adjust_confidence(
                signal, strategy_name, validation_results
            )
            
            # Шаг 4: Расчет приоритета
            priority = self._calculate_priority(signal, strategy_name, quality)
            
            # Шаг 5: Оценка риска
            risk_score = await self._assess_risk(signal, symbol)
            
            # Создаем обработанный сигнал
            processed = ProcessedSignal(
                original_signal=signal,
                strategy_name=strategy_name,
                symbol=symbol,
                quality=quality,
                confidence_adjusted=adjusted_confidence,
                priority=priority,
                risk_score=risk_score,
                timestamp=datetime.utcnow(),
                validation_results=validation_results,
                status=SignalStatus.VALIDATED
            )
            
            # Сохраняем в кеше
            self._cache_signal(processed)
            
            logger.info(
                f"✅ Сигнал обработан: {strategy_name} → {signal.action} "
                f"(quality: {quality.value}, priority: {priority})"
            )
            
            return processed
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки сигнала: {e}")
            return None
    
    async def aggregate_signals(self, signals: List[ProcessedSignal],
                              symbol: str) -> Optional[AggregatedSignal]:
        """
        Агрегация нескольких сигналов в один консенсусный
        
        Args:
            signals: Список обработанных сигналов
            symbol: Торговая пара
            
        Returns:
            AggregatedSignal или None если консенсус не достигнут
        """
        try:
            if not signals:
                return None
            
            logger.debug(f"🔄 Агрегация {len(signals)} сигналов для {symbol}")
            
            # Фильтруем свежие и качественные сигналы
            valid_signals = self._filter_signals_for_aggregation(signals)
            if len(valid_signals) < 2:
                return None
            
            # Группируем по действиям
            actions_groups = self._group_signals_by_action(valid_signals)
            
            # Находим консенсус
            consensus_action, consensus_signals = self._find_consensus(actions_groups)
            if not consensus_action:
                return None
            
            # Рассчитываем агрегированные параметры
            agg_params = self._calculate_aggregated_parameters(consensus_signals)
            
            # Оцениваем силу консенсуса
            consensus_strength = self._calculate_consensus_strength(
                consensus_signals, valid_signals
            )
            
            aggregated = AggregatedSignal(
                symbol=symbol,
                action=consensus_action,
                confidence=agg_params['confidence'],
                strategies_count=len(consensus_signals),
                strategy_names=[s.strategy_name for s in consensus_signals],
                individual_signals=consensus_signals,
                consensus_strength=consensus_strength,
                conflicting_signals=len(valid_signals) - len(consensus_signals),
                avg_stop_loss=agg_params['stop_loss'],
                avg_take_profit=agg_params['take_profit'],
                recommended_position_size=agg_params['position_size'],
                timestamp=datetime.utcnow()
            )
            
            logger.info(
                f"✅ Агрегированный сигнал: {consensus_action} для {symbol} "
                f"(консенсус: {consensus_strength:.2f}, стратегий: {len(consensus_signals)})"
            )
            
            return aggregated
            
        except Exception as e:
            logger.error(f"❌ Ошибка агрегации сигналов: {e}")
            return None
    
    async def _validate_signal(self, signal: TradingSignal, strategy_name: str,
                             symbol: str) -> Dict[str, Any]:
        """Валидация торгового сигнала"""
        validation = {
            'is_valid': True,
            'reason': '',
            'checks': {}
        }
        
        try:
            # Проверка базовых параметров
            if not signal.action or signal.action not in ['BUY', 'SELL', 'WAIT']:
                validation['is_valid'] = False
                validation['reason'] = 'Некорректное действие'
                return validation
            
            # Проверка уверенности
            if not (0 <= signal.confidence <= 1):
                validation['is_valid'] = False
                validation['reason'] = 'Некорректная уверенность'
                return validation
                
            validation['checks']['confidence'] = True
            
            # Проверка минимальной уверенности
            if signal.confidence < self.min_confidence:
                validation['is_valid'] = False
                validation['reason'] = f'Низкая уверенность: {signal.confidence:.2f}'
                return validation
                
            validation['checks']['min_confidence'] = True
            
            # Проверка актуальности (если есть timestamp)
            if hasattr(signal, 'timestamp') and signal.timestamp:
                age = datetime.utcnow() - signal.timestamp
                if age > self.max_signal_age:
                    validation['is_valid'] = False
                    validation['reason'] = f'Устаревший сигнал: {age}'
                    return validation
                    
            validation['checks']['freshness'] = True
            
            # Проверка дублирования
            if self._is_duplicate_signal(signal, strategy_name, symbol):
                validation['is_valid'] = False
                validation['reason'] = 'Дублирующий сигнал'
                return validation
                
            validation['checks']['uniqueness'] = True
            
            # Проверка корректности цен
            if signal.action != 'WAIT':
                if signal.stop_loss and signal.stop_loss <= 0:
                    validation['is_valid'] = False
                    validation['reason'] = 'Некорректный stop-loss'
                    return validation
                    
                if signal.take_profit and signal.take_profit <= 0:
                    validation['is_valid'] = False
                    validation['reason'] = 'Некорректный take-profit'
                    return validation
                    
            validation['checks']['price_levels'] = True
            
            return validation
            
        except Exception as e:
            logger.error(f"❌ Ошибка валидации сигнала: {e}")
            validation['is_valid'] = False
            validation['reason'] = f'Ошибка валидации: {e}'
            return validation
    
    def _determine_signal_quality(self, signal: TradingSignal,
                                validation_results: Dict[str, Any]) -> SignalQuality:
        """Определение качества сигнала"""
        try:
            confidence = signal.confidence
            
            # Учитываем результаты валидации
            quality_score = confidence
            
            # Бонус за полноту информации
            if signal.stop_loss and signal.take_profit:
                quality_score += 0.1
                
            if hasattr(signal, 'reason') and signal.reason:
                quality_score += 0.05
            
            # Штраф за проблемы валидации
            failed_checks = sum(
                1 for check, result in validation_results.get('checks', {}).items()
                if not result
            )
            quality_score -= failed_checks * 0.1
            
            # Определяем категорию качества
            if quality_score >= 0.8:
                return SignalQuality.EXCELLENT
            elif quality_score >= 0.6:
                return SignalQuality.GOOD
            elif quality_score >= 0.4:
                return SignalQuality.AVERAGE
            elif quality_score >= 0.2:
                return SignalQuality.POOR
            else:
                return SignalQuality.INVALID
                
        except Exception as e:
            logger.error(f"❌ Ошибка определения качества сигнала: {e}")
            return SignalQuality.POOR
    
    def _adjust_confidence(self, signal: TradingSignal, strategy_name: str,
                         validation_results: Dict[str, Any]) -> float:
        """Корректировка уверенности с учетом дополнительных факторов"""
        try:
            adjusted = signal.confidence
            
            # Корректировка по весу стратегии
            strategy_weight = self.strategy_weights.get(strategy_name, 1.0)
            adjusted *= strategy_weight
            
            # Корректировка по результатам валидации
            checks_passed = len([
                check for check, result in validation_results.get('checks', {}).items()
                if result
            ])
            total_checks = len(validation_results.get('checks', {}))
            
            if total_checks > 0:
                validation_factor = checks_passed / total_checks
                adjusted *= validation_factor
            
            # Ограничиваем диапазон
            return max(0.0, min(1.0, adjusted))
            
        except Exception as e:
            logger.error(f"❌ Ошибка корректировки уверенности: {e}")
            return signal.confidence
    
    def _calculate_priority(self, signal: TradingSignal, strategy_name: str,
                          quality: SignalQuality) -> int:
        """Расчет приоритета сигнала (1-10)"""
        try:
            # Базовый приоритет по качеству
            quality_priority = {
                SignalQuality.EXCELLENT: 9,
                SignalQuality.GOOD: 7,
                SignalQuality.AVERAGE: 5,
                SignalQuality.POOR: 3,
                SignalQuality.INVALID: 1
            }
            
            priority = quality_priority.get(quality, 5)
            
            # Модификация по типу действия
            if signal.action in ['BUY', 'SELL']:
                priority += 1  # Торговые сигналы важнее
            
            # Модификация по стратегии
            strategy_priority = {
                'multi_indicator': 1,
                'momentum': 1,
                'ml_prediction': 2,  # ML сигналы важнее
                'scalping': -1  # Скальпинг менее важен
            }
            
            priority += strategy_priority.get(strategy_name, 0)
            
            # Ограничиваем диапазон
            return max(1, min(10, priority))
            
        except Exception as e:
            logger.error(f"❌ Ошибка расчета приоритета: {e}")
            return 5
    
    async def _assess_risk(self, signal: TradingSignal, symbol: str) -> float:
        """Оценка риска сигнала (0-1, где 1 - максимальный риск)"""
        try:
            risk_score = 0.0
            
            # Базовый риск по типу действия
            if signal.action == 'WAIT':
                risk_score = 0.1
            else:
                risk_score = 0.5
            
            # Риск по отсутствию stop-loss
            if signal.action in ['BUY', 'SELL'] and not signal.stop_loss:
                risk_score += 0.3
            
            # Риск по соотношению stop/profit
            if signal.stop_loss and signal.take_profit:
                risk_reward = abs(signal.take_profit - signal.stop_loss) / abs(signal.stop_loss)
                if risk_reward < 1.5:  # Плохое соотношение риск/прибыль
                    risk_score += 0.2
            
            return min(1.0, risk_score)
            
        except Exception as e:
            logger.error(f"❌ Ошибка оценки риска: {e}")
            return 0.5
    
    def _cache_signal(self, signal: ProcessedSignal):
        """Кеширование обработанного сигнала"""
        try:
            # Сохраняем последний сигнал стратегии
            key = f"{signal.strategy_name}_{signal.symbol}"
            self.last_signals_by_strategy[key] = signal
            
            # Добавляем в общий кеш
            self.processed_signals.append(signal)
            
        except Exception as e:
            logger.error(f"❌ Ошибка кеширования сигнала: {e}")
    
    def _is_duplicate_signal(self, signal: TradingSignal, strategy_name: str,
                           symbol: str) -> bool:
        """Проверка на дублирование сигнала"""
        try:
            key = f"{strategy_name}_{symbol}"
            last_signal = self.last_signals_by_strategy.get(key)
            
            if not last_signal:
                return False
            
            # Проверяем временной интервал
            time_diff = datetime.utcnow() - last_signal.timestamp
            if time_diff < timedelta(minutes=1):  # Слишком частые сигналы
                # Проверяем идентичность
                if (last_signal.original_signal.action == signal.action and
                    abs(last_signal.original_signal.confidence - signal.confidence) < 0.1):
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки дублирования: {e}")
            return False
    
    def _filter_signals_for_aggregation(self, signals: List[ProcessedSignal]) -> List[ProcessedSignal]:
        """Фильтрация сигналов для агрегации"""
        try:
            valid = []
            
            for signal in signals:
                # Проверяем свежесть
                age = datetime.utcnow() - signal.timestamp
                if age > self.max_signal_age:
                    continue
                
                # Проверяем качество
                if signal.quality in [SignalQuality.INVALID, SignalQuality.POOR]:
                    continue
                
                # Проверяем не WAIT сигналы
                if signal.original_signal.action == 'WAIT':
                    continue
                
                valid.append(signal)
            
            return valid
            
        except Exception as e:
            logger.error(f"❌ Ошибка фильтрации сигналов: {e}")
            return signals
    
    def _group_signals_by_action(self, signals: List[ProcessedSignal]) -> Dict[str, List[ProcessedSignal]]:
        """Группировка сигналов по действиям"""
        groups = defaultdict(list)
        
        for signal in signals:
            action = signal.original_signal.action
            groups[action].append(signal)
        
        return dict(groups)
    
    def _find_consensus(self, actions_groups: Dict[str, List[ProcessedSignal]]) -> Tuple[Optional[str], List[ProcessedSignal]]:
        """Поиск консенсуса среди сигналов"""
        try:
            if not actions_groups:
                return None, []
            
            # Находим действие с наибольшим количеством сигналов
            best_action = max(actions_groups.keys(), key=lambda x: len(actions_groups[x]))
            best_signals = actions_groups[best_action]
            
            # Проверяем силу консенсуса
            total_signals = sum(len(signals) for signals in actions_groups.values())
            consensus_ratio = len(best_signals) / total_signals
            
            if consensus_ratio >= self.consensus_threshold:
                return best_action, best_signals
            else:
                return None, []
                
        except Exception as e:
            logger.error(f"❌ Ошибка поиска консенсуса: {e}")
            return None, []
    
    def _calculate_aggregated_parameters(self, signals: List[ProcessedSignal]) -> Dict[str, float]:
        """Расчет агрегированных параметров"""
        try:
            if not signals:
                return {
                    'confidence': 0.0,
                    'stop_loss': 0.0,
                    'take_profit': 0.0,
                    'position_size': 0.0
                }
            
            # Взвешенные параметры по уверенности
            total_weight = sum(s.confidence_adjusted for s in signals)
            
            if total_weight == 0:
                weights = [1/len(signals)] * len(signals)
            else:
                weights = [s.confidence_adjusted / total_weight for s in signals]
            
            # Агрегированная уверенность
            avg_confidence = sum(
                s.confidence_adjusted * w for s, w in zip(signals, weights)
            )
            
            # Агрегированные уровни (только если есть)
            stop_losses = [s.original_signal.stop_loss for s in signals if s.original_signal.stop_loss]
            take_profits = [s.original_signal.take_profit for s in signals if s.original_signal.take_profit]
            
            avg_stop_loss = np.mean(stop_losses) if stop_losses else 0.0
            avg_take_profit = np.mean(take_profits) if take_profits else 0.0
            
            # Рекомендуемый размер позиции (базовый расчет)
            position_size = avg_confidence * 0.1  # 10% максимум
            
            return {
                'confidence': avg_confidence,
                'stop_loss': avg_stop_loss,
                'take_profit': avg_take_profit,
                'position_size': position_size
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка расчета агрегированных параметров: {e}")
            return {
                'confidence': 0.5,
                'stop_loss': 0.0,
                'take_profit': 0.0,
                'position_size': 0.05
            }
    
    def _calculate_consensus_strength(self, consensus_signals: List[ProcessedSignal],
                                    all_signals: List[ProcessedSignal]) -> float:
        """Расчет силы консенсуса"""
        try:
            if not all_signals:
                return 0.0
            
            consensus_ratio = len(consensus_signals) / len(all_signals)
            
            # Взвешиваем по качеству сигналов
            consensus_quality = np.mean([
                s.confidence_adjusted for s in consensus_signals
            ])
            
            return consensus_ratio * consensus_quality
            
        except Exception as e:
            logger.error(f"❌ Ошибка расчета силы консенсуса: {e}")
            return 0.5
    
    def get_recent_signals(self, symbol: Optional[str] = None,
                         strategy: Optional[str] = None,
                         limit: int = 10) -> List[ProcessedSignal]:
        """Получение недавних обработанных сигналов"""
        try:
            signals = list(self.processed_signals)
            
            # Фильтрация по символу
            if symbol:
                signals = [s for s in signals if s.symbol == symbol]
            
            # Фильтрация по стратегии
            if strategy:
                signals = [s for s in signals if s.strategy_name == strategy]
            
            # Сортировка по времени (новые первые)
            signals.sort(key=lambda x: x.timestamp, reverse=True)
            
            return signals[:limit]
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения недавних сигналов: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики обработки сигналов"""
        try:
            total_signals = len(self.processed_signals)
            
            if total_signals == 0:
                return {
                    'total_processed': 0,
                    'quality_distribution': {},
                    'strategy_distribution': {},
                    'avg_confidence': 0.0
                }
            
            # Распределение по качеству
            quality_dist = defaultdict(int)
            for signal in self.processed_signals:
                quality_dist[signal.quality.value] += 1
            
            # Распределение по стратегиям
            strategy_dist = defaultdict(int)
            for signal in self.processed_signals:
                strategy_dist[signal.strategy_name] += 1
            
            # Средняя уверенность
            avg_confidence = np.mean([
                s.confidence_adjusted for s in self.processed_signals
            ])
            
            return {
                'total_processed': total_signals,
                'quality_distribution': dict(quality_dist),
                'strategy_distribution': dict(strategy_dist),
                'avg_confidence': avg_confidence
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики: {e}")
            return {}

# =================================================================
# ГЛОБАЛЬНЫЕ ФУНКЦИИ
# =================================================================

# Глобальный экземпляр
signal_processor = None

def get_signal_processor() -> SignalProcessor:
    """Получить глобальный экземпляр процессора сигналов"""
    global signal_processor
    
    if signal_processor is None:
        signal_processor = SignalProcessor()
    
    return signal_processor

def create_signal_processor(**kwargs) -> SignalProcessor:
    """Создать новый экземпляр процессора сигналов"""
    return SignalProcessor(**kwargs)

# Экспорты
__all__ = [
    'SignalProcessor',
    'ProcessedSignal',
    'AggregatedSignal',
    'SignalQuality',
    'SignalStatus',
    'get_signal_processor',
    'create_signal_processor'
]