"""
Базовый класс для всех торговых стратегий - ИСПРАВЛЕННАЯ ВЕРСИЯ
Путь: src/strategies/base.py
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class SignalAction(Enum):
    """Действия торгового сигнала"""
    BUY = "BUY"
    SELL = "SELL"
    WAIT = "WAIT"
    CLOSE = "CLOSE"

@dataclass
class TradingSignal:
    """
    Торговый сигнал от стратегии
    """
    action: str  # BUY, SELL, WAIT, CLOSE
    confidence: float  # 0-1, уверенность в сигнале
    price: float = 0  # Цена для исполнения
    stop_loss: Optional[float] = None  # Уровень стоп-лосса
    take_profit: Optional[float] = None  # Уровень тейк-профита
    reason: str = ""  # Причина сигнала
    risk_reward_ratio: Optional[float] = None  # Соотношение риск/прибыль
    indicators: Optional[Dict] = None  # Значения индикаторов
    strategy_name: str = ""  # Название стратегии
    symbol: str = ""  # Торговая пара
    timeframe: str = ""  # Таймфрейм
    timestamp: datetime = None  # Время сигнала
    metadata: Optional[Dict] = None  # Дополнительные данные
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.indicators is None:
            self.indicators = {}
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь"""
        return {
            'action': self.action,
            'confidence': self.confidence,
            'price': self.price,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'reason': self.reason,
            'risk_reward_ratio': self.risk_reward_ratio,
            'strategy_name': self.strategy_name,
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'indicators': self.indicators,
            'metadata': self.metadata
        }
    
    def is_valid(self) -> bool:
        """Проверка валидности сигнала"""
        if self.action not in ['BUY', 'SELL', 'WAIT', 'CLOSE']:
            return False
        if not 0 <= self.confidence <= 1:
            return False
        if self.price <= 0 and self.action in ['BUY', 'SELL']:
            return False
        return True

class BaseStrategy:
    """
    Базовый класс для всех торговых стратегий
    
    Предоставляет общий интерфейс и вспомогательные методы
    для реализации торговых стратегий.
    """
    
    # Метаданные стратегии (переопределяются в наследниках)
    NAME = "base"
    DESCRIPTION = "Базовая стратегия"
    TYPE = "general"
    RISK_LEVEL = "medium"
    TIMEFRAMES = ["5m", "15m", "1h"]
    MIN_CANDLES = 50
    
    def __init__(self, name: str = None, config: Dict[str, Any] = None):
        """
        Инициализация базовой стратегии
        
        Args:
            name: Название стратегии
            config: Конфигурация стратегии
        """
        self.NAME = name or self.NAME
        self.DESCRIPTION = getattr(self.__class__, '__doc__', '').strip()
        
        # ✅ КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Безопасная обработка config
        if config is None:
            self.config = {}
        elif isinstance(config, dict):
            self.config = config.copy()  # Создаем копию чтобы не изменять оригинал
        elif isinstance(config, str):
            # ❌ ОШИБКА: Если передана строка - это серьезная ошибка в коде
            logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА: Получена строка вместо dict для config стратегии {self.NAME}!")
            logger.error(f"❌ Полученное значение: '{config}' (тип: {type(config)})")
            logger.error("❌ Это указывает на ошибку в коде создания стратегии!")
            logger.error("❌ Исправьте код, передающий config как строку!")
            
            # Создаем пустой config но логируем ошибку
            self.config = {}
        else:
            # Если передан другой тип - логируем и используем пустой config
            logger.error(f"❌ ОШИБКА: Неожиданный тип config для стратегии {self.NAME}: {type(config)} = {config}")
            self.config = {}
        
        # Базовые параметры из конфигурации
        self.min_confidence = self.config.get('min_confidence', 0.6)
        self.min_risk_reward = self.config.get('min_risk_reward', 1.5)
        self.atr_multiplier_stop = self.config.get('atr_multiplier_stop', 2.0)
        self.atr_multiplier_take = self.config.get('atr_multiplier_take', 3.0)
        
        # Состояние стратегии
        self.last_signal = None
        self.last_analysis_time = None
        
        logger.debug(f"✅ Стратегия {self.NAME} инициализирована с config: {len(self.config)} параметров")
    
    def validate_dataframe(self, df: pd.DataFrame) -> bool:
        """
        Проверка корректности входных данных
        
        Args:
            df: DataFrame с рыночными данными
            
        Returns:
            bool: True если данные корректны
        """
        if df is None or df.empty:
            logger.warning(f"⚠️ Пустой DataFrame для стратегии {self.NAME}")
            return False
        
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            logger.warning(f"⚠️ Отсутствуют колонки {missing_columns} для стратегии {self.NAME}")
            return False
        
        if len(df) < self.MIN_CANDLES:
            logger.warning(f"⚠️ Недостаточно данных для стратегии {self.NAME}: {len(df)} < {self.MIN_CANDLES}")
            return False
        
        return True
    
    async def analyze(self, df: pd.DataFrame, symbol: str) -> TradingSignal:
        """
        Главный метод анализа - ДОЛЖЕН быть переопределен в наследниках
        
        Args:
            df: DataFrame с рыночными данными
            symbol: Торговая пара
            
        Returns:
            TradingSignal: Торговый сигнал
        """
        raise NotImplementedError("Метод analyze должен быть реализован в наследнике")
    
    def calculate_stop_loss(self, price: float, action: str, atr: float, multiplier: float = 2.0) -> float:
        """Расчет уровня стоп-лосса"""
        try:
            if action.upper() == 'BUY':
                return price - (atr * multiplier)
            else:  # SELL
                return price + (atr * multiplier)
        except Exception as e:
            logger.error(f"❌ Ошибка расчета стоп-лосса: {e}")
            # Возвращаем стоп на 2% от цены как fallback
            return price * (0.98 if action.upper() == 'BUY' else 1.02)
    
    def calculate_take_profit(self, price: float, action: str, atr: float, multiplier: float = 3.0) -> float:
        """Расчет уровня тейк-профита"""
        try:
            if action.upper() == 'BUY':
                return price + (atr * multiplier)
            else:  # SELL
                return price - (atr * multiplier)
        except Exception as e:
            logger.error(f"❌ Ошибка расчета тейк-профита: {e}")
            # Возвращаем профит на 3% от цены как fallback
            return price * (1.03 if action.upper() == 'BUY' else 0.97)
    
    def calculate_risk_reward(self, entry_price: float, stop_loss: float, take_profit: float) -> float:
        """Расчет соотношения риск/прибыль"""
        try:
            risk = abs(entry_price - stop_loss)
            reward = abs(take_profit - entry_price)
            return reward / risk if risk > 0 else 0
        except Exception as e:
            logger.error(f"❌ Ошибка расчета риск/прибыль: {e}")
            return 0
    
    def create_signal(self, action: str, confidence: float, price: float = 0, 
                     symbol: str = "", reason: str = "", 
                     stop_loss: float = None, take_profit: float = None,
                     indicators: Dict = None) -> TradingSignal:
        """
        Создание торгового сигнала
        
        Args:
            action: Действие (BUY/SELL/WAIT)
            confidence: Уверенность (0-1)
            price: Цена исполнения
            symbol: Торговая пара
            reason: Причина сигнала
            stop_loss: Стоп-лосс
            take_profit: Тейк-профит
            indicators: Значения индикаторов
            
        Returns:
            TradingSignal: Торговый сигнал
        """
        signal = TradingSignal(
            action=action,
            confidence=confidence,
            price=price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            reason=reason,
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
        self.last_analysis_time = datetime.utcnow()
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
            'last_signal': self.last_signal.to_dict() if self.last_signal else None,
            'last_analysis_time': self.last_analysis_time.isoformat() if self.last_analysis_time else None
        }
    
    def update_config(self, new_config: Dict[str, Any]):
        """
        Обновление конфигурации стратегии
        
        Args:
            new_config: Новая конфигурация
        """
        if not isinstance(new_config, dict):
            logger.error(f"❌ Попытка обновить config не-словарем: {type(new_config)}")
            return
            
        self.config.update(new_config)
        
        # Обновляем параметры
        self.min_confidence = self.config.get('min_confidence', 0.6)
        self.min_risk_reward = self.config.get('min_risk_reward', 1.5)
        self.atr_multiplier_stop = self.config.get('atr_multiplier_stop', 2.0)
        self.atr_multiplier_take = self.config.get('atr_multiplier_take', 3.0)
        
        logger.info(f"🔄 Конфигурация стратегии {self.NAME} обновлена")
    
    def __str__(self) -> str:
        """Строковое представление стратегии"""
        return f"{self.NAME} ({self.TYPE}, риск: {self.RISK_LEVEL})"
    
    def __repr__(self) -> str:
        """Подробное представление стратегии"""
        return f"<{self.__class__.__name__}: {self.NAME}>"

# Вспомогательные функции для совместимости
def create_wait_signal(reason: str = "Недостаточно данных", 
                      symbol: str = None) -> TradingSignal:
    """Создание сигнала ожидания"""
    return TradingSignal(
        action="WAIT",
        confidence=0.0,
        reason=reason,
        symbol=symbol or ""
    )

def create_buy_signal(price: float, confidence: float, 
                     symbol: str = "", reason: str = "",
                     stop_loss: float = None, take_profit: float = None) -> TradingSignal:
    """Создание сигнала покупки"""
    return TradingSignal(
        action="BUY",
        confidence=confidence,
        price=price,
        symbol=symbol,
        reason=reason,
        stop_loss=stop_loss,
        take_profit=take_profit
    )

def create_sell_signal(price: float, confidence: float,
                      symbol: str = "", reason: str = "",
                      stop_loss: float = None, take_profit: float = None) -> TradingSignal:
    """Создание сигнала продажи"""
    return TradingSignal(
        action="SELL",
        confidence=confidence,
        price=price,
        symbol=symbol,
        reason=reason,
        stop_loss=stop_loss,
        take_profit=take_profit
    )