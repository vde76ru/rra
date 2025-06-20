"""
Базовый класс для торговых стратегий - ИСПРАВЛЕННАЯ ВЕРСИЯ
Файл: src/strategies/base.py
"""

import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class TradingSignal:
    """Структура торгового сигнала"""
    action: str  # 'BUY', 'SELL', 'WAIT'
    confidence: float
    price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    reason: str = ""
    risk_reward_ratio: Optional[float] = None
    indicators: Optional[Dict] = None

class BaseStrategy(ABC):
    """
    Базовый класс для всех торговых стратегий
    ИСПРАВЛЕНО: Обработка параметров конфигурации
    """
    
    def __init__(self, strategy_name: str, config: Optional[Dict] = None):
        """
        Инициализация базовой стратегии
        
        Args:
            strategy_name: Название стратегии (строка)
            config: Конфигурация стратегии (словарь, опционально)
        """
        # ✅ ИСПРАВЛЕНИЕ: Правильная обработка параметров
        self.name = strategy_name
        
        # Если config не передан или это строка, создаем пустой словарь
        if config is None or isinstance(config, str):
            self.config = {}
        else:
            self.config = config
            
        # Базовые настройки стратегии (можно переопределить в конфигурации)
        self.timeframe = self.config.get('timeframe', '1h')
        self.risk_percent = self.config.get('risk_percent', 2.0)
        self.max_positions = self.config.get('max_positions', 1)
        
        # ATR множители для расчета стоп-лоссов и тейк-профитов
        self.atr_multiplier_stop = self.config.get('atr_multiplier_stop', 2.0)
        self.atr_multiplier_take = self.config.get('atr_multiplier_take', 3.0)
        
        # Минимальные требования к данным
        self.min_periods = self.config.get('min_periods', 50)
        
        logger.debug(f"✅ Инициализирована стратегия {self.name}")
    
    @abstractmethod
    async def analyze(self, df: pd.DataFrame, symbol: str) -> TradingSignal:
        """
        Основной метод анализа рынка
        
        Args:
            df: DataFrame с рыночными данными
            symbol: Торговая пара
            
        Returns:
            TradingSignal: Торговый сигнал
        """
        pass
    
    def validate_dataframe(self, df: pd.DataFrame) -> bool:
        """
        Валидация входных данных
        
        Args:
            df: DataFrame для проверки
            
        Returns:
            bool: True если данные корректны
        """
        if df is None or df.empty:
            logger.warning(f"❌ DataFrame пуст для стратегии {self.name}")
            return False
            
        if len(df) < self.min_periods:
            logger.warning(f"❌ Недостаточно данных для {self.name}: {len(df)} < {self.min_periods}")
            return False
            
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            logger.error(f"❌ Отсутствуют колонки в данных: {missing_columns}")
            return False
            
        # Проверяем на NaN значения в последних строках
        if df[required_columns].tail(10).isnull().any().any():
            logger.warning(f"⚠️ Обнаружены NaN значения в последних данных для {self.name}")
            
        return True
    
    def calculate_stop_loss(self, price: float, action: str, atr: float,
                          multiplier: Optional[float] = None) -> float:
        """
        Расчет уровня стоп-лосса на основе ATR
        
        Args:
            price: Цена входа
            action: Направление (BUY/SELL)
            atr: Average True Range
            multiplier: Множитель ATR
            
        Returns:
            Уровень стоп-лосса
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
    
    def calculate_risk_reward(self, entry_price: float, stop_loss: float, 
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
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """
        Получение информации о стратегии
        
        Returns:
            Словарь с информацией о стратегии
        """
        return {
            'name': self.name,
            'class': self.__class__.__name__,
            'timeframe': self.timeframe,
            'risk_percent': self.risk_percent,
            'max_positions': self.max_positions,
            'min_periods': self.min_periods,
            'config': self.config
        }
    
    def update_config(self, new_config: Dict[str, Any]):
        """
        Обновление конфигурации стратегии
        
        Args:
            new_config: Новая конфигурация
        """
        self.config.update(new_config)
        
        # Обновляем основные параметры
        self.timeframe = self.config.get('timeframe', self.timeframe)
        self.risk_percent = self.config.get('risk_percent', self.risk_percent)
        self.max_positions = self.config.get('max_positions', self.max_positions)
        self.atr_multiplier_stop = self.config.get('atr_multiplier_stop', self.atr_multiplier_stop)
        self.atr_multiplier_take = self.config.get('atr_multiplier_take', self.atr_multiplier_take)
        self.min_periods = self.config.get('min_periods', self.min_periods)
        
        logger.info(f"✅ Конфигурация стратегии {self.name} обновлена")
    
    def __str__(self) -> str:
        """Строковое представление стратегии"""
        return f"Strategy(name={self.name}, timeframe={self.timeframe})"
    
    def __repr__(self) -> str:
        """Подробное строковое представление"""
        return f"<{self.__class__.__name__}(name='{self.name}', config={self.config})>"