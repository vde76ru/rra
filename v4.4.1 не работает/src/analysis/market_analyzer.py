"""
Анализатор рынка
Путь: /var/www/www-root/data/www/systemetech.ru/src/analysis/market_analyzer.py
"""
import logging
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple, Dict, List, Optional
from datetime import datetime, timedelta

from src.exchange.client import exchange_client

logger = logging.getLogger(__name__)

class MarketAnalyzer:
    """Анализ рыночных данных"""
    
    def __init__(self):
        self.exchange = exchange_client
        self.cache = {}  # Кэш данных
        self.cache_ttl = 60  # TTL кэша в секундах
        
    async def analyze_symbol(self, symbol: str) -> Optional[Dict]:
        """Анализ конкретного символа"""
        try:
            # Проверяем кэш
            if self._is_cache_valid(symbol):
                logger.debug(f"Используем кэш для {symbol}")
                return self.cache[symbol]['data']
            
            # Получаем данные
            ohlcv = await self.exchange.fetch_ohlcv(symbol, '5m', 200)
            
            if not ohlcv:
                logger.warning(f"Нет данных для {symbol}")
                return None
            
            # Преобразуем в DataFrame
            df = pd.DataFrame(
                ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            # Получаем текущую цену
            ticker = await self.exchange.fetch_ticker(symbol)
            current_price = ticker['last']
            
            # Рассчитываем дополнительные метрики
            volatility = self.calculate_volatility(df)
            trend = self.detect_trend(df)
            support_resistance = self.find_support_resistance(df)
            volume_profile = self.analyze_volume(df)
            
            result = {
                'df': df,
                'current_price': current_price,
                'volatility': volatility,
                'trend': trend,
                'support': support_resistance['support'],
                'resistance': support_resistance['resistance'],
                'volume_analysis': volume_profile,
                'timestamp': datetime.now()
            }
            
            # Сохраняем в кэш
            self.cache[symbol] = {
                'data': result,
                'timestamp': datetime.now()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка анализа {symbol}: {e}")
            return None
    
    def calculate_volatility(self, df: pd.DataFrame) -> Dict:
        """Расчет волатильности"""
        # Дневная волатильность
        returns = df['close'].pct_change().dropna()
        daily_volatility = returns.std()
        
        # ATR (Average True Range)
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift())
        low_close = abs(df['low'] - df['close'].shift())
        
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=14).mean().iloc[-1]
        
        # Bollinger Bands width
        sma = df['close'].rolling(window=20).mean()
        std = df['close'].rolling(window=20).std()
        bb_width = (std * 2) / sma
        current_bb_width = bb_width.iloc[-1]
        
        return {
            'daily': daily_volatility,
            'atr': atr,
            'bb_width': current_bb_width,
            'is_high': daily_volatility > 0.02  # Высокая волатильность > 2%
        }
    
    def detect_trend(self, df: pd.DataFrame) -> Dict:
        """Определение тренда"""
        # Скользящие средние
        sma_20 = df['close'].rolling(window=20).mean()
        sma_50 = df['close'].rolling(window=50).mean()
        sma_200 = df['close'].rolling(window=200).mean()
        
        current_price = df['close'].iloc[-1]
        
        # Определение тренда по MA
        if current_price > sma_20.iloc[-1] > sma_50.iloc[-1]:
            trend_ma = 'UPTREND'
        elif current_price < sma_20.iloc[-1] < sma_50.iloc[-1]:
            trend_ma = 'DOWNTREND'
        else:
            trend_ma = 'SIDEWAYS'
        
        # Тренд по High/Low
        recent_highs = df['high'].rolling(window=20).max()
        recent_lows = df['low'].rolling(window=20).min()
        
        higher_highs = recent_highs.iloc[-1] > recent_highs.iloc[-20]
        higher_lows = recent_lows.iloc[-1] > recent_lows.iloc[-20]
        
        if higher_highs and higher_lows:
            trend_hl = 'UPTREND'
        elif not higher_highs and not higher_lows:
            trend_hl = 'DOWNTREND'
        else:
            trend_hl = 'SIDEWAYS'
        
        # Сила тренда
        trend_strength = abs(sma_20.iloc[-1] - sma_50.iloc[-1]) / sma_50.iloc[-1] * 100
        
        return {
            'direction': trend_ma,
            'direction_hl': trend_hl,
            'strength': trend_strength,
            'sma_20': sma_20.iloc[-1],
            'sma_50': sma_50.iloc[-1],
            'sma_200': sma_200.iloc[-1] if not pd.isna(sma_200.iloc[-1]) else None
        }
    
    def find_support_resistance(self, df: pd.DataFrame) -> Dict:
        """Поиск уровней поддержки и сопротивления"""
        # Простой метод - локальные минимумы и максимумы
        window = 20
        
        # Поддержка - локальные минимумы
        lows = df['low'].rolling(window=window).min()
        support_levels = []
        
        for i in range(window, len(df) - window):
            if df['low'].iloc[i] == lows.iloc[i]:
                support_levels.append(df['low'].iloc[i])
        
        # Сопротивление - локальные максимумы
        highs = df['high'].rolling(window=window).max()
        resistance_levels = []
        
        for i in range(window, len(df) - window):
            if df['high'].iloc[i] == highs.iloc[i]:
                resistance_levels.append(df['high'].iloc[i])
        
        # Кластеризация уровней
        current_price = df['close'].iloc[-1]
        
        # Ближайшие уровни
        nearest_support = None
        nearest_resistance = None
        
        if support_levels:
            below_price = [s for s in support_levels if s < current_price]
            if below_price:
                nearest_support = max(below_price)
        
        if resistance_levels:
            above_price = [r for r in resistance_levels if r > current_price]
            if above_price:
                nearest_resistance = min(above_price)
        
        return {
            'support': nearest_support,
            'resistance': nearest_resistance,
            'all_supports': sorted(set(support_levels))[-5:],  # Последние 5 уровней
            'all_resistances': sorted(set(resistance_levels))[:5]  # Первые 5 уровней
        }
    
    def analyze_volume(self, df: pd.DataFrame) -> Dict:
        """Анализ объемов"""
        # Средний объем
        avg_volume = df['volume'].rolling(window=20).mean()
        current_volume = df['volume'].iloc[-1]
        volume_ratio = current_volume / avg_volume.iloc[-1] if avg_volume.iloc[-1] > 0 else 1
        
        # Volume trend
        volume_sma_5 = df['volume'].rolling(window=5).mean()
        volume_sma_20 = df['volume'].rolling(window=20).mean()
        
        volume_trend = 'INCREASING' if volume_sma_5.iloc[-1] > volume_sma_20.iloc[-1] else 'DECREASING'
        
        # Price-Volume correlation
        price_change = df['close'].pct_change()
        volume_change = df['volume'].pct_change()
        correlation = price_change.corr(volume_change)
        
        return {
            'current': current_volume,
            'average': avg_volume.iloc[-1],
            'ratio': volume_ratio,
            'trend': volume_trend,
            'price_correlation': correlation,
            'is_high': volume_ratio > 1.5,
            'is_low': volume_ratio < 0.5
        }
    
    def _is_cache_valid(self, symbol: str) -> bool:
        """Проверка валидности кэша"""
        if symbol not in self.cache:
            return False
        
        cache_time = self.cache[symbol]['timestamp']
        return (datetime.now() - cache_time).total_seconds() < self.cache_ttl