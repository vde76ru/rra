# Файл: /var/www/www-root/data/www/systemetech.ru/src/bot/__init__.py
"""
Bot package initialization
"""

# Импортируем основные компоненты
try:
    from .manager import BotManager, bot_manager
except ImportError:
    # Если основной файл недоступен, используем заглушку
    try:
        from .bot_manager import BotManager
        bot_manager = BotManager()
    except ImportError:
        BotManager = None
        bot_manager = None

# Экспортируем публичные объекты
__all__ = ['BotManager', 'bot_manager']  # ИСПРАВЛЕНО: было **all** вместо __all__