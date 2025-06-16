"""
Модуль оценки влияния новостей на рынок
Файл: src/analysis/news/impact_scorer.py
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from collections import defaultdict
import json

from sqlalchemy import and_, func, desc
from sqlalchemy.orm import Session

from ...core.database import SessionLocal
from ...core.models import Trade, Signal
from ...logging.smart_logger import SmartLogger
from .nlp_analyzer import nlp_analyzer


class NewsImpactScorer:
    """
    Оценивает влияние новостей на движение цен криптовалют
    """
    
    # Веса для различных факторов
    IMPACT_WEIGHTS = {
        'sentiment_strength': 0.25,      # Сила sentiment
        'entity_importance': 0.20,       # Важность упомянутых сущностей
        'keyword_density': 0.15,         # Плотность ключевых слов
        'source_credibility': 0.20,      # Достоверность источника
        'temporal_relevance': 0.10,      # Временная релевантность
        'market_volatility': 0.10        # Текущая волатильность рынка
    }
    
    # Рейтинг источников новостей
    SOURCE_CREDIBILITY = {
        # Высокая достоверность
        'bloomberg': 0.95,
        'reuters': 0.95,
        'coindesk': 0.90,
        'cointelegraph': 0.85,
        'the block': 0.85,
        'decrypt': 0.80,
        
        # Средняя достоверность
        'cryptonews': 0.70,
        'bitcoinist': 0.65,
        'newsbtc': 0.60,
        'u.today': 0.60,
        
        # Низкая достоверность
        'cryptopotato': 0.50,
        'bitcoinmagazine': 0.55,
        'default': 0.40  # Неизвестные источники
    }
    
    # Важные события и их базовое влияние
    MAJOR_EVENTS = {
        'regulation': {
            'keywords': ['sec', 'regulation', 'ban', 'legal', 'lawsuit', 'government'],
            'base_impact': 7.0
        },
        'adoption': {
            'keywords': ['adopt', 'accept', 'payment', 'integration', 'partnership'],
            'base_impact': 6.0
        },
        'hack': {
            'keywords': ['hack', 'breach', 'exploit', 'vulnerability', 'attack'],
            'base_impact': 8.0
        },
        'institutional': {
            'keywords': ['institutional', 'investment', 'fund', 'etf', 'grayscale'],
            'base_impact': 7.0
        },
        'technical': {
            'keywords': ['upgrade', 'fork', 'mainnet', 'testnet', 'launch'],
            'base_impact': 5.0
        },
        'market': {
            'keywords': ['crash', 'rally', 'ath', 'dump', 'pump', 'volatility'],
            'base_impact': 6.0
        }
    }
    
    def __init__(self):
        self.logger = SmartLogger("NewsImpactScorer")
        
        # Кэш для исторических корреляций
        self.correlation_cache = {}
        
        # История влияния новостей
        self.impact_history = defaultdict(list)
        
    def calculate_sentiment_impact(self, sentiment: Dict[str, float]) -> float:
        """
        Рассчитывает влияние на основе sentiment
        
        Args:
            sentiment: Результат анализа sentiment
            
        Returns:
            Оценка влияния от 0 до 1
        """
        # Используем compound score как основу
        compound = abs(sentiment.get('compound', 0))
        
        # Учитываем уверенность модели
        confidence = sentiment.get('confidence', 0.5)
        
        # Комбинированная оценка
        impact = compound * confidence
        
        # Усиливаем экстремальные значения
        if compound > 0.8:
            impact *= 1.2
        elif compound < 0.2:
            impact *= 0.8
        
        return min(impact, 1.0)
    
    def calculate_entity_impact(self, entities: Dict[str, List[str]]) -> float:
        """
        Рассчитывает влияние на основе упомянутых сущностей
        
        Args:
            entities: Извлеченные сущности
            
        Returns:
            Оценка влияния от 0 до 1
        """
        impact = 0.0
        
        # Важные организации
        important_orgs = [
            'sec', 'cftc', 'fed', 'ecb', 'imf',
            'blackrock', 'grayscale', 'microstrategy',
            'tesla', 'paypal', 'visa', 'mastercard'
        ]
        
        # Важные персоны
        important_persons = [
            'musk', 'saylor', 'powell', 'gensler',
            'yellen', 'lagarde', 'dimon'
        ]
        
        # Проверка организаций
        for org in entities.get('organizations', []):
            org_lower = org.lower()
            if any(imp_org in org_lower for imp_org in important_orgs):
                impact += 0.3
        
        # Проверка персон
        for person in entities.get('persons', []):
            person_lower = person.lower()
            if any(imp_person in person_lower for imp_person in important_persons):
                impact += 0.2
        
        # Проверка локаций (страны с крипторегулированием)
        important_locations = ['usa', 'china', 'europe', 'japan', 'korea']
        for location in entities.get('locations', []):
            if any(imp_loc in location.lower() for imp_loc in important_locations):
                impact += 0.1
        
        return min(impact, 1.0)
    
    def calculate_keyword_impact(self, keywords: List[str], text: str) -> float:
        """
        Рассчитывает влияние на основе ключевых слов
        
        Args:
            keywords: Список ключевых слов
            text: Полный текст для анализа
            
        Returns:
            Оценка влияния от 0 до 1
        """
        impact = 0.0
        text_lower = text.lower()
        
        # Проверка наличия ключевых слов из важных событий
        for event_type, event_data in self.MAJOR_EVENTS.items():
            event_keywords = event_data['keywords']
            matches = sum(1 for kw in event_keywords if kw in text_lower)
            
            if matches > 0:
                # Нормализованное влияние события
                event_impact = (matches / len(event_keywords)) * (event_data['base_impact'] / 10)
                impact = max(impact, event_impact)
        
        # Дополнительный анализ плотности важных слов
        important_words = [
            'breaking', 'urgent', 'confirmed', 'official',
            'major', 'significant', 'unprecedented', 'historic'
        ]
        
        urgent_count = sum(1 for word in important_words if word in text_lower)
        if urgent_count > 0:
            impact += urgent_count * 0.1
        
        return min(impact, 1.0)
    
    def calculate_source_impact(self, source: str) -> float:
        """
        Рассчитывает влияние на основе источника
        
        Args:
            source: Название источника
            
        Returns:
            Оценка достоверности от 0 до 1
        """
        source_lower = source.lower()
        
        # Проверяем известные источники
        for known_source, credibility in self.SOURCE_CREDIBILITY.items():
            if known_source in source_lower:
                return credibility
        
        # Неизвестный источник
        return self.SOURCE_CREDIBILITY['default']
    
    def calculate_temporal_impact(self, published_time: datetime) -> float:
        """
        Рассчитывает временную релевантность новости
        
        Args:
            published_time: Время публикации
            
        Returns:
            Оценка релевантности от 0 до 1
        """
        now = datetime.utcnow()
        time_diff = now - published_time
        
        # Новости теряют влияние со временем
        if time_diff < timedelta(minutes=30):
            return 1.0  # Очень свежие
        elif time_diff < timedelta(hours=2):
            return 0.8  # Свежие
        elif time_diff < timedelta(hours=6):
            return 0.6  # Относительно свежие
        elif time_diff < timedelta(hours=24):
            return 0.4  # Вчерашние
        elif time_diff < timedelta(days=3):
            return 0.2  # Старые
        else:
            return 0.1  # Очень старые
    
    async def get_market_volatility(self, symbol: str) -> float:
        """
        Получает текущую волатильность рынка
        
        Args:
            symbol: Торговый символ
            
        Returns:
            Нормализованная волатильность от 0 до 1
        """
        try:
            # TODO: Интеграция с реальными данными о волатильности
            # Пока используем заглушку
            return 0.5
            
        except Exception as e:
            self.logger.error(
                f"Ошибка получения волатильности: {e}",
                category='impact',
                symbol=symbol
            )
            return 0.5
    
    async def calculate_impact_score(self,
                                   news_data: Dict[str, Any],
                                   symbol: str = None) -> Dict[str, Any]:
        """
        Рассчитывает общую оценку влияния новости
        
        Args:
            news_data: Данные новости с NLP анализом
            symbol: Торговый символ (опционально)
            
        Returns:
            Словарь с оценками влияния
        """
        try:
            # Извлекаем компоненты
            sentiment = news_data.get('sentiment', {})
            entities = news_data.get('entities', {})
            keywords = news_data.get('keywords', [])
            text = news_data.get('text', '')
            source = news_data.get('source', 'unknown')
            published_at = news_data.get('published_at', datetime.utcnow())
            
            # Рассчитываем компоненты влияния
            sentiment_impact = self.calculate_sentiment_impact(sentiment)
            entity_impact = self.calculate_entity_impact(entities)
            keyword_impact = self.calculate_keyword_impact(keywords, text)
            source_impact = self.calculate_source_impact(source)
            temporal_impact = self.calculate_temporal_impact(published_at)
            
            # Волатильность рынка
            market_volatility = 0.5
            if symbol:
                market_volatility = await self.get_market_volatility(symbol)
            
            # Взвешенная сумма
            components = {
                'sentiment_strength': sentiment_impact,
                'entity_importance': entity_impact,
                'keyword_density': keyword_impact,
                'source_credibility': source_impact,
                'temporal_relevance': temporal_impact,
                'market_volatility': market_volatility
            }
            
            # Общая оценка
            total_impact = sum(
                components[factor] * weight 
                for factor, weight in self.IMPACT_WEIGHTS.items()
            )
            
            # Нормализация до 0-10
            total_impact = min(total_impact * 10, 10.0)
            
            # Определение направления влияния
            direction = 'neutral'
            if sentiment.get('label') == 'positive' and total_impact > 3:
                direction = 'bullish'
            elif sentiment.get('label') == 'negative' and total_impact > 3:
                direction = 'bearish'
            
            # Рекомендации по торговле
            trading_signal = self._generate_trading_signal(
                total_impact, direction, components
            )
            
            result = {
                'total_impact': round(total_impact, 2),
                'direction': direction,
                'components': components,
                'trading_signal': trading_signal,
                'confidence': self._calculate_confidence(components),
                'timestamp': datetime.utcnow()
            }
            
            # Сохраняем в историю
            if symbol:
                self.impact_history[symbol].append({
                    'score': total_impact,
                    'direction': direction,
                    'timestamp': datetime.utcnow()
                })
            
            self.logger.info(
                f"Оценка влияния: {total_impact:.2f} ({direction})",
                category='impact',
                symbol=symbol,
                components=components
            )
            
            return result
            
        except Exception as e:
            self.logger.error(
                f"Ошибка расчета влияния: {e}",
                category='impact'
            )
            
            return {
                'total_impact': 0.0,
                'direction': 'neutral',
                'components': {},
                'trading_signal': 'hold',
                'confidence': 0.0,
                'timestamp': datetime.utcnow(),
                'error': str(e)
            }
    
    def _generate_trading_signal(self, 
                                impact: float, 
                                direction: str,
                                components: Dict[str, float]) -> str:
        """
        Генерирует торговый сигнал на основе влияния
        
        Args:
            impact: Общая оценка влияния
            direction: Направление (bullish/bearish/neutral)
            components: Компоненты оценки
            
        Returns:
            Торговый сигнал: buy/sell/hold/watch
        """
        # Проверяем достоверность источника
        if components.get('source_credibility', 0) < 0.5:
            return 'watch'  # Низкая достоверность - только наблюдаем
        
        # Проверяем временную релевантность
        if components.get('temporal_relevance', 0) < 0.3:
            return 'hold'  # Старая новость - не действуем
        
        # Генерируем сигнал на основе влияния и направления
        if impact >= 7.0:
            # Сильное влияние
            if direction == 'bullish':
                return 'strong_buy'
            elif direction == 'bearish':
                return 'strong_sell'
        elif impact >= 5.0:
            # Среднее влияние
            if direction == 'bullish':
                return 'buy'
            elif direction == 'bearish':
                return 'sell'
        elif impact >= 3.0:
            # Слабое влияние
            return 'watch'
        
        return 'hold'
    
    def _calculate_confidence(self, components: Dict[str, float]) -> float:
        """
        Рассчитывает уверенность в оценке
        
        Args:
            components: Компоненты оценки
            
        Returns:
            Уверенность от 0 до 1
        """
        # Базовая уверенность на основе достоверности источника
        confidence = components.get('source_credibility', 0.5)
        
        # Учитываем согласованность компонентов
        values = list(components.values())
        if values:
            # Низкая дисперсия = высокая согласованность
            std_dev = np.std(values)
            consistency = 1.0 - min(std_dev, 1.0)
            confidence = (confidence + consistency) / 2
        
        # Учитываем силу сигналов
        strong_signals = sum(1 for v in values if v > 0.7)
        if strong_signals >= 3:
            confidence *= 1.2
        
        return min(confidence, 1.0)
    
    async def analyze_news_batch(self, 
                               news_items: List[Dict[str, Any]],
                               target_symbols: List[str] = None) -> List[Dict[str, Any]]:
        """
        Анализирует пакет новостей
        
        Args:
            news_items: Список новостей
            target_symbols: Целевые символы
            
        Returns:
            Список результатов анализа
        """
        results = []
        
        for news in news_items:
            # NLP анализ если еще не выполнен
            if 'sentiment' not in news:
                nlp_result = await nlp_analyzer.analyze_text(
                    news.get('content', ''),
                    news.get('title', ''),
                    target_symbols
                )
                news.update(nlp_result)
            
            # Оценка влияния для каждого релевантного символа
            detected_cryptos = news.get('detected_cryptos', [])
            
            if target_symbols:
                # Анализируем только для целевых символов
                symbols_to_analyze = [s for s in detected_cryptos if s in target_symbols]
            else:
                symbols_to_analyze = detected_cryptos
            
            if symbols_to_analyze:
                for symbol in symbols_to_analyze:
                    impact_result = await self.calculate_impact_score(news, symbol)
                    impact_result['symbol'] = symbol
                    impact_result['news_id'] = news.get('id')
                    results.append(impact_result)
            else:
                # Общий анализ без привязки к символу
                impact_result = await self.calculate_impact_score(news)
                impact_result['news_id'] = news.get('id')
                results.append(impact_result)
        
        return results
    
    def get_impact_statistics(self, symbol: str = None) -> Dict[str, Any]:
        """
        Получает статистику по влиянию новостей
        
        Args:
            symbol: Торговый символ (опционально)
            
        Returns:
            Статистика влияния
        """
        if symbol:
            history = self.impact_history.get(symbol, [])
        else:
            # Вся история
            history = []
            for symbol_history in self.impact_history.values():
                history.extend(symbol_history)
        
        if not history:
            return {
                'total_news': 0,
                'avg_impact': 0.0,
                'bullish_count': 0,
                'bearish_count': 0,
                'neutral_count': 0
            }
        
        impacts = [item['score'] for item in history]
        directions = [item['direction'] for item in history]
        
        return {
            'total_news': len(history),
            'avg_impact': np.mean(impacts),
            'max_impact': max(impacts),
            'min_impact': min(impacts),
            'bullish_count': directions.count('bullish'),
            'bearish_count': directions.count('bearish'),
            'neutral_count': directions.count('neutral'),
            'recent_trend': self._calculate_recent_trend(history)
        }
    
    def _calculate_recent_trend(self, history: List[Dict]) -> str:
        """
        Определяет недавний тренд новостей
        
        Args:
            history: История влияния
            
        Returns:
            Тренд: bullish/bearish/neutral
        """
        if len(history) < 3:
            return 'neutral'
        
        # Берем последние 10 новостей
        recent = history[-10:]
        
        bullish = sum(1 for item in recent if item['direction'] == 'bullish')
        bearish = sum(1 for item in recent if item['direction'] == 'bearish')
        
        if bullish > bearish * 1.5:
            return 'bullish'
        elif bearish > bullish * 1.5:
            return 'bearish'
        
        return 'neutral'


# Создаем глобальный экземпляр
impact_scorer = NewsImpactScorer()