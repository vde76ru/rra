"""
News analysis модули
"""

try:
    from .impact_scorer import NewsImpactScorer
except ImportError:
    # Создаем заглушку если модуль отсутствует
    class NewsImpactScorer:
        def __init__(self):
            pass
        
        def score_news_impact(self, news):
            return 0.5
    
    print("⚠️ NewsImpactScorer - используется заглушка")

__all__ = ['NewsImpactScorer']