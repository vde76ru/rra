"""Единый клиент для работы с биржей"""
import ccxt
import asyncio
import random
import logging
from typing import Dict, Optional
from datetime import datetime

from ..core.config import config
from .humanizer import HumanBehaviorMixin

logger = logging.getLogger(__name__)

class ExchangeClient(HumanBehaviorMixin):
    """Единый клиент для работы с Bybit"""
    
    def __init__(self):
        self.exchange = self._create_exchange()
        self._init_human_behavior()
    
    def _create_exchange(self):
        """Создание подключения к бирже"""
        exchange_config = {
            'apiKey': config.BYBIT_API_KEY,
            'secret': config.BYBIT_API_SECRET,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'swap',
                'testnet': config.BYBIT_TESTNET
            }
        }
        
        exchange = ccxt.bybit(exchange_config)
        
        if config.BYBIT_TESTNET:
            exchange.set_sandbox_mode(True)
        
        return exchange
    
    async def fetch_balance(self) -> Dict:
        """Получить баланс с человеческим поведением"""
        await self.human_delay()
        
        try:
            balance = self.exchange.fetch_balance()
            logger.debug(f"Баланс получен: {balance.get('USDT', {}).get('free', 0)} USDT")
            return balance
        except Exception as e:
            logger.error(f"Ошибка получения баланса: {e}")
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
        
        # Человеческое округление
        amount = self.humanize_amount(amount)
        
        # Иногда "передумываем"
        if self.should_hesitate():
            logger.info("Имитация сомнений - отмена ордера")
            return None
        
        try:
            # Добавляем случайные микро-задержки
            await self.micro_delay()
            
            order = self.exchange.create_order(
                symbol=symbol,
                type=order_type,
                side=side,
                amount=amount,
                price=price
            )
            
            logger.info(f"Ордер создан: {side} {amount} {symbol}")
            return order
            
        except Exception as e:
            logger.error(f"Ошибка создания ордера: {e}")
            # Имитируем попытку повтора как человек
            if random.random() < 0.3:  # 30% шанс повтора
                await asyncio.sleep(random.uniform(2, 5))
                logger.info("Повторная попытка создания ордера")
                try:
                    return self.exchange.create_order(
                        symbol=symbol,
                        type=order_type,
                        side=side,
                        amount=amount,
                        price=price
                    )
                except:
                    pass
            raise