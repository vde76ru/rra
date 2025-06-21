"""
Analysis модули для торгового бота
Файл: src/analysis/__init__.py

Содержит модули для анализа рынка, новостей и социальных сигналов
"""

# Безопасный импорт компонентов с защитой от ошибок
try:
    from .market_analyzer import MarketAnalyzer
except ImportError as e:
    print(f"⚠️ Не удалось импортировать MarketAnalyzer: {e}")
    MarketAnalyzer = None

# Экспортируем все доступные компоненты
__all__ = [
    'MarketAnalyzer'
]

# Алиас для обратной совместимости
market_analyzer = MarketAnalyzer if MarketAnalyzer else None