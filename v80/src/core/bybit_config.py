"""
Конфигурация для работы с Bybit
Технические детали и параметры
"""
import os
from typing import Dict, Any

class BybitConfig:
    """
    Централизованная конфигурация для Bybit
    
    Архитектурные особенности:
    1. Поддержка spot и derivatives рынков
    2. Testnet и production окружения
    3. Rate limiting настройки
    4. WebSocket endpoints
    """
    
    @staticmethod
    def get_exchange_config() -> Dict[str, Any]:
        """Получение конфигурации для CCXT"""
        config = {
            'apiKey': os.getenv('BYBIT_API_KEY'),
            'secret': os.getenv('BYBIT_API_SECRET'),
            'enableRateLimit': True,
            'rateLimit': 50,  # Bybit позволяет 50 запросов в секунду
            'options': {
                'defaultType': 'spot',  # 'spot', 'future', 'swap', 'option'
                'adjustForTimeDifference': True,
                'recvWindow': 5000,
            }
        }
        
        # Testnet настройки
        if os.getenv('BYBIT_TESTNET', 'true').lower() == 'true':
            config['hostname'] = 'testnet.bybit.com'
            config['urls'] = {
                'logo': 'https://user-images.githubusercontent.com/1294454/51973377-9e74a500-24ae-11e9-869e-c09a5e3df9b7.jpg',
                'api': {
                    'public': 'https://api-testnet.bybit.com',
                    'private': 'https://api-testnet.bybit.com',
                },
                'www': 'https://testnet.bybit.com',
                'doc': [
                    'https://bybit-exchange.github.io/docs/inverse/',
                    'https://bybit-exchange.github.io/docs/linear/',
                ],
            }
        
        return config
    
    @staticmethod
    def get_trading_params() -> Dict[str, Any]:
        """
        Торговые параметры специфичные для Bybit
        
        Технические ограничения:
        - Минимальные размеры ордеров
        - Точность цен и объемов
        - Комиссии
        """
        return {
            'fee_maker': 0.001,  # 0.1% maker fee
            'fee_taker': 0.001,  # 0.1% taker fee
            'min_order_sizes': {
                'BTCUSDT': 0.001,
                'ETHUSDT': 0.01,
                'BNBUSDT': 0.1,
                'SOLUSDT': 0.1,
            },
            'price_precision': {
                'BTCUSDT': 2,
                'ETHUSDT': 2,
                'BNBUSDT': 3,
                'SOLUSDT': 3,
            },
            'amount_precision': {
                'BTCUSDT': 3,
                'ETHUSDT': 3,
                'BNBUSDT': 2,
                'SOLUSDT': 2,
            }
        }
    
    @staticmethod
    def get_websocket_config() -> Dict[str, str]:
        """WebSocket endpoints для стриминга данных"""
        is_testnet = os.getenv('BYBIT_TESTNET', 'true').lower() == 'true'
        
        if is_testnet:
            return {
                'spot': 'wss://stream-testnet.bybit.com/spot/public/v3',
                'perpetual': 'wss://stream-testnet.bybit.com/perpetual/public/v3',
                'private': 'wss://stream-testnet.bybit.com/realtime_private',
            }
        else:
            return {
                'spot': 'wss://stream.bybit.com/spot/public/v3',
                'perpetual': 'wss://stream.bybit.com/perpetual/public/v3',
                'private': 'wss://stream.bybit.com/realtime_private',
            }

# Экспорт конфигурации
bybit_config = BybitConfig()
