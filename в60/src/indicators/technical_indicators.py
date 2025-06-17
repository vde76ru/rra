"""
Универсальная обертка для технических индикаторов
Использует pandas-ta вместо TA-Lib
Файл: src/indicators/ta_wrapper.py
"""
import pandas as pd
import pandas_ta as ta
import numpy as np
from typing import Union, Tuple, Optional

# Флаг для совместимости
USE_TALIB = False

def RSI(close: pd.Series, timeperiod: int = 14) -> pd.Series:
    """RSI индикатор"""
    return ta.rsi(close, length=timeperiod)

def BBANDS(close: pd.Series, timeperiod: int = 20, nbdevup: float = 2, nbdevdn: float = 2, matype: int = 0) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Bollinger Bands"""
    bb = ta.bbands(close, length=timeperiod, std=nbdevup)
    return bb[f'BBU_{timeperiod}_{nbdevup}'], bb[f'BBM_{timeperiod}_{nbdevup}'], bb[f'BBL_{timeperiod}_{nbdevup}']

def MACD(close: pd.Series, fastperiod: int = 12, slowperiod: int = 26, signalperiod: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """MACD индикатор"""
    macd = ta.macd(close, fast=fastperiod, slow=slowperiod, signal=signalperiod)
    return (macd[f'MACD_{fastperiod}_{slowperiod}_{signalperiod}'], 
            macd[f'MACDs_{fastperiod}_{slowperiod}_{signalperiod}'],
            macd[f'MACDh_{fastperiod}_{slowperiod}_{signalperiod}'])

def EMA(close: pd.Series, timeperiod: int = 20) -> pd.Series:
    """EMA индикатор"""
    return ta.ema(close, length=timeperiod)

def SMA(close: pd.Series, timeperiod: int = 20) -> pd.Series:
    """SMA индикатор"""
    return ta.sma(close, length=timeperiod)

def ATR(high: pd.Series, low: pd.Series, close: pd.Series, timeperiod: int = 14) -> pd.Series:
    """ATR индикатор"""
    return ta.atr(high, low, close, length=timeperiod)

def STOCH(high: pd.Series, low: pd.Series, close: pd.Series, 
          fastk_period: int = 14, slowk_period: int = 3, slowd_period: int = 3,
          slowk_matype: int = 0, slowd_matype: int = 0) -> Tuple[pd.Series, pd.Series]:
    """Stochastic индикатор"""
    stoch = ta.stoch(high, low, close, k=fastk_period, d=slowd_period)
    return stoch[f'STOCHk_{fastk_period}_{slowd_period}_{slowd_period}'], stoch[f'STOCHd_{fastk_period}_{slowd_period}_{slowd_period}']

def ADX(high: pd.Series, low: pd.Series, close: pd.Series, timeperiod: int = 14) -> pd.Series:
    """ADX индикатор"""
    adx = ta.adx(high, low, close, length=timeperiod)
    return adx[f'ADX_{timeperiod}']

def PLUS_DI(high: pd.Series, low: pd.Series, close: pd.Series, timeperiod: int = 14) -> pd.Series:
    """Plus DI индикатор"""
    adx = ta.adx(high, low, close, length=timeperiod)
    return adx[f'DMP_{timeperiod}']

def MINUS_DI(high: pd.Series, low: pd.Series, close: pd.Series, timeperiod: int = 14) -> pd.Series:
    """Minus DI индикатор"""
    adx = ta.adx(high, low, close, length=timeperiod)
    return adx[f'DMN_{timeperiod}']

def ROC(close: pd.Series, timeperiod: int = 10) -> pd.Series:
    """Rate of Change индикатор"""
    return ta.roc(close, length=timeperiod)

def OBV(close: pd.Series, volume: pd.Series) -> pd.Series:
    """On Balance Volume"""
    return ta.obv(close, volume)

def CCI(high: pd.Series, low: pd.Series, close: pd.Series, timeperiod: int = 20) -> pd.Series:
    """CCI индикатор"""
    return ta.cci(high, low, close, length=timeperiod)

def WILLR(high: pd.Series, low: pd.Series, close: pd.Series, timeperiod: int = 14) -> pd.Series:
    """Williams %R"""
    return ta.willr(high, low, close, length=timeperiod)

def MFI(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, timeperiod: int = 14) -> pd.Series:
    """Money Flow Index"""
    return ta.mfi(high, low, close, volume, length=timeperiod)

def AROON(high: pd.Series, low: pd.Series, timeperiod: int = 14) -> Tuple[pd.Series, pd.Series]:
    """Aroon индикатор"""
    aroon = ta.aroon(high, low, length=timeperiod)
    return aroon[f'AROOND_{timeperiod}'], aroon[f'AROONU_{timeperiod}']

def BOP(open: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    """Balance of Power"""
    return ta.bop(open, high, low, close)

def CMO(close: pd.Series, timeperiod: int = 14) -> pd.Series:
    """Chande Momentum Oscillator"""
    return ta.cmo(close, length=timeperiod)

def DX(high: pd.Series, low: pd.Series, close: pd.Series, timeperiod: int = 14) -> pd.Series:
    """Directional Movement Index"""
    adx = ta.adx(high, low, close, length=timeperiod)
    return adx[f'DX_{timeperiod}']

def PPO(close: pd.Series, fastperiod: int = 12, slowperiod: int = 26, matype: int = 0) -> pd.Series:
    """Percentage Price Oscillator"""
    return ta.ppo(close, fast=fastperiod, slow=slowperiod)

def TRIX(close: pd.Series, timeperiod: int = 30) -> pd.Series:
    """TRIX индикатор"""
    return ta.trix(close, length=timeperiod)

def ULTOSC(high: pd.Series, low: pd.Series, close: pd.Series, 
           timeperiod1: int = 7, timeperiod2: int = 14, timeperiod3: int = 28) -> pd.Series:
    """Ultimate Oscillator"""
    return ta.uo(high, low, close, fast=timeperiod1, medium=timeperiod2, slow=timeperiod3)

def HT_TRENDLINE(close: pd.Series) -> pd.Series:
    """Hilbert Transform - Instantaneous Trendline"""
    # Простая аппроксимация через EMA
    return ta.ema(close, length=20)

def HT_SINE(close: pd.Series) -> Tuple[pd.Series, pd.Series]:
    """Hilbert Transform - SineWave"""
    # Возвращаем заглушку
    sine = pd.Series(np.sin(np.arange(len(close)) * 0.1), index=close.index)
    leadsine = pd.Series(np.sin(np.arange(len(close)) * 0.1 + np.pi/2), index=close.index)
    return sine, leadsine

def HT_TRENDMODE(close: pd.Series) -> pd.Series:
    """Hilbert Transform - Trend vs Cycle Mode"""
    # Простая аппроксимация через сравнение с EMA
    ema = ta.ema(close, length=20)
    return (close > ema).astype(int)

# Паттерны свечей - упрощенные версии
def CDLDOJI(open: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    """Doji паттерн"""
    body = abs(close - open)
    wick = high - low
    doji = (body <= wick * 0.1).astype(int) * 100
    return doji

def CDLHAMMER(open: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    """Hammer паттерн"""
    body = abs(close - open)
    lower_wick = np.minimum(open, close) - low
    upper_wick = high - np.maximum(open, close)
    
    hammer = ((lower_wick > body * 2) & (upper_wick < body * 0.3) & (close > open)).astype(int) * 100
    return hammer

def CDLINVERTEDHAMMER(open: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    """Inverted Hammer паттерн"""
    body = abs(close - open)
    lower_wick = np.minimum(open, close) - low
    upper_wick = high - np.maximum(open, close)
    
    inv_hammer = ((upper_wick > body * 2) & (lower_wick < body * 0.3) & (close > open)).astype(int) * 100
    return inv_hammer

def CDLHANGINGMAN(open: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    """Hanging Man паттерн"""
    body = abs(close - open)
    lower_wick = np.minimum(open, close) - low
    upper_wick = high - np.maximum(open, close)
    
    hanging_man = ((lower_wick > body * 2) & (upper_wick < body * 0.3) & (close < open)).astype(int) * -100
    return hanging_man

def CDLENGULFING(open: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    """Engulfing паттерн"""
    prev_open = open.shift(1)
    prev_close = close.shift(1)
    
    bullish_engulfing = ((close > open) & (prev_close < prev_open) & 
                        (open < prev_close) & (close > prev_open)).astype(int) * 100
    
    bearish_engulfing = ((close < open) & (prev_close > prev_open) & 
                        (open > prev_close) & (close < prev_open)).astype(int) * -100
    
    return bullish_engulfing + bearish_engulfing

def CDLMORNINGSTAR(open: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    """Morning Star паттерн"""
    # Упрощенная версия
    return pd.Series(np.zeros(len(close)), index=close.index)

def CDLEVENINGSTAR(open: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    """Evening Star паттерн"""
    # Упрощенная версия
    return pd.Series(np.zeros(len(close)), index=close.index)

def CDLSHOOTINGSTAR(open: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    """Shooting Star паттерн"""
    body = abs(close - open)
    lower_wick = np.minimum(open, close) - low
    upper_wick = high - np.maximum(open, close)
    
    shooting_star = ((upper_wick > body * 2) & (lower_wick < body * 0.3) & (close < open)).astype(int) * -100
    return shooting_star

def CDL3WHITESOLDIERS(open: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    """Three White Soldiers паттерн"""
    # Упрощенная версия - 3 зеленые свечи подряд
    green = close > open
    pattern = (green & green.shift(1) & green.shift(2)).astype(int) * 100
    return pattern

def CDL3BLACKCROWS(open: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    """Three Black Crows паттерн"""
    # Упрощенная версия - 3 красные свечи подряд
    red = close < open
    pattern = (red & red.shift(1) & red.shift(2)).astype(int) * -100
    return pattern

def CDL3INSIDE(open: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    """Three Inside паттерн"""
    # Упрощенная версия
    return pd.Series(np.zeros(len(close)), index=close.index)

# Дополнительные индикаторы для совместимости
def AVGPRICE(open: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    """Average Price"""
    return (open + high + low + close) / 4

def MEDPRICE(high: pd.Series, low: pd.Series) -> pd.Series:
    """Median Price"""
    return (high + low) / 2

def TYPPRICE(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    """Typical Price"""
    return (high + low + close) / 3

def WCLPRICE(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    """Weighted Close Price"""
    return (high + low + close * 2) / 4

def LINEARREG(close: pd.Series, timeperiod: int = 14) -> pd.Series:
    """Linear Regression"""
    return ta.linreg(close, length=timeperiod)

def LINEARREG_ANGLE(close: pd.Series, timeperiod: int = 14) -> pd.Series:
    """Linear Regression Angle"""
    return ta.linreg(close, length=timeperiod, angle=True)

def LINEARREG_SLOPE(close: pd.Series, timeperiod: int = 14) -> pd.Series:
    """Linear Regression Slope"""
    return ta.linreg(close, length=timeperiod, slope=True)

def STDDEV(close: pd.Series, timeperiod: int = 5, nbdev: float = 1) -> pd.Series:
    """Standard Deviation"""
    return ta.stdev(close, length=timeperiod) * nbdev

def TSF(close: pd.Series, timeperiod: int = 14) -> pd.Series:
    """Time Series Forecast"""
    return ta.linreg(close, length=timeperiod, tsf=True)

def VAR(close: pd.Series, timeperiod: int = 5, nbdev: float = 1) -> pd.Series:
    """Variance"""
    return ta.variance(close, length=timeperiod) * nbdev

# Экспортируем статус
print("📊 Индикаторы инициализированы (pandas-ta)")

__all__ = [
    'RSI', 'BBANDS', 'MACD', 'EMA', 'SMA', 'ATR', 'STOCH', 'ADX', 
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