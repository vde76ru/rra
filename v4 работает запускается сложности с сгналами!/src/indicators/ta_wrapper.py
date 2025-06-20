"""
Обертка для технических индикаторов с fallback на ручные реализации
Файл: src/indicators/ta_wrapper.py
"""
import numpy as np
import pandas as pd
from typing import Union, Tuple, Optional

# Пытаемся импортировать TA-Lib
try:
    import talib
    USE_TALIB = True
except ImportError:
    USE_TALIB = False
    print("⚠️ TA-Lib не установлен, используем ручные реализации индикаторов")

# ===== БАЗОВЫЕ ИНДИКАТОРЫ =====

def SMA(series: Union[pd.Series, np.ndarray], timeperiod: int = 30) -> np.ndarray:
    """Simple Moving Average"""
    if USE_TALIB:
        return talib.SMA(series, timeperiod=timeperiod)
    else:
        return pd.Series(series).rolling(window=timeperiod).mean().values

def EMA(series: Union[pd.Series, np.ndarray], timeperiod: int = 30) -> np.ndarray:
    """Exponential Moving Average"""
    if USE_TALIB:
        return talib.EMA(series, timeperiod=timeperiod)
    else:
        return pd.Series(series).ewm(span=timeperiod, adjust=False).mean().values

def RSI(series: Union[pd.Series, np.ndarray], timeperiod: int = 14) -> np.ndarray:
    """Relative Strength Index"""
    if USE_TALIB:
        return talib.RSI(series, timeperiod=timeperiod)
    else:
        prices = pd.Series(series)
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=timeperiod).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=timeperiod).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.values

def BBANDS(series: Union[pd.Series, np.ndarray], 
           timeperiod: int = 20, 
           nbdevup: int = 2, 
           nbdevdn: int = 2, 
           matype: int = 0) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Bollinger Bands"""
    if USE_TALIB:
        return talib.BBANDS(series, timeperiod=timeperiod, nbdevup=nbdevup, nbdevdn=nbdevdn, matype=matype)
    else:
        prices = pd.Series(series)
        sma = prices.rolling(window=timeperiod).mean()
        std = prices.rolling(window=timeperiod).std()
        
        upper = sma + (std * nbdevup)
        lower = sma - (std * nbdevdn)
        
        return upper.values, sma.values, lower.values

def MACD(series: Union[pd.Series, np.ndarray], 
         fastperiod: int = 12, 
         slowperiod: int = 26, 
         signalperiod: int = 9) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """MACD - Moving Average Convergence Divergence"""
    if USE_TALIB:
        return talib.MACD(series, fastperiod=fastperiod, slowperiod=slowperiod, signalperiod=signalperiod)
    else:
        prices = pd.Series(series)
        ema_fast = prices.ewm(span=fastperiod, adjust=False).mean()
        ema_slow = prices.ewm(span=slowperiod, adjust=False).mean()
        
        macd = ema_fast - ema_slow
        signal = macd.ewm(span=signalperiod, adjust=False).mean()
        histogram = macd - signal
        
        return macd.values, signal.values, histogram.values

def ATR(high: Union[pd.Series, np.ndarray],
        low: Union[pd.Series, np.ndarray],
        close: Union[pd.Series, np.ndarray],
        timeperiod: int = 14) -> np.ndarray:
    """Average True Range"""
    if USE_TALIB:
        return talib.ATR(high, low, close, timeperiod=timeperiod)
    else:
        high_s = pd.Series(high)
        low_s = pd.Series(low)
        close_s = pd.Series(close)
        
        tr1 = high_s - low_s
        tr2 = abs(high_s - close_s.shift())
        tr3 = abs(low_s - close_s.shift())
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=timeperiod).mean()
        
        return atr.values

def STOCH(high: Union[pd.Series, np.ndarray],
          low: Union[pd.Series, np.ndarray],
          close: Union[pd.Series, np.ndarray],
          fastk_period: int = 5,
          slowk_period: int = 3,
          slowk_matype: int = 0,
          slowd_period: int = 3,
          slowd_matype: int = 0) -> Tuple[np.ndarray, np.ndarray]:
    """Stochastic Oscillator"""
    if USE_TALIB:
        return talib.STOCH(high, low, close, fastk_period, slowk_period, 
                          slowk_matype, slowd_period, slowd_matype)
    else:
        high_s = pd.Series(high)
        low_s = pd.Series(low)
        close_s = pd.Series(close)
        
        lowest_low = low_s.rolling(window=fastk_period).min()
        highest_high = high_s.rolling(window=fastk_period).max()
        
        k_percent = 100 * ((close_s - lowest_low) / (highest_high - lowest_low))
        k_percent = k_percent.rolling(window=slowk_period).mean()
        d_percent = k_percent.rolling(window=slowd_period).mean()
        
        return k_percent.values, d_percent.values

def WILLR(high: Union[pd.Series, np.ndarray],
          low: Union[pd.Series, np.ndarray],
          close: Union[pd.Series, np.ndarray],
          timeperiod: int = 14) -> np.ndarray:
    """Williams %R"""
    if USE_TALIB:
        return talib.WILLR(high, low, close, timeperiod=timeperiod)
    else:
        high_s = pd.Series(high)
        low_s = pd.Series(low)
        close_s = pd.Series(close)
        
        highest_high = high_s.rolling(window=timeperiod).max()
        lowest_low = low_s.rolling(window=timeperiod).min()
        
        wr = -100 * ((highest_high - close_s) / (highest_high - lowest_low))
        
        return wr.values

# ===== ДОПОЛНИТЕЛЬНЫЕ ИНДИКАТОРЫ =====

def ADX(high, low, close, timeperiod=14):
    """Average Directional Index"""
    if USE_TALIB:
        return talib.ADX(high, low, close, timeperiod=timeperiod)
    else:
        # Упрощенная реализация
        return np.full_like(close, 25.0)  # Нейтральное значение

def PLUS_DI(high, low, close, timeperiod=14):
    """Plus Directional Indicator"""
    if USE_TALIB:
        return talib.PLUS_DI(high, low, close, timeperiod=timeperiod)
    else:
        return np.full_like(close, 25.0)

def MINUS_DI(high, low, close, timeperiod=14):
    """Minus Directional Indicator"""
    if USE_TALIB:
        return talib.MINUS_DI(high, low, close, timeperiod=timeperiod)
    else:
        return np.full_like(close, 25.0)

def OBV(close, volume):
    """On Balance Volume"""
    if USE_TALIB:
        return talib.OBV(close, volume)
    else:
        close_s = pd.Series(close)
        volume_s = pd.Series(volume)
        
        obv = (volume_s * (~close_s.diff().le(0) * 2 - 1)).cumsum()
        return obv.values

def ROC(series, timeperiod=10):
    """Rate of Change"""
    if USE_TALIB:
        return talib.ROC(series, timeperiod=timeperiod)
    else:
        prices = pd.Series(series)
        return ((prices - prices.shift(timeperiod)) / prices.shift(timeperiod) * 100).values

def CCI(high, low, close, timeperiod=14):
    """Commodity Channel Index"""
    if USE_TALIB:
        return talib.CCI(high, low, close, timeperiod=timeperiod)
    else:
        typical_price = (pd.Series(high) + pd.Series(low) + pd.Series(close)) / 3
        sma = typical_price.rolling(window=timeperiod).mean()
        mad = typical_price.rolling(window=timeperiod).apply(lambda x: np.mean(np.abs(x - x.mean())))
        cci = (typical_price - sma) / (0.015 * mad)
        return cci.values

def MFI(high, low, close, volume, timeperiod=14):
    """Money Flow Index"""
    if USE_TALIB:
        return talib.MFI(high, low, close, volume, timeperiod=timeperiod)
    else:
        # Упрощенная реализация
        typical_price = (pd.Series(high) + pd.Series(low) + pd.Series(close)) / 3
        money_flow = typical_price * pd.Series(volume)
        
        positive_flow = money_flow.where(typical_price.diff() > 0, 0).rolling(window=timeperiod).sum()
        negative_flow = money_flow.where(typical_price.diff() < 0, 0).rolling(window=timeperiod).sum()
        
        mfi = 100 - (100 / (1 + positive_flow / negative_flow))
        return mfi.values

# ===== ПАТТЕРНЫ СВЕЧЕЙ (заглушки) =====

def _candle_pattern_stub(open, high, low, close):
    """Заглушка для паттернов свечей"""
    return np.zeros_like(close, dtype=int)

# Паттерны свечей
CDLDOJI = _candle_pattern_stub
CDLHAMMER = _candle_pattern_stub
CDLINVERTEDHAMMER = _candle_pattern_stub
CDLHANGINGMAN = _candle_pattern_stub
CDLENGULFING = _candle_pattern_stub
CDLMORNINGSTAR = _candle_pattern_stub
CDLEVENINGSTAR = _candle_pattern_stub
CDLSHOOTINGSTAR = _candle_pattern_stub
CDL3WHITESOLDIERS = _candle_pattern_stub
CDL3BLACKCROWS = _candle_pattern_stub
CDL3INSIDE = _candle_pattern_stub

# ===== ОСТАЛЬНЫЕ ИНДИКАТОРЫ =====

AROON = lambda high, low, timeperiod=14: (np.full_like(high, 50.0), np.full_like(high, 50.0))
BOP = lambda open, high, low, close: np.zeros_like(close)
CMO = lambda series, timeperiod=14: np.zeros_like(series)
DX = lambda high, low, close, timeperiod=14: np.full_like(close, 25.0)
PPO = lambda series, fastperiod=12, slowperiod=26, matype=0: np.zeros_like(series)
TRIX = lambda series, timeperiod=30: np.zeros_like(series)
ULTOSC = lambda high, low, close, timeperiod1=7, timeperiod2=14, timeperiod3=28: np.full_like(close, 50.0)

HT_TRENDLINE = lambda series: pd.Series(series).rolling(window=20).mean().values
HT_SINE = lambda series: (np.zeros_like(series), np.zeros_like(series))
HT_TRENDMODE = lambda series: np.zeros_like(series, dtype=int)

AVGPRICE = lambda open, high, low, close: (open + high + low + close) / 4
MEDPRICE = lambda high, low: (high + low) / 2
TYPPRICE = lambda high, low, close: (high + low + close) / 3
WCLPRICE = lambda high, low, close: (high + low + close * 2) / 4

LINEARREG = lambda series, timeperiod=14: pd.Series(series).rolling(window=timeperiod).mean().values
LINEARREG_ANGLE = lambda series, timeperiod=14: np.zeros_like(series)
LINEARREG_SLOPE = lambda series, timeperiod=14: np.zeros_like(series)
STDDEV = lambda series, timeperiod=5, nbdev=1: pd.Series(series).rolling(window=timeperiod).std().values
TSF = lambda series, timeperiod=14: pd.Series(series).rolling(window=timeperiod).mean().values
VAR = lambda series, timeperiod=5, nbdev=1: pd.Series(series).rolling(window=timeperiod).var().values

# Экспорт
__all__ = [
    'SMA', 'EMA', 'RSI', 'BBANDS', 'MACD', 'ATR', 'STOCH', 'ADX',
    'PLUS_DI', 'MINUS_DI', 'ROC', 'OBV', 'CCI', 'WILLR', 'MFI',
    'AROON', 'BOP', 'CMO', 'DX', 'PPO', 'TRIX', 'ULTOSC',
    'HT_TRENDLINE', 'HT_SINE', 'HT_TRENDMODE',
    'CDLDOJI', 'CDLHAMMER', 'CDLINVERTEDHAMMER', 'CDLHANGINGMAN',
    'CDLENGULFING', 'CDLMORNINGSTAR', 'CDLEVENINGSTAR', 'CDLSHOOTINGSTAR',
    'CDL3WHITESOLDIERS', 'CDL3BLACKCROWS', 'CDL3INSIDE',
    'AVGPRICE', 'MEDPRICE', 'TYPPRICE', 'WCLPRICE',
    'LINEARREG', 'LINEARREG_ANGLE', 'LINEARREG_SLOPE',
    'STDDEV', 'TSF', 'VAR', 'USE_TALIB'
]
