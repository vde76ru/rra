"""
Модуль работы с биржей - ОБНОВЛЕННАЯ ВЕРСИЯ
"""
from .client import (
    ExchangeClient, 
    exchange_client, 
    get_exchange_client,
    create_exchange_client,
    test_connection,
    get_balance_sync,
    get_price_sync
)

__all__ = [
    'ExchangeClient', 
    'exchange_client',
    'get_exchange_client',
    'create_exchange_client', 
    'test_connection',
    'get_balance_sync',
    'get_price_sync'
]