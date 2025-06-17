"""
Пакет индикаторов для технического анализа
Путь: src/indicators/__init__.py

Этот модуль обеспечивает совместимость с различными библиотеками
технических индикаторов (TA-Lib, pandas-ta) через единый интерфейс.
"""

# Импортируем все функции из ta_wrapper
from .ta_wrapper import *

# Создаем класс-обертку для совместимости с кодом, который ожидает TechnicalIndicators
class TechnicalIndicators:
    """
    Класс-обертка для совместимости с существующим кодом
    
    Этот класс предоставляет статические методы, которые используют
    функции из ta_wrapper.py для расчета технических индикаторов.
    """
    
    @staticmethod
    def sma(data, period=20):
        """Simple Moving Average через ta_wrapper"""
        return SMA(data, timeperiod=period)
    
    @staticmethod
    def ema(data, period=20):
        """Exponential Moving Average через ta_wrapper"""
        return EMA(data, timeperiod=period)
    
    @staticmethod
    def rsi(data, period=14):
        """RSI через ta_wrapper"""
        return RSI(data, timeperiod=period)
    
    @staticmethod
    def macd(data, fast=12, slow=26, signal=9):
        """MACD через ta_wrapper"""
        macd_line, signal_line, histogram = MACD(data, fastperiod=fast, slowperiod=slow, signalperiod=signal)
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }
    
    @staticmethod
    def bollinger_bands(data, period=20, std_dev=2.0):
        """Bollinger Bands через ta_wrapper"""
        upper, middle, lower = BBANDS(data, timeperiod=period, nbdevup=std_dev, nbdevdn=std_dev)
        return {
            'upper': upper,
            'middle': middle,
            'lower': lower
        }
    
    @staticmethod
    def stochastic(high, low, close, k_period=14, d_period=3):
        """Stochastic Oscillator через ta_wrapper"""
        k_percent, d_percent = STOCH(high, low, close, fastk_period=k_period, slowd_period=d_period)
        return {
            'k': k_percent,
            'd': d_percent
        }
    
    @staticmethod
    def atr(high, low, close, period=14):
        """Average True Range через ta_wrapper"""
        return ATR(high, low, close, timeperiod=period)
    
    @staticmethod
    def williams_r(high, low, close, period=14):
        """Williams %R через ta_wrapper"""
        return WILLR(high, low, close, timeperiod=period)
    
    @classmethod
    def get_all_indicators(cls, high, low, close, volume=None):
        """
        Получить все основные индикаторы
        
        Это метод для совместимости с существующим кодом
        """
        indicators = {}
        
        try:
            # Скользящие средние
            indicators['sma_20'] = cls.sma(close, 20)
            indicators['sma_50'] = cls.sma(close, 50)
            indicators['ema_12'] = cls.ema(close, 12)
            indicators['ema_26'] = cls.ema(close, 26)
            
            # Осцилляторы
            indicators['rsi'] = cls.rsi(close)
            indicators['williams_r'] = cls.williams_r(high, low, close)
            
            # MACD
            indicators['macd'] = cls.macd(close)
            
            # Bollinger Bands
            indicators['bollinger'] = cls.bollinger_bands(close)
            
            # Stochastic
            indicators['stochastic'] = cls.stochastic(high, low, close)
            
            # ATR
            indicators['atr'] = cls.atr(high, low, close)
            
            if volume is not None:
                # Индикаторы с объемом
                indicators['obv'] = OBV(close, volume)
                indicators['mfi'] = MFI(high, low, close, volume)
                
        except Exception as e:
            indicators['error'] = str(e)
        
        return indicators

# Экспортируем все, что нужно
__all__ = [
    'TechnicalIndicators',  # Основной класс для совместимости
    # Функции из ta_wrapper
    'RSI', 'BBANDS', 'MACD', 'EMA', 'SMA', 'ATR', 'STOCH', 'ADX',
    'PLUS_DI', 'MINUS_DI', 'ROC', 'OBV', 'CCI', 'WILLR', 'MFI',
    'AROON', 'BOP', 'CMO', 'DX', 'PPO', 'TRIX', 'ULTOSC',
    'HT_TRENDLINE', 'HT_SINE', 'HT_TRENDMODE',
    # Паттерны свечей
    'CDLDOJI', 'CDLHAMMER', 'CDLINVERTEDHAMMER', 'CDLHANGINGMAN',
    'CDLENGULFING', 'CDLMORNINGSTAR', 'CDLEVENINGSTAR', 'CDLSHOOTINGSTAR',
    'CDL3WHITESOLDIERS', 'CDL3BLACKCROWS', 'CDL3INSIDE',
    # Ценовые индикаторы
    'AVGPRICE', 'MEDPRICE', 'TYPPRICE', 'WCLPRICE',
    # Статистические функции
    'LINEARREG', 'LINEARREG_ANGLE', 'LINEARREG_SLOPE',
    'STDDEV', 'TSF', 'VAR', 'USE_TALIB'
]

__version__ = "1.0.0"

# Сообщение для отладки
print("✅ Модуль indicators инициализирован с TechnicalIndicators классом")