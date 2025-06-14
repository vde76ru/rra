"""
API endpoints для управления ботом (дополненная версия)
Путь: /var/www/www-root/data/www/systemetech.ru/src/web/api_routes.py
"""
import asyncio
import json
import io
import csv
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from .dashboard import get_dashboard_html


from ..core.database import get_db
from ..core.models import Trade, Signal, TradingPair, User, BotState, Balance
from ..bot.manager import bot_manager
from .auth import get_current_user
from ..core.clean_logging import get_clean_logger

logger = get_clean_logger(__name__)

# ✅ Pydantic модели (оставляем как есть)
class BotStartRequest(BaseModel):
    strategy: Optional[str] = None
    pairs: Optional[List[str]] = None

class SettingsRequest(BaseModel):
    max_position_size: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    max_daily_trades: Optional[int] = None
    trading_pairs: Optional[List[str]] = None
    email_notifications: bool = True
    telegram_notifications: bool = False
    telegram_token: Optional[str] = None

class TradeResponse(BaseModel):
    id: int
    timestamp: datetime
    symbol: str
    side: str
    amount: float
    price: float
    profit: Optional[float]
    strategy: Optional[str]
    status: str

# ✅ WebSocket менеджер (оставляем как есть)
class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"🔌 WebSocket подключен. Активных соединений: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"🔌 WebSocket отключен. Активных соединений: {len(self.active_connections)}")
    
    async def broadcast(self, data: dict):
        """Отправка данных всем подключенным клиентам"""
        if not self.active_connections:
            return
        
        message = json.dumps(data, default=str, ensure_ascii=False)
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Ошибка отправки WebSocket сообщения: {e}")
                disconnected.append(connection)
        
        # Удаляем отключенные соединения
        for connection in disconnected:
            self.disconnect(connection)

# Глобальный менеджер WebSocket
ws_manager = WebSocketManager()

router = APIRouter()

# ✅ НОВЫЙ РОУТ - Главная страница
@router.get("/", response_class=HTMLResponse)
async def dashboard():
    """Главная страница с полноценным дашбордом"""
    return get_dashboard_html()

# ✅ НОВЫЙ РОУТ - Простое API приветствие
@router.get("/api")
async def api_info():
    """
    Базовая информация об API
    
    Возвращает JSON с информацией о доступных endpoints
    и текущем состоянии системы.
    """
    try:
        # Получаем базовую информацию о боте
        bot_status = "unknown"
        try:
            if hasattr(bot_manager, 'get_status'):
                status_info = bot_manager.get_status()
                bot_status = status_info.get('status', 'unknown')
        except Exception as e:
            logger.warning(f"Не удалось получить статус бота: {e}")
        
        return {
            "service": "Crypto Trading Bot API",
            "version": "3.0.0",
            "status": "running",
            "bot_status": bot_status,
            "timestamp": datetime.utcnow(),
            "endpoints": {
                "documentation": "/docs",
                "redoc": "/redoc", 
                "health": "/health",
                "status": "/status",
                "websocket": "/ws"
            },
            "features": [
                "Automated trading",
                "Multiple strategies",
                "Real-time monitoring",
                "WebSocket support",
                "Advanced analytics"
            ]
        }
    except Exception as e:
        logger.error(f"Ошибка в api_info: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "message": str(e)}
        )

# ✅ Улучшенный health check
@router.get("/health")
async def health_check():
    """
    Детальная проверка состояния системы
    
    Проверяет все компоненты системы и возвращает
    подробную информацию о их состоянии.
    """
    try:
        health_info = {
            "status": "healthy",
            "timestamp": datetime.utcnow(),
            "components": {
                "api": "healthy",
                "database": "unknown",
                "bot_manager": "unknown",
                "websocket": "healthy"
            },
            "metrics": {
                "websocket_connections": len(ws_manager.active_connections),
                "uptime_seconds": 0
            }
        }
        
        # Проверяем BotManager
        try:
            if hasattr(bot_manager, 'get_health_check'):
                bot_health = bot_manager.get_health_check()
                health_info["components"]["bot_manager"] = bot_health.get("overall_status", "unknown")
                health_info["bot_details"] = bot_health
            else:
                health_info["components"]["bot_manager"] = "available"
        except Exception as e:
            health_info["components"]["bot_manager"] = "error"
            health_info["bot_error"] = str(e)
        
        # Проверяем базу данных
        try:
            # Простая проверка подключения к БД
            from ..core.database import SessionLocal
            from sqlalchemy import text
            
            db = SessionLocal()
            result = db.execute(text("SELECT 1")).scalar()
            db.close()
            
            if result == 1:
                health_info["components"]["database"] = "healthy"
            else:
                health_info["components"]["database"] = "unhealthy"
                
        except Exception as e:
            health_info["components"]["database"] = "error"
            health_info["database_error"] = str(e)
        
        # Определяем общий статус
        component_statuses = list(health_info["components"].values())
        if "error" in component_statuses or "unhealthy" in component_statuses:
            health_info["status"] = "degraded"
        
        return health_info
        
    except Exception as e:
        logger.error(f"Ошибка в health_check: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "unhealthy", 
                "timestamp": datetime.utcnow(),
                "error": str(e)
            }
        )

# Функция для установки менеджера бота
def set_bot_manager(manager):
    """Установить ссылку на менеджера бота"""
    global bot_manager
    bot_manager = manager
    logger.info("✅ BotManager установлен в API роутах")

# ✅ Все остальные роуты остаются как есть...
# (Вставьте сюда все остальные роуты из оригинального файла)

# WebSocket endpoint
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket для real-time обновлений"""
    await ws_manager.connect(websocket)
    try:
        while True:
            await asyncio.sleep(5)
            
            status_data = {
                "type": "bot_status",
                "status": bot_manager.get_status() if hasattr(bot_manager, 'get_status') else {"status": "unknown"},
                "timestamp": datetime.utcnow()
            }
            await websocket.send_text(json.dumps(status_data, default=str))
    
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket ошибка: {e}")
        ws_manager.disconnect(websocket)

# Остальные endpoints (оставляем все как есть)
@router.get("/status")
async def get_bot_status():
    """Получить статус бота (упрощенная версия без аутентификации для начала)"""
    try:
        if hasattr(bot_manager, 'get_status'):
            base_status = bot_manager.get_status()
            return base_status
        else:
            return {
                "status": "unknown",
                "message": "BotManager не инициализирован",
                "timestamp": datetime.utcnow()
            }
    except Exception as e:
        logger.error(f"Ошибка получения статуса: {e}")
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.utcnow()
        }

# Добавляем остальные роуты...
# (Здесь должны быть все остальные роуты из оригинального файла)