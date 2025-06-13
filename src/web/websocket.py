"""
WebSocket менеджер для real-time обновлений
Путь: /var/www/www-root/data/www/systemetech.ru/src/web/websocket.py
"""
from typing import Dict, List
from fastapi import WebSocket
import json
import asyncio
import logging

logger = logging.getLogger(__name__)

class WebSocketManager:
    """Менеджер WebSocket соединений"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self._broadcast_task = None
        
    async def connect(self, websocket: WebSocket, client_id: str):
        """Подключение нового клиента"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"WebSocket клиент {client_id} подключен")
        
        # Отправляем приветственное сообщение
        await self.send_personal_message(
            {"type": "connection", "message": "Connected to Crypto Bot"},
            client_id
        )
        
    def disconnect(self, client_id: str):
        """Отключение клиента"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"WebSocket клиент {client_id} отключен")
    
    async def send_personal_message(self, message: dict, client_id: str):
        """Отправка сообщения конкретному клиенту"""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_json(message)
            except Exception as e:
                logger.error(f"Ошибка отправки сообщения клиенту {client_id}: {e}")
                self.disconnect(client_id)
    
    async def broadcast(self, message: dict):
        """Отправка сообщения всем подключенным клиентам"""
        disconnected_clients = []
        
        for client_id, connection in self.active_connections.items():
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Ошибка отправки broadcast клиенту {client_id}: {e}")
                disconnected_clients.append(client_id)
        
        # Удаляем отключенных клиентов
        for client_id in disconnected_clients:
            self.disconnect(client_id)
    
    async def start_broadcast_loop(self):
        """Запуск цикла рассылки обновлений"""
        from ..bot.manager import bot_manager
        from ..core.database import SessionLocal
        from ..core.models import Trade, Signal, Balance
        
        while True:
            try:
                # Получаем статус бота
                bot_status = bot_manager.get_status()
                
                # Получаем последние данные из БД
                db = SessionLocal()
                try:
                    # Последние сделки
                    recent_trades = db.query(Trade).order_by(
                        Trade.created_at.desc()
                    ).limit(5).all()
                    
                    # Последние сигналы
                    recent_signals = db.query(Signal).order_by(
                        Signal.created_at.desc()
                    ).limit(5).all()
                    
                    # Текущий баланс
                    latest_balance = db.query(Balance).filter(
                        Balance.currency == 'USDT'
                    ).order_by(Balance.timestamp.desc()).first()
                    
                finally:
                    db.close()
                
                # Формируем сообщение
                update_message = {
                    "type": "update",
                    "data": {
                        "bot_status": bot_status,
                        "recent_trades": [
                            {
                                "symbol": t.symbol,
                                "side": t.side.value,
                                "status": t.status.value,
                                "profit": t.profit,
                                "created_at": t.created_at.isoformat()
                            }
                            for t in recent_trades
                        ],
                        "recent_signals": [
                            {
                                "symbol": s.symbol,
                                "action": s.action,
                                "confidence": s.confidence,
                                "created_at": s.created_at.isoformat()
                            }
                            for s in recent_signals
                        ],
                        "balance": {
                            "total": latest_balance.total if latest_balance else 0,
                            "free": latest_balance.free if latest_balance else 0
                        }
                    }
                }
                
                # Отправляем всем клиентам
                await self.broadcast(update_message)
                
                # Пауза между обновлениями
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Ошибка в broadcast loop: {e}")
                await asyncio.sleep(10)

# Глобальный экземпляр
ws_manager = WebSocketManager()