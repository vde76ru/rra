"""
Web интерфейс торгового бота
"""

try:
    from .app import create_app
except ImportError:
    create_app = None

__all__ = ['create_app']