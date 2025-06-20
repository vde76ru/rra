"""
Исправленный базовый класс для всех торговых стратегий
Путь: src/strategies/base.py
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from enum import Enum
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

class SignalAction(Enum):
    """Действия торгового сигнала"""
    BUY = "BUY"
    SELL = "SELL" 
    WAIT = "WAIT"
    HOLD = "HOLD"
    CLOSE_LONG = "CLOSE_LONG"
    CLOSE_SHORT = "CLOSE_SHORT"

class SignalStrength(Enum):
    """Сила сигнала"""
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    VERY_STRONG = "very_strong"

@dataclass
class TradingSignal:
    """
    Унифицированный торговый сигнал от стратегии
    
    Attributes:
        action: Действие (BUY, SELL, WAIT, HOLD)
        confidence: Уверенность в сигнале (0.0 - 1.0)
        price: Цена входа/выхода
        stop_loss: Уровень стоп-лосса
        take_profit: Уровень тейк-профита
        reason: Причина сигнала
        risk_reward_ratio: Соотношение риск/прибыль
        indicators: Значения индикаторов
        metadata: Дополнительные данные
        strength: Сила сигнала
        timeframe: Таймфрейм анализа
        timestamp: Время создания сигнала
        strategy_name: Название стратегии
        symbol: Торговая пара
        volume_score: Оценка объема
        volatility_score: Оценка волатильности
        market_condition: Состояние рынка
    """
    action: Union[str, SignalAction]
    confidence: float
    price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    reason: Optional[str] = None
    risk_reward_ratio: Optional[float] = None
    indicators: Optional[Dict[str, Any]] = field(default_factory=dict)
    metadata: Optional[Dict[str, Any]] = field(default_factory=dict)
    strength: Optional[SignalStrength] = None
    timeframe: Optional[str] = None
    timestamp: Optional[datetime] = field(default_factory=datetime.utcnow)
    strategy_name: Optional[str] = None
    symbol: Optional[str] = None
    volume_score: Optional[float] = None
    volatility_score: Optional[float] = None
    market_condition: Optional[str] = None
    
    def __post_init__(self):
        """Валидация и нормализация данных после создания"""
        # Нормализация action
        if isinstance(self.action, str):
            self.action = self.action.upper()
            
        # Валидация confidence
        if not 0.0 <= self.confidence <= 1.0:
            logger.warning(f"Confidence {self.confidence} вне диапазона [0,1]. Нормализуем.")
            self.confidence = max(0.0, min(1.0, self.confidence))
            
        # Определение силы сигнала если не задана
        if self.strength is None:
            if self.confidence >= 0.8:
                self.strength = SignalStrength.VERY_STRONG
            elif self.confidence >= 0.65:
                self.strength = SignalStrength.STRONG
            elif self.confidence >= 0.4:
                self.strength = SignalStrength.MODERATE
            else:
                self.strength = SignalStrength.WEAK
                
        # Валидация risk_reward_ratio
        if self.risk_reward_ratio is not None and self.risk_reward_ratio < 0:
            logger.warning(f"Отрицательный risk_reward_ratio: {self.risk_reward_ratio}")
            
    def is_actionable(self, min_confidence: float = 0.6, min_risk_reward: float = 1.5) -> bool:
        """
        Проверка, стоит ли действовать по сигналу
        
        Args:
            min_confidence: Минимальная уверенность
            min_risk_reward: Минимальное соотношение риск/прибыль
            
        Returns:
            True если сигнал подходит для исполнения
        """
        if self.action in ['WAIT', 'HOLD']:
            return False
            
        if self.confidence < min_confidence:
            return False
            
        if (self.risk_reward_ratio is not None and 
            self.risk_reward_ratio < min_risk_reward):
            return False
            
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертация в словарь для JSON serialization"""
        return {
            'action': self.action,
            'confidence': self.confidence,
            'price': self.price,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'reason': self.reason,
            'risk_reward_ratio': self.risk_reward_ratio,
            'indicators': self.indicators,
            'metadata': self.metadata,
            'strength': self.strength.value if self.strength else None,
            'timeframe': self.timeframe,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'strategy_name': self.strategy_name,
            'symbol': self.symbol,
            'volume_score': self.volume_score,
            'volatility_score': self.volatility_score,
            'market_condition': self.market_condition
        }

class RiskManager:
    """Менеджер рисков для стратегий"""
    
    def __init__(self, max_risk_per_trade: float = 0.02, max_portfolio_risk: float = 0.1):
        self.max_risk_per_trade = max_risk_per_trade  # 2% риска на сделку
        self.max_portfolio_risk = max_portfolio_risk   # 10% риска портфеля
        
    def calculate_position_size(self, account_balance: float, entry_price: float, 
                              stop_loss: float) -> float:
        """Расчет размера позиции на основе риска"""
        if stop_loss == 0 or entry_price == 0:
            return 0
            
        risk_amount = account_balance * self.max_risk_per_trade
        price_risk = abs(entry_price - stop_loss)
        
        if price_risk == 0:
            return 0
            
        position_size = risk_amount / price_risk
        return min(position_size, account_balance * 0.95)  # Не более 95% баланса
    
    def validate_risk_reward(self, entry_price: float, stop_loss: float, 
                           take_profit: float, min_ratio: float = 1.5) -> bool:
        """Валидация соотношения риск/прибыль"""
        if any(x == 0 for x in [entry_price, stop_loss, take_profit]):
            return False
            
        risk = abs(entry_price - stop_loss)
        reward = abs(take_profit - entry_price)
        
        if risk == 0:
            return False
            
        ratio = reward / risk
        return ratio >= min_ratio

class BaseStrategy(ABC):
    """
    Улучшенный базовый класс для всех торговых стратегий
    
    Предоставляет унифицированный интерфейс и общую функциональность
    """
    
    # Метаданные стратегии (переопределить в наследниках)
    NAME = "BaseStrategy"
    DESCRIPTION = "Базовый класс стратегии"
    TYPE = "base"  # momentum, mean_reversion, ml_based, scalping, etc.
    RISK_LEVEL = "medium"  # low, medium, high
    TIMEFRAMES = ["5m", "15m", "1h"]  # Поддерживаемые таймфреймы
    MIN_CANDLES = 50  # Минимальное количество свечей для анализа
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Инициализация стратегии
        
        Args:
            config: Конфигурация стратегии
        """
        self.config = config or {}
        self.last_signal = None
        self.initialized = False
        self.risk_manager = RiskManager()
        
        # Параметры по умолчанию
        self.min_confidence = self.config.get('min_confidence', 0.6)
        self.min_risk_reward = self.config.get('min_risk_reward', 1.5)
        self.atr_multiplier_stop = self.config.get('atr_multiplier_stop', 2.0)
        self.atr_multiplier_take = self.config.get('atr_multiplier_take', 3.0)
        
        logger.info(f"✅ Стратегия {self.NAME} инициализирована")
        
    @abstractmethod
    async def analyze(self, df: pd.DataFrame, symbol: str, 
                     timeframe: str = "5m") -> TradingSignal:
        """
        Анализирует данные и генерирует торговый сигнал
        
        Args:
            df: DataFrame с OHLCV данными
            symbol: Торговая пара (например, BTCUSDT)
            timeframe: Таймфрейм данных
            
        Returns:
            TradingSignal с рекомендацией
        """
        pass
    
    def validate_dataframe(self, df: pd.DataFrame) -> bool:
        """
        Проверка корректности входных данных
        
        Args:
            df: DataFrame для валидации
            
        Returns:
            True если данные корректны
        """
        if df is None or df.empty:
            logger.warning("DataFrame пуст")
            return False
            
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            logger.error(f"Отсутствуют столбцы: {missing_columns}")
            return False
            
        if len(df) < self.MIN_CANDLES:
            logger.warning(f"Недостаточно данных: {len(df)} < {self.MIN_CANDLES}")
            return False
            
        # Проверка на NaN значения
        if df[required_columns].isnull().any().any():
            logger.warning("Обнаружены NaN значения в данных")
            return False
            
        return True
    
    def calculate_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        """
        Расчет Average True Range для определения волатильности
        
        Args:
            df: DataFrame с OHLC данными
            period: Период для расчета
            
        Returns:
            Значение ATR
        """
        try:
            high_low = df['high'] - df['low']
            high_close = np.abs(df['high'] - df['close'].shift())
            low_close = np.abs(df['low'] - df['close'].shift())
            
            true_range = np.maximum(high_low, np.maximum(high_close, low_close))
            atr = true_range.rolling(window=period).mean().iloc[-1]
            
            return float(atr) if not pd.isna(atr) else 0.0
            
        except Exception as e:
            logger.error(f"Ошибка расчета ATR: {e}")
            return 0.0
    
    def calculate_stop_loss(self, price: float, action: str, atr: float, 
                          multiplier: Optional[float] = None) -> float:
        """
        Расчет уровня stop-loss на основе ATR
        
        Args:
            price: Цена входа
            action: Направление (BUY/SELL)
            atr: Average True Range
            multiplier: Множитель ATR
            
        Returns:
            Уровень stop-loss
        """
        if multiplier is None:
            multiplier = self.atr_multiplier_stop
            
        if action.upper() == 'BUY':
            return max(0, price - (atr * multiplier))
        else:  # SELL
            return price + (atr * multiplier)
    
    def calculate_take_profit(self, price: float, action: str, atr: float,
                            multiplier: Optional[float] = None) -> float:
        """
        Расчет уровня take-profit на основе ATR
        
        Args:
            price: Цена входа
            action: Направление (BUY/SELL)
            atr: Average True Range
            multiplier: Множитель ATR
            
        Returns:
            Уровень take-profit
        """
        if multiplier is None:
            multiplier = self.atr_multiplier_take
            
        if action.upper() == 'BUY':
            return price + (atr * multiplier)
        else:  # SELL
            return max(0, price - (atr * multiplier))
    
    def calculate_risk_reward_ratio(self, entry_price: float, stop_loss: float, 
                                  take_profit: float) -> float:
        """
        Расчет соотношения риск/прибыль
        
        Args:
            entry_price: Цена входа
            stop_loss: Уровень стоп-лосса
            take_profit: Уровень тейк-профита
            
        Returns:
            Соотношение риск/прибыль
        """
        try:
            risk = abs(entry_price - stop_loss)
            reward = abs(take_profit - entry_price)
            
            if risk == 0:
                return 0.0
                
            return reward / risk
            
        except (ZeroDivisionError, TypeError):
            return 0.0
    
    def get_market_condition(self, df: pd.DataFrame) -> str:
        """
        Определение состояния рынка
        
        Args:
            df: DataFrame с данными
            
        Returns:
            Состояние рынка: trending_up, trending_down, sideways, volatile
        """
        try:
            # Простой анализ тренда по EMA
            close_prices = df['close'].tail(20)
            ema_short = close_prices.ewm(span=5).mean()
            ema_long = close_prices.ewm(span=20).mean()
            
            current_price = close_prices.iloc[-1]
            ema_short_val = ema_short.iloc[-1]
            ema_long_val = ema_long.iloc[-1]
            
            # Анализ волатильности
            volatility = close_prices.std() / close_prices.mean()
            
            if volatility > 0.05:
                return "volatile"
            elif ema_short_val > ema_long_val and current_price > ema_short_val:
                return "trending_up"
            elif ema_short_val < ema_long_val and current_price < ema_short_val:
                return "trending_down"
            else:
                return "sideways"
                
        except Exception as e:
            logger.error(f"Ошибка определения состояния рынка: {e}")
            return "unknown"
    
    def create_signal(self, action: str, confidence: float, price: float,
                     stop_loss: float, take_profit: float, reason: str,
                     symbol: str, indicators: Dict[str, Any] = None) -> TradingSignal:
        """
        Создание торгового сигнала с автоматическим расчетом параметров
        
        Args:
            action: Действие
            confidence: Уверенность
            price: Цена
            stop_loss: Стоп-лосс
            take_profit: Тейк-профит
            reason: Причина
            symbol: Символ
            indicators: Индикаторы
            
        Returns:
            Готовый TradingSignal
        """
        risk_reward = self.calculate_risk_reward_ratio(price, stop_loss, take_profit)
        
        signal = TradingSignal(
            action=action,
            confidence=confidence,
            price=price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            reason=reason,
            risk_reward_ratio=risk_reward,
            indicators=indicators or {},
            strategy_name=self.NAME,
            symbol=symbol,
            timeframe=self.config.get('timeframe', '5m'),
            metadata={
                'config': self.config,
                'min_confidence': self.min_confidence,
                'min_risk_reward': self.min_risk_reward
            }
        )
        
        self.last_signal = signal
        return signal
    
    def get_info(self) -> Dict[str, Any]:
        """
        Получение информации о стратегии
        
        Returns:
            Словарь с метаданными стратегии
        """
        return {
            'name': self.NAME,
            'description': self.DESCRIPTION,
            'type': self.TYPE,
            'risk_level': self.RISK_LEVEL,
            'timeframes': self.TIMEFRAMES,
            'min_candles': self.MIN_CANDLES,
            'config': self.config,
            'last_signal': self.last_signal.to_dict() if self.last_signal else None
        }
    
    def update_config(self, new_config: Dict[str, Any]):
        """
        Обновление конфигурации стратегии
        
        Args:
            new_config: Новая конфигурация
        """
        self.config.update(new_config)
        
        # Обновляем параметры
        self.min_confidence = self.config.get('min_confidence', 0.6)
        self.min_risk_reward = self.config.get('min_risk_reward', 1.5)
        self.atr_multiplier_stop = self.config.get('atr_multiplier_stop', 2.0)
        self.atr_multiplier_take = self.config.get('atr_multiplier_take', 3.0)
        
        logger.info(f"🔄 Конфигурация стратегии {self.NAME} обновлена")

# Вспомогательные функции для совместимости
def create_wait_signal(reason: str = "Недостаточно данных", 
                      symbol: str = None) -> TradingSignal:
    """Создание сигнала ожидания"""
    return TradingSignal(
        action="WAIT",
        confidence=0.0,
        reason=reason,
        symbol=symbol
    )