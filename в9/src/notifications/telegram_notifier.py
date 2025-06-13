import os
import asyncio
from datetime import datetime
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError
import logging
from typing import Optional, List, Dict
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class NotificationMessage:
    title: str
    text: str
    level: str  # INFO, WARNING, ERROR, TRADE
    data: Optional[Dict] = None
    
class TelegramNotifier:
    """Система уведомлений через Telegram"""
    
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.bot = Bot(token=self.bot_token) if self.bot_token else None
        self.enabled = bool(self.bot_token and self.chat_id)
        
        if not self.enabled:
            logger.warning("Telegram уведомления отключены - нет токена или chat_id")
    
    async def send_notification(self, message: NotificationMessage):
        """Отправка уведомления"""
        if not self.enabled:
            return
        
        try:
            # Форматируем сообщение
            text = self._format_message(message)
            
            # Добавляем клавиатуру для важных сообщений
            reply_markup = None
            if message.level == 'TRADE' and message.data:
                reply_markup = self._create_trade_keyboard(message.data)
            
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=text,
                parse_mode='HTML',
                reply_markup=reply_markup
            )
            
        except TelegramError as e:
            logger.error(f"Ошибка отправки в Telegram: {e}")
    
    def _format_message(self, message: NotificationMessage) -> str:
        """Форматирование сообщения"""
        # Иконки для разных уровней
        icons = {
            'INFO': 'ℹ️',
            'WARNING': '⚠️',
            'ERROR': '🚨',
            'TRADE': '💰',
            'SUCCESS': '✅',
            'LOSS': '❌'
        }
        
        icon = icons.get(message.level, '📌')
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        text = f"{icon} <b>{message.title}</b>\n"
        text += f"⏰ {timestamp}\n\n"
        text += f"{message.text}\n"
        
        # Добавляем дополнительные данные
        if message.data:
            text += "\n<b>Детали:</b>\n"
            for key, value in message.data.items():
                if isinstance(value, float):
                    text += f"• {key}: {value:.4f}\n"
                else:
                    text += f"• {key}: {value}\n"
        
        return text
    
    def _create_trade_keyboard(self, trade_data: Dict) -> InlineKeyboardMarkup:
        """Создание клавиатуры для управления сделкой"""
        keyboard = []
        
        if trade_data.get('status') == 'SIGNAL':
            keyboard.append([
                InlineKeyboardButton("✅ Исполнить", callback_data=f"execute_{trade_data['id']}"),
                InlineKeyboardButton("❌ Отменить", callback_data=f"cancel_{trade_data['id']}")
            ])
        
        return InlineKeyboardMarkup(keyboard) if keyboard else None
    
    async def send_trade_opened(self, trade):
        """Уведомление об открытии сделки"""
        message = NotificationMessage(
            title="Позиция открыта",
            text=f"Открыта {trade.side} позиция по {trade.symbol}",
            level="TRADE",
            data={
                "Символ": trade.symbol,
                "Направление": trade.side,
                "Цена входа": trade.entry_price,
                "Объем": trade.quantity,
                "Stop Loss": trade.stop_loss if hasattr(trade, 'stop_loss') else 'Не установлен',
                "Take Profit": trade.take_profit if hasattr(trade, 'take_profit') else 'Не установлен'
            }
        )
        await self.send_notification(message)
    
    async def send_trade_closed(self, trade):
        """Уведомление о закрытии сделки"""
        profit_emoji = "✅" if trade.profit >= 0 else "❌"
        
        message = NotificationMessage(
            title=f"{profit_emoji} Позиция закрыта",
            text=f"Закрыта позиция по {trade.symbol}",
            level="SUCCESS" if trade.profit >= 0 else "LOSS",
            data={
                "Символ": trade.symbol,
                "Прибыль": f"${trade.profit:.2f}",
                "Прибыль %": f"{(trade.profit / (trade.entry_price * trade.quantity)) * 100:.2f}%",
                "Время в сделке": str(trade.closed_at - trade.created_at) if trade.closed_at else "N/A"
            }
        )
        await self.send_notification(message)
    
    async def send_daily_report(self, stats):
        """Ежедневный отчет"""
        message = NotificationMessage(
            title="📊 Дневной отчет",
            text="Статистика за последние 24 часа",
            level="INFO",
            data={
                "Всего сделок": stats['total_trades'],
                "Прибыльных": stats['profitable_trades'],
                "Убыточных": stats['losing_trades'],
                "Общая прибыль": f"${stats['total_profit']:.2f}",
                "Win Rate": f"{stats['win_rate']:.1f}%",
                "Лучшая сделка": f"${stats['best_trade']:.2f}",
                "Худшая сделка": f"${stats['worst_trade']:.2f}"
            }
        )
        await self.send_notification(message)