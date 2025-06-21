"""
Social analysis модули
"""

try:
    from .signal_extractor import SocialSignalExtractor
except ImportError:
    # Создаем заглушку если модуль отсутствует
    class SocialSignalExtractor:
        def __init__(self):
            pass
        
        def extract_signals_from_text(self, text, source="unknown"):
            return []
        
        def extract_signals(self, data_sources):
            return []
    
    print("⚠️ SocialSignalExtractor - используется заглушка")

__all__ = ['SocialSignalExtractor']