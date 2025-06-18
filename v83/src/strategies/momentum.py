"""
Momentum стратегия
Путь: /var/www/www-root/data/www/systemetech.ru/src/strategies/momentum.py
"""
import pandas as pd
import numpy as np
from typing import Dict  # ✅ ИСПРАВЛЕНО: добавлен импорт Dict
from ta.momentum import RSIIndicator, ROCIndicator
from ta.trend import EMAIndicator
from ta.volatility import AverageTrueRange
import logging
from typing import Dict

from .base import BaseStrategy, TradingSignal

logger = logging.getLogger(__name__)

class MomentumStrategy(BaseStrategy):
    """
    Улучшенная momentum стратегия
    Торгует по направлению сильного движения с защитой от ошибок
    """
    
    # ✅ УЛУЧШЕНИЕ: Константы вместо магических чисел
    PRICE_CHANGE_THRESHOLD_5D = 1.0
    PRICE_CHANGE_THRESHOLD_10D = 2.0
    ROC_BULLISH_THRESHOLD = 2.0
    ROC_BEARISH_THRESHOLD = -2.0
    VOLUME_RATIO_THRESHOLD = 1.5
    RSI_NEUTRAL = 50
    
    def __init__(self):
        super().__init__("momentum")
        self.rsi_period = 14
        self.ema_fast = 9
        self.ema_slow = 21
        self.roc_period = 10
        self.min_momentum_score = 0.6
        
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
            logger.error(f"Ошибка анализа momentum для {symbol}: {e}")
            return TradingSignal('WAIT', 0, 0, reason=f'Ошибка анализа: {e}')
    
    def _calculate_indicators(self, df: pd.DataFrame) -> Dict:
        """Расчет индикаторов momentum с защитой от ошибок"""
        indicators = {}
        
        try:
            # ✅ УЛУЧШЕНИЕ: Проверка достаточности данных
            if len(df) < max(self.rsi_period, self.ema_slow, self.roc_period):
                logger.warning("Недостаточно данных для расчета всех индикаторов")
                return {}
            
            # RSI
            rsi = RSIIndicator(df['close'], window=self.rsi_period)
            rsi_values = rsi.rsi()
            indicators['rsi'] = rsi_values.iloc[-1] if not rsi_values.empty else self.RSI_NEUTRAL
            indicators['rsi_prev'] = rsi_values.iloc[-2] if len(rsi_values) > 1 else self.RSI_NEUTRAL
            
            # EMA
            ema_fast_values = EMAIndicator(df['close'], window=self.ema_fast).ema_indicator()
            ema_slow_values = EMAIndicator(df['close'], window=self.ema_slow).ema_indicator()
            indicators['ema_fast'] = ema_fast_values.iloc[-1]
            indicators['ema_slow'] = ema_slow_values.iloc[-1]
            
            # Rate of Change
            roc = ROCIndicator(df['close'], window=self.roc_period)
            indicators['roc'] = roc.roc().iloc[-1]
            
            # Price momentum с защитой от выхода за границы
            indicators['price_change_5'] = self._safe_price_change(df, 6)
            indicators['price_change_10'] = self._safe_price_change(df, 11)
            
            # Volume momentum
            volume_mean = df['volume'].rolling(window=20).mean()
            indicators['volume_ratio'] = (df['volume'].iloc[-1] / volume_mean.iloc[-1] 
                                       if volume_mean.iloc[-1] > 0 else 1.0)
            
            # ATR для volatility
            atr = AverageTrueRange(df['high'], df['low'], df['close'])
            indicators['atr'] = atr.average_true_range().iloc[-1]
            
            # Текущая цена
            indicators['current_price'] = df['close'].iloc[-1]
            
            return indicators
            
        except Exception as e:
            logger.error(f"Ошибка расчета индикаторов: {e}")
            return {}
    
    def _safe_price_change(self, df: pd.DataFrame, periods: int) -> float:
        """✅ НОВОЕ: Безопасный расчет изменения цены"""
        try:
            if len(df) >= periods:
                current_price = df['close'].iloc[-1]
                past_price = df['close'].iloc[-periods]
                return ((current_price - past_price) / past_price) * 100
            else:
                return 0.0
        except (IndexError, ZeroDivisionError):
            return 0.0
    
    def _analyze_momentum(self, indicators: Dict) -> Dict:
        """Анализ силы momentum"""
        momentum_score = {
            'direction': None,
            'strength': 0,
            'components': []
        }
        
        bullish_score = 0
        bearish_score = 0
        
        # RSI momentum
        if indicators['rsi'] > self.RSI_NEUTRAL and indicators['rsi'] > indicators['rsi_prev']:
            bullish_score += 0.2
            momentum_score['components'].append('RSI восходящий')
        elif indicators['rsi'] < self.RSI_NEUTRAL and indicators['rsi'] < indicators['rsi_prev']:
            bearish_score += 0.2
            momentum_score['components'].append('RSI нисходящий')
        
        # EMA momentum
        if indicators['ema_fast'] > indicators['ema_slow']:
            bullish_score += 0.25
            momentum_score['components'].append('EMA бычий крест')
        else:
            bearish_score += 0.25
            momentum_score['components'].append('EMA медвежий крест')
        
        # Price momentum
        if (indicators['price_change_5'] > self.PRICE_CHANGE_THRESHOLD_5D and 
            indicators['price_change_10'] > self.PRICE_CHANGE_THRESHOLD_10D):
            bullish_score += 0.3
            momentum_score['components'].append(f"Рост цены {indicators['price_change_5']:.1f}%")
        elif (indicators['price_change_5'] < -self.PRICE_CHANGE_THRESHOLD_5D and 
              indicators['price_change_10'] < -self.PRICE_CHANGE_THRESHOLD_10D):
            bearish_score += 0.3
            momentum_score['components'].append(f"Падение цены {indicators['price_change_5']:.1f}%")
        
        # ROC momentum
        if indicators['roc'] > self.ROC_BULLISH_THRESHOLD:
            bullish_score += 0.15
            momentum_score['components'].append('Сильный ROC')
        elif indicators['roc'] < self.ROC_BEARISH_THRESHOLD:
            bearish_score += 0.15
            momentum_score['components'].append('Слабый ROC')
        
        # Volume confirmation
        if indicators['volume_ratio'] > self.VOLUME_RATIO_THRESHOLD:
            if bullish_score > bearish_score:
                bullish_score += 0.1
            else:
                bearish_score += 0.1
            momentum_score['components'].append('Высокий объем')
        
        # Определяем направление и силу
        if bullish_score > bearish_score:
            momentum_score['direction'] = 'BULLISH'
            momentum_score['strength'] = bullish_score
        else:
            momentum_score['direction'] = 'BEARISH'
            momentum_score['strength'] = bearish_score
        
        return momentum_score
    
    def _make_decision(self, momentum_score: Dict, indicators: Dict, df: pd.DataFrame) -> TradingSignal:
        """Принятие решения на основе momentum"""
        
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
        else:
            action = 'SELL'
        
        # Расчет уровней
        atr = indicators['atr']
        stop_loss = self.calculate_stop_loss(indicators['current_price'], action, atr, 2.0)
        take_profit = self.calculate_take_profit(indicators['current_price'], action, atr, 3.0)
        risk_reward = self.calculate_risk_reward(indicators['current_price'], stop_loss, take_profit)
        
        # Формируем причину
        reason = f"Momentum {momentum_score['direction']}: {', '.join(momentum_score['components'][:2])}"
        
        return TradingSignal(
            action=action,
            confidence=min(0.9, momentum_score['strength']),
            price=indicators['current_price'],
            stop_loss=stop_loss,
            take_profit=take_profit,
            reason=reason,
            risk_reward_ratio=risk_reward,
            indicators=indicators
        )