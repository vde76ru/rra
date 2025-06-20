"""
Momentum стратегия - ИСПРАВЛЕННАЯ ВЕРСИЯ
Файл: src/strategies/momentum.py
"""
import pandas as pd
import numpy as np
from typing import Dict, Optional
import logging

try:
    from ta.momentum import RSIIndicator, ROCIndicator
    from ta.trend import EMAIndicator
    from ta.volatility import AverageTrueRange
    TA_AVAILABLE = True
except ImportError:
    TA_AVAILABLE = False
    logging.warning("⚠️ TA-Lib не установлен, используем ручные реализации")

from .base import BaseStrategy, TradingSignal

logger = logging.getLogger(__name__)

class MomentumStrategy(BaseStrategy):
    """
    Улучшенная momentum стратегия - ИСПРАВЛЕННАЯ ВЕРСИЯ
    Торгует по направлению сильного движения с защитой от ошибок
    
    ИСПРАВЛЕНИЯ:
    - Правильная инициализация с новым BaseStrategy
    - Обработка отсутствия TA-Lib
    - Улучшенная обработка ошибок
    """
    
    # Константы стратегии
    PRICE_CHANGE_THRESHOLD_5D = 1.0
    PRICE_CHANGE_THRESHOLD_10D = 2.0
    ROC_BULLISH_THRESHOLD = 2.0
    ROC_BEARISH_THRESHOLD = -2.0
    VOLUME_RATIO_THRESHOLD = 1.5
    RSI_NEUTRAL = 50
    
    # Метаинформация для фабрики
    STRATEGY_TYPE = 'momentum'
    RISK_LEVEL = 'medium'
    TIMEFRAMES = ['1h', '4h', '1d']
    
    def __init__(self, strategy_name: str = "momentum", config: Optional[Dict] = None):
        """
        Инициализация momentum стратегии
        
        Args:
            strategy_name: Название стратегии
            config: Конфигурация стратегии
        """
        # ✅ ИСПРАВЛЕНИЕ: Правильный вызов родительского конструктора
        super().__init__(strategy_name, config)
        
        # Специфичные для momentum настройки
        self.rsi_period = self.config.get('rsi_period', 14)
        self.ema_fast = self.config.get('ema_fast', 9)
        self.ema_slow = self.config.get('ema_slow', 21)
        self.roc_period = self.config.get('roc_period', 10)
        self.min_momentum_score = self.config.get('min_momentum_score', 0.6)
        
        logger.debug(f"✅ MomentumStrategy инициализирована: {self.name}")
        
    async def analyze(self, df: pd.DataFrame, symbol: str) -> TradingSignal:
        """Анализ momentum с улучшенной обработкой ошибок"""
        
        if not self.validate_dataframe(df):
            return TradingSignal('WAIT', 0, 0, reason='Недостаточно данных')
        
        try:
            # Рассчитываем индикаторы
            indicators = self._calculate_indicators(df)
            
            # Проверяем корректность данных
            if not indicators:
                return TradingSignal('WAIT', 0, 0, reason='Ошибка расчета индикаторов')
            
            # Анализируем momentum
            momentum_score = self._analyze_momentum(indicators)
            
            # Принимаем решение
            return self._make_decision(momentum_score, indicators, df)
            
        except Exception as e:
            logger.error(f"❌ Ошибка анализа momentum для {symbol}: {e}")
            return TradingSignal('WAIT', 0, 0, reason=f'Ошибка анализа: {e}')
    
    def _calculate_indicators(self, df: pd.DataFrame) -> Dict:
        """Расчет индикаторов momentum с защитой от ошибок"""
        indicators = {}
        
        try:
            # Текущая цена
            indicators['current_price'] = float(df['close'].iloc[-1])
            
            if TA_AVAILABLE:
                # Используем TA-Lib если доступен
                indicators.update(self._calculate_with_talib(df))
            else:
                # Используем ручные реализации
                indicators.update(self._calculate_manual(df))
            
            # Анализ объема
            if 'volume' in df.columns:
                volume_sma = df['volume'].rolling(window=20).mean()
                current_volume = df['volume'].iloc[-1]
                avg_volume = volume_sma.iloc[-1]
                
                indicators['volume_ratio'] = current_volume / avg_volume if avg_volume > 0 else 1.0
            else:
                indicators['volume_ratio'] = 1.0
            
            return indicators
            
        except Exception as e:
            logger.error(f"❌ Ошибка расчета индикаторов: {e}")
            return {}
    
    def _calculate_with_talib(self, df: pd.DataFrame) -> Dict:
        """Расчет индикаторов с помощью TA-Lib"""
        indicators = {}
        
        try:
            # RSI
            rsi_indicator = RSIIndicator(df['close'], window=self.rsi_period)
            indicators['rsi'] = float(rsi_indicator.rsi().iloc[-1])
            
            # EMA
            ema_fast = EMAIndicator(df['close'], window=self.ema_fast)
            ema_slow = EMAIndicator(df['close'], window=self.ema_slow)
            indicators['ema_fast'] = float(ema_fast.ema_indicator().iloc[-1])
            indicators['ema_slow'] = float(ema_slow.ema_indicator().iloc[-1])
            
            # Rate of Change
            roc_indicator = ROCIndicator(df['close'], window=self.roc_period)
            indicators['roc'] = float(roc_indicator.roc().iloc[-1])
            
            # ATR
            atr_indicator = AverageTrueRange(df['high'], df['low'], df['close'], window=14)
            indicators['atr'] = float(atr_indicator.average_true_range().iloc[-1])
            
        except Exception as e:
            logger.warning(f"⚠️ Ошибка расчета с TA-Lib: {e}, переключаемся на ручной расчет")
            return self._calculate_manual(df)
            
        return indicators
    
    def _calculate_manual(self, df: pd.DataFrame) -> Dict:
        """Ручной расчет индикаторов"""
        indicators = {}
        
        try:
            # RSI (упрощенная версия)
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            indicators['rsi'] = float(rsi.iloc[-1]) if not rsi.iloc[-1] is pd.isna(rsi.iloc[-1]) else 50.0
            
            # EMA
            ema_fast = df['close'].ewm(span=self.ema_fast).mean()
            ema_slow = df['close'].ewm(span=self.ema_slow).mean()
            indicators['ema_fast'] = float(ema_fast.iloc[-1])
            indicators['ema_slow'] = float(ema_slow.iloc[-1])
            
            # Rate of Change
            roc = ((df['close'] - df['close'].shift(self.roc_period)) / df['close'].shift(self.roc_period)) * 100
            indicators['roc'] = float(roc.iloc[-1]) if not pd.isna(roc.iloc[-1]) else 0.0
            
            # ATR (упрощенная версия)
            high_low = df['high'] - df['low']
            high_close = abs(df['high'] - df['close'].shift())
            low_close = abs(df['low'] - df['close'].shift())
            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr = true_range.rolling(window=14).mean()
            indicators['atr'] = float(atr.iloc[-1]) if not pd.isna(atr.iloc[-1]) else 1.0
            
        except Exception as e:
            logger.error(f"❌ Ошибка ручного расчета индикаторов: {e}")
            # Возвращаем дефолтные значения
            indicators = {
                'rsi': 50.0,
                'ema_fast': float(df['close'].iloc[-1]),
                'ema_slow': float(df['close'].iloc[-1]),
                'roc': 0.0,
                'atr': float(df['close'].iloc[-1]) * 0.02  # 2% от цены
            }
            
        return indicators
    
    def _analyze_momentum(self, indicators: Dict) -> Dict:
        """Анализ momentum на основе индикаторов"""
        momentum_score = {
            'direction': 'NEUTRAL',
            'strength': 0.0,
            'components': []
        }
        
        bullish_score = 0.0
        bearish_score = 0.0
        
        try:
            # EMA тренд
            if indicators['ema_fast'] > indicators['ema_slow']:
                bullish_score += 0.3
                momentum_score['components'].append('EMA бычий')
            else:
                bearish_score += 0.3
                momentum_score['components'].append('EMA медвежий')
            
            # RSI momentum
            rsi = indicators['rsi']
            if rsi > 60:
                bullish_score += 0.2
                momentum_score['components'].append('RSI сильный')
            elif rsi < 40:
                bearish_score += 0.2
                momentum_score['components'].append('RSI слабый')
            
            # ROC momentum
            roc = indicators['roc']
            if roc > self.ROC_BULLISH_THRESHOLD:
                bullish_score += 0.25
                momentum_score['components'].append('ROC растет')
            elif roc < self.ROC_BEARISH_THRESHOLD:
                bearish_score += 0.25
                momentum_score['components'].append('ROC падает')
            
            # Volume confirmation
            if indicators['volume_ratio'] > self.VOLUME_RATIO_THRESHOLD:
                if bullish_score > bearish_score:
                    bullish_score += 0.15
                    momentum_score['components'].append('Объем подтверждает')
                else:
                    bearish_score += 0.15
                    momentum_score['components'].append('Объем подтверждает')
            
            # Определяем направление и силу
            if bullish_score > bearish_score and bullish_score > 0.5:
                momentum_score['direction'] = 'BULLISH'
                momentum_score['strength'] = bullish_score
            elif bearish_score > bullish_score and bearish_score > 0.5:
                momentum_score['direction'] = 'BEARISH'
                momentum_score['strength'] = bearish_score
            else:
                momentum_score['direction'] = 'NEUTRAL'
                momentum_score['strength'] = max(bullish_score, bearish_score)
                
        except Exception as e:
            logger.error(f"❌ Ошибка анализа momentum: {e}")
            
        return momentum_score
    
    def _make_decision(self, momentum_score: Dict, indicators: Dict, df: pd.DataFrame) -> TradingSignal:
        """Принятие решения на основе momentum"""
        
        try:
            # Проверяем минимальную силу momentum
            if momentum_score['strength'] < self.min_momentum_score:
                return TradingSignal(
                    action='WAIT',
                    confidence=0,
                    price=indicators['current_price'],
                    reason=f"Слабый momentum: {momentum_score['strength']:.2f}"
                )
            
            # Определяем действие
            if momentum_score['direction'] == 'BULLISH':
                action = 'BUY'
            elif momentum_score['direction'] == 'BEARISH':
                action = 'SELL'
            else:
                return TradingSignal(
                    action='WAIT',
                    confidence=0,
                    price=indicators['current_price'],
                    reason="Нейтральный momentum"
                )
            
            # Расчет уровней
            current_price = indicators['current_price']
            atr = indicators['atr']
            
            stop_loss = self.calculate_stop_loss(current_price, action, atr, 2.0)
            take_profit = self.calculate_take_profit(current_price, action, atr, 3.0)
            risk_reward = self.calculate_risk_reward(current_price, stop_loss, take_profit)
            
            # Проверяем минимальный risk/reward
            if risk_reward < 1.5:
                return TradingSignal(
                    action='WAIT',
                    confidence=0,
                    price=current_price,
                    reason=f"Плохой R/R: {risk_reward:.2f}"
                )
            
            # Формируем причину
            components_str = ', '.join(momentum_score['components'][:3])
            reason = f"Momentum {momentum_score['direction']}: {components_str}"
            
            # Создаем сигнал
            return TradingSignal(
                action=action,
                confidence=min(0.9, momentum_score['strength']),
                price=current_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                reason=reason,
                risk_reward_ratio=risk_reward,
                indicators=indicators
            )
            
        except Exception as e:
            logger.error(f"❌ Ошибка принятия решения: {e}")
            return TradingSignal(
                action='WAIT',
                confidence=0,
                price=indicators.get('current_price', 0),
                reason=f'Ошибка решения: {e}'
            )