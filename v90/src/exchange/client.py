"""
Единый клиент для работы с биржей Bybit
Путь: /var/www/www-root/data/www/systemetech.ru/src/exchange/client.py
"""
import ccxt
import asyncio
import sys
import random
import logging
from typing import Dict, Any, List, Optional, Tuple, Dict, Optional, List
from datetime import datetime

from ..core.config import config
from .humanizer import HumanBehaviorMixin

logger = logging.getLogger(__name__)

class ExchangeClient(HumanBehaviorMixin):
    """
    Единый клиент для работы с Bybit
    Включает имитацию человеческого поведения
    """
    
    def __init__(self):
        """Инициализация клиента"""
        self.exchange = self._create_exchange()
        self._init_human_behavior()
        logger.info(f"✅ Exchange клиент инициализирован ({'TESTNET' if config.BYBIT_TESTNET else 'MAINNET'})")
    
    def _create_exchange(self):
        """Создание подключения к бирже"""
        exchange_config = {
            'apiKey': config.BYBIT_API_KEY,
            'secret': config.BYBIT_API_SECRET,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'swap',  # Для бессрочных контрактов
                'testnet': config.BYBIT_TESTNET
            }
        }
        
        exchange = ccxt.bybit(exchange_config)
        
        if config.BYBIT_TESTNET:
            exchange.set_sandbox_mode(True)
        
        return exchange
    
    async def test_connection(self) -> bool:
        """Тест подключения к бирже"""
        try:
            await self.human_delay()
            self.exchange.fetch_time()
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка подключения: {e}")
            return False
    
    async def fetch_balance(self) -> Dict:
        """Получить баланс"""
        await self.human_delay()
        
        try:
            balance = self.exchange.fetch_balance()
            
            # Фильтруем только значимые балансы
            filtered_balance = {}
            for currency, amounts in balance.items():
                if isinstance(amounts, dict) and amounts.get('total', 0) > 0:
                    filtered_balance[currency] = amounts
            
            logger.debug(f"💰 Баланс получен: {len(filtered_balance)} валют")
            return filtered_balance
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения баланса: {e}")
            raise
    
    async def fetch_ticker(self, symbol: str) -> Dict:
        """Получить текущую цену"""
        await self.micro_delay()  # Короткая задержка для тикера
        
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return ticker
        except Exception as e:
            logger.error(f"❌ Ошибка получения тикера {symbol}: {e}")
            raise
    
    async def fetch_ohlcv(self, symbol: str, timeframe: str = '5m', limit: int = 100) -> List:
        """Получить исторические данные"""
        await self.human_delay()
        
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            logger.debug(f"📊 Получено {len(ohlcv)} свечей для {symbol}")
            return ohlcv
        except Exception as e:
            logger.error(f"❌ Ошибка получения OHLCV {symbol}: {e}")
            raise
    
    
    
    async def create_order(
        self,
        symbol: str,
        side: str,
        amount: float,
        order_type: str = 'market',
        price: Optional[float] = None
    ) -> Optional[Dict]:
        """Создание ордера с имитацией человека"""
        
        # Имитация раздумий перед ордером
        await self.think_before_action()
        
        # Человеческое округление количества
        amount = self.humanize_amount(amount)
        
        # Иногда "передумываем"
        if self.should_hesitate():
            logger.info(f"😕 Имитация сомнений - отмена ордера {symbol}")
            return None
        
        # Иногда "случайно" делаем ошибку в размере (но не критичную)
        if config.ENABLE_HUMAN_MODE and random.random() < 0.02:  # 2% шанс
            error_factor = random.uniform(0.95, 1.05)  # ±5%
            amount = self.humanize_amount(amount * error_factor)
            logger.info(f"🤏 Имитация небольшой ошибки в размере: {amount}")
        
        try:
            # Добавляем случайные микро-задержки
            await self.micro_delay()
            
            # Создаем ордер
            order = self.exchange.create_order(
                symbol=symbol,
                type=order_type,
                side=side.lower(),
                amount=amount,
                price=price
            )
            
            logger.info(f"✅ Ордер создан: {side} {amount} {symbol} @ {order.get('price', 'market')}")
            
            # Иногда проверяем ордер после создания (как человек)
            if config.ENABLE_HUMAN_MODE and random.random() < 0.3:  # 30% шанс
                await asyncio.sleep(random.uniform(2, 5))
                logger.debug("👀 Проверяем созданный ордер...")
                
            return order
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания ордера: {e}")
            
            # Имитируем попытку повтора как человек
            if config.ENABLE_HUMAN_MODE and random.random() < 0.3:  # 30% шанс повтора
                await asyncio.sleep(random.uniform(2, 5))
                logger.info("🔄 Повторная попытка создания ордера")
                try:
                    return self.exchange.create_order(
                        symbol=symbol,
                        type=order_type,
                        side=side.lower(),
                        amount=amount,
                        price=price
                    )
                except:
                    pass
            raise
    
    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Отмена ордера"""
        await self.human_delay()
        
        try:
            self.exchange.cancel_order(order_id, symbol)
            logger.info(f"❌ Ордер {order_id} отменен")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка отмены ордера: {e}")
            return False
    
    async def fetch_order_book(self, symbol: str, limit: int = 10) -> Dict:
        """Получить стакан"""
        await self.micro_delay()
        
        try:
            order_book = self.exchange.fetch_order_book(symbol, limit)
            return order_book
        except Exception as e:
            logger.error(f"❌ Ошибка получения стакана {symbol}: {e}")
            raise
    
    async def fetch_trades(self, symbol: str, limit: int = 50) -> List:
        """Получить последние сделки"""
        await self.micro_delay()
        
        try:
            trades = self.exchange.fetch_trades(symbol, limit=limit)
            return trades
        except Exception as e:
            logger.error(f"❌ Ошибка получения сделок {symbol}: {e}")
            raise
    
    async def fetch_my_trades(self, symbol: str = None, limit: int = 50) -> List:
        """Получить свои сделки"""
        await self.human_delay()
        
        try:
            if symbol:
                trades = self.exchange.fetch_my_trades(symbol, limit=limit)
            else:
                trades = self.exchange.fetch_my_trades(limit=limit)
            return trades
        except Exception as e:
            logger.error(f"❌ Ошибка получения своих сделок: {e}")
            raise
    
    async def fetch_positions(self) -> List:
        """Получить открытые позиции"""
        await self.human_delay()
        
        try:
            positions = self.exchange.fetch_positions()
            return positions
        except Exception as e:
            logger.error(f"❌ Ошибка получения позиций: {e}")
            raise
    
    def calculate_position_size(self, symbol: str, balance: float, risk_percent: float) -> float:
        """Расчет размера позиции"""
        try:
            # Получаем информацию о рынке
            market = self.exchange.market(symbol)
            
            # Рассчитываем размер позиции
            risk_amount = balance * (risk_percent / 100)
            
            # Учитываем минимальный размер позиции
            min_amount = market.get('limits', {}).get('amount', {}).get('min', 0.001)
            
            # Округляем до precision
            precision = market.get('precision', {}).get('amount', 8)
            amount = round(risk_amount, precision)
            
            # Проверяем минимум
            if amount < min_amount:
                amount = min_amount
                
            return amount
            
        except Exception as e:
            logger.error(f"❌ Ошибка расчета размера позиции: {e}")
            return 0.001  # Минимальный размер по умолчанию

# Глобальный экземпляр клиента
exchange_client = ExchangeClient()