"""
Telegram уведомления
Путь: /var/www/www-root/data/www/systemetech.ru/src/notifications/telegram.py
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
    
    def __init__(self):
        self.bot_token = config.TELEGRAM_BOT_TOKEN
        self.chat_id = config.TELEGRAM_CHAT_ID
        self.enabled = bool(self.bot_token and self.chat_id)
        
        if not self.enabled:
            logger.warning("⚠️ Telegram уведомления отключены (не настроены токен или chat_id)")
        
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        
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
    
    async def send_startup_message(self, pairs: List[str], mode: str):
        """Уведомление о запуске бота"""
        text = f"""🚀 <b>Бот запущен</b>
        
📊 Режим: <code>{mode}</code>
💱 Пары: <code>{', '.join(pairs)}</code>
⏰ Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🌐 Веб: <a href="http://systemetech.ru:8000">Открыть дашборд</a>
        
<i>Удачной торговли!</i>"""
        
        await self.send_message(text)
    
    async def send_shutdown_message(self, runtime: Optional[timedelta], trades_count: int):
        """Уведомление об остановке бота"""
        runtime_str = str(runtime).split('.')[0] if runtime else "Неизвестно"
        
        text = f"""🛑 <b>Бот остановлен</b>
        
⏱️ Время работы: <code>{runtime_str}</code>
📊 Сделок за сессию: <code>{trades_count}</code>
⏰ Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
<i>До встречи!</i>"""
        
        await self.send_message(text)
    
    async def send_trade_opened(self, symbol: str, side: str, amount: float, price: float):
        """Уведомление об открытии сделки"""
        emoji = "🟢" if side == "BUY" else "🔴"
        
        text = f"""{emoji} <b>Открыта позиция</b>
        
💱 Пара: <code>{symbol}</code>
📊 Сторона: <code>{side}</code>
📈 Количество: <code>{amount:.4f}</code>
💵 Цена входа: <code>${price:.2f}</code>
⏰ Время: {datetime.now().strftime('%H:%M:%S')}"""
        
        await self.send_message(text)
    
    async def send_trade_closed(self, symbol: str, side: str, profit: float, reason: str):
        """Уведомление о закрытии сделки"""
        emoji = "✅" if profit > 0 else "❌"
        profit_emoji = "📈" if profit > 0 else "📉"
        
        text = f"""{emoji} <b>Закрыта позиция</b>
        
💱 Пара: <code>{symbol}</code>
📊 Сторона: <code>{side}</code>
{profit_emoji} Прибыль: <code>${profit:.2f}</code>
📝 Причина: <i>{reason}</i>
⏰ Время: {datetime.now().strftime('%H:%M:%S')}"""
        
        await self.send_message(text)
    
    async def send_daily_report(self, stats: Dict):
        """Ежедневный отчет"""
        text = f"""📊 <b>Дневной отчет</b>
        
📅 Дата: {datetime.now().strftime('%Y-%m-%d')}

📈 <b>Статистика:</b>
- Всего сделок: <code>{stats.get('total_trades', 0)}</code>
- Прибыльных: <code>{stats.get('profitable_trades', 0)}</code>
- Убыточных: <code>{stats.get('losing_trades', 0)}</code>
- Win Rate: <code>{stats.get('win_rate', 0):.1f}%</code>

💰 <b>Финансы:</b>
- Общая прибыль: <code>${stats.get('total_profit', 0):.2f}</code>
- Средняя прибыль: <code>${stats.get('avg_profit', 0):.2f}</code>
- Лучшая сделка: <code>${stats.get('best_trade', 0):.2f}</code>
- Худшая сделка: <code>${stats.get('worst_trade', 0):.2f}</code>

💼 <b>Баланс:</b>
- Начальный: <code>${stats.get('start_balance', 0):.2f}</code>
- Текущий: <code>${stats.get('current_balance', 0):.2f}</code>
- Изменение: <code>{stats.get('balance_change', 0):.2f}%</code>

🏆 <b>Лучшая пара:</b> <code>{stats.get('best_pair', 'N/A')}</code>
        
<i>Хорошего дня!</i>"""
        
        await self.send_message(text, disable_notification=True)
    
    async def send_error(self, error: str):
        """Уведомление об ошибке"""
        # Ограничиваем длину сообщения
        if len(error) > 500:
            error = error[:497] + "..."
        
        text = f"""🚨 <b>Ошибка</b>
        
<code>{error}</code>
        
⏰ Время: {datetime.now().strftime('%H:%M:%S')}"""
        
        await self.send_message(text)
    
    async def send_warning(self, warning: str):
        """Уведомление о предупреждении"""
        text = f"""⚠️ <b>Предупреждение</b>
        
{warning}
        
⏰ Время: {datetime.now().strftime('%H:%M:%S')}"""
        
        await self.send_message(text, disable_notification=True)

# Глобальный экземпляр
telegram_notifier = TelegramNotifier()