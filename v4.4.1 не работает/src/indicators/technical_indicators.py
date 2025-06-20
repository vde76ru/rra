"""
Модуль технических индикаторов
Файл: src/indicators/technical_indicators.py
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Tuple, List
import logging

# Проверяем наличие pandas_ta
try:
    import pandas_ta as ta
    HAS_PANDAS_TA = True
except ImportError:
    HAS_PANDAS_TA = False
    print("⚠️ pandas_ta не установлен, используем базовые индикаторы")

# Импортируем наш wrapper с fallback реализациями
from .ta_wrapper import *

logger = logging.getLogger(__name__)


class TechnicalIndicators:
    """Класс для расчета технических индикаторов"""
    
    def __init__(self):
        """Инициализация индикаторов"""
        self.has_pandas_ta = HAS_PANDAS_TA
        logger.info(f"✅ TechnicalIndicators инициализирован (pandas_ta: {self.has_pandas_ta})")
    
    def calculate_all(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Рассчитать все индикаторы для датафрейма
        
        Args:
            df: DataFrame с колонками open, high, low, close, volume
            
        Returns:
            DataFrame с добавленными индикаторами
        """
        if df.empty or len(df) < 30:
            return df
        
        # Копируем датафрейм
        result = df.copy()
        
        try:
            # Базовые скользящие средние
            result['sma_10'] = self.sma(result['close'], 10)
            result['sma_20'] = self.sma(result['close'], 20)
            result['sma_50'] = self.sma(result['close'], 50)
            result['ema_12'] = self.ema(result['close'], 12)
            result['ema_26'] = self.ema(result['close'], 26)
            
            # RSI
            result['rsi'] = self.rsi(result['close'])
            
            # MACD
            macd, signal, hist = self.macd(result['close'])
            result['macd'] = macd
            result['macd_signal'] = signal
            result['macd_hist'] = hist
            
            # Bollinger Bands
            upper, middle, lower = self.bollinger_bands(result['close'])
            result['bb_upper'] = upper
            result['bb_middle'] = middle
            result['bb_lower'] = lower
            
            # ATR
            result['atr'] = self.atr(result['high'], result['low'], result['close'])
            
            # Stochastic
            k, d = self.stochastic(result['high'], result['low'], result['close'])
            result['stoch_k'] = k
            result['stoch_d'] = d
            
            # Volume indicators
            if 'volume' in result.columns:
                result['volume_sma'] = self.sma(result['volume'], 20)
                result['obv'] = self.obv(result['close'], result['volume'])
            
        except Exception as e:
            logger.error(f"Ошибка расчета индикаторов: {e}")
        
        return result
    
    def sma(self, series: pd.Series, period: int) -> pd.Series:
        """Simple Moving Average"""
        if self.has_pandas_ta:
            return ta.sma(series, length=period)
        else:
            return pd.Series(SMA(series.values, timeperiod=period), index=series.index)
    
    def ema(self, series: pd.Series, period: int) -> pd.Series:
        """Exponential Moving Average"""
        if self.has_pandas_ta:
            return ta.ema(series, length=period)
        else:
            return pd.Series(EMA(series.values, timeperiod=period), index=series.index)
    
    def rsi(self, series: pd.Series, period: int = 14) -> pd.Series:
        """Relative Strength Index"""
        if self.has_pandas_ta:
            return ta.rsi(series, length=period)
        else:
            return pd.Series(RSI(series.values, timeperiod=period), index=series.index)
    
    def macd(self, series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """MACD indicator"""
        if self.has_pandas_ta:
            result = ta.macd(series, fast=fast, slow=slow, signal=signal)
            return (
                result[f'MACD_{fast}_{slow}_{signal}'],
                result[f'MACDs_{fast}_{slow}_{signal}'],
                result[f'MACDh_{fast}_{slow}_{signal}']
            )
        else:
            macd_line, signal_line, histogram = MACD(series.values, fastperiod=fast, slowperiod=slow, signalperiod=signal)
            return (
                pd.Series(macd_line, index=series.index),
                pd.Series(signal_line, index=series.index),
                pd.Series(histogram, index=series.index)
            )
    
    def bollinger_bands(self, series: pd.Series, period: int = 20, std: int = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Bollinger Bands"""
        if self.has_pandas_ta:
            result = ta.bbands(series, length=period, std=std)
            return (
                result[f'BBU_{period}_{std}'],
                result[f'BBM_{period}_{std}'],
                result[f'BBL_{period}_{std}']
            )
        else:
            upper, middle, lower = BBANDS(series.values, timeperiod=period, nbdevup=std, nbdevdn=std)
            return (
                pd.Series(upper, index=series.index),
                pd.Series(middle, index=series.index),
                pd.Series(lower, index=series.index)
            )
    
    def atr(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Average True Range"""
        if self.has_pandas_ta:
            return ta.atr(high, low, close, length=period)
        else:
            return pd.Series(ATR(high.values, low.values, close.values, timeperiod=period), index=close.index)
    
    def stochastic(self, high: pd.Series, low: pd.Series, close: pd.Series, 
                   k_period: int = 14, d_period: int = 3) -> Tuple[pd.Series, pd.Series]:
        """Stochastic Oscillator"""
        if self.has_pandas_ta:
            result = ta.stoch(high, low, close, k=k_period, d=d_period)
            return (
                result[f'STOCHk_{k_period}_{d_period}_3'],
                result[f'STOCHd_{k_period}_{d_period}_3']
            )
        else:
            k, d = STOCH(high.values, low.values, close.values, 
                         fastk_period=k_period, slowk_period=d_period, 
                         slowd_period=d_period)
            return (
                pd.Series(k, index=close.index),
                pd.Series(d, index=close.index)
            )
    
    def obv(self, close: pd.Series, volume: pd.Series) -> pd.Series:
        """On Balance Volume"""
        if self.has_pandas_ta:
            return ta.obv(close, volume)
        else:
            return pd.Series(OBV(close.values, volume.values), index=close.index)
    
    def adx(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Average Directional Index"""
        if self.has_pandas_ta:
            return ta.adx(high, low, close, length=period)['ADX_14']
        else:
            return pd.Series(ADX(high.values, low.values, close.values, timeperiod=period), index=close.index)
    
    def calculate_signals(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Рассчитать торговые сигналы на основе индикаторов
        
        Returns:
            Словарь с сигналами и их силой
        """
        signals = {
            'rsi': 0,
            'macd': 0,
            'bb': 0,
            'sma': 0,
            'overall': 0
        }
        
        if df.empty or len(df) < 50:
            return signals
        
        try:
            last_row = df.iloc[-1]
            
            # RSI сигналы
            if 'rsi' in df.columns:
                if last_row['rsi'] < 30:
                    signals['rsi'] = 1  # Oversold - buy signal
                elif last_row['rsi'] > 70:
                    signals['rsi'] = -1  # Overbought - sell signal
            
            # MACD сигналы
            if 'macd' in df.columns and 'macd_signal' in df.columns:
                if last_row['macd'] > last_row['macd_signal']:
                    signals['macd'] = 1
                else:
                    signals['macd'] = -1
            
            # Bollinger Bands сигналы
            if all(col in df.columns for col in ['bb_upper', 'bb_lower', 'close']):
                if last_row['close'] < last_row['bb_lower']:
                    signals['bb'] = 1  # Price below lower band - buy
                elif last_row['close'] > last_row['bb_upper']:
                    signals['bb'] = -1  # Price above upper band - sell
            
            # SMA сигналы
            if all(col in df.columns for col in ['sma_10', 'sma_20']):
                if last_row['sma_10'] > last_row['sma_20']:
                    signals['sma'] = 1
                else:
                    signals['sma'] = -1
            
            # Общий сигнал
            total_signal = sum(signals.values()) - signals['overall']
            signals['overall'] = 1 if total_signal > 1 else (-1 if total_signal < -1 else 0)
            
        except Exception as e:
            logger.error(f"Ошибка расчета сигналов: {e}")
        
        return signals


# Создаем глобальный экземпляр для удобства
indicators = TechnicalIndicators()

# Экспорт
__all__ = ['TechnicalIndicators', 'indicators']
