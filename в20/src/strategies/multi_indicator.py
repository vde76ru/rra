"""
Мульти-индикаторная стратегия
Путь: /var/www/www-root/data/www/systemetech.ru/src/strategies/multi_indicator.py
"""
import pandas as pd
import numpy as np
from typing import Dict  # ✅ ИСПРАВЛЕНО: добавлен импорт Dict
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.trend import EMAIndicator, MACD, ADXIndicator
from ta.volatility import BollingerBands, AverageTrueRange
from ta.volume import OnBalanceVolumeIndicator
import logging
from typing import Dict

from .base import BaseStrategy, TradingSignal

logger = logging.getLogger(__name__)

class MultiIndicatorStrategy(BaseStrategy):
    """
    Продвинутая стратегия с множественными индикаторами
    Использует подтверждение от нескольких индикаторов
    """
    
    # ✅ УЛУЧШЕНИЕ: Константы для лучшей читаемости
    RSI_OVERSOLD = 30
    RSI_OVERBOUGHT = 70
    STOCH_OVERSOLD = 20
    STOCH_OVERBOUGHT = 80
    ADX_TREND_THRESHOLD = 25
    VOLUME_RATIO_THRESHOLD = 1.5
    BB_LOWER_THRESHOLD = 0.2
    BB_UPPER_THRESHOLD = 0.8
    
    def __init__(self):
        super().__init__("multi_indicator")
        self.min_confidence = 0.65
        self.min_indicators_confirm = 3  # Минимум 3 индикатора должны подтвердить
    
    async def analyze(self, df: pd.DataFrame, symbol: str) -> TradingSignal:
        """Комплексный анализ с множественными подтверждениями"""
        
        if not self.validate_dataframe(df):
            return TradingSignal('WAIT', 0, 0, reason='Недостаточно данных')
        
        try:
            # Рассчитываем все индикаторы
            indicators = self._calculate_indicators(df)
            
            # ✅ УЛУЧШЕНИЕ: Проверяем корректность индикаторов
            if not indicators:
                return TradingSignal('WAIT', 0, 0, reason='Ошибка расчета индикаторов')
            
            # Анализируем сигналы от каждого индикатора
            signals = self._analyze_signals(indicators, df)
            
            # Принимаем решение на основе всех сигналов
            return self._make_decision(signals, indicators, df)
            
        except Exception as e:
            logger.error(f"Ошибка анализа {symbol}: {e}")
            return TradingSignal('WAIT', 0, 0, reason=f'Ошибка анализа: {e}')
    
    def _calculate_indicators(self, df: pd.DataFrame) -> Dict:
        """Расчет всех индикаторов с защитой от ошибок"""
        indicators = {}
        
        try:
            # ✅ УЛУЧШЕНИЕ: Проверка достаточности данных
            required_length = max(200, 50, 21, 20, 14)  # Максимальный период из всех индикаторов
            if len(df) < required_length:
                logger.warning(f"Недостаточно данных для всех индикаторов: {len(df)} < {required_length}")
                # Возвращаем пустой словарь, если данных мало
                return {}
            
            # RSI с проверкой
            rsi_indicator = RSIIndicator(df['close'], window=14)
            rsi_values = rsi_indicator.rsi()
            indicators['rsi'] = rsi_values.iloc[-1] if not rsi_values.empty else 50.0
            
            # MACD с проверкой
            macd = MACD(df['close'])
            macd_line = macd.macd()
            macd_signal = macd.macd_signal()
            macd_diff = macd.macd_diff()
            
            indicators['macd'] = macd_line.iloc[-1] if not macd_line.empty else 0.0
            indicators['macd_signal'] = macd_signal.iloc[-1] if not macd_signal.empty else 0.0
            indicators['macd_diff'] = macd_diff.iloc[-1] if not macd_diff.empty else 0.0
            
            # Bollinger Bands с проверкой
            bb = BollingerBands(df['close'], window=20, window_dev=2)
            bb_upper = bb.bollinger_hband()
            bb_middle = bb.bollinger_mavg()
            bb_lower = bb.bollinger_lband()
            bb_width = bb.bollinger_wband()
            bb_percent = bb.bollinger_pband()
            
            indicators['bb_upper'] = bb_upper.iloc[-1] if not bb_upper.empty else df['close'].iloc[-1]
            indicators['bb_middle'] = bb_middle.iloc[-1] if not bb_middle.empty else df['close'].iloc[-1]
            indicators['bb_lower'] = bb_lower.iloc[-1] if not bb_lower.empty else df['close'].iloc[-1]
            indicators['bb_width'] = bb_width.iloc[-1] if not bb_width.empty else 0.0
            indicators['bb_percent'] = bb_percent.iloc[-1] if not bb_percent.empty else 0.5
            
            # EMA с проверкой
            self._calculate_ema_safely(df, indicators)
            
            # ADX с проверкой
            self._calculate_adx_safely(df, indicators)
            
            # ATR для stop loss
            atr = AverageTrueRange(df['high'], df['low'], df['close'])
            atr_values = atr.average_true_range()
            indicators['atr'] = atr_values.iloc[-1] if not atr_values.empty else df['close'].iloc[-1] * 0.02
            
            # Volume indicators с проверкой
            self._calculate_volume_safely(df, indicators)
            
            # Stochastic с проверкой
            self._calculate_stochastic_safely(df, indicators)
            
            # Price action
            indicators['current_price'] = df['close'].iloc[-1]
            if len(df) >= 2:
                indicators['price_change'] = ((df['close'].iloc[-1] - df['close'].iloc[-2]) / 
                                            df['close'].iloc[-2] * 100)
            else:
                indicators['price_change'] = 0.0
            
            return indicators
            
        except Exception as e:
            logger.error(f"Ошибка расчета индикаторов: {e}")
            return {}
    
    def _calculate_ema_safely(self, df: pd.DataFrame, indicators: Dict):
        """✅ НОВОЕ: Безопасный расчет EMA"""
        try:
            periods = [9, 21, 50, 200]
            for period in periods:
                if len(df) >= period:
                    ema_indicator = EMAIndicator(df['close'], window=period)
                    ema_values = ema_indicator.ema_indicator()
                    indicators[f'ema_{period}'] = ema_values.iloc[-1] if not ema_values.empty else df['close'].iloc[-1]
                else:
                    indicators[f'ema_{period}'] = df['close'].iloc[-1]
        except Exception as e:
            logger.error(f"Ошибка расчета EMA: {e}")
            # Используем текущую цену как fallback
            for period in [9, 21, 50, 200]:
                indicators[f'ema_{period}'] = df['close'].iloc[-1]
    
    def _calculate_adx_safely(self, df: pd.DataFrame, indicators: Dict):
        """✅ НОВОЕ: Безопасный расчет ADX"""
        try:
            if len(df) >= 14:  # ADX требует минимум 14 периодов
                adx = ADXIndicator(df['high'], df['low'], df['close'])
                adx_values = adx.adx()
                adx_pos_values = adx.adx_pos()
                adx_neg_values = adx.adx_neg()
                
                indicators['adx'] = adx_values.iloc[-1] if not adx_values.empty else 0.0
                indicators['adx_pos'] = adx_pos_values.iloc[-1] if not adx_pos_values.empty else 0.0
                indicators['adx_neg'] = adx_neg_values.iloc[-1] if not adx_neg_values.empty else 0.0
            else:
                indicators['adx'] = 0.0
                indicators['adx_pos'] = 0.0
                indicators['adx_neg'] = 0.0
        except Exception as e:
            logger.error(f"Ошибка расчета ADX: {e}")
            indicators['adx'] = 0.0
            indicators['adx_pos'] = 0.0
            indicators['adx_neg'] = 0.0
    
    def _calculate_volume_safely(self, df: pd.DataFrame, indicators: Dict):
        """✅ НОВОЕ: Безопасный расчет объемных индикаторов"""
        try:
            if len(df) >= 20:
                volume_sma = df['volume'].rolling(window=20).mean()
                indicators['volume_sma'] = volume_sma.iloc[-1] if not volume_sma.empty else df['volume'].iloc[-1]
                
                if indicators['volume_sma'] > 0:
                    indicators['volume_ratio'] = df['volume'].iloc[-1] / indicators['volume_sma']
                else:
                    indicators['volume_ratio'] = 1.0
            else:
                indicators['volume_sma'] = df['volume'].mean()
                indicators['volume_ratio'] = 1.0
        except Exception as e:
            logger.error(f"Ошибка расчета объемных индикаторов: {e}")
            indicators['volume_sma'] = df['volume'].iloc[-1] if len(df) > 0 else 1.0
            indicators['volume_ratio'] = 1.0
    
    def _calculate_stochastic_safely(self, df: pd.DataFrame, indicators: Dict):
        """✅ НОВОЕ: Безопасный расчет Stochastic"""
        try:
            if len(df) >= 14:  # Stochastic требует минимум 14 периодов
                stoch = StochasticOscillator(df['high'], df['low'], df['close'])
                stoch_k_values = stoch.stoch()
                stoch_d_values = stoch.stoch_signal()
                
                indicators['stoch_k'] = stoch_k_values.iloc[-1] if not stoch_k_values.empty else 50.0
                indicators['stoch_d'] = stoch_d_values.iloc[-1] if not stoch_d_values.empty else 50.0
            else:
                indicators['stoch_k'] = 50.0
                indicators['stoch_d'] = 50.0
        except Exception as e:
            logger.error(f"Ошибка расчета Stochastic: {e}")
            indicators['stoch_k'] = 50.0
            indicators['stoch_d'] = 50.0
    
    def _analyze_signals(self, indicators: Dict, df: pd.DataFrame) -> Dict:
        """Анализ сигналов от каждого индикатора"""
        signals = {
            'buy_signals': [],
            'sell_signals': [],
            'neutral_signals': []
        }
        
        # RSI сигналы
        if indicators['rsi'] < self.RSI_OVERSOLD:
            signals['buy_signals'].append(('RSI', 'Перепроданность', 0.8))
        elif indicators['rsi'] > self.RSI_OVERBOUGHT:
            signals['sell_signals'].append(('RSI', 'Перекупленность', 0.8))
        
        # MACD сигналы
        if indicators['macd'] > indicators['macd_signal'] and indicators['macd_diff'] > 0:
            signals['buy_signals'].append(('MACD', 'Бычье пересечение', 0.7))
        elif indicators['macd'] < indicators['macd_signal'] and indicators['macd_diff'] < 0:
            signals['sell_signals'].append(('MACD', 'Медвежье пересечение', 0.7))
        
        # Bollinger Bands сигналы
        if indicators['bb_percent'] < self.BB_LOWER_THRESHOLD:
            signals['buy_signals'].append(('BB', 'Цена у нижней границы', 0.6))
        elif indicators['bb_percent'] > self.BB_UPPER_THRESHOLD:
            signals['sell_signals'].append(('BB', 'Цена у верхней границы', 0.6))
        
        # EMA тренд
        if (indicators['ema_9'] > indicators['ema_21'] > indicators['ema_50'] and 
            indicators['current_price'] > indicators['ema_9']):
            signals['buy_signals'].append(('EMA', 'Восходящий тренд', 0.7))
        elif (indicators['ema_9'] < indicators['ema_21'] < indicators['ema_50'] and 
              indicators['current_price'] < indicators['ema_9']):
            signals['sell_signals'].append(('EMA', 'Нисходящий тренд', 0.7))
        
        # ADX сила тренда
        if indicators['adx'] > self.ADX_TREND_THRESHOLD:
            if indicators['adx_pos'] > indicators['adx_neg']:
                signals['buy_signals'].append(('ADX', 'Сильный восходящий тренд', 0.6))
            else:
                signals['sell_signals'].append(('ADX', 'Сильный нисходящий тренд', 0.6))
        
        # Volume подтверждение
        if indicators['volume_ratio'] > self.VOLUME_RATIO_THRESHOLD:
            signals['neutral_signals'].append(('Volume', 'Высокий объем', 0.5))
        
        # Stochastic сигналы
        if indicators['stoch_k'] < self.STOCH_OVERSOLD and indicators['stoch_k'] > indicators['stoch_d']:
            signals['buy_signals'].append(('Stochastic', 'Перепроданность + пересечение', 0.6))
        elif indicators['stoch_k'] > self.STOCH_OVERBOUGHT and indicators['stoch_k'] < indicators['stoch_d']:
            signals['sell_signals'].append(('Stochastic', 'Перекупленность + пересечение', 0.6))
        
        return signals
    
    def _make_decision(self, signals: Dict, indicators: Dict, df: pd.DataFrame) -> TradingSignal:
        """Принятие решения на основе всех сигналов"""
        buy_score = sum(signal[2] for signal in signals['buy_signals'])
        sell_score = sum(signal[2] for signal in signals['sell_signals'])
        
        buy_count = len(signals['buy_signals'])
        sell_count = len(signals['sell_signals'])
        
        current_price = indicators['current_price']
        atr = indicators['atr']
        
        # Проверяем минимальное количество подтверждений
        if buy_count >= self.min_indicators_confirm and buy_score > sell_score:
            # Расчет уровней
            stop_loss = self.calculate_stop_loss(current_price, 'BUY', atr)
            take_profit = self.calculate_take_profit(current_price, 'BUY', atr)
            risk_reward = self.calculate_risk_reward(current_price, stop_loss, take_profit)
            
            # Расчет уверенности
            confidence = min(0.95, buy_score / (buy_count * 0.8))
            
            # Формируем причину
            reasons = [f"{sig[0]}: {sig[1]}" for sig in signals['buy_signals']]
            reason = "; ".join(reasons[:3])  # Берем топ-3 причины
            
            return TradingSignal(
                action='BUY',
                confidence=confidence,
                price=current_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                reason=reason,
                risk_reward_ratio=risk_reward,
                indicators=indicators
            )
            
        elif sell_count >= self.min_indicators_confirm and sell_score > buy_score:
            # Расчет уровней
            stop_loss = self.calculate_stop_loss(current_price, 'SELL', atr)
            take_profit = self.calculate_take_profit(current_price, 'SELL', atr)
            risk_reward = self.calculate_risk_reward(current_price, stop_loss, take_profit)
            
            # Расчет уверенности
            confidence = min(0.95, sell_score / (sell_count * 0.8))
            
            # Формируем причину
            reasons = [f"{sig[0]}: {sig[1]}" for sig in signals['sell_signals']]
            reason = "; ".join(reasons[:3])
            
            return TradingSignal(
                action='SELL',
                confidence=confidence,
                price=current_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                reason=reason,
                risk_reward_ratio=risk_reward,
                indicators=indicators
            )
        
        else:
            # Нет достаточных сигналов
            reason = f"Недостаточно подтверждений (BUY: {buy_count}, SELL: {sell_count})"
            
            return TradingSignal(
                action='WAIT',
                confidence=0,
                price=current_price,
                reason=reason,
                indicators=indicators
            )