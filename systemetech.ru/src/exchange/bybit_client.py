import ccxt
import asyncio
import time
import random
from typing import Dict, Optional
import os
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)

class HumanizedBybitClient:
    """Клиент Bybit с имитацией человеческого поведения"""
    
    def __init__(self):
        self.testnet = os.getenv('BYBIT_TESTNET', 'true').lower() == 'true'
        
        # Настройка подключения
        if self.testnet:
            self.exchange = ccxt.bybit({
                'apiKey': os.getenv('BYBIT_API_KEY'),
                'secret': os.getenv('BYBIT_API_SECRET'),
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'swap',  # Для бессрочных контрактов
                    'testnet': True
                }
            })
            self.exchange.set_sandbox_mode(True)
        else:
            self.exchange = ccxt.bybit({
                'apiKey': os.getenv('BYBIT_API_KEY'),
                'secret': os.getenv('BYBIT_API_SECRET'),
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'swap'
                }
            })
    
    async def human_delay(self):
        """Человеческая задержка между действиями"""
        delay = random.uniform(
            float(os.getenv('MIN_DELAY_SECONDS', 0.5)),
            float(os.getenv('MAX_DELAY_SECONDS', 3.0))
        )
        await asyncio.sleep(delay)
    
    async def fetch_balance(self) -> Dict:
        """Получить баланс с человеческой задержкой"""
        await self.human_delay()
        try:
            balance = self.exchange.fetch_balance()
            return balance
        except Exception as e:
            logger.error(f"Ошибка получения баланса: {e}")
            return {}
    
    async def fetch_ticker(self, symbol: str) -> Dict:
        """Получить текущую цену"""
        await self.human_delay()
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return ticker
        except Exception as e:
            logger.error(f"Ошибка получения цены: {e}")
            return {}
    
    async def create_order(self, symbol: str, side: str, amount: float, price: Optional[float] = None):
        """Создать ордер с человеческим поведением"""
        # Думаем перед ордером
        thinking_time = random.uniform(1.0, 3.0)
        await asyncio.sleep(thinking_time)
        
        # Округляем размер позиции по-человечески
        if amount > 100:
            amount = round(amount, -1)  # До десятков
        elif amount > 10:
            amount = round(amount, 0)   # До целых
        else:
            amount = round(amount, 2)   # До сотых
        
        try:
            # Иногда делаем "ошибку" и отменяем
            if random.random() < 0.02:  # 2% шанс
                logger.info("Имитация ошибки - отмена действия")
                await asyncio.sleep(random.uniform(0.5, 1.5))
                return None
            
            # Создаем ордер
            order_type = 'market'
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
            return None