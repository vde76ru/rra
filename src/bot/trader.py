"""
Модуль для исполнения торговых операций
Путь: /var/www/www-root/data/www/systemetech.ru/src/bot/trader.py
"""
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from ..core.models import Trade, Signal, OrderSide, TradeStatus
from ..core.database import SessionLocal
from ..core.config import config
from ..exchange.client import ExchangeClient

logger = logging.getLogger(__name__)

class Trader:
    """Класс для исполнения торговых операций"""
    
    def __init__(self, exchange: ExchangeClient):
        self.exchange = exchange
        
    async def execute_signal(self, signal: Signal) -> Optional[Trade]:
        """Исполнение торгового сигнала"""
        try:
            # Получаем текущий баланс
            balance = await self.exchange.fetch_balance()
            usdt_balance = balance.get('USDT', {}).get('free', 0)
            
            if usdt_balance < 10:  # Минимальный баланс
                logger.warning(f"Недостаточный баланс: {usdt_balance} USDT")
                return None
            
            # Рассчитываем размер позиции
            position_size_usdt = usdt_balance * (config.MAX_POSITION_SIZE_PERCENT / 100)
            
            # Получаем текущую цену
            ticker = await self.exchange.fetch_ticker(signal.symbol)
            current_price = ticker['last']
            
            # Рассчитываем количество
            amount = self.exchange.calculate_position_size(
                signal.symbol, 
                position_size_usdt, 
                config.MAX_POSITION_SIZE_PERCENT
            )
            
            if amount <= 0:
                logger.warning(f"Рассчитанный размер позиции слишком мал: {amount}")
                return None
            
            # Создаем ордер
            order = await self.exchange.create_order(
                symbol=signal.symbol,
                side=signal.action,
                amount=amount,
                order_type='market'
            )
            
            if not order:
                logger.error("Не удалось создать ордер")
                return None
            
            # Создаем запись о сделке
            trade = Trade(
                symbol=signal.symbol,
                side=OrderSide[signal.action],
                entry_price=order.get('price', current_price),
                quantity=amount,
                status=TradeStatus.OPEN,
                strategy=signal.strategy,
                stop_loss=signal.stop_loss,
                take_profit=signal.take_profit,
                created_at=datetime.utcnow()
            )
            
            # Сохраняем в БД
            db = SessionLocal()
            try:
                db.add(trade)
                db.commit()
                db.refresh(trade)
            finally:
                db.close()
            
            logger.info(f"✅ Открыта позиция: {trade.side.value} {trade.quantity} {trade.symbol} @ {trade.entry_price}")
            
            return trade
            
        except Exception as e:
            logger.error(f"❌ Ошибка исполнения сигнала: {e}")
            return None
    
    async def close_position(self, trade: Trade, current_price: float) -> bool:
        """Закрытие позиции"""
        try:
            # Определяем направление закрывающего ордера
            close_side = 'SELL' if trade.side == OrderSide.BUY else 'BUY'
            
            # Создаем закрывающий ордер
            order = await self.exchange.create_order(
                symbol=trade.symbol,
                side=close_side,
                amount=trade.quantity,
                order_type='market'
            )
            
            if not order:
                logger.error("Не удалось создать закрывающий ордер")
                return False
            
            logger.info(f"✅ Закрыта позиция: {trade.symbol} @ {current_price}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка закрытия позиции: {e}")
            return False