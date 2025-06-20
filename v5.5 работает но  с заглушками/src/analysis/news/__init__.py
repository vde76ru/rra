"""
News analysis module for crypto trading bot
"""
from .news_collector import NewsCollector
from .nlp_analyzer import NLPAnalyzer
from .impact_scorer import ImpactScorer

__all__ = ['NewsCollector', 'NLPAnalyzer', 'ImpactScorer']