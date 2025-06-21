"""
Telegram Notifier - Система уведомлений через Telegram
Файл: src/notifications/telegram.py

🎯 ФУНКЦИИ:
✅ Уведомления о торговых операциях
✅ Алерты об ошибках и проблемах
✅ Ежедневные отчеты о производительности
✅ Настраиваемые форматы сообщений
"""

import asyncio
import aiohttp
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import logging

from ..core.config import config

logger = logging.getLogger(__name__)

class TelegramNotifier:
    """
    Система уведомлений через Telegram Bot API
    
    🔥 ПОЛНАЯ ИНТЕГРАЦИЯ С БОТОМ:
    - Уведомления о каждой торговой операции
    - Алерты при критических ошибках
    - Ежедневные/еженедельные отчеты
    - Форматированные сообщения с эмодзи
    """
    
    def __init__(self, token: str = None, chat_id: str = None):
        """Инициализация Telegram уведомлений"""
        self.token = token or config.TELEGRAM_BOT_TOKEN
        self.chat_id = chat_id or config.TELEGRAM_CHAT_ID
        self.enabled = config.TELEGRAM_ENABLED
        
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.session = None
        
        # Настройки уведомлений
        self.enable_trade_alerts = config.TELEGRAM_ENABLE_TRADE_ALERTS
        self.enable_error_alerts = config.TELEGRAM_ENABLE_ERROR_ALERTS
        self.enable_daily_summary = config.TELEGRAM_ENABLE_DAILY_SUMMARY
        
        # Эмодзи для разных типов сообщений
        self.emojis = {
            'buy': '💚',
            'sell': '❤️',
            'profit': '💰',
            'loss': '📉',
            'warning': '⚠️',
            'error': '🚨',
            'info': 'ℹ️',
            'success': '✅',
            'robot': '🤖',
            'chart': '📊',
            'rocket': '🚀',
            'fire': '🔥'
        }
        
        if self.enabled and self.token and self.chat_id:
            logger.info("✅ Telegram уведомления активированы")
        else:
            logger.warning("⚠️ Telegram уведомления отключены (проверьте конфигурацию)")
    
    async def _get_session(self):
        """Получение HTTP сессии"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def send_message(self, message: str, parse_mode: str = 'HTML',
                          disable_notification: bool = False) -> bool:
        """
        Отправка сообщения в Telegram
        
        Args:
            message: Текст сообщения
            parse_mode: Режим форматирования (HTML/Markdown)
            disable_notification: Отключить звуковое уведомление
            
        Returns:
            bool: Успешность отправки
        """
        if not self.enabled or not self.token or not self.chat_id:
            logger.debug(f"📱 Telegram (отключен): {message}")
            return False
        
        try:
            session = await self._get_session()
            
            url = f"{self.base_url}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': parse_mode,
                'disable_notification': disable_notification
            }
            
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    logger.debug("✅ Telegram сообщение отправлено")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Ошибка отправки Telegram: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Исключение при отправке Telegram: {e}")
            return False
    
    async def send_trade_alert(self, trade_info: Dict[str, Any]) -> bool:
        """
        Уведомление о торговой операции
        
        Args:
            trade_info: Информация о сделке
        """
        if not self.enable_trade_alerts:
            return False
        
        try:
            action = trade_info.get('action', 'unknown').upper()
            symbol = trade_info.get('symbol', 'Unknown')
            amount = trade_info.get('amount', 0)
            price = trade_info.get('price', 0)
            strategy = trade_info.get('strategy', 'unknown')
            profit = trade_info.get('profit', 0)
            
            # Выбираем эмодзи
            emoji = self.emojis.get(action.lower(), self.emojis['info'])
            profit_emoji = self.emojis['profit'] if profit > 0 else self.emojis['loss']
            
            # Форматируем сообщение
            message = f"""
{self.emojis['robot']} <b>Торговый сигнал</b>

{emoji} <b>Действие:</b> {action}
💎 <b>Символ:</b> {symbol}
📊 <b>Количество:</b> {amount:.6f}
💲 <b>Цена:</b> ${price:.4f}
🎯 <b>Стратегия:</b> {strategy}
"""
            
            if profit != 0:
                message += f"{profit_emoji} <b>P&L:</b> ${profit:.2f} ({profit/abs(profit)*100:+.1f}%)\n"
            
            message += f"\n🕐 <b>Время:</b> {datetime.utcnow().strftime('%H:%M:%S UTC')}"
            
            return await self.send_message(message)
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки торгового алерта: {e}")
            return False
    
    async def send_error_alert(self, error_info: Dict[str, Any]) -> bool:
        """
        Уведомление об ошибке
        
        Args:
            error_info: Информация об ошибке
        """
        if not self.enable_error_alerts:
            return False
        
        try:
            error_type = error_info.get('type', 'Unknown Error')
            error_message = error_info.get('message', 'No details')
            component = error_info.get('component', 'unknown')
            severity = error_info.get('severity', 'medium')
            
            # Выбираем эмодзи по серьезности
            severity_emojis = {
                'low': self.emojis['warning'],
                'medium': self.emojis['error'],
                'high': '🚨🚨',
                'critical': '🚨🚨🚨'
            }
            
            emoji = severity_emojis.get(severity, self.emojis['error'])
            
            message = f"""
{emoji} <b>Ошибка в торговом боте</b>

🔴 <b>Тип:</b> {error_type}
🔧 <b>Компонент:</b> {component}
📝 <b>Описание:</b> {error_message}
⚡ <b>Серьезность:</b> {severity.upper()}

🕐 <b>Время:</b> {datetime.utcnow().strftime('%H:%M:%S UTC')}
"""
            
            return await self.send_message(message)
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки error алерта: {e}")
            return False
    
    async def send_daily_summary(self, summary_info: Dict[str, Any]) -> bool:
        """
        Ежедневный отчет о работе бота
        
        Args:
            summary_info: Сводная информация за день
        """
        if not self.enable_daily_summary:
            return False
        
        try:
            total_trades = summary_info.get('total_trades', 0)
            profitable_trades = summary_info.get('profitable_trades', 0)
            daily_pnl = summary_info.get('daily_pnl', 0)
            win_rate = summary_info.get('win_rate', 0)
            best_trade = summary_info.get('best_trade', 0)
            worst_trade = summary_info.get('worst_trade', 0)
            active_positions = summary_info.get('active_positions', 0)
            
            # Эмодзи для PnL
            pnl_emoji = self.emojis['profit'] if daily_pnl > 0 else self.emojis['loss']
            trend_emoji = self.emojis['rocket'] if daily_pnl > 0 else '📉'
            
            message = f"""
{self.emojis['chart']} <b>Ежедневный отчет торгового бота</b>

📈 <b>Сделки:</b> {total_trades} (из них прибыльных: {profitable_trades})
{pnl_emoji} <b>P&L за день:</b> ${daily_pnl:.2f}
🎯 <b>Win Rate:</b> {win_rate:.1f}%

{self.emojis['fire']} <b>Лучшая сделка:</b> ${best_trade:.2f}
📉 <b>Худшая сделка:</b> ${worst_trade:.2f}
💼 <b>Активных позиций:</b> {active_positions}

{trend_emoji} <b>Общий тренд:</b> {'Прибыльный день' if daily_pnl > 0 else 'Убыточный день'}

📅 <b>Дата:</b> {datetime.utcnow().strftime('%Y-%m-%d')}
"""
            
            return await self.send_message(message)
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки ежедневного отчета: {e}")
            return False
    
    async def send_bot_status(self, status_info: Dict[str, Any]) -> bool:
        """
        Уведомление о статусе бота
        
        Args:
            status_info: Информация о статусе
        """
        try:
            status = status_info.get('status', 'unknown')
            uptime = status_info.get('uptime', 'unknown')
            balance = status_info.get('balance', 0)
            active_strategies = status_info.get('active_strategies', [])
            
            status_emojis = {
                'starting': '🟡',
                'running': '🟢',
                'stopping': '🟠',
                'stopped': '🔴',
                'error': '🚨'
            }
            
            emoji = status_emojis.get(status, self.emojis['info'])
            
            message = f"""
{self.emojis['robot']} <b>Статус торгового бота</b>

{emoji} <b>Состояние:</b> {status.upper()}
⏰ <b>Время работы:</b> {uptime}
💰 <b>Баланс:</b> ${balance:.2f}
🎯 <b>Активные стратегии:</b> {', '.join(active_strategies) if active_strategies else 'Нет'}

🕐 <b>Обновлено:</b> {datetime.utcnow().strftime('%H:%M:%S UTC')}
"""
            
            return await self.send_message(message)
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки статуса бота: {e}")
            return False
    
    async def send_market_alert(self, market_info: Dict[str, Any]) -> bool:
        """
        Уведомление о важных рыночных событиях
        
        Args:
            market_info: Информация о рыночном событии
        """
        try:
            event_type = market_info.get('type', 'market_event')
            symbol = market_info.get('symbol', '')
            message_text = market_info.get('message', '')
            impact = market_info.get('impact', 'medium')
            
            impact_emojis = {
                'low': '🟢',
                'medium': '🟡',
                'high': '🔴',
                'critical': '🚨'
            }
            
            emoji = impact_emojis.get(impact, self.emojis['info'])
            
            message = f"""
{emoji} <b>Рыночное событие</b>

💎 <b>Символ:</b> {symbol}
📢 <b>Событие:</b> {message_text}
⚡ <b>Важность:</b> {impact.upper()}

🕐 <b>Время:</b> {datetime.utcnow().strftime('%H:%M:%S UTC')}
"""
            
            return await self.send_message(message)
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки рыночного алерта: {e}")
            return False
    
    async def close(self):
        """Закрытие HTTP сессии"""
        if self.session:
            await self.session.close()
            self.session = None

# Создаем глобальный экземпляр
telegram_notifier = TelegramNotifier()

# Экспорт
__all__ = [
    'TelegramNotifier',
    'telegram_notifier'
]