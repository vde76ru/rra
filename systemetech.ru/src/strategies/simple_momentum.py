import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator
import logging

logger = logging.getLogger(__name__)

class SimpleMomentumStrategy:
    """Простая momentum стратегия с защитой от шума"""
    
    def __init__(self):
        self.rsi_period = 14
        self.ema_fast = 9
        self.ema_slow = 21
        self.rsi_oversold = 30
        self.rsi_overbought = 70
        
    def analyze(self, df: pd.DataFrame) -> dict:
        """Анализ данных и генерация сигнала"""
        if len(df) < 50:
            return {'signal': 'WAIT', 'confidence': 0}
        
        # Расчет индикаторов
        df['rsi'] = RSIIndicator(df['close'], window=self.rsi_period).rsi()
        df['ema_fast'] = EMAIndicator(df['close'], window=self.ema_fast).ema_indicator()
        df['ema_slow'] = EMAIndicator(df['close'], window=self.ema_slow).ema_indicator()
        
        # Последние значения
        current_rsi = df['rsi'].iloc[-1]
        current_ema_fast = df['ema_fast'].iloc[-1]
        current_ema_slow = df['ema_slow'].iloc[-1]
        current_volume = df['volume'].iloc[-1]
        avg_volume = df['volume'].rolling(20).mean().iloc[-1]
        
        signal = 'WAIT'
        confidence = 0.0
        
        # Условия для покупки
        if (current_ema_fast > current_ema_slow and
            self.rsi_oversold < current_rsi < 50 and
            current_volume > avg_volume * 1.2):
            
            signal = 'BUY'
            confidence = min(0.8, (current_volume / avg_volume) * 0.4 + 0.4)
            
        # Условия для продажи
        elif (current_ema_fast < current_ema_slow and
              50 < current_rsi < self.rsi_overbought and
              current_volume > avg_volume):
            
            signal = 'SELL'
            confidence = min(0.8, (current_volume / avg_volume) * 0.4 + 0.4)
        
        return {
            'signal': signal,
            'confidence': confidence,
            'rsi': current_rsi,
            'ema_diff': current_ema_fast - current_ema_slow,
            'volume_ratio': current_volume / avg_volume if avg_volume > 0 else 1
        }