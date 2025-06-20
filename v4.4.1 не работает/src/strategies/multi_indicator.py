"""
Мульти-индикаторная стратегия
Путь: /var/www/www-root/data/www/systemetech.ru/src/strategies/multi_indicator.py

🎯 ОСНОВНЫЕ УЛУЧШЕНИЯ:
- Исправлены все импорты
- Добавлена расширенная валидация данных
- Улучшена обработка ошибок
- Добавлено кеширование для производительности
- Усилена безопасность вычислений
"""

import pandas as pd
import numpy as np
import logging
import hashlib
from typing import Dict, Any, Optional, List, Tuple  # ✅ ВСЕ импорты из typing в одной строке

# Импорты технических индикаторов
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.trend import EMAIndicator, MACD, ADXIndicator
from ta.volatility import BollingerBands, AverageTrueRange
from ta.volume import OnBalanceVolumeIndicator

from .base import BaseStrategy, TradingSignal

logger = logging.getLogger(__name__)


class MultiIndicatorStrategy(BaseStrategy):
    """
    🎯 Продвинутая стратегия с множественными индикаторами
    
    Особенности:
    - Использует подтверждение от нескольких индикаторов
    - Кеширует вычисления для повышения производительности
    - Имеет расширенную валидацию входных данных
    - Защищена от ошибок деления на ноль и некорректных данных
    """
    
    # ✅ КОНСТАНТЫ: Все настройки в одном месте для легкой настройки
    RSI_OVERSOLD = 30
    RSI_OVERBOUGHT = 70
    STOCH_OVERSOLD = 20
    STOCH_OVERBOUGHT = 80
    ADX_TREND_THRESHOLD = 25
    VOLUME_RATIO_THRESHOLD = 1.5
    BB_LOWER_THRESHOLD = 0.2
    BB_UPPER_THRESHOLD = 0.8
    MIN_DATA_LENGTH = 200  # Минимум данных для корректной работы всех индикаторов
    MIN_VOLATILITY_THRESHOLD = 0.01  # Минимальная волатильность для торговли
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        🏗️ КОНСТРУКТОР с гибкой конфигурацией
        
        Args:
            config: Словарь настроек стратегии
                - min_confidence: минимальная уверенность для сигнала (default: 0.65)
                - min_indicators_confirm: минимум индикаторов для подтверждения (default: 3)
                - rsi_oversold/overbought: пороги RSI (default: 30/70)
                - и другие параметры...
        """
        super().__init__("multi_indicator")
        
        # ✅ ГИБКАЯ КОНФИГУРАЦИЯ: Можно настроить через config или использовать по умолчанию
        if config:
            self.min_confidence = config.get('min_confidence', 0.65)
            self.min_indicators_confirm = config.get('min_indicators_confirm', 3)
            
            # Переопределяем константы из конфига, если они есть
            self.RSI_OVERSOLD = config.get('rsi_oversold', self.RSI_OVERSOLD)
            self.RSI_OVERBOUGHT = config.get('rsi_overbought', self.RSI_OVERBOUGHT)
            self.STOCH_OVERSOLD = config.get('stoch_oversold', self.STOCH_OVERSOLD)
            self.STOCH_OVERBOUGHT = config.get('stoch_overbought', self.STOCH_OVERBOUGHT)
            self.ADX_TREND_THRESHOLD = config.get('adx_threshold', self.ADX_TREND_THRESHOLD)
            self.VOLUME_RATIO_THRESHOLD = config.get('volume_threshold', self.VOLUME_RATIO_THRESHOLD)
        else:
            # Значения по умолчанию
            self.min_confidence = 0.65
            self.min_indicators_confirm = 3
        
        # ✅ КЕШИРОВАНИЕ: Для повышения производительности
        self._indicators_cache = {}
        self._last_df_hash = None
        
        logger.info(f"🚀 MultiIndicatorStrategy инициализирована с min_confidence={self.min_confidence}")
    
    async def analyze(self, df: pd.DataFrame, symbol: str) -> TradingSignal:
        """
        🔍 ГЛАВНЫЙ МЕТОД АНАЛИЗА с комплексными проверками
        
        Args:
            df: DataFrame с OHLCV данными
            symbol: Символ торгового инструмента
            
        Returns:
            TradingSignal: Сигнал с рекомендацией (BUY/SELL/WAIT)
        """
        
        # ✅ РАННЯЯ ВАЛИДАЦИЯ: Проверяем данные перед началом работы
        validation_result = self._validate_input_data(df, symbol)
        if validation_result:
            return validation_result  # Возвращаем сигнал WAIT с описанием проблемы
        
        try:
            # ✅ КЕШИРОВАНИЕ: Проверяем, не вычисляли ли мы уже эти данные
            df_hash = self._calculate_dataframe_hash(df)
            if df_hash == self._last_df_hash and self._indicators_cache:
                logger.debug(f"📋 Используем кешированные индикаторы для {symbol}")
                indicators = self._indicators_cache
            else:
                # Вычисляем индикаторы заново
                logger.debug(f"🔄 Вычисляем новые индикаторы для {symbol}")
                indicators = self._calculate_indicators(df)
                
                # Проверяем успешность вычислений
                if not indicators:
                    return TradingSignal('WAIT', 0, 0, reason='❌ Ошибка расчета индикаторов')
                
                # Сохраняем в кеш
                self._indicators_cache = indicators
                self._last_df_hash = df_hash
            
            # Анализируем сигналы от каждого индикатора
            signals = self._analyze_signals(indicators, df)
            
            # Принимаем финальное решение
            return self._make_decision(signals, indicators, df, symbol)
            
        except Exception as e:
            logger.error(f"💥 Критическая ошибка анализа {symbol}: {e}", exc_info=True)
            return TradingSignal('WAIT', 0, 0, reason=f'💥 Критическая ошибка: {str(e)[:100]}')
    
    def _validate_input_data(self, df: pd.DataFrame, symbol: str) -> Optional[TradingSignal]:
        """
        🛡️ РАСШИРЕННАЯ ВАЛИДАЦИЯ входных данных
        
        Проверяет:
        - Существование и непустоту DataFrame
        - Наличие всех необходимых колонок
        - Отсутствие NaN и некорректных значений
        - Достаточность данных для вычислений
        
        Returns:
            None если данные корректны, иначе TradingSignal с ошибкой
        """
        
        # Проверка на None и пустоту
        if df is None:
            logger.error(f"❌ DataFrame is None для {symbol}")
            return TradingSignal('WAIT', 0, 0, reason='❌ Отсутствуют данные')
        
        if df.empty:
            logger.error(f"❌ DataFrame пустой для {symbol}")
            return TradingSignal('WAIT', 0, 0, reason='❌ Пустой набор данных')
        
        # Проверка обязательных колонок
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            logger.error(f"❌ Отсутствуют колонки {missing_columns} для {symbol}")
            return TradingSignal('WAIT', 0, 0, 
                               reason=f'❌ Отсутствуют данные: {", ".join(missing_columns)}')
        
        # Проверка на NaN значения
        nan_columns = df[required_columns].columns[df[required_columns].isnull().any()].tolist()
        if nan_columns:
            logger.warning(f"⚠️ NaN значения в колонках {nan_columns} для {symbol}")
            return TradingSignal('WAIT', 0, 0, 
                               reason=f'⚠️ Неполные данные в: {", ".join(nan_columns)}')
        
        # Проверка на некорректные цены (отрицательные или нулевые)
        price_columns = ['open', 'high', 'low', 'close']
        invalid_prices = (df[price_columns] <= 0).any()
        if invalid_prices.any():
            invalid_cols = invalid_prices[invalid_prices].index.tolist()
            logger.error(f"❌ Некорректные цены в {invalid_cols} для {symbol}")
            return TradingSignal('WAIT', 0, 0, 
                               reason=f'❌ Некорректные цены в: {", ".join(invalid_cols)}')
        
        # Проверка логики цен (high >= low, close между high и low)
        if (df['high'] < df['low']).any():
            logger.error(f"❌ High < Low в данных для {symbol}")
            return TradingSignal('WAIT', 0, 0, reason='❌ Нарушена логика цен (High < Low)')
        
        if ((df['close'] > df['high']) | (df['close'] < df['low'])).any():
            logger.error(f"❌ Close вне диапазона High-Low для {symbol}")
            return TradingSignal('WAIT', 0, 0, reason='❌ Close цена вне диапазона High-Low')
        
        # Проверка достаточности данных
        if len(df) < self.MIN_DATA_LENGTH:
            logger.warning(f"⚠️ Недостаточно данных для {symbol}: {len(df)} < {self.MIN_DATA_LENGTH}")
            return TradingSignal('WAIT', 0, 0, 
                               reason=f'⚠️ Мало данных: {len(df)}/{self.MIN_DATA_LENGTH}')
        
        # Проверка на отрицательные объемы
        if (df['volume'] < 0).any():
            logger.error(f"❌ Отрицательные объемы для {symbol}")
            return TradingSignal('WAIT', 0, 0, reason='❌ Некорректные данные объемов')
        
        logger.debug(f"✅ Валидация данных пройдена для {symbol}")
        return None  # Все проверки пройдены
    
    def _calculate_dataframe_hash(self, df: pd.DataFrame) -> str:
        """
        🔢 ВЫЧИСЛЕНИЕ ХЕША DataFrame для кеширования
        
        Создает уникальный хеш на основе последних 50 строк данных.
        Это позволяет определить, изменились ли данные с последнего анализа.
        """
        try:
            # Берем последние 50 строк для хеширования (достаточно для определения изменений)
            recent_data = df.tail(50)
            data_string = recent_data.to_string()
            return hashlib.md5(data_string.encode()).hexdigest()
        except Exception as e:
            logger.warning(f"⚠️ Ошибка вычисления хеша: {e}")
            return str(hash(str(df.iloc[-1].tolist())))  # Fallback хеш
    
    def _calculate_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        📊 БЕЗОПАСНЫЙ РАСЧЕТ ВСЕХ ИНДИКАТОРОВ с защитой от ошибок
        
        Returns:
            Dict с рассчитанными индикаторами или пустой dict при ошибке
        """
        indicators = {}
        
        try:
            logger.debug("📊 Начинаем расчет технических индикаторов...")
            
            # ✅ RSI - Индекс относительной силы
            indicators.update(self._calculate_rsi_safely(df))
            
            # ✅ MACD - Схождение-расхождение скользящих средних
            indicators.update(self._calculate_macd_safely(df))
            
            # ✅ Bollinger Bands - Полосы Боллинджера
            indicators.update(self._calculate_bollinger_safely(df))
            
            # ✅ EMA - Экспоненциальные скользящие средние
            indicators.update(self._calculate_ema_safely(df))
            
            # ✅ ADX - Индекс направленного движения
            indicators.update(self._calculate_adx_safely(df))
            
            # ✅ ATR - Средний истинный диапазон (для стоп-лоссов)
            indicators.update(self._calculate_atr_safely(df))
            
            # ✅ Volume indicators - Объемные индикаторы
            indicators.update(self._calculate_volume_safely(df))
            
            # ✅ Stochastic - Стохастический осциллятор
            indicators.update(self._calculate_stochastic_safely(df))
            
            # ✅ Price action - Ценовые данные
            indicators.update(self._calculate_price_action(df))
            
            logger.debug(f"✅ Успешно рассчитано {len(indicators)} индикаторов")
            return indicators
            
        except Exception as e:
            logger.error(f"💥 Критическая ошибка расчета индикаторов: {e}", exc_info=True)
            return {}
    
    def _calculate_rsi_safely(self, df: pd.DataFrame) -> Dict[str, float]:
        """📈 БЕЗОПАСНЫЙ РАСЧЕТ RSI"""
        try:
            if len(df) >= 14:  # RSI требует минимум 14 периодов
                rsi_indicator = RSIIndicator(df['close'], window=14)
                rsi_values = rsi_indicator.rsi()
                
                if not rsi_values.empty and not pd.isna(rsi_values.iloc[-1]):
                    return {'rsi': float(rsi_values.iloc[-1])}
            
            logger.warning("⚠️ Недостаточно данных для RSI, используем нейтральное значение")
            return {'rsi': 50.0}  # Нейтральное значение
            
        except Exception as e:
            logger.error(f"❌ Ошибка расчета RSI: {e}")
            return {'rsi': 50.0}
    
    def _calculate_macd_safely(self, df: pd.DataFrame) -> Dict[str, float]:
        """📊 БЕЗОПАСНЫЙ РАСЧЕТ MACD"""
        try:
            if len(df) >= 26:  # MACD требует минимум 26 периодов
                macd = MACD(df['close'])
                macd_line = macd.macd()
                macd_signal = macd.macd_signal()
                macd_diff = macd.macd_diff()
                
                result = {}
                
                # Проверяем каждое значение отдельно
                if not macd_line.empty and not pd.isna(macd_line.iloc[-1]):
                    result['macd'] = float(macd_line.iloc[-1])
                else:
                    result['macd'] = 0.0
                
                if not macd_signal.empty and not pd.isna(macd_signal.iloc[-1]):
                    result['macd_signal'] = float(macd_signal.iloc[-1])
                else:
                    result['macd_signal'] = 0.0
                
                if not macd_diff.empty and not pd.isna(macd_diff.iloc[-1]):
                    result['macd_diff'] = float(macd_diff.iloc[-1])
                else:
                    result['macd_diff'] = 0.0
                
                return result
            
            logger.warning("⚠️ Недостаточно данных для MACD")
            return {'macd': 0.0, 'macd_signal': 0.0, 'macd_diff': 0.0}
            
        except Exception as e:
            logger.error(f"❌ Ошибка расчета MACD: {e}")
            return {'macd': 0.0, 'macd_signal': 0.0, 'macd_diff': 0.0}
    
    def _calculate_bollinger_safely(self, df: pd.DataFrame) -> Dict[str, float]:
        """📏 БЕЗОПАСНЫЙ РАСЧЕТ BOLLINGER BANDS"""
        try:
            if len(df) >= 20:  # BB требует минимум 20 периодов
                bb = BollingerBands(df['close'], window=20, window_dev=2)
                
                bb_upper = bb.bollinger_hband()
                bb_middle = bb.bollinger_mavg()
                bb_lower = bb.bollinger_lband()
                bb_width = bb.bollinger_wband()
                bb_percent = bb.bollinger_pband()
                
                current_price = df['close'].iloc[-1]
                
                result = {}
                
                # Безопасное извлечение значений
                result['bb_upper'] = float(bb_upper.iloc[-1]) if not bb_upper.empty and not pd.isna(bb_upper.iloc[-1]) else current_price * 1.02
                result['bb_middle'] = float(bb_middle.iloc[-1]) if not bb_middle.empty and not pd.isna(bb_middle.iloc[-1]) else current_price
                result['bb_lower'] = float(bb_lower.iloc[-1]) if not bb_lower.empty and not pd.isna(bb_lower.iloc[-1]) else current_price * 0.98
                result['bb_width'] = float(bb_width.iloc[-1]) if not bb_width.empty and not pd.isna(bb_width.iloc[-1]) else 0.02
                result['bb_percent'] = float(bb_percent.iloc[-1]) if not bb_percent.empty and not pd.isna(bb_percent.iloc[-1]) else 0.5
                
                return result
            
            current_price = df['close'].iloc[-1]
            logger.warning("⚠️ Недостаточно данных для Bollinger Bands")
            return {
                'bb_upper': current_price * 1.02,
                'bb_middle': current_price,
                'bb_lower': current_price * 0.98,
                'bb_width': 0.02,
                'bb_percent': 0.5
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка расчета Bollinger Bands: {e}")
            current_price = df['close'].iloc[-1] if len(df) > 0 else 100.0
            return {
                'bb_upper': current_price * 1.02,
                'bb_middle': current_price,
                'bb_lower': current_price * 0.98,
                'bb_width': 0.02,
                'bb_percent': 0.5
            }
    
    def _calculate_ema_safely(self, df: pd.DataFrame) -> Dict[str, float]:
        """📈 БЕЗОПАСНЫЙ РАСЧЕТ EMA для разных периодов"""
        result = {}
        periods = [9, 21, 50, 200]
        current_price = df['close'].iloc[-1]
        
        for period in periods:
            try:
                if len(df) >= period:
                    ema_indicator = EMAIndicator(df['close'], window=period)
                    ema_values = ema_indicator.ema_indicator()
                    
                    if not ema_values.empty and not pd.isna(ema_values.iloc[-1]):
                        result[f'ema_{period}'] = float(ema_values.iloc[-1])
                    else:
                        result[f'ema_{period}'] = current_price
                else:
                    # Если данных мало, используем текущую цену
                    result[f'ema_{period}'] = current_price
                    
            except Exception as e:
                logger.error(f"❌ Ошибка расчета EMA-{period}: {e}")
                result[f'ema_{period}'] = current_price
        
        return result
    
    def _calculate_adx_safely(self, df: pd.DataFrame) -> Dict[str, float]:
        """💪 БЕЗОПАСНЫЙ РАСЧЕТ ADX (сила тренда)"""
        try:
            if len(df) >= 14:  # ADX требует минимум 14 периодов
                adx = ADXIndicator(df['high'], df['low'], df['close'])
                adx_values = adx.adx()
                adx_pos_values = adx.adx_pos()
                adx_neg_values = adx.adx_neg()
                
                result = {}
                result['adx'] = float(adx_values.iloc[-1]) if not adx_values.empty and not pd.isna(adx_values.iloc[-1]) else 0.0
                result['adx_pos'] = float(adx_pos_values.iloc[-1]) if not adx_pos_values.empty and not pd.isna(adx_pos_values.iloc[-1]) else 0.0
                result['adx_neg'] = float(adx_neg_values.iloc[-1]) if not adx_neg_values.empty and not pd.isna(adx_neg_values.iloc[-1]) else 0.0
                
                return result
            
            logger.warning("⚠️ Недостаточно данных для ADX")
            return {'adx': 0.0, 'adx_pos': 0.0, 'adx_neg': 0.0}
            
        except Exception as e:
            logger.error(f"❌ Ошибка расчета ADX: {e}")
            return {'adx': 0.0, 'adx_pos': 0.0, 'adx_neg': 0.0}
    
    def _calculate_atr_safely(self, df: pd.DataFrame) -> Dict[str, float]:
        """📏 БЕЗОПАСНЫЙ РАСЧЕТ ATR для стоп-лоссов"""
        try:
            if len(df) >= 14:  # ATR требует минимум 14 периодов
                atr = AverageTrueRange(df['high'], df['low'], df['close'])
                atr_values = atr.average_true_range()
                
                if not atr_values.empty and not pd.isna(atr_values.iloc[-1]):
                    return {'atr': float(atr_values.iloc[-1])}
            
            # Fallback: 2% от текущей цены
            fallback_atr = df['close'].iloc[-1] * 0.02
            logger.warning(f"⚠️ Используем fallback ATR: {fallback_atr}")
            return {'atr': fallback_atr}
            
        except Exception as e:
            logger.error(f"❌ Ошибка расчета ATR: {e}")
            return {'atr': df['close'].iloc[-1] * 0.02}
    
    def _calculate_volume_safely(self, df: pd.DataFrame) -> Dict[str, float]:
        """📊 БЕЗОПАСНЫЙ РАСЧЕТ ОБЪЕМНЫХ ИНДИКАТОРОВ"""
        try:
            current_volume = df['volume'].iloc[-1]
            
            if len(df) >= 20:
                volume_sma = df['volume'].rolling(window=20).mean().iloc[-1]
                
                # Защита от деления на ноль
                if pd.notna(volume_sma) and volume_sma > 0:
                    volume_ratio = current_volume / volume_sma
                else:
                    volume_ratio = 1.0
                    volume_sma = current_volume
            else:
                # Если данных мало, берем среднее из доступных
                volume_sma = df['volume'].mean()
                volume_ratio = current_volume / volume_sma if volume_sma > 0 else 1.0
            
            return {
                'volume_sma': float(volume_sma),
                'volume_ratio': float(volume_ratio)
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка расчета объемных индикаторов: {e}")
            current_volume = df['volume'].iloc[-1] if len(df) > 0 else 1.0
            return {'volume_sma': current_volume, 'volume_ratio': 1.0}
    
    def _calculate_stochastic_safely(self, df: pd.DataFrame) -> Dict[str, float]:
        """📈 БЕЗОПАСНЫЙ РАСЧЕТ STOCHASTIC"""
        try:
            if len(df) >= 14:  # Stochastic требует минимум 14 периодов
                stoch = StochasticOscillator(df['high'], df['low'], df['close'])
                stoch_k_values = stoch.stoch()
                stoch_d_values = stoch.stoch_signal()
                
                result = {}
                result['stoch_k'] = float(stoch_k_values.iloc[-1]) if not stoch_k_values.empty and not pd.isna(stoch_k_values.iloc[-1]) else 50.0
                result['stoch_d'] = float(stoch_d_values.iloc[-1]) if not stoch_d_values.empty and not pd.isna(stoch_d_values.iloc[-1]) else 50.0
                
                return result
            
            logger.warning("⚠️ Недостаточно данных для Stochastic")
            return {'stoch_k': 50.0, 'stoch_d': 50.0}
            
        except Exception as e:
            logger.error(f"❌ Ошибка расчета Stochastic: {e}")
            return {'stoch_k': 50.0, 'stoch_d': 50.0}
    
    def _calculate_price_action(self, df: pd.DataFrame) -> Dict[str, float]:
        """💰 РАСЧЕТ ЦЕНОВЫХ ХАРАКТЕРИСТИК"""
        try:
            current_price = float(df['close'].iloc[-1])
            
            # Изменение цены за последний период
            if len(df) >= 2:
                prev_price = df['close'].iloc[-2]
                price_change = ((current_price - prev_price) / prev_price * 100) if prev_price > 0 else 0.0
            else:
                price_change = 0.0
            
            return {
                'current_price': current_price,
                'price_change': float(price_change)
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка расчета ценовых данных: {e}")
            return {'current_price': 100.0, 'price_change': 0.0}
    
    def _analyze_signals(self, indicators: Dict[str, Any], df: pd.DataFrame) -> Dict[str, List]:
        """
        🔍 АНАЛИЗ СИГНАЛОВ от каждого индикатора
        
        Каждый сигнал представлен как кортеж: (название_индикатора, описание, вес)
        Вес от 0.0 до 1.0 показывает силу сигнала
        """
        signals = {
            'buy_signals': [],
            'sell_signals': [],
            'neutral_signals': []
        }
        
        try:
            # 📈 RSI СИГНАЛЫ
            rsi = indicators.get('rsi', 50)
            if rsi < self.RSI_OVERSOLD:
                signals['buy_signals'].append(('RSI', f'Перепроданность ({rsi:.1f})', 0.8))
            elif rsi > self.RSI_OVERBOUGHT:
                signals['sell_signals'].append(('RSI', f'Перекупленность ({rsi:.1f})', 0.8))
            
            # 📊 MACD СИГНАЛЫ
            macd = indicators.get('macd', 0)
            macd_signal = indicators.get('macd_signal', 0)
            macd_diff = indicators.get('macd_diff', 0)
            
            if macd > macd_signal and macd_diff > 0:
                signals['buy_signals'].append(('MACD', 'Бычье пересечение', 0.7))
            elif macd < macd_signal and macd_diff < 0:
                signals['sell_signals'].append(('MACD', 'Медвежье пересечение', 0.7))
            
            # 📏 BOLLINGER BANDS СИГНАЛЫ
            bb_percent = indicators.get('bb_percent', 0.5)
            if bb_percent < self.BB_LOWER_THRESHOLD:
                signals['buy_signals'].append(('BB', f'Цена у нижней границы ({bb_percent:.2f})', 0.6))
            elif bb_percent > self.BB_UPPER_THRESHOLD:
                signals['sell_signals'].append(('BB', f'Цена у верхней границы ({bb_percent:.2f})', 0.6))
            
            # 📈 EMA ТРЕНД АНАЛИЗ
            current_price = indicators.get('current_price', 0)
            ema_9 = indicators.get('ema_9', 0)
            ema_21 = indicators.get('ema_21', 0)
            ema_50 = indicators.get('ema_50', 0)
            
            # Проверяем восходящий тренд
            if (ema_9 > ema_21 > ema_50 and current_price > ema_9):
                signals['buy_signals'].append(('EMA', 'Восходящий тренд', 0.7))
            # Проверяем нисходящий тренд
            elif (ema_9 < ema_21 < ema_50 and current_price < ema_9):
                signals['sell_signals'].append(('EMA', 'Нисходящий тренд', 0.7))
            
            # 💪 ADX СИЛА ТРЕНДА
            adx = indicators.get('adx', 0)
            adx_pos = indicators.get('adx_pos', 0)
            adx_neg = indicators.get('adx_neg', 0)
            
            if adx > self.ADX_TREND_THRESHOLD:
                if adx_pos > adx_neg:
                    signals['buy_signals'].append(('ADX', f'Сильный восходящий тренд ({adx:.1f})', 0.6))
                else:
                    signals['sell_signals'].append(('ADX', f'Сильный нисходящий тренд ({adx:.1f})', 0.6))
            
            # 📊 VOLUME ПОДТВЕРЖДЕНИЕ
            volume_ratio = indicators.get('volume_ratio', 1.0)
            if volume_ratio > self.VOLUME_RATIO_THRESHOLD:
                signals['neutral_signals'].append(('Volume', f'Высокий объем ({volume_ratio:.1f}x)', 0.5))
            
            # 📈 STOCHASTIC СИГНАЛЫ
            stoch_k = indicators.get('stoch_k', 50)
            stoch_d = indicators.get('stoch_d', 50)
            
            if stoch_k < self.STOCH_OVERSOLD and stoch_k > stoch_d:
                signals['buy_signals'].append(('Stochastic', f'Перепроданность + пересечение ({stoch_k:.1f})', 0.6))
            elif stoch_k > self.STOCH_OVERBOUGHT and stoch_k < stoch_d:
                signals['sell_signals'].append(('Stochastic', f'Перекупленность + пересечение ({stoch_k:.1f})', 0.6))
            
            logger.debug(f"🔍 Найдено сигналов: BUY={len(signals['buy_signals'])}, SELL={len(signals['sell_signals'])}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка анализа сигналов: {e}")
        
        return signals
    
    def _make_decision(self, signals: Dict[str, List], indicators: Dict[str, Any], 
                      df: pd.DataFrame, symbol: str) -> TradingSignal:
        """
        🎯 ПРИНЯТИЕ ФИНАЛЬНОГО РЕШЕНИЯ на основе всех сигналов
        
        Алгоритм:
        1. Подсчитываем общий счет и количество сигналов
        2. Проверяем минимальные требования
        3. Проверяем рыночные условия (волатильность)
        4. Формируем итоговый сигнал
        """
        
        try:
            buy_signals = signals.get('buy_signals', [])
            sell_signals = signals.get('sell_signals', [])
            
            # Защита от пустых сигналов
            if not buy_signals and not sell_signals:
                return TradingSignal('WAIT', 0, 0, reason='🤷 Нет торговых сигналов', indicators=indicators)
            
            # Подсчет очков и количества
            buy_score = sum(signal[2] for signal in buy_signals)
            sell_score = sum(signal[2] for signal in sell_signals)
            buy_count = len(buy_signals)
            sell_count = len(sell_signals)
            
            current_price = indicators.get('current_price', 0)
            if current_price <= 0:
                return TradingSignal('WAIT', 0, 0, reason='❌ Некорректная цена', indicators=indicators)
            
            atr = indicators.get('atr', current_price * 0.02)
            
            # ✅ ПРОВЕРКА ВОЛАТИЛЬНОСТИ: Избегаем торговли при низкой волатильности
            bb_width = indicators.get('bb_width', 0)
            if bb_width < self.MIN_VOLATILITY_THRESHOLD:
                return TradingSignal('WAIT', 0, 0, 
                                   reason=f'📊 Низкая волатильность ({bb_width:.3f})', 
                                   indicators=indicators)
            
            logger.debug(f"📊 Счет сигналов для {symbol}: BUY={buy_score:.2f}({buy_count}), SELL={sell_score:.2f}({sell_count})")
            
            # 🔍 ЛОГИКА ПРИНЯТИЯ РЕШЕНИЯ
            
            # BUY СИГНАЛ
            if (buy_count >= self.min_indicators_confirm and 
                buy_score > sell_score and 
                buy_score >= self.min_confidence):
                
                return self._create_buy_signal(current_price, atr, buy_score, buy_count, 
                                             buy_signals, indicators)
            
            # SELL СИГНАЛ
            elif (sell_count >= self.min_indicators_confirm and 
                  sell_score > buy_score and 
                  sell_score >= self.min_confidence):
                
                return self._create_sell_signal(current_price, atr, sell_score, sell_count, 
                                              sell_signals, indicators)
            
            # WAIT СИГНАЛ
            else:
                reason_parts = []
                
                if buy_count < self.min_indicators_confirm and sell_count < self.min_indicators_confirm:
                    reason_parts.append(f"Мало подтверждений (BUY:{buy_count}, SELL:{sell_count})")
                
                if max(buy_score, sell_score) < self.min_confidence:
                    reason_parts.append(f"Низкая уверенность ({max(buy_score, sell_score):.2f})")
                
                if abs(buy_score - sell_score) < 0.3:
                    reason_parts.append("Противоречивые сигналы")
                
                reason = " | ".join(reason_parts) if reason_parts else "Нет четких сигналов"
                
                return TradingSignal('WAIT', 0, current_price, reason=f'⏳ {reason}', indicators=indicators)
        
        except Exception as e:
            logger.error(f"💥 Ошибка принятия решения для {symbol}: {e}")
            return TradingSignal('WAIT', 0, 0, reason=f'💥 Ошибка принятия решения: {str(e)[:100]}')
    
    def _create_buy_signal(self, current_price: float, atr: float, buy_score: float, 
                          buy_count: int, buy_signals: List, indicators: Dict) -> TradingSignal:
        """🟢 СОЗДАНИЕ BUY СИГНАЛА"""
        try:
            # Расчет уровней
            stop_loss = self.calculate_stop_loss(current_price, 'BUY', atr)
            take_profit = self.calculate_take_profit(current_price, 'BUY', atr)
            risk_reward = self.calculate_risk_reward(current_price, stop_loss, take_profit)
            
            # Расчет уверенности (нормализуем к максимум 0.95)
            max_possible_score = buy_count * 0.8  # Средний максимальный вес сигнала
            confidence = min(0.95, buy_score / max_possible_score) if max_possible_score > 0 else 0.5
            
            # Формируем причины (топ-3 самых сильных)
            top_signals = sorted(buy_signals, key=lambda x: x[2], reverse=True)[:3]
            reasons = [f"{sig[0]}: {sig[1]}" for sig in top_signals]
            reason = " | ".join(reasons)
            
            return TradingSignal(
                action='BUY',
                confidence=confidence,
                price=current_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                reason=f'🟢 {reason}',
                risk_reward_ratio=risk_reward,
                indicators=indicators
            )
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания BUY сигнала: {e}")
            return TradingSignal('WAIT', 0, current_price, reason='❌ Ошибка создания BUY сигнала')
    
    def _create_sell_signal(self, current_price: float, atr: float, sell_score: float, 
                           sell_count: int, sell_signals: List, indicators: Dict) -> TradingSignal:
        """🔴 СОЗДАНИЕ SELL СИГНАЛА"""
        try:
            # Расчет уровней
            stop_loss = self.calculate_stop_loss(current_price, 'SELL', atr)
            take_profit = self.calculate_take_profit(current_price, 'SELL', atr)
            risk_reward = self.calculate_risk_reward(current_price, stop_loss, take_profit)
            
            # Расчет уверенности
            max_possible_score = sell_count * 0.8
            confidence = min(0.95, sell_score / max_possible_score) if max_possible_score > 0 else 0.5
            
            # Формируем причины (топ-3 самых сильных)
            top_signals = sorted(sell_signals, key=lambda x: x[2], reverse=True)[:3]
            reasons = [f"{sig[0]}: {sig[1]}" for sig in top_signals]
            reason = " | ".join(reasons)
            
            return TradingSignal(
                action='SELL',
                confidence=confidence,
                price=current_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                reason=f'🔴 {reason}',
                risk_reward_ratio=risk_reward,
                indicators=indicators
            )
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания SELL сигнала: {e}")
            return TradingSignal('WAIT', 0, current_price, reason='❌ Ошибка создания SELL сигнала')