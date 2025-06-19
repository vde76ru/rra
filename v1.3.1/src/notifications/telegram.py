"""
Telegram уведомления с Singleton паттерном
"""
import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, List
import aiohttp

from ..core.config import config

logger = logging.getLogger(__name__)

class TelegramNotifier:
    """Отправка уведомлений в Telegram"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TelegramNotifier, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.bot_token = config.TELEGRAM_BOT_TOKEN
            self.chat_id = config.TELEGRAM_CHAT_ID
            self.enabled = bool(self.bot_token and self.chat_id)
            
            if not self.enabled:
                logger.warning("⚠️ Telegram уведомления отключены")
            else:
                logger.info(f"✅ Telegram уведомления включены")
            
            self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
            self.initialized = True
    
    async def send_message(self, text: str, parse_mode: str = 'HTML', disable_notification: bool = False):
        """Отправка сообщения"""
        if not self.enabled:
            return
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/sendMessage"
                data = {
                    'chat_id': self.chat_id,
                    'text': text,
                    'parse_mode': parse_mode,
                    'disable_notification': disable_notification
                }
                
                async with session.post(url, json=data) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"❌ Ошибка отправки в Telegram: {error_text}")
                    
        except Exception as e:
            logger.error(f"❌ Ошибка отправки в Telegram: {e}")

# Создаем глобальный экземпляр
telegram_notifier = TelegramNotifier()