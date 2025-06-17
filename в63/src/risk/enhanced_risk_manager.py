"""
Улучшенный менеджер рисков с ML-интеграцией
Файл: src/risk/enhanced_risk_manager.py
"""
from ..core.models import (
    TradingLog, BotState, Trade, Signal,
    Balance, TradingPair, MLModel, User
)
import asyncio
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import numpy as np
from sqlalchemy.orm import Session

from ..core.database import SessionLocal
from ..core.models import Trade, MarketCondition
from ..logging.smart_logger import SmartLogger
from ..ml.models.classifier import DirectionClassifier
from ..ml.features.feature_engineering import FeatureEngineering

logger = SmartLogger(__name__)


@dataclass
class RiskParameters:
    """Параметры управления рисками"""
    max_position_size: float = 0.1  # Максимум 10% от баланса на позицию
    max_daily_loss: float = 0.05    # Максимум 5% убытка в день
    max_drawdown: float = 0.15      # Максимальная просадка 15%
    max_open_positions: int = 5     # Максимум открытых позиций
    risk_per_trade: float = 0.02    # Риск на сделку 2%
    correlation_threshold: float = 0.7  # Порог корреляции для диверсификации
    volatility_adjustment: bool = True  # Адаптация к волатильности
    ml_confidence_threshold: float = 0.65  # Минимальная уверенность ML


class EnhancedRiskManager:
    """
    Улучшенный менеджер рисков с ML-прогнозированием
    """
    
    def __init__(self, initial_balance: float):
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.risk_params = RiskParameters()
        
        # ML компоненты
        self.ml_classifier = DirectionClassifier()
        self.feature_engineering = FeatureEngineering()
        
        # Статистика
        self.daily_pnl = 0.0
        self.peak_balance = initial_balance
        self.current_drawdown = 0.0
        self.open_positions: Dict[str, Trade] = {}
        self.daily_trades_count = 0
        self.last_reset = datetime.utcnow()
        
        # Кеш волатильности
        self.volatility_cache: Dict[str, float] = {}
        self.correlation_cache: Dict[Tuple[str, str], float] = {}
    
    async def can_open_position(self, symbol: str, side: str, 
                               quantity: float, price: float,
                               market_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Проверяет возможность открытия позиции
        
        Returns:
            (can_open, reason)
        """
        try:
            # 1. Проверка количества открытых позиций
            if len(self.open_positions) >= self.risk_params.max_open_positions:
                return False, f"Достигнут лимит открытых позиций: {self.risk_params.max_open_positions}"
            
            # 2. Проверка дневного убытка
            if self.daily_pnl < -self.initial_balance * self.risk_params.max_daily_loss:
                return False, f"Достигнут дневной лимит убытков: {self.daily_pnl:.2f}"
            
            # 3. Проверка текущей просадки
            if self.current_drawdown > self.risk_params.max_drawdown:
                return False, f"Текущая просадка слишком высока: {self.current_drawdown:.2%}"
            
            # 4. Проверка размера позиции
            position_value = quantity * price
            max_position_value = self.current_balance * self.risk_params.max_position_size
            
            if position_value > max_position_value:
                return False, f"Размер позиции превышает лимит: {position_value:.2f} > {max_position_value:.2f}"
            
            # 5. ML-проверка рыночных условий
            ml_check = await self._check_ml_conditions(symbol, side, market_data)
            if not ml_check[0]:
                return False, ml_check[1]
            
            # 6. Проверка корреляции с существующими позициями
            correlation_check = await self._check_correlation(symbol)
            if not correlation_check[0]:
                return False, correlation_check[1]
            
            # 7. Проверка волатильности
            volatility_check = await self._check_volatility(symbol, market_data)
            if not volatility_check[0]:
                return False, volatility_check[1]
            
            logger.info(
                "Позиция одобрена менеджером рисков",
                category='risk',
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=price,
                daily_pnl=self.daily_pnl,
                drawdown=self.current_drawdown
            )
            
            return True, "Все проверки пройдены"
            
        except Exception as e:
            logger.error(
                f"Ошибка в проверке рисков: {e}",
                category='risk',
                symbol=symbol,
                error=str(e)
            )
            return False, f"Ошибка проверки: {e}"
    
    async def _check_ml_conditions(self, symbol: str, side: str, 
                                  market_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Проверка ML-прогнозов"""
        try:
            # Извлекаем признаки
            features_dict = self.feature_engineering.extract_features(
                market_data['candles'],
                market_data.get('order_book', {}),
                market_data.get('trades', [])
            )
            
            if features_dict['features'] is None:
                return True, "Недостаточно данных для ML-анализа"
            
            features = features_dict['features']
            
            # Получаем прогноз
            prediction = self.ml_classifier.predict_proba(features.reshape(1, -1))
            
            # Проверяем уверенность
            max_confidence = np.max(prediction[0])
            if max_confidence < self.risk_params.ml_confidence_threshold:
                return False, f"Низкая уверенность ML модели: {max_confidence:.2%}"
            
            # Проверяем соответствие направления
            predicted_direction = np.argmax(prediction[0])
            if (predicted_direction == 0 and side == 'buy') or \
               (predicted_direction == 2 and side == 'sell'):
                return False, f"ML прогнозирует противоположное направление"
            
            return True, f"ML уверенность: {max_confidence:.2%}"
            
        except Exception as e:
            logger.warning(
                f"Ошибка ML проверки: {e}",
                category='risk',
                symbol=symbol
            )
            return True, "ML проверка пропущена из-за ошибки"
    
    async def _check_correlation(self, symbol: str) -> Tuple[bool, str]:
        """Проверка корреляции с существующими позициями"""
        if len(self.open_positions) == 0:
            return True, "Нет открытых позиций"
        
        high_correlation_count = 0
        
        for existing_symbol in self.open_positions:
            if existing_symbol == symbol:
                continue
            
            # Получаем корреляцию из кеша или вычисляем
            correlation = await self._get_correlation(symbol, existing_symbol)
            
            if abs(correlation) > self.risk_params.correlation_threshold:
                high_correlation_count += 1
        
        # Не более 2 высоко коррелированных позиций
        if high_correlation_count >= 2:
            return False, f"Слишком много коррелированных позиций: {high_correlation_count}"
        
        return True, "Корреляция в норме"
    
    async def _check_volatility(self, symbol: str, 
                              market_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Проверка волатильности"""
        try:
            # Вычисляем текущую волатильность
            candles = market_data.get('candles', [])
            if len(candles) < 20:
                return True, "Недостаточно данных для оценки волатильности"
            
            # ATR для оценки волатильности
            high_prices = [c['high'] for c in candles[-20:]]
            low_prices = [c['low'] for c in candles[-20:]]
            close_prices = [c['close'] for c in candles[-20:]]
            
            tr_values = []
            for i in range(1, len(close_prices)):
                tr = max(
                    high_prices[i] - low_prices[i],
                    abs(high_prices[i] - close_prices[i-1]),
                    abs(low_prices[i] - close_prices[i-1])
                )
                tr_values.append(tr)
            
            atr = np.mean(tr_values)
            atr_percent = (atr / close_prices[-1]) * 100
            
            # Кешируем волатильность
            self.volatility_cache[symbol] = atr_percent
            
            # Проверка экстремальной волатильности
            if atr_percent > 10:  # Более 10% волатильность
                return False, f"Экстремальная волатильность: {atr_percent:.2%}"
            
            return True, f"Волатильность в норме: {atr_percent:.2%}"
            
        except Exception as e:
            logger.warning(
                f"Ошибка проверки волатильности: {e}",
                category='risk',
                symbol=symbol
            )
            return True, "Проверка волатильности пропущена"
    
    async def _get_correlation(self, symbol1: str, symbol2: str) -> float:
        """Получает корреляцию между символами"""
        # Проверяем кеш
        cache_key = tuple(sorted([symbol1, symbol2]))
        if cache_key in self.correlation_cache:
            return self.correlation_cache[cache_key]
        
        # TODO: Вычислить реальную корреляцию из исторических данных
        # Пока используем случайное значение для демонстрации
        correlation = np.random.uniform(-0.3, 0.3)
        
        # Кешируем на 1 час
        self.correlation_cache[cache_key] = correlation
        
        return correlation
    
    def calculate_position_size(self, symbol: str, entry_price: float, 
                              stop_loss: float) -> float:
        """
        Рассчитывает размер позиции на основе риска
        
        Kelly Criterion с учетом волатильности
        """
        # Риск на сделку
        risk_amount = self.current_balance * self.risk_params.risk_per_trade
        
        # Риск на единицу
        risk_per_unit = abs(entry_price - stop_loss)
        
        if risk_per_unit == 0:
            return 0
        
        # Базовый размер позиции
        base_position_size = risk_amount / risk_per_unit
        
        # Корректировка на волатильность
        if self.risk_params.volatility_adjustment and symbol in self.volatility_cache:
            volatility = self.volatility_cache[symbol]
            # Уменьшаем позицию при высокой волатильности
            volatility_multiplier = max(0.5, min(1.0, 5.0 / volatility))
            base_position_size *= volatility_multiplier
        
        # Ограничения
        max_position_size = self.current_balance * self.risk_params.max_position_size / entry_price
        
        return min(base_position_size, max_position_size)
    
    async def update_position(self, trade: Trade):
        """Обновляет информацию о позиции"""
        if trade.status == 'open':
            self.open_positions[trade.symbol] = trade
        elif trade.status == 'closed' and trade.symbol in self.open_positions:
            del self.open_positions[trade.symbol]
            
            # Обновляем PnL
            if trade.profit:
                self.daily_pnl += trade.profit
                self.current_balance += trade.profit
                
                # Обновляем drawdown
                if self.current_balance > self.peak_balance:
                    self.peak_balance = self.current_balance
                    self.current_drawdown = 0
                else:
                    self.current_drawdown = (self.peak_balance - self.current_balance) / self.peak_balance
        
        # Сброс дневной статистики
        if (datetime.utcnow() - self.last_reset).days >= 1:
            self.daily_pnl = 0
            self.daily_trades_count = 0
            self.last_reset = datetime.utcnow()
    
    def get_risk_metrics(self) -> Dict[str, Any]:
        """Возвращает текущие метрики риска"""
        return {
            'current_balance': self.current_balance,
            'daily_pnl': self.daily_pnl,
            'daily_pnl_percent': (self.daily_pnl / self.initial_balance) * 100,
            'current_drawdown': self.current_drawdown * 100,
            'peak_balance': self.peak_balance,
            'open_positions': len(self.open_positions),
            'position_symbols': list(self.open_positions.keys()),
            'risk_utilization': len(self.open_positions) / self.risk_params.max_open_positions,
            'volatility_cache': dict(self.volatility_cache)
        }
    
    async def emergency_close_all(self, reason: str):
        """Экстренное закрытие всех позиций"""
        logger.critical(
            f"Экстренное закрытие всех позиций: {reason}",
            category='risk',
            open_positions=len(self.open_positions),
            reason=reason
        )
        
        # TODO: Реализовать закрытие через exchange API
        # Пока просто очищаем локальный список
        self.open_positions.clear()
    
    def adjust_risk_parameters(self, performance_metrics: Dict[str, float]):
        """
        Динамическая корректировка параметров риска на основе производительности
        """
        win_rate = performance_metrics.get('win_rate', 0.5)
        sharpe_ratio = performance_metrics.get('sharpe_ratio', 0)
        
        # Увеличиваем риск при хорошей производительности
        if win_rate > 0.6 and sharpe_ratio > 1.5:
            self.risk_params.risk_per_trade = min(0.03, self.risk_params.risk_per_trade * 1.1)
            self.risk_params.max_position_size = min(0.15, self.risk_params.max_position_size * 1.1)
            logger.info(
                "Увеличены параметры риска из-за хорошей производительности",
                category='risk',
                risk_per_trade=self.risk_params.risk_per_trade,
                max_position_size=self.risk_params.max_position_size
            )
        
        # Уменьшаем риск при плохой производительности
        elif win_rate < 0.4 or sharpe_ratio < 0:
            self.risk_params.risk_per_trade = max(0.01, self.risk_params.risk_per_trade * 0.9)
            self.risk_params.max_position_size = max(0.05, self.risk_params.max_position_size * 0.9)
            logger.warning(
                "Уменьшены параметры риска из-за плохой производительности",
                category='risk',
                risk_per_trade=self.risk_params.risk_per_trade,
                max_position_size=self.risk_params.max_position_size
            )