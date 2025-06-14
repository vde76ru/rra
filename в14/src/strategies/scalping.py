"""
Скальпинг стратегия
Путь: /var/www/www-root/data/www/systemetech.ru/src/strategies/scalping.py
"""
import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands, AverageTrueRange
from ta.volume import VolumeWeightedAveragePrice
import logging
from typing import Dict

from .base import BaseStrategy, TradingSignal

logger = logging.getLogger(__name__)

class ScalpingStrategy(BaseStrategy):
    """
    Скальпинг стратегия для быстрых сделок
    Работает на малых таймфреймах с жесткими стопами
    """
    
    def __init__(self):
        super().__init__("scalping")
        self.bb_period = 20
        self.bb_std = 2
        self.rsi_period = 7  # Быстрый RSI
        self.min_profit_percent = 0.3  # Минимум 0.3% профита
        self.max_loss_percent = 0.5    # Максимум 0.5% убытка
        self.min_volume_ratio = 1.2   # Минимальный объем
        
    async def analyze(self, df: pd.DataFrame, symbol: str) -> TradingSignal:
        """Анализ для скальпинга"""
        
        if not self.validate_dataframe(df):
            return TradingSignal('WAIT', 0, 0, reason='Недостаточно данных')
        
        try:
            # Рассчитываем индикаторы
            indicators = self._calculate_indicators(df)
            
            # Проверяем условия для скальпинга
            scalp_signal = self._check_scalping_conditions(indicators)
            
            # Принимаем решение
            return self._make_scalping_decision(scalp_signal, indicators)
            
        except Exception as e:
            logger.error(f"Ошибка анализа скальпинга для {symbol}: {e}")
            return TradingSignal('WAIT', 0, 0, reason=f'Ошибка анализа: {e}')
    
    def _calculate_indicators(self, df: pd.DataFrame) -> Dict:
        """Расчет индикаторов для скальпинга"""
        indicators = {}
        
        # Bollinger Bands
        bb = BollingerBands(df['close'], window=self.bb_period, window_dev=self.bb_std)
        indicators['bb_upper'] = bb.bollinger_hband().iloc[-1]
        indicators['bb_lower'] = bb.bollinger_lband().iloc[-1]
        indicators['bb_middle'] = bb.bollinger_mavg().iloc[-1]
        indicators['bb_width'] = bb.bollinger_wband().iloc[-1]
        indicators['bb_percent'] = bb.bollinger_pband().iloc[-1]
        
        # RSI
        rsi = RSIIndicator(df['close'], window=self.rsi_period)
        indicators['rsi'] = rsi.rsi().iloc[-1]
        
        # VWAP
        vwap = VolumeWeightedAveragePrice(df['high'], df['low'], df['close'], df['volume'])
        indicators['vwap'] = vwap.volume_weighted_average_price().iloc[-1]
        
        # ATR для расчета стопов
        atr = AverageTrueRange(df['high'], df['low'], df['close'], window=14)
        indicators['atr'] = atr.average_true_range().iloc[-1]
        indicators['atr_percent'] = (indicators['atr'] / df['close'].iloc[-1]) * 100
        
        # Volume analysis
        indicators['volume_sma'] = df['volume'].rolling(window=20).mean().iloc[-1]
        indicators['volume_ratio'] = df['volume'].iloc[-1] / indicators['volume_sma']
        
        # Price action
        indicators['current_price'] = df['close'].iloc[-1]
        indicators['price_range'] = df['high'].iloc[-1] - df['low'].iloc[-1]
        indicators['candle_body'] = abs(df['close'].iloc[-1] - df['open'].iloc[-1])
        indicators['upper_wick'] = df['high'].iloc[-1] - max(df['close'].iloc[-1], df['open'].iloc[-1])
        indicators['lower_wick'] = min(df['close'].iloc[-1], df['open'].iloc[-1]) - df['low'].iloc[-1]
        
        # Микро-тренд (последние 5 свечей)
        indicators['micro_trend'] = 'UP' if df['close'].iloc[-1] > df['close'].iloc[-5] else 'DOWN'
        
        return indicators
    
    def _check_scalping_conditions(self, indicators: Dict) -> Dict:
        """Проверка условий для скальпинга"""
        signal = {
            'direction': None,
            'strength': 0,
            'entry_type': None,
            'reasons': []
        }
        
        # Проверяем волатильность - для скальпинга нужна умеренная волатильность
        if indicators['atr_percent'] > 3:
            signal['reasons'].append('Слишком высокая волатильность')
            return signal
        
        if indicators['atr_percent'] < 0.5:
            signal['reasons'].append('Слишком низкая волатильность')
            return signal
        
        # Проверяем объем
        if indicators['volume_ratio'] < self.min_volume_ratio:
            signal['reasons'].append('Недостаточный объем')
            return signal
        
        # === УСЛОВИЯ ДЛЯ ПОКУПКИ ===
        
        # 1. Отскок от нижней BB
        if (indicators['bb_percent'] < 0.2 and 
            indicators['rsi'] < 35 and
            indicators['lower_wick'] > indicators['candle_body'] * 1.5):  # Длинная нижняя тень
            
            signal['direction'] = 'BUY'
            signal['entry_type'] = 'BB_BOUNCE'
            signal['strength'] = 0.8
            signal['reasons'].append('Отскок от нижней BB с подтверждением')
        
        # 2. Прорыв VWAP вверх с объемом
        elif (indicators['current_price'] > indicators['vwap'] and
              indicators['current_price'] < indicators['vwap'] * 1.002 and  # Только что пробили
              indicators['volume_ratio'] > 1.5 and
              indicators['micro_trend'] == 'UP'):
            
            signal['direction'] = 'BUY'
            signal['entry_type'] = 'VWAP_BREAK'
            signal['strength'] = 0.7
            signal['reasons'].append('Прорыв VWAP с объемом')
        
        # === УСЛОВИЯ ДЛЯ ПРОДАЖИ ===
        
        # 1. Отскок от верхней BB
        elif (indicators['bb_percent'] > 0.8 and
              indicators['rsi'] > 65 and
              indicators['upper_wick'] > indicators['candle_body'] * 1.5):  # Длинная верхняя тень
            
            signal['direction'] = 'SELL'
            signal['entry_type'] = 'BB_BOUNCE'
            signal['strength'] = 0.8
            signal['reasons'].append('Отскок от верхней BB с подтверждением')
        
        # 2. Пробой VWAP вниз с объемом
        elif (indicators['current_price'] < indicators['vwap'] and
              indicators['current_price'] > indicators['vwap'] * 0.998 and  # Только что пробили
              indicators['volume_ratio'] > 1.5 and
              indicators['micro_trend'] == 'DOWN'):
            
            signal['direction'] = 'SELL'
            signal['entry_type'] = 'VWAP_BREAK'
            signal['strength'] = 0.7
            signal['reasons'].append('Пробой VWAP с объемом')
        
        return signal
    
    def _make_scalping_decision(self, scalp_signal: Dict, indicators: Dict) -> TradingSignal:
        """Принятие решения для скальпинга"""
        
        if not scalp_signal['direction']:
            reason = scalp_signal['reasons'][0] if scalp_signal['reasons'] else 'Нет сигнала'
            return TradingSignal(
                action='WAIT',
                confidence=0,
                price=indicators['current_price'],
                reason=reason
            )
        
        # Расчет жестких уровней для скальпинга
        current_price = indicators['current_price']
        
        if scalp_signal['direction'] == 'BUY':
            # Для покупки
            stop_loss = current_price * (1 - self.max_loss_percent / 100)
            take_profit = current_price * (1 + self.min_profit_percent / 100)
        else:
            # Для продажи
            stop_loss = current_price * (1 + self.max_loss_percent / 100)
            take_profit = current_price * (1 - self.min_profit_percent / 100)
        
        # Проверяем risk/reward
        risk_reward = self.calculate_risk_reward(current_price, stop_loss, take_profit)
        
        if risk_reward < 0.6:  # Для скальпинга допустим меньший R:R
            return TradingSignal(
                action='WAIT',
                confidence=0,
                price=current_price,
                reason=f"Низкий R:R для скальпинга: {risk_reward:.2f}"
            )
        
        # Формируем сигнал
        return TradingSignal(
            action=scalp_signal['direction'],
            confidence=scalp_signal['strength'],
            price=current_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            reason=f"Скальпинг: {scalp_signal['reasons'][0]}",
            risk_reward_ratio=risk_reward,
            indicators=indicators
        )
