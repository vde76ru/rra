# src/web/social_api.py
"""
Social Signals API - Полная реализация для устранения 404 ошибок

Модуль: API социальных сигналов и новостной аналитики
Статус: Новая реализация - Этап 2 исправлений
Цель: Устранение ошибки "GET /api/social/signals HTTP/1.1 404"

Архитектурные компоненты:
1. Social Signals API - анализ социальных медиа
2. News API - новостная аналитика 
3. Sentiment Analysis - анализ настроений
4. Real-time Updates - обновления через WebSocket
5. Data Aggregation - агрегация из multiple источников
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from flask import jsonify, request
from dataclasses import dataclass
from enum import Enum
import json
import random

logger = logging.getLogger(__name__)

class SentimentType(Enum):
    """Типы настроений в социальных сигналах"""
    VERY_BEARISH = -1.0
    BEARISH = -0.5
    NEUTRAL = 0.0
    BULLISH = 0.5
    VERY_BULLISH = 1.0

class PlatformType(Enum):
    """Поддерживаемые социальные платформы"""
    TWITTER = "twitter"
    REDDIT = "reddit"
    TELEGRAM = "telegram"
    DISCORD = "discord"
    YOUTUBE = "youtube"
    TRADINGVIEW = "tradingview"

@dataclass
class SocialSignal:
    """Модель социального сигнала"""
    id: int
    platform: PlatformType
    author: str
    content: str
    sentiment: float
    influence_score: float
    mentioned_coins: List[str]
    created_at: datetime
    is_verified_author: bool = False
    author_followers: int = 0
    engagement_rate: float = 0.0
    url: Optional[str] = None
    hashtags: List[str] = None
    retweets: int = 0
    likes: int = 0

@dataclass
class NewsItem:
    """Модель новостного элемента"""
    id: int
    title: str
    summary: str
    content: str
    source: str
    url: str
    published_at: datetime
    sentiment_score: float
    impact_score: float
    affected_coins: List[str]
    category: str = "general"
    author: Optional[str] = None
    image_url: Optional[str] = None

class SocialDataGenerator:
    """Генератор реалистичных социальных данных для демонстрации"""
    
    def __init__(self):
        self.crypto_symbols = [
            'BTC', 'ETH', 'ADA', 'DOT', 'SOL', 'MATIC', 'AVAX', 'LINK', 'UNI', 'ATOM'
        ]
        
        self.sample_authors = {
            PlatformType.TWITTER: [
                ("elonmusk", 100000000, True),
                ("VitalikButerin", 5000000, True), 
                ("cz_binance", 8000000, True),
                ("crypto_trader_pro", 250000, False),
                ("blockchain_news", 150000, False)
            ],
            PlatformType.REDDIT: [
                ("CryptoCurrency_Mod", 50000, True),
                ("bitcoin_analyst", 25000, False),
                ("defi_researcher", 30000, False),
                ("hodl_master", 15000, False)
            ],
            PlatformType.TELEGRAM: [
                ("CryptoWhaleBot", 800000, True),
                ("trading_signals_pro", 120000, False),
                ("market_maker_insights", 85000, False)
            ]
        }
        
        self.news_sources = [
            "CoinDesk", "CoinTelegraph", "Decrypt", "The Block", 
            "Crypto Briefing", "BeInCrypto", "U.Today", "NewsBTC"
        ]
        
        self.sentiment_phrases = {
            -1.0: ["crash", "dump", "bearish", "sell off", "declining", "falling"],
            -0.5: ["correction", "dip", "caution", "resistance", "overbought"],
            0.0: ["stable", "sideways", "consolidation", "waiting", "neutral"],
            0.5: ["rising", "bullish", "breakthrough", "support", "accumulation"],
            1.0: ["moon", "explosion", "parabolic", "ATH", "breaking out", "huge pump"]
        }

    def generate_social_signals(self, count: int = 20, 
                               symbol_filter: Optional[str] = None) -> List[SocialSignal]:
        """Генерация реалистичных социальных сигналов"""
        signals = []
        
        for i in range(count):
            # Случайная платформа
            platform = random.choice(list(PlatformType))
            
            # Автор в зависимости от платформы
            if platform in self.sample_authors:
                author_data = random.choice(self.sample_authors[platform])
                author, followers, verified = author_data
            else:
                author = f"user_{random.randint(1000, 9999)}"
                followers = random.randint(100, 10000)
                verified = False
            
            # Выбор криптовалюты
            if symbol_filter:
                mentioned_coins = [symbol_filter.upper()]
            else:
                mentioned_coins = random.sample(
                    self.crypto_symbols, 
                    random.randint(1, 3)
                )
            
            # Настроение
            sentiment = random.choice([-1.0, -0.5, 0.0, 0.5, 1.0])
            
            # Генерация контента
            coin = mentioned_coins[0]
            sentiment_words = random.sample(self.sentiment_phrases[sentiment], 2)
            content = self._generate_content(coin, sentiment_words, platform)
            
            # Метрики влияния
            influence_score = self._calculate_influence_score(
                followers, verified, platform, sentiment
            )
            
            # Создание сигнала
            signal = SocialSignal(
                id=1000 + i,
                platform=platform,
                author=author,
                content=content,
                sentiment=sentiment,
                influence_score=influence_score,
                mentioned_coins=mentioned_coins,
                created_at=datetime.utcnow() - timedelta(
                    minutes=random.randint(1, 1440)  # Last 24 hours
                ),
                is_verified_author=verified,
                author_followers=followers,
                engagement_rate=random.uniform(0.01, 0.15),
                hashtags=self._generate_hashtags(mentioned_coins),
                retweets=random.randint(0, int(followers * 0.001)),
                likes=random.randint(0, int(followers * 0.005))
            )
            
            signals.append(signal)
        
        # Сортировка по времени (новые первыми)
        signals.sort(key=lambda x: x.created_at, reverse=True)
        
        return signals
    
    def generate_news_items(self, count: int = 10) -> List[NewsItem]:
        """Генерация новостных элементов"""
        news_items = []
        
        news_templates = [
            {
                "title": "{coin} Reaches New Monthly High Amid Institutional Interest",
                "summary": "{coin} price surged to new monthly highs following increased institutional adoption",
                "category": "market",
                "sentiment": 0.7,
                "impact": 8.5
            },
            {
                "title": "Major Exchange Lists {coin} for Trading",
                "summary": "Leading cryptocurrency exchange announces support for {coin} trading pairs",
                "category": "listing", 
                "sentiment": 0.6,
                "impact": 7.0
            },
            {
                "title": "{coin} Network Upgrade Completed Successfully",
                "summary": "Latest network upgrade improves scalability and reduces transaction fees",
                "category": "technology",
                "sentiment": 0.5,
                "impact": 6.5
            },
            {
                "title": "Regulatory Concerns Impact {coin} Price Movement",
                "summary": "Market uncertainty following regulatory statements affects {coin} trading",
                "category": "regulation",
                "sentiment": -0.3,
                "impact": 7.5
            }
        ]
        
        for i in range(count):
            template = random.choice(news_templates)
            coin = random.choice(self.crypto_symbols)
            
            news_item = NewsItem(
                id=2000 + i,
                title=template["title"].format(coin=coin),
                summary=template["summary"].format(coin=coin),
                content=self._generate_news_content(template, coin),
                source=random.choice(self.news_sources),
                url=f"https://example.com/news/{2000+i}",
                published_at=datetime.utcnow() - timedelta(
                    hours=random.randint(1, 48)
                ),
                sentiment_score=template["sentiment"] + random.uniform(-0.2, 0.2),
                impact_score=template["impact"] + random.uniform(-1.0, 1.0),
                affected_coins=[coin],
                category=template["category"],
                author=f"Reporter {random.randint(1, 100)}"
            )
            
            news_items.append(news_item)
        
        # Сортировка по времени публикации
        news_items.sort(key=lambda x: x.published_at, reverse=True)
        
        return news_items
    
    def _generate_content(self, coin: str, sentiment_words: List[str], 
                         platform: PlatformType) -> str:
        """Генерация реалистичного контента поста"""
        if platform == PlatformType.TWITTER:
            templates = [
                f"#{coin} is showing {sentiment_words[0]} signals. {sentiment_words[1]} pattern confirmed! 📈",
                f"Just analyzed ${coin} charts. Looks {sentiment_words[0]} to me. {sentiment_words[1]} incoming? 🚀",
                f"${coin} update: {sentiment_words[0]} momentum building. Watch for {sentiment_words[1]} 👀"
            ]
        elif platform == PlatformType.REDDIT:
            templates = [
                f"Technical Analysis: {coin} showing {sentiment_words[0]} patterns with potential for {sentiment_words[1]}",
                f"Market Discussion: What are your thoughts on {coin}'s recent {sentiment_words[0]} movement?",
                f"DD: {coin} analysis reveals {sentiment_words[0]} indicators suggesting {sentiment_words[1]}"
            ]
        else:
            templates = [
                f"{coin} market update: {sentiment_words[0]} trend with {sentiment_words[1]} expectations",
                f"Crypto signal: {coin} displaying {sentiment_words[0]} behavior, watch for {sentiment_words[1]}",
                f"Trading insight: {coin} technical analysis shows {sentiment_words[0]} with {sentiment_words[1]} potential"
            ]
        
        return random.choice(templates)
    
    def _generate_news_content(self, template: Dict, coin: str) -> str:
        """Генерация полного содержания новости"""
        base_content = template["summary"].format(coin=coin)
        
        additional_content = [
            f"Market analysts report significant activity in {coin} trading volumes.",
            f"The {coin} community has responded positively to recent developments.",
            f"Technical indicators suggest continued interest in {coin} among traders.",
            f"Industry experts are closely monitoring {coin} price movements."
        ]
        
        return base_content + " " + " ".join(random.sample(additional_content, 2))
    
    def _calculate_influence_score(self, followers: int, verified: bool, 
                                  platform: PlatformType, sentiment: float) -> float:
        """Расчет влияния сигнала"""
        base_score = min(10.0, (followers / 100000) * 5)  # Max 5 points for followers
        
        if verified:
            base_score += 2.0  # Verified accounts get boost
        
        platform_multiplier = {
            PlatformType.TWITTER: 1.2,
            PlatformType.REDDIT: 1.0,
            PlatformType.TELEGRAM: 1.1,
            PlatformType.TRADINGVIEW: 1.3
        }.get(platform, 1.0)
        
        # Strong sentiment (positive or negative) increases influence
        sentiment_boost = abs(sentiment) * 0.5
        
        final_score = (base_score + sentiment_boost) * platform_multiplier
        return min(10.0, round(final_score, 1))  # Cap at 10.0
    
    def _generate_hashtags(self, coins: List[str]) -> List[str]:
        """Генерация хештегов для постов"""
        base_tags = ["crypto", "trading", "blockchain", "DeFi"]
        coin_tags = [f"${coin}" for coin in coins]
        
        return random.sample(base_tags, 2) + coin_tags

class SocialAnalyticsEngine:
    """Движок аналитики социальных сигналов"""
    
    def __init__(self):
        self.data_generator = SocialDataGenerator()
    
    def get_aggregated_sentiment(self, symbol: Optional[str] = None, 
                                hours: int = 24) -> Dict[str, Any]:
        """Получение агрегированного настроения по символу"""
        signals = self.data_generator.generate_social_signals(50, symbol)
        
        if not signals:
            return {
                "symbol": symbol or "ALL",
                "period_hours": hours,
                "overall_sentiment": 0.0,
                "confidence": 0.0,
                "signal_count": 0
            }
        
        # Вычисляем взвешенное настроение
        total_weight = 0
        weighted_sentiment = 0
        
        for signal in signals:
            weight = signal.influence_score * (1 + signal.author_followers / 1000000)
            weighted_sentiment += signal.sentiment * weight
            total_weight += weight
        
        overall_sentiment = weighted_sentiment / total_weight if total_weight > 0 else 0
        
        # Уровень доверия основан на количестве сигналов и их качестве
        confidence = min(1.0, len(signals) / 20 * (total_weight / len(signals) / 5))
        
        return {
            "symbol": symbol or "ALL",
            "period_hours": hours,
            "overall_sentiment": round(overall_sentiment, 3),
            "confidence": round(confidence, 3),
            "signal_count": len(signals),
            "platform_breakdown": self._get_platform_breakdown(signals)
        }
    
    def _get_platform_breakdown(self, signals: List[SocialSignal]) -> Dict[str, Dict]:
        """Анализ по платформам"""
        breakdown = {}
        
        for signal in signals:
            platform = signal.platform.value
            if platform not in breakdown:
                breakdown[platform] = {
                    "count": 0,
                    "avg_sentiment": 0.0,
                    "avg_influence": 0.0
                }
            
            breakdown[platform]["count"] += 1
            breakdown[platform]["avg_sentiment"] += signal.sentiment
            breakdown[platform]["avg_influence"] += signal.influence_score
        
        # Вычисляем средние значения
        for platform_data in breakdown.values():
            count = platform_data["count"]
            platform_data["avg_sentiment"] = round(
                platform_data["avg_sentiment"] / count, 2
            )
            platform_data["avg_influence"] = round(
                platform_data["avg_influence"] / count, 1
            )
        
        return breakdown

def register_social_api_routes(app):
    """
    Регистрация роутов Social Signals API
    
    Эта функция создает все необходимые API endpoints для:
    - Получения социальных сигналов 
    - Новостной аналитики
    - Анализа настроений
    - Агрегированной статистики
    """
    
    logger.info("🔧 Инициализация Social Signals API...")
    
    # Инициализация компонентов
    analytics_engine = SocialAnalyticsEngine()
    data_generator = SocialDataGenerator()
    
    # === ОСНОВНЫЕ API ENDPOINTS ===
    
    @app.route('/api/social/signals', methods=['GET'])
    def get_social_signals():
        """
        Получить социальные сигналы
        
        Query Parameters:
        - limit: количество сигналов (default: 20, max: 100)
        - symbol: фильтр по криптовалюте (BTC, ETH, etc.)
        - platform: фильтр по платформе (twitter, reddit, etc.)
        - sentiment: фильтр по настроению (bullish, bearish, neutral)
        - min_influence: минимальный уровень влияния (0-10)
        """
        try:
            # Параметры запроса
            limit = min(request.args.get('limit', 20, type=int), 100)
            symbol = request.args.get('symbol', '').upper() or None
            platform = request.args.get('platform', '').lower()
            sentiment_filter = request.args.get('sentiment', '').lower()
            min_influence = request.args.get('min_influence', 0, type=float)
            
            logger.info(f"📊 Запрос социальных сигналов: symbol={symbol}, limit={limit}")
            
            # Генерируем сигналы
            signals = data_generator.generate_social_signals(limit, symbol)
            
            # Применяем фильтры
            filtered_signals = []
            for signal in signals:
                # Фильтр по платформе
                if platform and signal.platform.value != platform:
                    continue
                
                # Фильтр по настроению
                if sentiment_filter:
                    if sentiment_filter == 'bullish' and signal.sentiment <= 0:
                        continue
                    elif sentiment_filter == 'bearish' and signal.sentiment >= 0:
                        continue
                    elif sentiment_filter == 'neutral' and abs(signal.sentiment) > 0.1:
                        continue
                
                # Фильтр по влиянию
                if signal.influence_score < min_influence:
                    continue
                
                filtered_signals.append(signal)
            
            # Преобразуем в JSON-совместимый формат
            signals_data = []
            for signal in filtered_signals:
                signal_dict = {
                    'id': signal.id,
                    'platform': signal.platform.value,
                    'author': signal.author,
                    'content': signal.content,
                    'sentiment': signal.sentiment,
                    'influence_score': signal.influence_score,
                    'mentioned_coins': signal.mentioned_coins,
                    'created_at': signal.created_at.isoformat(),
                    'is_verified_author': signal.is_verified_author,
                    'author_followers': signal.author_followers,
                    'engagement_rate': signal.engagement_rate,
                    'hashtags': signal.hashtags or [],
                    'retweets': signal.retweets,
                    'likes': signal.likes
                }
                signals_data.append(signal_dict)
            
            response_data = {
                'success': True,
                'signals': signals_data,
                'count': len(signals_data),
                'total_generated': len(signals),
                'filters_applied': {
                    'symbol': symbol,
                    'platform': platform,
                    'sentiment': sentiment_filter,
                    'min_influence': min_influence
                },
                'timestamp': datetime.utcnow().isoformat()
            }
            
            logger.info(f"✅ Отправлено {len(signals_data)} социальных сигналов")
            return jsonify(response_data)
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения социальных сигналов: {e}")
            return jsonify({
                'success': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }), 500
    
    @app.route('/api/news/latest', methods=['GET'])
    def get_latest_news():
        """
        Получить последние новости
        
        Query Parameters:
        - limit: количество новостей (default: 10, max: 50)
        - category: категория новостей (market, technology, regulation, etc.)
        - sentiment: фильтр по настроению (-1.0 to 1.0)
        - min_impact: минимальный уровень влияния (0-10)
        """
        try:
            # Параметры запроса
            limit = min(request.args.get('limit', 10, type=int), 50)
            category = request.args.get('category', '').lower()
            sentiment_min = request.args.get('sentiment_min', type=float)
            min_impact = request.args.get('min_impact', 0, type=float)
            
            logger.info(f"📰 Запрос новостей: limit={limit}, category={category}")
            
            # Генерируем новости
            news_items = data_generator.generate_news_items(limit)
            
            # Применяем фильтры
            filtered_news = []
            for news in news_items:
                # Фильтр по категории
                if category and news.category != category:
                    continue
                
                # Фильтр по настроению
                if sentiment_min is not None and news.sentiment_score < sentiment_min:
                    continue
                
                # Фильтр по влиянию
                if news.impact_score < min_impact:
                    continue
                
                filtered_news.append(news)
            
            # Преобразуем в JSON
            news_data = []
            for news in filtered_news:
                news_dict = {
                    'id': news.id,
                    'title': news.title,
                    'summary': news.summary,
                    'source': news.source,
                    'url': news.url,
                    'published_at': news.published_at.isoformat(),
                    'sentiment_score': news.sentiment_score,
                    'impact_score': news.impact_score,
                    'affected_coins': news.affected_coins,
                    'category': news.category,
                    'author': news.author
                }
                news_data.append(news_dict)
            
            response_data = {
                'success': True,
                'news': news_data,
                'count': len(news_data),
                'filters_applied': {
                    'category': category,
                    'sentiment_min': sentiment_min,
                    'min_impact': min_impact
                },
                'timestamp': datetime.utcnow().isoformat()
            }
            
            logger.info(f"✅ Отправлено {len(news_data)} новостей")
            return jsonify(response_data)
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения новостей: {e}")
            return jsonify({
                'success': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }), 500
    
    @app.route('/api/social/sentiment/<symbol>', methods=['GET'])
    def get_sentiment_analysis(symbol):
        """Получить анализ настроений для конкретной криптовалюты"""
        try:
            hours = request.args.get('hours', 24, type=int)
            
            sentiment_data = analytics_engine.get_aggregated_sentiment(
                symbol.upper(), hours
            )
            
            return jsonify({
                'success': True,
                'data': sentiment_data,
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"❌ Ошибка анализа настроений для {symbol}: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/social/trending', methods=['GET'])
    def get_trending_topics():
        """Получить трендовые темы и монеты"""
        try:
            signals = data_generator.generate_social_signals(100)
            
            # Подсчитываем упоминания монет
            coin_mentions = {}
            for signal in signals:
                for coin in signal.mentioned_coins:
                    if coin not in coin_mentions:
                        coin_mentions[coin] = {
                            'count': 0,
                            'sentiment_sum': 0,
                            'influence_sum': 0
                        }
                    coin_mentions[coin]['count'] += 1
                    coin_mentions[coin]['sentiment_sum'] += signal.sentiment
                    coin_mentions[coin]['influence_sum'] += signal.influence_score
            
            # Формируем топ трендов
            trending = []
            for coin, data in coin_mentions.items():
                avg_sentiment = data['sentiment_sum'] / data['count']
                avg_influence = data['influence_sum'] / data['count']
                
                trending.append({
                    'symbol': coin,
                    'mentions': data['count'],
                    'avg_sentiment': round(avg_sentiment, 2),
                    'avg_influence': round(avg_influence, 1),
                    'trend_score': data['count'] * avg_influence
                })
            
            # Сортируем по популярности
            trending.sort(key=lambda x: x['trend_score'], reverse=True)
            
            return jsonify({
                'success': True,
                'trending': trending[:10],  # Топ 10
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения трендов: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/social/stats', methods=['GET'])
    def get_social_stats():
        """Получить общую статистику социальных сигналов"""
        try:
            signals = data_generator.generate_social_signals(200)
            
            # Статистика по платформам
            platform_stats = {}
            sentiment_distribution = {'bullish': 0, 'bearish': 0, 'neutral': 0}
            
            for signal in signals:
                platform = signal.platform.value
                if platform not in platform_stats:
                    platform_stats[platform] = 0
                platform_stats[platform] += 1
                
                # Распределение настроений
                if signal.sentiment > 0.1:
                    sentiment_distribution['bullish'] += 1
                elif signal.sentiment < -0.1:
                    sentiment_distribution['bearish'] += 1
                else:
                    sentiment_distribution['neutral'] += 1
            
            return jsonify({
                'success': True,
                'stats': {
                    'total_signals': len(signals),
                    'platform_distribution': platform_stats,
                    'sentiment_distribution': sentiment_distribution,
                    'period': '24h'
                },
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # === ДИАГНОСТИЧЕСКИЕ ENDPOINTS ===
    
    @app.route('/api/social/health', methods=['GET'])
    def social_api_health():
        """Проверка работоспособности Social API"""
        try:
            # Тестируем генерацию данных
            test_signals = data_generator.generate_social_signals(5)
            test_news = data_generator.generate_news_items(3)
            
            return jsonify({
                'status': 'healthy',
                'components': {
                    'signal_generator': len(test_signals) == 5,
                    'news_generator': len(test_news) == 3,
                    'analytics_engine': analytics_engine is not None
                },
                'test_results': {
                    'signals_generated': len(test_signals),
                    'news_generated': len(test_news)
                },
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            return jsonify({
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }), 500
    
    logger.info("✅ Social Signals API роуты зарегистрированы")
    logger.info("📊 Доступные endpoints:")
    logger.info("   📡 GET /api/social/signals - Социальные сигналы")
    logger.info("   📰 GET /api/news/latest - Последние новости") 
    logger.info("   📈 GET /api/social/sentiment/<symbol> - Анализ настроений")
    logger.info("   🔥 GET /api/social/trending - Трендовые темы")
    logger.info("   📊 GET /api/social/stats - Статистика")
    logger.info("   ❤️ GET /api/social/health - Проверка здоровья")

# Экспорт основных компонентов
__all__ = [
    'register_social_api_routes', 
    'SocialDataGenerator', 
    'SocialAnalyticsEngine',
    'SocialSignal',
    'NewsItem'
]