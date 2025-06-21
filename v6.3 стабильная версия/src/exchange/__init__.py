"""
Exchange модули для работы с биржами
"""

try:
    from .client import ExchangeClient
except ImportError:
    ExchangeClient = None

try:
    from .real_client import get_real_exchange_client
except ImportError:
    get_real_exchange_client = None

try:
    from .position_manager import get_position_manager
except ImportError:
    get_position_manager = None

try:
    from .execution_engine import get_execution_engine
except ImportError:
    get_execution_engine = None

__all__ = [
    'ExchangeClient',
    'get_real_exchange_client',
    'get_position_manager',
    'get_execution_engine'
]
