"""
Скальпинг стратегия - ИСПРАВЛЕННАЯ ВЕРСИЯ
Путь: /var/www/www-root/data/www/systemetech.ru/src/strategies/scalping.py
"""
import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, Optional  # ✅ ИСПРАВЛЕНО: добавлен Any

from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands, AverageTrueRange
from ta.volume import VolumeWeightedAveragePrice

from .base import BaseStrategy, TradingSignal

logger = logging.getLogger(__name__)

class ScalpingStrategy(BaseStrategy):
    """
    🚀 Скальпинг стратегия для быстрых сделок
    
    Особенности:
    - Работает на малых таймфреймах (1m, 5m)
    - Использует жесткие стоп-лоссы
    - Быстрый вход и выход из позиций
    - Основана на Bollinger Bands, RSI и VWAP
    """
    
    # ✅ КОНСТАНТЫ для настройки стратегии
    STRATEGY_TYPE = "scalping"
    RISK_LEVEL = "high"
    TIMEFRAMES = ["1m", "5m", "15m"]
    MIN_VOLATILITY = 0.5  # Минимальная волатильность в %
    MAX_VOLATILITY = 3.0  # Максимальная волатильность в %
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        🏗️ Инициализация скальпинг стратегии
        
        Args:
            config: Словарь настроек:
                - bb_period: период Bollinger Bands (default: 20)
                - bb_std: стандартное отклонение BB (default: 2)
                - rsi_period: период RSI (default: 7)
                - min_profit_percent: минимальная прибыль % (default: 0.3)
                - max_loss_percent: максимальная потеря % (default: 0.2)
                - min_volume_ratio: минимальный объем (default: 1.5)
        """
        super().__init__("scalping")
        
        # ✅ БЕЗОПАСНАЯ ОБРАБОТКА КОНФИГА
        if config is None:
            config = {}
        elif not isinstance(config, dict):
            logger.error(f"❌ Config должен быть dict, получен {type(config)}: {config}")
            config = {}
        
        # Параметры Bollinger Bands
        self.bb_period = config.get('bb_period', 20)
        self.bb_std = config.get('bb_std', 2)
        
        # Параметры RSI
        self.rsi_period = config.get('rsi_period', 7)
        
        # Параметры риск-менеджмента для скальпинга
        self.min_profit_percent = config.get('min_profit_percent', 0.3)  # 0.3% минимум
        self.max_loss_percent = config.get('max_loss_percent', 0.2)      # 0.2% максимум
        
        # Параметры объема
        self.min_volume_ratio = config.get('min_volume_ratio', 1.5)
        
        # Параметры подтверждения
        self.min_confidence = config.get('min_confidence', 0.7)
        
        logger.info(f"🚀 ScalpingStrategy инициализирована: profit={self.min_profit_percent}%, loss={self.max_loss_percent}%")
    
    async def analyze(self, df: pd.DataFrame, symbol: str) -> TradingSignal:
        """
        🔍 Главный метод анализа для скальпинга
        
        Args:
            df: DataFrame с OHLCV данными
            symbol: Символ торгового инструмента
            
        Returns:
            TradingSignal: Сигнал для скальпинга
        """
        
        # ✅ ВАЛИДАЦИЯ ДАННЫХ
        validation_result = self._validate_scalping_data(df, symbol)
        if validation_result:
            return validation_result
        
        try:
            logger.debug(f"📊 Анализ скальпинга для {symbol}, данных: {len(df)}")
            
            # Рассчитываем индикаторы
            indicators = self._calculate_scalping_indicators(df)
            
            if not indicators:
                return TradingSignal('WAIT', 0, 0, reason='❌ Ошибка расчета индикаторов')
            
            # Проверяем условия для скальпинга
            scalp_signal = self._check_scalping_conditions(indicators)
            
            # Принимаем решение
            return self._make_scalping_decision(scalp_signal, indicators, symbol)
            
        except Exception as e:
            logger.error(f"💥 Ошибка анализа скальпинга для {symbol}: {e}", exc_info=True)
            return TradingSignal('WAIT', 0, 0, reason=f'💥 Ошибка анализа: {str(e)[:100]}')
    
    def _validate_scalping_data(self, df: pd.DataFrame, symbol: str) -> Optional[TradingSignal]:
        """
        🛡️ ВАЛИДАЦИЯ ДАННЫХ для скальпинга
        
        Скальпинг требует качественных и свежих данных
        """
        
        # Базовая валидация
        if not self.validate_dataframe(df):
            return TradingSignal('WAIT', 0, 0, reason='❌ Недостаточно данных для скальпинга')
        
        # Проверка минимального количества данных для скальпинга
        min_required = max(self.bb_period, self.rsi_period, 20)
        if len(df) < min_required:
            return TradingSignal('WAIT', 0, 0, 
                               reason=f'⚠️ Мало данных для скальпинга: {len(df)}/{min_required}')
        
        # Проверка наличия обязательных колонок
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            return TradingSignal('WAIT', 0, 0, 
                               reason=f'❌ Отсутствуют колонки: {", ".join(missing_cols)}')
        
        # Проверка качества данных (отсутствие NaN в последних записях)
        recent_data = df.tail(5)
        if recent_data[required_cols].isnull().any().any():
            return TradingSignal('WAIT', 0, 0, reason='❌ Неполные данные в последних записях')
        
        # Проверка на нулевые объемы
        if (recent_data['volume'] == 0).any():
            return TradingSignal('WAIT', 0, 0, reason='⚠️ Нулевые объемы в данных')
        
        return None  # Валидация пройдена
    
    def _calculate_scalping_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        📊 РАСЧЕТ ИНДИКАТОРОВ для скальпинга
        
        Returns:
            Dict с рассчитанными индикаторами
        """
        indicators = {}
        
        try:
            current_price = df['close'].iloc[-1]
            
            # ✅ BOLLINGER BANDS - основа для скальпинга
            try:
                bb = BollingerBands(df['close'], window=self.bb_period, window_dev=self.bb_std)
                
                bb_upper = bb.bollinger_hband()
                bb_lower = bb.bollinger_lband()
                bb_middle = bb.bollinger_mavg()
                bb_width = bb.bollinger_wband()
                bb_percent = bb.bollinger_pband()
                
                indicators['bb_upper'] = bb_upper.iloc[-1] if not bb_upper.empty else current_price * 1.02
                indicators['bb_lower'] = bb_lower.iloc[-1] if not bb_lower.empty else current_price * 0.98
                indicators['bb_middle'] = bb_middle.iloc[-1] if not bb_middle.empty else current_price
                indicators['bb_width'] = bb_width.iloc[-1] if not bb_width.empty else 0.02
                indicators['bb_percent'] = bb_percent.iloc[-1] if not bb_percent.empty else 0.5
                
            except Exception as e:
                logger.error(f"❌ Ошибка BB: {e}")
                indicators.update({
                    'bb_upper': current_price * 1.02,
                    'bb_lower': current_price * 0.98,
                    'bb_middle': current_price,
                    'bb_width': 0.02,
                    'bb_percent': 0.5
                })
            
            # ✅ RSI - для определения перекупленности/перепроданности
            try:
                rsi = RSIIndicator(df['close'], window=self.rsi_period)
                rsi_values = rsi.rsi()
                indicators['rsi'] = rsi_values.iloc[-1] if not rsi_values.empty else 50.0
            except Exception as e:
                logger.error(f"❌ Ошибка RSI: {e}")
                indicators['rsi'] = 50.0
            
            # ✅ VWAP - важен для скальпинга
            try:
                vwap = VolumeWeightedAveragePrice(df['high'], df['low'], df['close'], df['volume'])
                vwap_values = vwap.volume_weighted_average_price()
                indicators['vwap'] = vwap_values.iloc[-1] if not vwap_values.empty else current_price
            except Exception as e:
                logger.error(f"❌ Ошибка VWAP: {e}")
                indicators['vwap'] = current_price
            
            # ✅ ATR - для расчета стоп-лоссов
            try:
                atr = AverageTrueRange(df['high'], df['low'], df['close'], window=14)
                atr_values = atr.average_true_range()
                atr_value = atr_values.iloc[-1] if not atr_values.empty else current_price * 0.01
                
                indicators['atr'] = atr_value
                indicators['atr_percent'] = (atr_value / current_price) * 100
            except Exception as e:
                logger.error(f"❌ Ошибка ATR: {e}")
                indicators['atr'] = current_price * 0.01
                indicators['atr_percent'] = 1.0
            
            # ✅ ОБЪЕМНЫЙ АНАЛИЗ
            try:
                volume_sma = df['volume'].rolling(window=20).mean().iloc[-1]
                current_volume = df['volume'].iloc[-1]
                
                indicators['volume_sma'] = volume_sma if pd.notna(volume_sma) else current_volume
                indicators['volume_ratio'] = current_volume / indicators['volume_sma'] if indicators['volume_sma'] > 0 else 1.0
            except Exception as e:
                logger.error(f"❌ Ошибка Volume: {e}")
                indicators['volume_sma'] = df['volume'].iloc[-1]
                indicators['volume_ratio'] = 1.0
            
            # ✅ PRICE ACTION АНАЛИЗ
            try:
                last_candle = df.iloc[-1]
                
                indicators['current_price'] = current_price
                indicators['price_range'] = last_candle['high'] - last_candle['low']
                indicators['candle_body'] = abs(last_candle['close'] - last_candle['open'])
                indicators['upper_wick'] = last_candle['high'] - max(last_candle['close'], last_candle['open'])
                indicators['lower_wick'] = min(last_candle['close'], last_candle['open']) - last_candle['low']
                
                # Относительные размеры
                if indicators['price_range'] > 0:
                    indicators['body_ratio'] = indicators['candle_body'] / indicators['price_range']
                    indicators['upper_wick_ratio'] = indicators['upper_wick'] / indicators['price_range']
                    indicators['lower_wick_ratio'] = indicators['lower_wick'] / indicators['price_range']
                else:
                    indicators['body_ratio'] = 0.5
                    indicators['upper_wick_ratio'] = 0.0
                    indicators['lower_wick_ratio'] = 0.0
                
            except Exception as e:
                logger.error(f"❌ Ошибка Price Action: {e}")
                indicators.update({
                    'current_price': current_price,
                    'price_range': current_price * 0.01,
                    'candle_body': current_price * 0.005,
                    'upper_wick': 0,
                    'lower_wick': 0,
                    'body_ratio': 0.5,
                    'upper_wick_ratio': 0.0,
                    'lower_wick_ratio': 0.0
                })
            
            # ✅ МИКРО-ТРЕНД (последние 5 свечей)
            try:
                if len(df) >= 5:
                    price_5_ago = df['close'].iloc[-5]
                    indicators['micro_trend'] = 'UP' if current_price > price_5_ago else 'DOWN'
                    indicators['micro_trend_strength'] = abs(current_price - price_5_ago) / price_5_ago * 100
                else:
                    indicators['micro_trend'] = 'FLAT'
                    indicators['micro_trend_strength'] = 0.0
            except Exception as e:
                logger.error(f"❌ Ошибка Micro Trend: {e}")
                indicators['micro_trend'] = 'FLAT'
                indicators['micro_trend_strength'] = 0.0
            
            logger.debug(f"✅ Рассчитано {len(indicators)} индикаторов для скальпинга")
            return indicators
            
        except Exception as e:
            logger.error(f"💥 Критическая ошибка расчета индикаторов: {e}", exc_info=True)
            return {}
    
    def _check_scalping_conditions(self, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """
        🎯 ПРОВЕРКА УСЛОВИЙ для скальпинга
        
        Returns:
            Dict с информацией о сигнале
        """
        signal = {
            'direction': None,
            'strength': 0.0,
            'entry_type': None,
            'reasons': [],
            'confidence': 0.0
        }
        
        try:
            # ✅ ПРОВЕРКА ВОЛАТИЛЬНОСТИ
            atr_percent = indicators.get('atr_percent', 1.0)
            
            if atr_percent > self.MAX_VOLATILITY:
                signal['reasons'].append(f'Слишком высокая волатильность: {atr_percent:.2f}%')
                return signal
            
            if atr_percent < self.MIN_VOLATILITY:
                signal['reasons'].append(f'Слишком низкая волатильность: {atr_percent:.2f}%')
                return signal
            
            # ✅ ПРОВЕРКА ОБЪЕМА
            volume_ratio = indicators.get('volume_ratio', 1.0)
            if volume_ratio < self.min_volume_ratio:
                signal['reasons'].append(f'Недостаточный объем: {volume_ratio:.2f}x')
                return signal
            
            # Получаем основные параметры
            bb_percent = indicators.get('bb_percent', 0.5)
            rsi = indicators.get('rsi', 50.0)
            current_price = indicators.get('current_price', 0)
            vwap = indicators.get('vwap', current_price)
            lower_wick_ratio = indicators.get('lower_wick_ratio', 0.0)
            upper_wick_ratio = indicators.get('upper_wick_ratio', 0.0)
            micro_trend = indicators.get('micro_trend', 'FLAT')
            
            # === 🟢 УСЛОВИЯ ДЛЯ ПОКУПКИ ===
            
            # 1. Отскок от нижней Bollinger Band
            if (bb_percent < 0.2 and 
                rsi < 35 and
                lower_wick_ratio > 0.4):  # Длинная нижняя тень (40% от диапазона)
                
                signal['direction'] = 'BUY'
                signal['entry_type'] = 'BB_BOUNCE_LOW'
                signal['strength'] = 0.8
                signal['confidence'] = 0.8
                signal['reasons'].append(f'Отскок от нижней BB: RSI={rsi:.1f}, BB%={bb_percent:.2f}')
            
            # 2. Прорыв VWAP вверх с объемом
            elif (current_price > vwap and
                  current_price < vwap * 1.003 and  # В пределах 0.3% от VWAP
                  volume_ratio > self.min_volume_ratio and
                  micro_trend == 'UP' and
                  bb_percent > 0.3 and bb_percent < 0.7):  # В средней зоне BB
                
                signal['direction'] = 'BUY'
                signal['entry_type'] = 'VWAP_BREAKOUT_UP'
                signal['strength'] = 0.7
                signal['confidence'] = 0.75
                signal['reasons'].append(f'Прорыв VWAP вверх: объем={volume_ratio:.1f}x, тренд={micro_trend}')
            
            # 3. Быстрый отскок в средней зоне BB
            elif (bb_percent > 0.3 and bb_percent < 0.5 and
                  rsi > 45 and rsi < 55 and
                  lower_wick_ratio > 0.3 and
                  volume_ratio > 1.3):
                
                signal['direction'] = 'BUY'
                signal['entry_type'] = 'MIDDLE_BOUNCE'
                signal['strength'] = 0.6
                signal['confidence'] = 0.65
                signal['reasons'].append(f'Отскок в средней зоне: RSI={rsi:.1f}, тень={lower_wick_ratio:.2f}')
            
            # === 🔴 УСЛОВИЯ ДЛЯ ПРОДАЖИ ===
            
            # 1. Отскок от верхней Bollinger Band
            elif (bb_percent > 0.8 and
                  rsi > 65 and
                  upper_wick_ratio > 0.4):  # Длинная верхняя тень
                
                signal['direction'] = 'SELL'
                signal['entry_type'] = 'BB_BOUNCE_HIGH'
                signal['strength'] = 0.8
                signal['confidence'] = 0.8
                signal['reasons'].append(f'Отскок от верхней BB: RSI={rsi:.1f}, BB%={bb_percent:.2f}')
            
            # 2. Пробой VWAP вниз с объемом
            elif (current_price < vwap and
                  current_price > vwap * 0.997 and  # В пределах 0.3% от VWAP
                  volume_ratio > self.min_volume_ratio and
                  micro_trend == 'DOWN' and
                  bb_percent > 0.3 and bb_percent < 0.7):  # В средней зоне BB
                
                signal['direction'] = 'SELL'
                signal['entry_type'] = 'VWAP_BREAKOUT_DOWN'
                signal['strength'] = 0.7
                signal['confidence'] = 0.75
                signal['reasons'].append(f'Пробой VWAP вниз: объем={volume_ratio:.1f}x, тренд={micro_trend}')
            
            # 3. Быстрый разворот в средней зоне BB
            elif (bb_percent > 0.5 and bb_percent < 0.7 and
                  rsi > 45 and rsi < 55 and
                  upper_wick_ratio > 0.3 and
                  volume_ratio > 1.3):
                
                signal['direction'] = 'SELL'
                signal['entry_type'] = 'MIDDLE_REVERSAL'
                signal['strength'] = 0.6
                signal['confidence'] = 0.65
                signal['reasons'].append(f'Разворот в средней зоне: RSI={rsi:.1f}, тень={upper_wick_ratio:.2f}')
            
            else:
                # Нет подходящих условий для скальпинга
                signal['reasons'].append('Нет подходящих условий для скальпинга')
            
            return signal
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки условий скальпинга: {e}")
            signal['reasons'].append(f'Ошибка анализа: {str(e)[:50]}')
            return signal
    
    def _make_scalping_decision(self, scalp_signal: Dict[str, Any], 
                              indicators: Dict[str, Any], symbol: str) -> TradingSignal:
        """
        🎯 ПРИНЯТИЕ РЕШЕНИЯ для скальпинга
        
        Args:
            scalp_signal: Результат анализа условий
            indicators: Рассчитанные индикаторы
            symbol: Символ инструмента
            
        Returns:
            TradingSignal: Финальный сигнал
        """
        
        try:
            current_price = indicators.get('current_price', 0)
            
            # Если нет направления - ждем
            if not scalp_signal.get('direction'):
                reason = scalp_signal['reasons'][0] if scalp_signal['reasons'] else 'Нет сигнала скальпинга'
                return TradingSignal(
                    action='WAIT',
                    confidence=0,
                    price=current_price,
                    reason=f'⏳ {reason}',
                    indicators=indicators
                )
            
            # Проверяем минимальную уверенность
            confidence = scalp_signal.get('confidence', 0)
            if confidence < self.min_confidence:
                return TradingSignal(
                    action='WAIT',
                    confidence=confidence,
                    price=current_price,
                    reason=f'⚠️ Низкая уверенность для скальпинга: {confidence:.2f}',
                    indicators=indicators
                )
            
            # ✅ РАСЧЕТ УРОВНЕЙ для скальпинга (жесткие стопы!)
            direction = scalp_signal['direction']
            
            if direction == 'BUY':
                # Для покупки - жесткие уровни
                stop_loss = current_price * (1 - self.max_loss_percent / 100)
                take_profit = current_price * (1 + self.min_profit_percent / 100)
                
            else:  # SELL
                # Для продажи - жесткие уровни
                stop_loss = current_price * (1 + self.max_loss_percent / 100)
                take_profit = current_price * (1 - self.min_profit_percent / 100)
            
            # ✅ ПРОВЕРКА RISK/REWARD для скальпинга
            risk_reward = self.calculate_risk_reward(current_price, stop_loss, take_profit)
            
            # Для скальпинга допустим более низкий R:R
            min_rr = 0.8  # Минимум 0.8:1 для скальпинга
            if risk_reward < min_rr:
                return TradingSignal(
                    action='WAIT',
                    confidence=confidence,
                    price=current_price,
                    reason=f'⚠️ Низкий R:R для скальпинга: {risk_reward:.2f} < {min_rr}',
                    indicators=indicators
                )
            
            # ✅ ФОРМИРУЕМ ФИНАЛЬНЫЙ СИГНАЛ
            entry_type = scalp_signal.get('entry_type', 'UNKNOWN')
            reasons = scalp_signal.get('reasons', ['Скальпинг сигнал'])
            main_reason = reasons[0] if reasons else 'Скальпинг возможность'
            
            return TradingSignal(
                action=direction,
                confidence=confidence,
                price=current_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                reason=f'🚀 Скальпинг ({entry_type}): {main_reason}',
                risk_reward_ratio=risk_reward,
                indicators=indicators
            )
            
        except Exception as e:
            logger.error(f"💥 Ошибка принятия решения скальпинга для {symbol}: {e}")
            return TradingSignal(
                action='WAIT',
                confidence=0,
                price=indicators.get('current_price', 0),
                reason=f'💥 Ошибка принятия решения: {str(e)[:100]}'
            )