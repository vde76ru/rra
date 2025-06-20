"""
Feature Engineering для ML моделей криптотрейдинга
Файл: src/ml/features/feature_engineering.py
"""
import numpy as np
import pandas as pd
import pandas_ta as ta
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import asyncio
from sqlalchemy.orm import Session

from ...core.database import SessionLocal
from ...core.models import Candle, MarketCondition, Signal, Trade
from ...indicators.technical_indicators import TechnicalIndicators


class FeatureEngineer:
    """
    Извлечение и подготовка признаков для ML моделей
    """
    
    def __init__(self):
        self.tech_indicators = TechnicalIndicators()
        
        # Список базовых признаков
        self.price_features = [
            'open', 'high', 'low', 'close', 'volume',
            'price_change', 'price_change_pct', 'volume_change_pct'
        ]
        
        # Технические индикаторы
        self.technical_features = [
            'rsi', 'macd', 'macd_signal', 'macd_hist',
            'bb_upper', 'bb_middle', 'bb_lower', 'bb_width', 'bb_percent',
            'ema_9', 'ema_21', 'ema_50', 'ema_200',
            'atr', 'adx', 'obv', 'vwap'
        ]
        
        # Паттерны свечей
        self.candle_patterns = [
            'doji', 'hammer', 'inverted_hammer', 'bullish_engulfing',
            'bearish_engulfing', 'morning_star', 'evening_star',
            'three_white_soldiers', 'three_black_crows'
        ]
        
        # Временные признаки
        self.time_features = [
            'hour', 'day_of_week', 'day_of_month', 'is_weekend',
            'is_asia_session', 'is_europe_session', 'is_us_session'
        ]
        
        # Микроструктура рынка
        self.market_microstructure = [
            'bid_ask_spread', 'order_flow_imbalance',
            'volume_at_bid', 'volume_at_ask', 'trades_per_minute'
        ]
    
    async def extract_features(self, symbol: str, timeframe: str = '5m', 
                              lookback_periods: int = 100) -> pd.DataFrame:
        """
        Извлекает все признаки для символа
        
        Args:
            symbol: Торговая пара
            timeframe: Временной интервал
            lookback_periods: Количество периодов для анализа
            
        Returns:
            DataFrame с признаками
        """
        db = SessionLocal()
        try:
            # Получаем свечи
            candles = db.query(Candle).filter(
                Candle.symbol == symbol,
                Candle.timeframe == timeframe
            ).order_by(Candle.timestamp.desc()).limit(lookback_periods * 2).all()
            
            if len(candles) < lookback_periods:
                return pd.DataFrame()
            
            # Конвертируем в DataFrame
            df = pd.DataFrame([{
                'timestamp': c.timestamp,
                'open': float(c.open),
                'high': float(c.high),
                'low': float(c.low),
                'close': float(c.close),
                'volume': float(c.volume)
            } for c in reversed(candles)])
            
            # Добавляем все группы признаков
            df = self._add_price_features(df)
            df = self._add_technical_indicators(df)
            df = self._add_candle_patterns(df)
            df = self._add_time_features(df)
            df = await self._add_market_microstructure(df, symbol)
            df = await self._add_market_conditions(df, symbol, timeframe)
            df = await self._add_historical_performance(df, symbol)
            
            # Добавляем лаговые признаки
            df = self._add_lag_features(df)
            
            # Добавляем скользящие статистики
            df = self._add_rolling_features(df)
            
            # Удаляем NaN
            df = df.dropna()
            
            return df
            
        finally:
            db.close()
    
    def _add_price_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Добавляет ценовые признаки"""
        # Изменения цены
        df['price_change'] = df['close'] - df['open']
        df['price_change_pct'] = (df['close'] - df['open']) / df['open'] * 100
        
        # Изменения относительно предыдущего периода
        df['close_change'] = df['close'].diff()
        df['close_change_pct'] = df['close'].pct_change() * 100
        
        # Изменения объема
        df['volume_change'] = df['volume'].diff()
        df['volume_change_pct'] = df['volume'].pct_change() * 100
        
        # High-Low spread
        df['hl_spread'] = df['high'] - df['low']
        df['hl_spread_pct'] = (df['high'] - df['low']) / df['low'] * 100
        
        # Позиция закрытия в диапазоне
        df['close_position'] = (df['close'] - df['low']) / (df['high'] - df['low'])
        
        return df
    
    def _add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Добавляет технические индикаторы используя pandas-ta"""
        # RSI
        df['rsi'] = ta.rsi(df['close'], length=14)
        df['rsi_oversold'] = (df['rsi'] < 30).astype(int)
        df['rsi_overbought'] = (df['rsi'] > 70).astype(int)
        
        # MACD
        macd = ta.macd(df['close'], fast=12, slow=26, signal=9)
        df['macd'] = macd['MACD_12_26_9']
        df['macd_signal'] = macd['MACDs_12_26_9']
        df['macd_hist'] = macd['MACDh_12_26_9']
        df['macd_cross'] = np.where(
            (df['macd'] > df['macd_signal']) & 
            (df['macd'].shift(1) <= df['macd_signal'].shift(1)), 1,
            np.where(
                (df['macd'] < df['macd_signal']) & 
                (df['macd'].shift(1) >= df['macd_signal'].shift(1)), -1, 0
            )
        )
        
        # Bollinger Bands
        bb = ta.bbands(df['close'], length=20, std=2)
        df['bb_upper'] = bb['BBU_20_2.0']
        df['bb_middle'] = bb['BBM_20_2.0']
        df['bb_lower'] = bb['BBL_20_2.0']
        df['bb_width'] = df['bb_upper'] - df['bb_lower']
        df['bb_percent'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        # EMA
        for period in [9, 21, 50, 200]:
            df[f'ema_{period}'] = ta.ema(df['close'], length=period)
        
        # EMA slopes
        df['ema_9_slope'] = (df['ema_9'] - df['ema_9'].shift(5)) / 5
        df['ema_21_slope'] = (df['ema_21'] - df['ema_21'].shift(5)) / 5
        
        # ATR
        df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=14)
        df['atr_pct'] = df['atr'] / df['close'] * 100
        
        # ADX
        adx = ta.adx(df['high'], df['low'], df['close'], length=14)
        df['adx'] = adx['ADX_14']
        df['plus_di'] = adx['DMP_14']
        df['minus_di'] = adx['DMN_14']
        
        # OBV
        df['obv'] = ta.obv(df['close'], df['volume'])
        df['obv_ema'] = ta.ema(df['obv'], length=21)
        df['obv_signal'] = np.where(df['obv'] > df['obv_ema'], 1, -1)
        
        # VWAP
        df['vwap'] = ta.vwap(df['high'], df['low'], df['close'], df['volume'])
        df['price_vs_vwap'] = (df['close'] - df['vwap']) / df['vwap'] * 100
        
        # Stochastic
        stoch = ta.stoch(df['high'], df['low'], df['close'], k=14, d=3)
        df['stoch_k'] = stoch['STOCHk_14_3_3']
        df['stoch_d'] = stoch['STOCHd_14_3_3']
        
        # CCI
        df['cci'] = ta.cci(df['high'], df['low'], df['close'], length=20)
        
        # Williams %R
        df['williams_r'] = ta.willr(df['high'], df['low'], df['close'], length=14)
        
        return df
    
    def _add_candle_patterns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Добавляет паттерны свечей используя pandas-ta"""
        # Получаем все доступные паттерны
        df_patterns = df.ta.cdl_pattern(name="all")
        
        # Если паттерны найдены, добавляем их
        if df_patterns is not None and not df_patterns.empty:
            pattern_cols = df_patterns.columns.tolist()
            
            # Переименовываем некоторые паттерны для совместимости
            rename_map = {
                'CDL_DOJI': 'doji',
                'CDL_HAMMER': 'hammer',
                'CDL_INVERTEDHAMMER': 'inverted_hammer',
                'CDL_HANGINGMAN': 'hanging_man',
                'CDL_ENGULFING': 'bullish_engulfing',
                'CDL_MORNINGSTAR': 'morning_star',
                'CDL_EVENINGSTAR': 'evening_star',
                'CDL_SHOOTINGSTAR': 'shooting_star',
                'CDL_3WHITESOLDIERS': 'three_white_soldiers',
                'CDL_3BLACKCROWS': 'three_black_crows',
                'CDL_3INSIDE': 'three_inside'
            }
            
            for old_name, new_name in rename_map.items():
                if old_name in df_patterns.columns:
                    df[new_name] = df_patterns[old_name]
            
            # Bearish engulfing - инвертируем значение
            if 'CDL_ENGULFING' in df_patterns.columns:
                df['bearish_engulfing'] = df_patterns['CDL_ENGULFING'] * -1
            
            # Создаем суммарный паттерн-сигнал
            pattern_cols = [col for col in df.columns if col in rename_map.values()]
            if pattern_cols:
                df['pattern_strength'] = df[pattern_cols].abs().sum(axis=1)
                df['pattern_direction'] = df[pattern_cols].sum(axis=1)
            else:
                df['pattern_strength'] = 0
                df['pattern_direction'] = 0
        else:
            # Если паттерны не найдены, создаем пустые колонки
            for pattern in ['doji', 'hammer', 'inverted_hammer', 'hanging_man',
                          'bullish_engulfing', 'bearish_engulfing', 'morning_star',
                          'evening_star', 'shooting_star', 'three_white_soldiers',
                          'three_black_crows', 'three_inside']:
                df[pattern] = 0
            df['pattern_strength'] = 0
            df['pattern_direction'] = 0
        
        return df
    
    def _add_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Добавляет временные признаки"""
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['day_of_month'] = df['timestamp'].dt.day
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        
        # Торговые сессии (UTC)
        df['is_asia_session'] = df['hour'].between(0, 8).astype(int)
        df['is_europe_session'] = df['hour'].between(7, 16).astype(int)
        df['is_us_session'] = df['hour'].between(13, 22).astype(int)
        
        # Циклические признаки для часа
        df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
        
        # Циклические признаки для дня недели
        df['dow_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
        df['dow_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
        
        return df
    
    async def _add_market_microstructure(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """Добавляет признаки микроструктуры рынка"""
        # Заглушка - будет реализована позже
        df['bid_ask_spread'] = np.random.uniform(0.01, 0.05, len(df))
        df['order_flow_imbalance'] = np.random.uniform(-1, 1, len(df))
        df['volume_at_bid'] = df['volume'] * np.random.uniform(0.4, 0.6, len(df))
        df['volume_at_ask'] = df['volume'] - df['volume_at_bid']
        df['trades_per_minute'] = np.random.uniform(10, 100, len(df))
        
        return df
    
    async def _add_market_conditions(self, df: pd.DataFrame, symbol: str, timeframe: str) -> pd.DataFrame:
        """Добавляет рыночные условия"""
        db = SessionLocal()
        try:
            # Получаем последние рыночные условия
            market_condition = db.query(MarketCondition).filter(
                MarketCondition.symbol == symbol,
                MarketCondition.timeframe == timeframe
            ).order_by(MarketCondition.timestamp.desc()).first()
            
            if market_condition:
                df['market_trend'] = 1 if market_condition.trend == 'UPTREND' else (-1 if market_condition.trend == 'DOWNTREND' else 0)
                df['market_volatility'] = market_condition.volatility_level
                df['market_strength'] = market_condition.trend_strength
            else:
                df['market_trend'] = 0
                df['market_volatility'] = 0.5
                df['market_strength'] = 0.5
                
        finally:
            db.close()
            
        return df
    
    async def _add_historical_performance(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """Добавляет историческую производительность"""
        db = SessionLocal()
        try:
            # Последние сделки
            recent_trades = db.query(Trade).filter(
                Trade.symbol == symbol,
                Trade.created_at >= datetime.utcnow() - timedelta(days=7)
            ).all()
            
            if recent_trades:
                win_rate = sum(1 for t in recent_trades if t.profit and t.profit > 0) / len(recent_trades)
                avg_profit = np.mean([t.profit for t in recent_trades if t.profit])
                
                df['recent_win_rate'] = win_rate
                df['recent_avg_profit'] = avg_profit
            else:
                df['recent_win_rate'] = 0.5
                df['recent_avg_profit'] = 0
                
        finally:
            db.close()
            
        return df
    
    def _add_lag_features(self, df: pd.DataFrame, lags: List[int] = [1, 3, 5, 10]) -> pd.DataFrame:
        """Добавляет лаговые признаки"""
        for lag in lags:
            # Лаги цены
            df[f'close_lag_{lag}'] = df['close'].shift(lag)
            df[f'volume_lag_{lag}'] = df['volume'].shift(lag)
            df[f'rsi_lag_{lag}'] = df['rsi'].shift(lag)
            
            # Изменения от лага
            df[f'close_change_from_lag_{lag}'] = (df['close'] - df[f'close_lag_{lag}']) / df[f'close_lag_{lag}'] * 100
            
        return df
    
    def _add_rolling_features(self, df: pd.DataFrame, windows: List[int] = [5, 10, 20]) -> pd.DataFrame:
        """Добавляет скользящие статистики"""
        for window in windows:
            # Скользящие средние
            df[f'close_sma_{window}'] = df['close'].rolling(window=window).mean()
            df[f'volume_sma_{window}'] = df['volume'].rolling(window=window).mean()
            
            # Скользящие стандартные отклонения
            df[f'close_std_{window}'] = df['close'].rolling(window=window).std()
            df[f'volume_std_{window}'] = df['volume'].rolling(window=window).std()
            
            # Скользящие минимумы и максимумы
            df[f'high_max_{window}'] = df['high'].rolling(window=window).max()
            df[f'low_min_{window}'] = df['low'].rolling(window=window).min()
            
            # Позиция цены относительно скользящих экстремумов
            df[f'price_position_{window}'] = (df['close'] - df[f'low_min_{window}']) / (df[f'high_max_{window}'] - df[f'low_min_{window}'])
            
        return df