"""Telegram уведомления"""
import os
import asyncio
import logging
from datetime import datetime
from telegram import Bot
from telegram.error import TelegramError
from typing import Optional, List

from ..core.config import config

logger = logging.getLogger(__name__)

class TelegramNotifier:
    """Отправка уведомлений в Telegram"""
    
    def __init__(self):
        self.bot = Bot(token=config.TELEGRAM_BOT_TOKEN) if config.TELEGRAM_BOT_TOKEN else None
        self.chat_id = config.TELEGRAM_CHAT_ID
        self.enabled = bool(self.bot and self.chat_id)
        
        if not self.enabled:
            logger.warning("Telegram уведомления отключены")
    
    async def send_message(self, text: str, parse_mode: str = 'HTML'):
        """Отправка сообщения"""
        if not self.enabled:
            return
        
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=text,
                parse_mode=parse_mode
            )
        except TelegramError as e:
            logger.error(f"Ошибка отправки в Telegram: {e}")
    
    async def send_startup_message(self, pairs: List[str], mode: str):
        """Уведомление о запуске"""
        text = f"""🚀 <b>Бот запущен</b>
        
📊 Режим: {mode}
💱 Пары: {', '.join(pairs)}
⏰ Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        await self.send_message(text)
    
    async def send_trade_opened(self, symbol: str, side: str, amount: float, price: float):
        """Уведомление об открытии сделки"""
        emoji = "🟢" if side == "BUY" else "🔴"
        text = f"""{emoji} <b>Открыта позиция</b>
        
💱 {symbol}
📊 {side} {amount:.4f}
💵 Цена: ${price:.2f}
        """
        await self.send_message(text)
    
    async def send_error(self, error: str):
        """Уведомление об ошибке"""
        text = f"""🚨 <b>Ошибка</b>
        
{error[:500]}
        """
        await self.send_message(text)
