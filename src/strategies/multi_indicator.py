"""
Мульти-индикаторная стратегия
Путь: /var/www/www-root/data/www/systemetech.ru/src/strategies/multi_indicator.py
"""
import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.trend import EMAIndicator, MACD, ADXIndicator
from ta.volatility import BollingerBands, AverageTrueRange
from ta.volume import OnBalanceVolumeIndicator
import logging

from .base import BaseStrategy, TradingSignal

logger = logging.getLogger(__name__)

class MultiIndicatorStrategy(BaseStrategy):
    """
    Продвинутая стратегия с множественными индикаторами
    Использует подтверждение от нескольких индикаторов
    """
    
    def __init__(self):
        super().__init__("multi_indicator")
        self.min_confidence = 0.65
        self.min_indicators_confirm = 3  # Минимум 3 индикатора должны подтвердить
    
    async def analyze(self, df: pd.DataFrame, symbol: str) -> TradingSignal:
        """Комплексный анализ с множественными подтверждениями"""
        
        if not self.validate_dataframe(df):
            return TradingSignal('WAIT', 0, 0, reason='Недостаточно данных')
        
        try:
            # Рассчитываем все индикаторы
            indicators = self._calculate_indicators(df)
            
            # Анализируем сигналы от каждого индикатора
            signals = self._analyze_signals(indicators, df)
            
            # Принимаем решение на основе всех сигналов
            return self._make_decision(signals, indicators, df)
            
        except Exception as e:
            logger.error(f"Ошибка анализа {symbol}: {e}")
            return TradingSignal('WAIT', 0, 0, reason=f'Ошибка анализа: {e}')
    
    def _calculate_indicators(self, df: pd.DataFrame) -> Dict:
        """Расчет всех индикаторов"""
        indicators = {}
        
        # RSI
        rsi = RSIIndicator(df['close'], window=14)
        indicators['rsi'] = rsi.rsi().iloc[-1]
        
        # MACD
        macd = MACD(df['close'])
        indicators['macd'] = macd.macd().iloc[-1]
        indicators['macd_signal'] = macd.macd_signal().iloc[-1]
        indicators['macd_diff'] = macd.macd_diff().iloc[-1]
        
        # Bollinger Bands
        bb = BollingerBands(df['close'], window=20, window_dev=2)
        indicators['bb_upper'] = bb.bollinger_hband().iloc[-1]
        indicators['bb_middle'] = bb.bollinger_mavg().iloc[-1]
        indicators['bb_lower'] = bb.bollinger_lband().iloc[-1]
        indicators['bb_width'] = bb.bollinger_wband().iloc[-1]
        indicators['bb_percent'] = bb.bollinger_pband().iloc[-1]
        
        # EMA
        indicators['ema_9'] = EMAIndicator(df['close'], window=9).ema_indicator().iloc[-1]
        indicators['ema_21'] = EMAIndicator(df['close'], window=21).ema_indicator().iloc[-1]
        indicators['ema_50'] = EMAIndicator(df['close'], window=50).ema_indicator().iloc[-1]
        indicators['ema_200'] = EMAIndicator(df['close'], window=200).ema_indicator().iloc[-1]
        
        # ADX
        adx = ADXIndicator(df['high'], df['low'], df['close'])
        indicators['adx'] = adx.adx().iloc[-1]
        indicators['adx_pos'] = adx.adx_pos().iloc[-1]
        indicators['adx_neg'] = adx.adx_neg().iloc[-1]
        
        # ATR для stop loss
        atr = AverageTrueRange(df['high'], df['low'], df['close'])
        indicators['atr'] = atr.average_true_range().iloc[-1]
        
        # Volume indicators
        indicators['volume_sma'] = df['volume'].rolling(window=20).mean().iloc[-1]
        indicators['volume_ratio'] = df['volume'].iloc[-1] / indicators['volume_sma']
        
        # Stochastic
        stoch = StochasticOscillator(df['high'], df['low'], df['close'])
        indicators['stoch_k'] = stoch.stoch().iloc[-1]
        indicators['stoch_d'] = stoch.stoch_signal().iloc[-1]
        
        # Price action
        indicators['current_price'] = df['close'].iloc[-1]
        indicators['price_change'] = (df['close'].iloc[-1] - df['close'].iloc[-2]) / df['close'].iloc[-2] * 100
        
        return indicators
    
    def _analyze_signals(self, indicators: Dict, df: pd.DataFrame) -> Dict:
        """Анализ сигналов от каждого индикатора"""
        signals = {
            'buy_signals': [],
            'sell_signals': [],
            'neutral_signals': []
        }
        
        # RSI сигналы
        if indicators['rsi'] < 30:
            signals['buy_signals'].append(('RSI', 'Перепроданность', 0.8))
        elif indicators['rsi'] > 70:
            signals['sell_signals'].append(('RSI', 'Перекупленность', 0.8))
        
        # MACD сигналы
        if indicators['macd'] > indicators['macd_signal'] and indicators['macd_diff'] > 0:
            signals['buy_signals'].append(('MACD', 'Бычье пересечение', 0.7))
        elif indicators['macd'] < indicators['macd_signal'] and indicators['macd_diff'] < 0:
            signals['sell_signals'].append(('MACD', 'Медвежье пересечение', 0.7))
        
        # Bollinger Bands сигналы
        if indicators['bb_percent'] < 0.2:
            signals['buy_signals'].append(('BB', 'Цена у нижней границы', 0.6))
        elif indicators['bb_percent'] > 0.8:
            signals['sell_signals'].append(('BB', 'Цена у верхней границы', 0.6))
        
        # EMA тренд
        if (indicators['ema_9'] > indicators['ema_21'] > indicators['ema_50'] and 
            indicators['current_price'] > indicators['ema_9']):
            signals['buy_signals'].append(('EMA', 'Восходящий тренд', 0.7))
        elif (indicators['ema_9'] < indicators['ema_21'] < indicators['ema_50'] and 
              indicators['current_price'] < indicators['ema_9']):
            signals['sell_signals'].append(('EMA', 'Нисходящий тренд', 0.7))
        
        # ADX сила тренда
        if indicators['adx'] > 25:
            if indicators['adx_pos'] > indicators['adx_neg']:
                signals['buy_signals'].append(('ADX', 'Сильный восходящий тренд', 0.6))
            else:
                signals['sell_signals'].append(('ADX', 'Сильный нисходящий тренд', 0.6))
        
        # Volume подтверждение
        if indicators['volume_ratio'] > 1.5:
            signals['neutral_signals'].append(('Volume', 'Высокий объем', 0.5))
        
        # Stochastic сигналы
        if indicators['stoch_k'] < 20 and indicators['stoch_k'] > indicators['stoch_d']:
            signals['buy_signals'].append(('Stochastic', 'Перепроданность + пересечение', 0.6))
        elif indicators['stoch_k'] > 80 and indicators['stoch_k'] < indicators['stoch_d']:
            signals['sell_signals'].append(('Stochastic', 'Перекупленность + пересечение', 0.6))
        
        return signals
    
    def _make_decision(self, signals: Dict, indicators: Dict, df: pd.DataFrame) -> TradingSignal:
        """Принятие решения на основе всех сигналов"""
        buy_score = sum(signal[2] for signal in signals['buy_signals'])
        sell_score = sum(signal[2] for signal in signals['sell_signals'])
        
        buy_count = len(signals['buy_signals'])
        sell_count = len(signals['sell_signals'])
        
        current_price = indicators['current_price']
        atr = indicators['atr']
        
        # Проверяем минимальное количество подтверждений
        if buy_count >= self.min_indicators_confirm and buy_score > sell_score:
            # Расчет уровней
            stop_loss = self.calculate_stop_loss(current_price, 'BUY', atr)
            take_profit = self.calculate_take_profit(current_price, 'BUY', atr)
            risk_reward = self.calculate_risk_reward(current_price, stop_loss, take_profit)
            
            # Расчет уверенности
            confidence = min(0.95, buy_score / (buy_count * 0.8))
            
            # Формируем причину
            reasons = [f"{sig[0]}: {sig[1]}" for sig in signals['buy_signals']]
            reason = "; ".join(reasons[:3])  # Берем топ-3 причины
            
            return TradingSignal(
                action='BUY',
                confidence=confidence,
                price=current_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                reason=reason,
                risk_reward_ratio=risk_reward,
                indicators=indicators
            )
            
        elif sell_count >= self.min_indicators_confirm and sell_score > buy_score:
            # Расчет уровней
            stop_loss = self.calculate_stop_loss(current_price, 'SELL', atr)
            take_profit = self.calculate_take_profit(current_price, 'SELL', atr)
            risk_reward = self.calculate_risk_reward(current_price, stop_loss, take_profit)
            
            # Расчет уверенности
            confidence = min(0.95, sell_score / (sell_count * 0.8))
            
            # Формируем причину
            reasons = [f"{sig[0]}: {sig[1]}" for sig in signals['sell_signals']]
            reason = "; ".join(reasons[:3])
            
            return TradingSignal(
                action='SELL',
                confidence=confidence,
                price=current_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                reason=reason,
                risk_reward_ratio=risk_reward,
                indicators=indicators
            )
        
        else:
            # Нет достаточных сигналов
            reason = f"Недостаточно подтверждений (BUY: {buy_count}, SELL: {sell_count})"
            
            return TradingSignal(
                action='WAIT',
                confidence=0,
                price=current_price,
                reason=reason,
                indicators=indicators
            )