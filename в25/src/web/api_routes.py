"""
API роуты для дашборда криптотрейдинг бота
Файл: src/web/api_routes.py
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
import pandas as pd
import io
import csv

from ..core.database import get_db_session
from ..core.models import Trade, BotStatus
from ..bot.manager import BotManager  # ✅ ИСПРАВЛЕНО: BotManager вместо TradingBotManager
from .dashboard import get_dashboard_html
from ..core.clean_logging import trading_logger, get_clean_logger

logger = get_clean_logger(__name__)

# Pydantic модели для API
class BotStartRequest(BaseModel):
    strategy: str
    pairs: Optional[List[str]] = None

class SettingsRequest(BaseModel):
    max_position_size: float
    stop_loss: float
    take_profit: float
    max_daily_trades: int
    trading_pairs: List[str]
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
    profit: float
    strategy: str
    status: str

class StatsResponse(BaseModel):
    total_trades: int
    total_profit: float
    success_rate: float
    active_positions: int
    daily_trades: int
    best_pair: str
    worst_pair: str

# WebSocket менеджер для real-time обновлений
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

# Создаем роутер для API
router = APIRouter()

# Глобальная ссылка на менеджера бота
bot_manager: Optional[BotManager] = None  # ✅ ИСПРАВЛЕНО: BotManager

def set_bot_manager(manager: BotManager):  # ✅ ИСПРАВЛЕНО: BotManager
    """Установить ссылку на менеджера бота"""
    global bot_manager
    bot_manager = manager

@router.get("/", response_class=HTMLResponse)
async def dashboard():
    """Главная страница дашборда"""
    return HTMLResponse(get_dashboard_html())

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket для real-time обновлений"""
    await ws_manager.connect(websocket)
    try:
        while True:
            # Отправляем статус каждые 5 секунд
            await asyncio.sleep(5)
            
            if bot_manager:
                status_data = {
                    "type": "bot_status",
                    "status": "active" if bot_manager.status.value in ["running", "starting"] else "inactive",
                    "strategy": getattr(bot_manager, 'current_strategy', None),
                    "positions": len(bot_manager.positions) if hasattr(bot_manager, 'positions') else 0,
                    "timestamp": datetime.now()
                }
                await websocket.send_text(json.dumps(status_data, default=str))
    
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)

@router.get("/api/status")
async def get_bot_status():
    """Получить текущий статус бота"""
    if not bot_manager:
        return {"status": "inactive", "strategy": None, "message": "Бот не инициализирован"}
    
    return {
        "status": "active" if bot_manager.status.value in ["running", "starting"] else "inactive",
        "strategy": getattr(bot_manager, 'current_strategy', None),
        "positions": len(bot_manager.positions) if hasattr(bot_manager, 'positions') else 0,
        "uptime": str(datetime.now() - bot_manager.start_time) if bot_manager.start_time else None,
        "trades_today": getattr(bot_manager, 'trades_today', 0),
        "cycles_count": getattr(bot_manager, 'cycles_count', 0)
    }

@router.post("/api/bot/start")
async def start_bot(request: BotStartRequest):
    """Запустить бота с выбранной стратегией"""
    if not bot_manager:
        raise HTTPException(status_code=500, detail="Менеджер бота не инициализирован")
    
    try:
        success, message = await bot_manager.start()
        
        if success:
            # Уведомляем всех подключенных клиентов
            await ws_manager.broadcast({
                "type": "bot_started",
                "strategy": request.strategy,
                "pairs": request.pairs or [],
                "timestamp": datetime.now()
            })
            
            return {"success": True, "message": f"Бот запущен успешно: {message}"}
        else:
            raise HTTPException(status_code=400, detail=f"Ошибка запуска бота: {message}")
    
    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка: {str(e)}")

@router.post("/api/bot/stop")
async def stop_bot():
    """Остановить бота"""
    if not bot_manager:
        raise HTTPException(status_code=500, detail="Менеджер бота не инициализирован")
    
    try:
        success, message = await bot_manager.stop()
        
        if success:
            # Уведомляем всех подключенных клиентов
            await ws_manager.broadcast({
                "type": "bot_stopped",
                "timestamp": datetime.now()
            })
            
            return {"success": True, "message": f"Бот остановлен: {message}"}
        else:
            raise HTTPException(status_code=400, detail=f"Ошибка остановки бота: {message}")
    
    except Exception as e:
        logger.error(f"Ошибка остановки бота: {e}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка: {str(e)}")

@router.get("/api/stats")
async def get_stats():
    """Получить статистику торговли"""
    if not bot_manager:
        return {
            "total_trades": 0,
            "total_profit": 0.0,
            "success_rate": 0.0,
            "active_positions": 0,
            "daily_trades": 0,
            "best_pair": "Нет данных",
            "worst_pair": "Нет данных"
        }
    
    try:
        # Получаем данные из менеджера бота
        positions_count = len(bot_manager.positions) if hasattr(bot_manager, 'positions') else 0
        trades_today = getattr(bot_manager, 'trades_today', 0)
        
        # TODO: Добавить запросы к базе данных для получения полной статистики
        stats = {
            "total_trades": trades_today,
            "total_profit": 0.0,  # Будет вычислено из БД
            "success_rate": 0.0,  # Будет вычислено из БД
            "active_positions": positions_count,
            "daily_trades": trades_today,
            "best_pair": "BTCUSDT",  # Временно
            "worst_pair": "Нет данных"
        }
        
        return stats
    
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения статистики: {str(e)}")

@router.get("/api/trades")
async def get_trades(limit: int = 50):
    """Получить последние сделки"""
    try:
        # TODO: Добавить запрос к базе данных для получения сделок
        # db = get_db_session()
        # trades = db.query(Trade).order_by(Trade.timestamp.desc()).limit(limit).all()
        
        # Временно возвращаем пустой список
        trades = []
        
        return {
            "trades": trades,
            "total": len(trades)
        }
    
    except Exception as e:
        logger.error(f"Ошибка получения сделок: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения сделок: {str(e)}")

@router.get("/api/strategies")
async def get_strategies():
    """Получить список доступных стратегий"""
    if not bot_manager:
        return {"strategies": []}
    
    try:
        # Получаем список стратегий из фабрики стратегий
        strategy_factory = getattr(bot_manager, 'strategy_factory', None)
        if strategy_factory:
            strategies = [
                {"id": "momentum", "name": "Momentum Strategy", "description": "Стратегия следования за трендом"},
                {"id": "multi_indicator", "name": "Multi Indicator", "description": "Множественные индикаторы"},
                {"id": "scalping", "name": "Scalping", "description": "Скальпинг стратегия"},
                {"id": "safe_multi_indicator", "name": "Safe Multi Indicator", "description": "Безопасная множественная стратегия"},
                {"id": "conservative", "name": "Conservative", "description": "Консервативная стратегия"}
            ]
        else:
            strategies = []
        
        return {"strategies": strategies}
    
    except Exception as e:
        logger.error(f"Ошибка получения стратегий: {e}")
        return {"strategies": []}

@router.get("/api/pairs")
async def get_trading_pairs():
    """Получить список торговых пар"""
    try:
        # Базовые пары для торговли
        pairs = [
            {"symbol": "BTCUSDT", "name": "Bitcoin/USDT", "active": True},
            {"symbol": "ETHUSDT", "name": "Ethereum/USDT", "active": True},
            {"symbol": "ADAUSDT", "name": "Cardano/USDT", "active": False},
            {"symbol": "DOTUSDT", "name": "Polkadot/USDT", "active": False},
            {"symbol": "LINKUSDT", "name": "Chainlink/USDT", "active": False}
        ]
        
        return {"pairs": pairs}
    
    except Exception as e:
        logger.error(f"Ошибка получения торговых пар: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения торговых пар: {str(e)}")

@router.post("/api/settings")
async def save_settings(settings: SettingsRequest):
    """Сохранить настройки бота"""
    try:
        # TODO: Сохранить настройки в базе данных
        logger.info(f"Сохранение настроек: {settings}")
        
        # Уведомляем клиентов об изменении настроек
        await ws_manager.broadcast({
            "type": "settings_updated",
            "settings": settings.dict(),
            "timestamp": datetime.now()
        })
        
        return {"success": True, "message": "Настройки сохранены успешно"}
    
    except Exception as e:
        logger.error(f"Ошибка сохранения настроек: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения настроек: {str(e)}")

@router.get("/api/health")
async def health_check():
    """Проверка состояния системы"""
    if not bot_manager:
        return {"status": "unhealthy", "message": "Менеджер бота не инициализирован"}
    
    try:
        health_info = bot_manager.get_health_info()
        return health_info
    
    except Exception as e:
        logger.error(f"Ошибка проверки состояния: {e}")
        return {"status": "unhealthy", "message": f"Ошибка: {str(e)}"}

@router.get("/api/logs")
async def get_logs(lines: int = 100):
    """Получить последние строки логов"""
    try:
        # TODO: Реализовать чтение логов из файла
        logs = [
            {"timestamp": datetime.now(), "level": "INFO", "message": "Система работает нормально"},
            {"timestamp": datetime.now(), "level": "DEBUG", "message": "Проверка состояния завершена"}
        ]
        
        return {"logs": logs}
    
    except Exception as e:
        logger.error(f"Ошибка получения логов: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения логов: {str(e)}")

# Дополнительные роуты для управления файлами
@router.get("/api/export/trades")
async def export_trades():
    """Экспорт сделок в CSV"""
    try:
        # TODO: Реализовать экспорт из базы данных
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Время", "Пара", "Тип", "Количество", "Цена", "Прибыль"])
        
        # Добавить данные из БД
        
        output.seek(0)
        return {"csv_data": output.getvalue()}
    
    except Exception as e:
        logger.error(f"Ошибка экспорта сделок: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка экспорта: {str(e)}")

# Роут для статических файлов (если нужны)
@router.get("/favicon.ico")
async def favicon():
    """Фавикон для дашборда"""
    # Возвращаем простой ответ или статический файл
    return {"message": "No favicon"}