"""
Momentum стратегия
Путь: /var/www/www-root/data/www/systemetech.ru/src/strategies/momentum.py
"""
import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator, ROCIndicator
from ta.trend import EMAIndicator
from ta.volatility import AverageTrueRange
import logging

from .base import BaseStrategy, TradingSignal

logger = logging.getLogger(__name__)

class MomentumStrategy(BaseStrategy):
    """
    Простая momentum стратегия
    Торгует по направлению сильного движения
    """
    
    def __init__(self):
        super().__init__("momentum")
        self.rsi_period = 14
        self.ema_fast = 9
        self.ema_slow = 21
        self.roc_period = 10
        self.min_momentum_score = 0.6
        
    async def analyze(self, df: pd.DataFrame, symbol: str) -> TradingSignal:
        """Анализ momentum"""
        
        if not self.validate_dataframe(df):
            return TradingSignal('WAIT', 0, 0, reason='Недостаточно данных')
        
        try:
            # Рассчитываем индикаторы
            indicators = self._calculate_indicators(df)
            
            # Анализируем momentum
            momentum_score = self._analyze_momentum(indicators)
            
            # Принимаем решение
            return self._make_decision(momentum_score, indicators, df)
            
        except Exception as e:
            logger.error(f"Ошибка анализа momentum для {symbol}: {e}")
            return TradingSignal('WAIT', 0, 0, reason=f'Ошибка анализа: {e}')
    
    def _calculate_indicators(self, df: pd.DataFrame) -> Dict:
        """Расчет индикаторов momentum"""
        indicators = {}
        
        # RSI
        rsi = RSIIndicator(df['close'], window=self.rsi_period)
        indicators['rsi'] = rsi.rsi().iloc[-1]
        indicators['rsi_prev'] = rsi.rsi().iloc[-2]
        
        # EMA
        indicators['ema_fast'] = EMAIndicator(df['close'], window=self.ema_fast).ema_indicator().iloc[-1]
        indicators['ema_slow'] = EMAIndicator(df['close'], window=self.ema_slow).ema_indicator().iloc[-1]
        
        # Rate of Change
        roc = ROCIndicator(df['close'], window=self.roc_period)
        indicators['roc'] = roc.roc().iloc[-1]
        
        # Price momentum
        indicators['price_change_5'] = ((df['close'].iloc[-1] - df['close'].iloc[-6]) / df['close'].iloc[-6]) * 100
        indicators['price_change_10'] = ((df['close'].iloc[-1] - df['close'].iloc[-11]) / df['close'].iloc[-11]) * 100
        
        # Volume momentum
        indicators['volume_ratio'] = df['volume'].iloc[-1] / df['volume'].rolling(window=20).mean().iloc[-1]
        
        # ATR для volatility
        atr = AverageTrueRange(df['high'], df['low'], df['close'])
        indicators['atr'] = atr.average_true_range().iloc[-1]
        
        # Текущая цена
        indicators['current_price'] = df['close'].iloc[-1]
        
        return indicators
    
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
        if indicators['rsi'] > 50 and indicators['rsi'] > indicators['rsi_prev']:
            bullish_score += 0.2
            momentum_score['components'].append('RSI восходящий')
        elif indicators['rsi'] < 50 and indicators['rsi'] < indicators['rsi_prev']:
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
        if indicators['price_change_5'] > 1 and indicators['price_change_10'] > 2:
            bullish_score += 0.3
            momentum_score['components'].append(f"Рост цены {indicators['price_change_5']:.1f}%")
        elif indicators['price_change_5'] < -1 and indicators['price_change_10'] < -2:
            bearish_score += 0.3
            momentum_score['components'].append(f"Падение цены {indicators['price_change_5']:.1f}%")
        
        # ROC momentum
        if indicators['roc'] > 2:
            bullish_score += 0.15
            momentum_score['components'].append('Сильный ROC')
        elif indicators['roc'] < -2:
            bearish_score += 0.15
            momentum_score['components'].append('Слабый ROC')
        
        # Volume confirmation
        if indicators['volume_ratio'] > 1.5:
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