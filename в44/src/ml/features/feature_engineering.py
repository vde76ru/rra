"""
Feature Engineering для ML моделей криптотрейдинга
Файл: src/ml/features/feature_engineering.py
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import talib
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
        """Добавляет технические индикаторы"""
        # RSI
        df['rsi'] = talib.RSI(df['close'], timeperiod=14)
        df['rsi_oversold'] = (df['rsi'] < 30).astype(int)
        df['rsi_overbought'] = (df['rsi'] > 70).astype(int)
        
        # MACD
        df['macd'], df['macd_signal'], df['macd_hist'] = talib.MACD(
            df['close'], fastperiod=12, slowperiod=26, signalperiod=9
        )
        df['macd_cross'] = np.where(
            (df['macd'] > df['macd_signal']) & 
            (df['macd'].shift(1) <= df['macd_signal'].shift(1)), 1,
            np.where(
                (df['macd'] < df['macd_signal']) & 
                (df['macd'].shift(1) >= df['macd_signal'].shift(1)), -1, 0
            )
        )
        
        # Bollinger Bands
        df['bb_upper'], df['bb_middle'], df['bb_lower'] = talib.BBANDS(
            df['close'], timeperiod=20, nbdevup=2, nbdevdn=2
        )
        df['bb_width'] = df['bb_upper'] - df['bb_lower']
        df['bb_percent'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        # EMA
        for period in [9, 21, 50, 200]:
            df[f'ema_{period}'] = talib.EMA(df['close'], timeperiod=period)
        
        # EMA slopes
        df['ema_9_slope'] = (df['ema_9'] - df['ema_9'].shift(5)) / 5
        df['ema_21_slope'] = (df['ema_21'] - df['ema_21'].shift(5)) / 5
        
        # ATR
        df['atr'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=14)
        df['atr_pct'] = df['atr'] / df['close'] * 100
        
        # ADX
        df['adx'] = talib.ADX(df['high'], df['low'], df['close'], timeperiod=14)
        df['plus_di'] = talib.PLUS_DI(df['high'], df['low'], df['close'], timeperiod=14)
        df['minus_di'] = talib.MINUS_DI(df['high'], df['low'], df['close'], timeperiod=14)
        
        # OBV
        df['obv'] = talib.OBV(df['close'], df['volume'])
        df['obv_ema'] = talib.EMA(df['obv'], timeperiod=21)
        df['obv_signal'] = np.where(df['obv'] > df['obv_ema'], 1, -1)
        
        # VWAP
        df['vwap'] = (df['close'] * df['volume']).cumsum() / df['volume'].cumsum()
        df['price_vs_vwap'] = (df['close'] - df['vwap']) / df['vwap'] * 100
        
        # Stochastic
        df['stoch_k'], df['stoch_d'] = talib.STOCH(
            df['high'], df['low'], df['close'],
            fastk_period=14, slowk_period=3, slowd_period=3
        )
        
        # CCI
        df['cci'] = talib.CCI(df['high'], df['low'], df['close'], timeperiod=20)
        
        # Williams %R
        df['williams_r'] = talib.WILLR(df['high'], df['low'], df['close'], timeperiod=14)
        
        return df
    
    def _add_candle_patterns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Добавляет паттерны свечей"""
        # Doji
        df['doji'] = talib.CDLDOJI(df['open'], df['high'], df['low'], df['close'])
        
        # Hammer patterns
        df['hammer'] = talib.CDLHAMMER(df['open'], df['high'], df['low'], df['close'])
        df['inverted_hammer'] = talib.CDLINVERTEDHAMMER(df['open'], df['high'], df['low'], df['close'])
        df['hanging_man'] = talib.CDLHANGINGMAN(df['open'], df['high'], df['low'], df['close'])
        
        # Engulfing patterns
        df['bullish_engulfing'] = talib.CDLENGULFING(df['open'], df['high'], df['low'], df['close'])
        df['bearish_engulfing'] = talib.CDLENGULFING(df['open'], df['high'], df['low'], df['close']) * -1
        
        # Star patterns
        df['morning_star'] = talib.CDLMORNINGSTAR(df['open'], df['high'], df['low'], df['close'])
        df['evening_star'] = talib.CDLEVENINGSTAR(df['open'], df['high'], df['low'], df['close'])
        df['shooting_star'] = talib.CDLSHOOTINGSTAR(df['open'], df['high'], df['low'], df['close'])
        
        # Three patterns
        df['three_white_soldiers'] = talib.CDL3WHITESOLDIERS(df['open'], df['high'], df['low'], df['close'])
        df['three_black_crows'] = talib.CDL3BLACKCROWS(df['open'], df['high'], df['low'], df['close'])
        df['three_inside'] = talib.CDL3INSIDE(df['open'], df['high'], df['low'], df['close'])
        
        # Создаем суммарный паттерн-сигнал
        pattern_cols = [col for col in df.columns if col.startswith(('doji', 'hammer', 'bullish', 'bearish', 
                                                                     'morning', 'evening', 'three'))]
        df['pattern_strength'] = df[pattern_cols].abs().sum(axis=1)
        df['pattern_direction'] = df[pattern_cols].sum(axis=1)
        
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
        
        # Циклические признаки
        df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
        df['day_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
        df['day_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
        
        return df
    
    async def _add_market_microstructure(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """Добавляет признаки микроструктуры рынка"""
        # Здесь должна быть интеграция с биржевым API для получения данных orderbook
        # Пока используем приближенные значения
        
        # Bid-Ask spread approximation
        df['bid_ask_spread'] = df['hl_spread'] * 0.1  # Примерная оценка
        df['bid_ask_spread_pct'] = df['bid_ask_spread'] / df['close'] * 100
        
        # Order flow imbalance approximation
        df['order_flow_imbalance'] = np.where(
            df['close'] > df['open'],
            df['volume'] * 0.6,  # 60% на покупку
            df['volume'] * 0.4   # 40% на покупку
        )
        
        # Volume at bid/ask approximation
        df['volume_at_bid'] = df['volume'] * (1 - df['close_position'])
        df['volume_at_ask'] = df['volume'] * df['close_position']
        
        # Trades intensity
        df['trades_intensity'] = df['volume'] / df['hl_spread']
        
        return df
    
    async def _add_market_conditions(self, df: pd.DataFrame, symbol: str, 
                                   timeframe: str) -> pd.DataFrame:
        """Добавляет рыночные условия из БД"""
        db = SessionLocal()
        try:
            # Получаем последние рыночные условия
            conditions = db.query(MarketCondition).filter(
                MarketCondition.symbol == symbol,
                MarketCondition.timeframe == timeframe
            ).order_by(MarketCondition.timestamp.desc()).limit(len(df)).all()
            
            if conditions:
                # Создаем словарь условий по временным меткам
                condition_dict = {}
                for cond in conditions:
                    timestamp = cond.timestamp.replace(second=0, microsecond=0)
                    if cond.condition_type not in condition_dict:
                        condition_dict[cond.condition_type] = {}
                    condition_dict[cond.condition_type][timestamp] = {
                        'value': cond.condition_value,
                        'strength': cond.strength
                    }
                
                # Добавляем в DataFrame
                for cond_type, values in condition_dict.items():
                    df[f'market_{cond_type}'] = df['timestamp'].map(
                        lambda x: values.get(x.replace(second=0, microsecond=0), {}).get('value', 'unknown')
                    )
                    df[f'market_{cond_type}_strength'] = df['timestamp'].map(
                        lambda x: values.get(x.replace(second=0, microsecond=0), {}).get('strength', 0)
                    )
            
            return df
            
        finally:
            db.close()
    
    async def _add_historical_performance(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """Добавляет историческую производительность"""
        db = SessionLocal()
        try:
            # Получаем последние сделки
            recent_trades = db.query(Trade).filter(
                Trade.symbol == symbol,
                Trade.status == 'closed'
            ).order_by(Trade.closed_at.desc()).limit(50).all()
            
            if recent_trades:
                # Рассчитываем метрики
                win_rate = len([t for t in recent_trades if t.profit > 0]) / len(recent_trades)
                avg_profit = np.mean([t.profit for t in recent_trades])
                avg_profit_pct = np.mean([t.profit_percent for t in recent_trades])
                
                # Добавляем как константы
                df['historical_win_rate'] = win_rate
                df['historical_avg_profit'] = avg_profit
                df['historical_avg_profit_pct'] = avg_profit_pct
                
                # Win/Loss streaks
                profits = [t.profit > 0 for t in recent_trades]
                current_streak = 1
                for i in range(1, len(profits)):
                    if profits[i] == profits[i-1]:
                        current_streak += 1
                    else:
                        break
                
                df['current_streak'] = current_streak if profits[0] else -current_streak
                df['is_winning_streak'] = (df['current_streak'] > 0).astype(int)
            
            return df
            
        finally:
            db.close()
    
    def _add_lag_features(self, df: pd.DataFrame, lags: List[int] = [1, 2, 3, 5, 10]) -> pd.DataFrame:
        """Добавляет лаговые признаки"""
        # Важные признаки для лагов
        lag_features = ['close', 'volume', 'rsi', 'macd', 'atr', 'adx']
        
        for feature in lag_features:
            if feature in df.columns:
                for lag in lags:
                    df[f'{feature}_lag_{lag}'] = df[feature].shift(lag)
                    df[f'{feature}_change_lag_{lag}'] = df[feature] - df[feature].shift(lag)
                    df[f'{feature}_pct_change_lag_{lag}'] = (
                        (df[feature] - df[feature].shift(lag)) / df[feature].shift(lag) * 100
                    )
        
        return df
    
    def _add_rolling_features(self, df: pd.DataFrame, 
                            windows: List[int] = [5, 10, 20, 50]) -> pd.DataFrame:
        """Добавляет скользящие статистики"""
        # Признаки для скользящих окон
        rolling_features = ['close', 'volume', 'rsi', 'atr']
        
        for feature in rolling_features:
            if feature in df.columns:
                for window in windows:
                    # Скользящие статистики
                    df[f'{feature}_rolling_mean_{window}'] = df[feature].rolling(window).mean()
                    df[f'{feature}_rolling_std_{window}'] = df[feature].rolling(window).std()
                    df[f'{feature}_rolling_min_{window}'] = df[feature].rolling(window).min()
                    df[f'{feature}_rolling_max_{window}'] = df[feature].rolling(window).max()
                    
                    # Позиция текущего значения в скользящем окне
                    df[f'{feature}_rolling_position_{window}'] = (
                        (df[feature] - df[f'{feature}_rolling_min_{window}']) /
                        (df[f'{feature}_rolling_max_{window}'] - df[f'{feature}_rolling_min_{window}'])
                    )
                    
                    # Z-score
                    df[f'{feature}_rolling_zscore_{window}'] = (
                        (df[feature] - df[f'{feature}_rolling_mean_{window}']) /
                        df[f'{feature}_rolling_std_{window}']
                    )
        
        return df
    
    def get_feature_names(self) -> List[str]:
        """Возвращает список всех возможных признаков"""
        all_features = (
            self.price_features +
            self.technical_features +
            self.candle_patterns +
            self.time_features +
            self.market_microstructure
        )
        
        # Добавляем производные признаки
        all_features.extend([
            'price_vs_vwap', 'rsi_oversold', 'rsi_overbought',
            'macd_cross', 'bb_percent', 'obv_signal',
            'pattern_strength', 'pattern_direction',
            'hour_sin', 'hour_cos', 'day_sin', 'day_cos',
            'bid_ask_spread_pct', 'trades_intensity',
            'historical_win_rate', 'historical_avg_profit',
            'current_streak', 'is_winning_streak'
        ])
        
        return all_features
    
    def prepare_training_data(self, df: pd.DataFrame, 
                            target_type: str = 'direction',
                            target_periods: int = 5) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Подготавливает данные для обучения
        
        Args:
            df: DataFrame с признаками
            target_type: Тип целевой переменной ('direction', 'profit', 'entry')
            target_periods: Количество периодов вперед для предсказания
            
        Returns:
            X: Признаки
            y: Целевая переменная
        """
        df = df.copy()
        
        if target_type == 'direction':
            # Предсказываем направление движения
            future_price = df['close'].shift(-target_periods)
            df['target'] = np.where(
                future_price > df['close'] * 1.002,  # +0.2%
                1,  # UP
                np.where(
                    future_price < df['close'] * 0.998,  # -0.2%
                    -1,  # DOWN
                    0  # SIDEWAYS
                )
            )
        
        elif target_type == 'profit':
            # Предсказываем потенциальную прибыль
            future_price = df['close'].shift(-target_periods)
            df['target'] = (future_price - df['close']) / df['close'] * 100
        
        elif target_type == 'entry':
            # Предсказываем хорошие точки входа
            # Смотрим на максимальную прибыль в следующие N периодов
            max_profit = pd.Series([
                df['high'].iloc[i:i+target_periods].max() if i+target_periods < len(df) else np.nan
                for i in range(len(df))
            ])
            df['target'] = np.where(
                (max_profit - df['close']) / df['close'] > 0.01,  # >1% прибыли
                1,  # Good entry
                0  # Bad entry
            )
        
        # Удаляем строки с NaN в target
        df = df.dropna(subset=['target'])
        
        # Выбираем только числовые признаки
        feature_cols = [col for col in df.columns if col not in [
            'timestamp', 'target', 'open', 'high', 'low', 'close', 'volume'
        ]]
        
        X = df[feature_cols]
        y = df['target']
        
        return X, y