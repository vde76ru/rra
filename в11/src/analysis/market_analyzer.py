"""Анализатор рынка"""
import logging
from typing import Dict, List
import pandas as pd
from ..exchange.client import exchange_client

logger = logging.getLogger(__name__)

class MarketAnalyzer:
    """Анализ рыночных данных"""
    
    def __init__(self):
        self.exchange = exchange_client
    
    async def analyze_market(self, symbols: List[str]) -> Dict[str, pd.DataFrame]:
        """Анализ рынка для списка символов"""
        market_data = {}
        
        for symbol in symbols:
            try:
                # Получаем исторические данные
                ohlcv = await self.exchange.fetch_ohlcv(symbol, '5m', 200)
                
                # Преобразуем в DataFrame
                df = pd.DataFrame(
                    ohlcv,
                    columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
                )
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('timestamp', inplace=True)
                
                market_data[symbol] = df
                
            except Exception as e:
                logger.error(f"Ошибка анализа {symbol}: {e}")
        
        return market_data
    
    def calculate_volatility(self, df: pd.DataFrame) -> float:
        """Расчет волатильности"""
        returns = df['close'].pct_change().dropna()
        return returns.std() * (252 ** 0.5)  # Годовая волатильность
    
    def detect_trend(self, df: pd.DataFrame) -> str:
        """Определение тренда"""
        sma_short = df['close'].rolling(window=20).mean()
        sma_long = df['close'].rolling(window=50).mean()
        
        if sma_short.iloc[-1] > sma_long.iloc[-1]:
            return 'UPTREND'
        elif sma_short.iloc[-1] < sma_long.iloc[-1]:
            return 'DOWNTREND'
        else:
            return 'SIDEWAYS'
