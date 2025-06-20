"""
Класс для исполнения торговых операций с безопасными импортами
Путь: src/bot/trader.py
"""
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
import numpy as pd
from collections import deque

# Импорты моделей из core
from ..core.models import Trade, Signal, Order
from ..core.database import SessionLocal
from ..core.config import config
from ..exchange.client import ExchangeClient

# ML модули - используем try/except для безопасного импорта
try:
    from ..ml.strategy_selector import MLStrategySelector
except ImportError:
    MLStrategySelector = None
    
try:
    from ..ml.models.regressor import PriceLevelRegressor
except ImportError:
    PriceLevelRegressor = None
    
try:
    from ..ml.models.reinforcement import TradingRLAgent
except ImportError:
    TradingRLAgent = None
    
try:
    from ..ml.features.feature_engineering import FeatureEngineering
except ImportError:
    FeatureEngineering = None

# Модули анализа - также с защитой от отсутствия
try:
    from ..analysis.news.impact_scorer import NewsImpactScorer
except ImportError:
    NewsImpactScorer = None
    
try:
    from ..analysis.social.signal_extractor import SocialSignalExtractor
except ImportError:
    SocialSignalExtractor = None

# Логирование
try:
    from ..logging.smart_logger import SmartLogger
    logger = SmartLogger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

class Trader:
    """Класс для исполнения торговых операций"""
    
    def __init__(self, exchange: ExchangeClient):
        self.exchange = exchange
        
        # Инициализируем ML компоненты если они доступны
        self.ml_strategy_selector = MLStrategySelector() if MLStrategySelector else None
        self.price_regressor = PriceLevelRegressor() if PriceLevelRegressor else None
        self.rl_agent = TradingRLAgent() if TradingRLAgent else None
        self.feature_engineering = FeatureEngineering() if FeatureEngineering else None
        
        # Инициализируем модули анализа
        self.news_scorer = NewsImpactScorer() if NewsImpactScorer else None
        self.social_extractor = SocialSignalExtractor() if SocialSignalExtractor else None
        
        logger.info(f"Trader инициализирован. ML модули: {self.ml_strategy_selector is not None}")
        
    async def execute_signal(self, signal: Signal) -> Optional[Trade]:
        """Исполнение торгового сигнала"""
        try:
            # Получаем текущий баланс
            balance = await self.exchange.fetch_balance()
            usdt_balance = balance.get('USDT', {}).get('free', 0)
            
            if usdt_balance < 10:  # Минимальный баланс
                logger.warning(f"Недостаточный баланс: {usdt_balance} USDT")
                return None
            
            # Расчет размера позиции
            position_size = self._calculate_position_size(
                balance=usdt_balance,
                signal=signal
            )
            
            # Создание ордера
            order_params = {
                'symbol': signal.symbol,
                'side': signal.action,  # BUY или SELL
                'type': 'MARKET',
                'quantity': position_size
            }
            
            # Добавляем ML-предсказания если доступны
            if self.ml_strategy_selector and self.feature_engineering:
                try:
                    # Здесь можно добавить ML логику
                    pass
                except Exception as e:
                    logger.warning(f"Ошибка ML предсказания: {e}")
            
            # Исполняем ордер
            order_result = await self.exchange.create_order(**order_params)
            
            if order_result:
                # Создаем запись о сделке
                trade = Trade(
                    signal_id=signal.id,
                    symbol=signal.symbol,
                    side=signal.action,
                    quantity=position_size,
                    price=order_result['price'],
                    total=order_result['cost'],
                    fee=order_result['fee']['cost'] if order_result.get('fee') else 0,
                    status='FILLED',
                    order_id=str(order_result['id']),
                    strategy=signal.strategy
                )
                
                logger.info(
                    f"✅ Сделка исполнена: {signal.symbol} {signal.action} "
                    f"{position_size} @ {order_result['price']}"
                )
                
                return trade
            
        except Exception as e:
            logger.error(f"Ошибка исполнения сигнала: {e}")
            return None
    
    def _calculate_position_size(self, balance: float, signal: Signal) -> float:
        """Расчет размера позиции"""
        # Базовый расчет - 10% от баланса
        base_size = balance * 0.1
        
        # Корректировка на основе уверенности сигнала
        if hasattr(signal, 'confidence') and signal.confidence:
            base_size *= signal.confidence
        
        # Минимальный размер позиции
        min_size = 10.0  # USDT
        
        return max(base_size, min_size)