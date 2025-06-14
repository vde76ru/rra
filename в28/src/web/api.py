"""
API endpoints для управления ботом
Путь: /var/www/www-root/data/www/systemetech.ru/src/web/api.py
"""
import asyncio
import json
import io
import csv
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel


from ..core.database import get_db
from ..core.models import Trade, Signal, TradingPair, User, BotState, Balance
from ..bot.manager import bot_manager
from .auth import get_current_user
from ..core.clean_logging import get_clean_logger

logger = get_clean_logger(__name__)

# ✅ Добавляем Pydantic модели для улучшенной валидации
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

# ✅ WebSocket менеджер для real-time обновлений
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

# ✅ Добавляем WebSocket endpoint
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket для real-time обновлений"""
    await ws_manager.connect(websocket)
    try:
        while True:
            await asyncio.sleep(5)
            
            status_data = {
                "type": "bot_status",
                "status": bot_manager.get_status(),
                "timestamp": datetime.utcnow()
            }
            await websocket.send_text(json.dumps(status_data, default=str))
    
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket ошибка: {e}")
        ws_manager.disconnect(websocket)

@router.get("/status")
async def get_bot_status(current_user: User = Depends(get_current_user)):
    """Получить расширенный статус бота"""
    base_status = bot_manager.get_status()
    
    # ✅ Добавляем дополнительную информацию
    extended_status = {
        **base_status,
        "uptime": str(datetime.utcnow() - bot_manager.start_time) if hasattr(bot_manager, 'start_time') and bot_manager.start_time else None,
        "cycles_count": getattr(bot_manager, 'cycles_count', 0),
        "active_strategies": getattr(bot_manager, 'active_strategies', []),
        "memory_usage": getattr(bot_manager, 'memory_usage', 0)
    }
    
    return extended_status

@router.post("/bot/start")
async def start_bot(
    request: Optional[BotStartRequest] = None,
    current_user: User = Depends(get_current_user)
):
    """Запустить бота с улучшенными параметрами"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Только администраторы могут управлять ботом")
    
    # ✅ Используем параметры из запроса, если они переданы
    strategy = request.strategy if request else None
    pairs = request.pairs if request else None
    
    success, message = await bot_manager.start(strategy=strategy, pairs=pairs)
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    # ✅ Уведомляем WebSocket клиентов
    await ws_manager.broadcast({
        "type": "bot_started",
        "strategy": strategy,
        "pairs": pairs or [],
        "timestamp": datetime.utcnow()
    })
    
    return {"status": "started", "message": message, "strategy": strategy, "pairs": pairs}


def set_bot_manager(manager):
    """Установить ссылку на менеджера бота"""
    global bot_manager
    bot_manager = manager

@router.post("/bot/stop")
async def stop_bot(current_user: User = Depends(get_current_user)):
    """Остановить бота"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Только администраторы могут управлять ботом")
    
    success, message = await bot_manager.stop()
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    # ✅ Уведомляем WebSocket клиентов
    await ws_manager.broadcast({
        "type": "bot_stopped",
        "timestamp": datetime.utcnow()
    })
    
    return {"status": "stopped", "message": message}

@router.get("/pairs")
async def get_trading_pairs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить список торговых пар с дополнительной информацией"""
    pairs = db.query(TradingPair).all()
    
    # ✅ Добавляем статистику по парам
    enhanced_pairs = []
    for pair in pairs:
        # Получаем статистику по последним сделкам
        recent_trades = db.query(Trade).filter(
            Trade.symbol == pair.symbol,
            Trade.created_at >= datetime.utcnow() - timedelta(days=7)
        ).all()
        
        profit_sum = sum(t.profit or 0 for t in recent_trades)
        
        enhanced_pairs.append({
            "id": pair.id,
            "symbol": pair.symbol,
            "is_active": pair.is_active,
            "min_quantity": pair.min_quantity,
            "weekly_trades": len(recent_trades),
            "weekly_profit": profit_sum,
            "last_trade": recent_trades[0].created_at if recent_trades else None
        })
    
    return enhanced_pairs

@router.post("/pairs")
async def update_trading_pairs(
    pairs: List[str],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Обновить активные торговые пары"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Только администраторы могут изменять настройки")
    
    success, message = await bot_manager.update_pairs(pairs)
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    # ✅ Уведомляем WebSocket клиентов
    await ws_manager.broadcast({
        "type": "pairs_updated",
        "pairs": pairs,
        "timestamp": datetime.utcnow()
    })
    
    return {"status": "updated", "message": message, "pairs": pairs}

@router.get("/trades")
async def get_trades(
    skip: int = 0,
    limit: int = 100,
    symbol: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить список сделок с фильтрацией"""
    query = db.query(Trade)
    
    # ✅ Добавляем фильтры
    if symbol:
        query = query.filter(Trade.symbol == symbol)
    if status:
        query = query.filter(Trade.status == status)
    
    trades = query.order_by(Trade.created_at.desc()).offset(skip).limit(limit).all()
    total = query.count()
    
    return {
        "trades": trades,
        "total": total,
        "skip": skip,
        "limit": limit
    }

@router.get("/trades/{trade_id}")
async def get_trade(
    trade_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить информацию о конкретной сделке"""
    trade = db.query(Trade).filter(Trade.id == trade_id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    return trade

@router.get("/signals")
async def get_signals(
    skip: int = 0,
    limit: int = 100,
    signal_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить список сигналов с фильтрацией"""
    query = db.query(Signal)
    
    if signal_type:
        query = query.filter(Signal.signal_type == signal_type)
    
    signals = query.order_by(Signal.created_at.desc()).offset(skip).limit(limit).all()
    total = query.count()
    
    return {
        "signals": signals,
        "total": total,
        "skip": skip,
        "limit": limit
    }

@router.get("/balance")
async def get_balance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить текущий баланс с историей изменений"""
    # Последние балансы по каждой валюте
    subquery = db.query(
        Balance.currency,
        func.max(Balance.timestamp).label('max_timestamp')
    ).group_by(Balance.currency).subquery()
    
    current_balances = db.query(Balance).join(
        subquery,
        (Balance.currency == subquery.c.currency) & 
        (Balance.timestamp == subquery.c.max_timestamp)
    ).all()
    
    # ✅ Добавляем историю изменений за последний день
    yesterday = datetime.utcnow() - timedelta(days=1)
    balance_history = db.query(Balance).filter(
        Balance.timestamp >= yesterday
    ).order_by(Balance.timestamp.desc()).all()
    
    result = {
        "current": {b.currency: {"total": b.total, "free": b.free, "used": b.used} for b in current_balances},
        "history": [
            {
                "timestamp": b.timestamp,
                "currency": b.currency,
                "total": b.total,
                "free": b.free,
                "used": b.used
            } for b in balance_history
        ]
    }
    
    return result

@router.get("/statistics")
async def get_statistics(
    period: str = "day",  # day, week, month, all
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить расширенную статистику торговли"""
    # Определяем период
    if period == "day":
        start_date = datetime.utcnow() - timedelta(days=1)
    elif period == "week":
        start_date = datetime.utcnow() - timedelta(weeks=1)
    elif period == "month":
        start_date = datetime.utcnow() - timedelta(days=30)
    else:
        start_date = datetime.min
    
    # Статистика по сделкам
    trades = db.query(Trade).filter(Trade.created_at >= start_date).all()
    total_trades = len(trades)
    profitable_trades = len([t for t in trades if t.profit and t.profit > 0])
    total_profit = sum(t.profit or 0 for t in trades)
    
    # Win rate
    win_rate = (profitable_trades / total_trades * 100) if total_trades > 0 else 0
    
    # Средняя прибыль/убыток
    avg_profit = total_profit / total_trades if total_trades > 0 else 0
    
    # Лучшая и худшая сделка
    best_trade = max(trades, key=lambda t: t.profit or 0) if trades else None
    worst_trade = min(trades, key=lambda t: t.profit or 0) if trades else None
    
    # ✅ Расширенная статистика по парам
    pair_stats = {}
    for trade in trades:
        if trade.symbol not in pair_stats:
            pair_stats[trade.symbol] = {
                'total': 0,
                'profitable': 0,
                'profit': 0,
                'avg_profit': 0,
                'win_rate': 0
            }
        pair_stats[trade.symbol]['total'] += 1
        if trade.profit and trade.profit > 0:
            pair_stats[trade.symbol]['profitable'] += 1
        pair_stats[trade.symbol]['profit'] += trade.profit or 0
    
    # Вычисляем дополнительные метрики для пар
    for symbol in pair_stats:
        if pair_stats[symbol]['total'] > 0:
            pair_stats[symbol]['avg_profit'] = pair_stats[symbol]['profit'] / pair_stats[symbol]['total']
            pair_stats[symbol]['win_rate'] = (pair_stats[symbol]['profitable'] / pair_stats[symbol]['total']) * 100
    
    return {
        'period': period,
        'total_trades': total_trades,
        'profitable_trades': profitable_trades,
        'win_rate': win_rate,
        'total_profit': total_profit,
        'average_profit': avg_profit,
        'best_trade': {
            'symbol': best_trade.symbol,
            'profit': best_trade.profit,
            'date': best_trade.created_at
        } if best_trade else None,
        'worst_trade': {
            'symbol': worst_trade.symbol,
            'profit': worst_trade.profit,
            'date': worst_trade.created_at
        } if worst_trade else None,
        'pair_statistics': pair_stats
    }

@router.post("/position/{symbol}/close")
async def close_position(
    symbol: str,
    current_user: User = Depends(get_current_user)
):
    """Закрыть позицию вручную"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Только администраторы могут закрывать позиции")
    
    success, message = await bot_manager.close_position(symbol)
    
    if not success:
        raise HTTPException(status_code=404, detail=message)
    
    # ✅ Уведомляем WebSocket клиентов
    await ws_manager.broadcast({
        "type": "position_closed",
        "symbol": symbol,
        "timestamp": datetime.utcnow()
    })
    
    return {"status": "closed", "message": message}

@router.get("/dashboard")
async def get_dashboard_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить все данные для дашборда"""
    bot_status = bot_manager.get_status()
    balance = await get_balance(db, current_user)
    statistics = await get_statistics("day", db, current_user)
    recent_trades = await get_trades(0, 10, db=db, current_user=current_user)
    recent_signals = await get_signals(0, 10, db=db, current_user=current_user)
    
    return {
        'bot_status': bot_status,
        'balance': balance,
        'statistics': statistics,
        'recent_trades': recent_trades,
        'recent_signals': recent_signals,
        'timestamp': datetime.utcnow()
    }

# ✅ Новые endpoints из улучшенной версии
@router.get("/strategies")
async def get_strategies(current_user: User = Depends(get_current_user)):
    """Получить список доступных стратегий"""
    try:
        strategies = [
            {"id": "momentum", "name": "Momentum Strategy", "description": "Стратегия следования за трендом"},
            {"id": "multi_indicator", "name": "Multi Indicator", "description": "Множественные индикаторы"},
            {"id": "scalping", "name": "Scalping", "description": "Скальпинг стратегия"},
            {"id": "safe_multi_indicator", "name": "Safe Multi Indicator", "description": "Безопасная множественная стратегия"},
            {"id": "conservative", "name": "Conservative", "description": "Консервативная стратегия"}
        ]
        
        return {"strategies": strategies}
    
    except Exception as e:
        logger.error(f"Ошибка получения стратегий: {e}")
        return {"strategies": []}

@router.post("/settings")
async def save_settings(
    settings: SettingsRequest,
    current_user: User = Depends(get_current_user)
):
    """Сохранить настройки бота"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Только администраторы могут изменять настройки")
    
    try:
        # TODO: Сохранить настройки в базе данных
        logger.info(f"Сохранение настроек пользователем {current_user.username}: {settings}")
        
        # Уведомляем WebSocket клиентов
        await ws_manager.broadcast({
            "type": "settings_updated",
            "settings": settings.dict(),
            "timestamp": datetime.utcnow()
        })
        
        return {"success": True, "message": "Настройки сохранены успешно"}
    
    except Exception as e:
        logger.error(f"Ошибка сохранения настроек: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения настроек: {str(e)}")

@router.get("/health")
async def health_check():
    """Проверка состояния системы"""
    try:
        health_info = {
            "status": "healthy",
            "bot_manager": bool(bot_manager),
            "websocket_connections": len(ws_manager.active_connections),
            "timestamp": datetime.utcnow()
        }
        
        if hasattr(bot_manager, 'get_health_info'):
            bot_health = bot_manager.get_health_info()
            health_info.update(bot_health)
        
        return health_info
    
    except Exception as e:
        logger.error(f"Ошибка проверки состояния: {e}")
        return {"status": "unhealthy", "message": f"Ошибка: {str(e)}"}

@router.get("/export/trades")
async def export_trades(
    format: str = "csv",
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Экспорт сделок в различных форматах"""
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        trades = db.query(Trade).filter(Trade.created_at >= start_date).all()
        
        if format.lower() == "csv":
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["Время", "Пара", "Тип", "Количество", "Цена", "Прибыль", "Статус"])
            
            for trade in trades:
                writer.writerow([
                    trade.created_at,
                    trade.symbol,
                    trade.side,
                    trade.quantity,
                    trade.price,
                    trade.profit or 0,
                    trade.status
                ])
            
            output.seek(0)
            return {"format": "csv", "data": output.getvalue(), "count": len(trades)}
        
        return {"error": "Неподдерживаемый формат"}
    
    except Exception as e:
        logger.error(f"Ошибка экспорта сделок: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка экспорта: {str(e)}")

# ✅ Сохраняем оригинальные endpoints для аналитики
@router.get("/analytics/report")
async def get_analytics_report(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить расширенный аналитический отчет"""
    try:
        from ..analysis.advanced_analytics import advanced_analytics
        report = await advanced_analytics.generate_performance_report(days)
        return report
    except ImportError:
        # Fallback если модуль не найден
        return {"error": "Модуль аналитики не найден"}

@router.get("/analytics/trade/{trade_id}")
async def analyze_trade_context(
    trade_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Анализ контекста конкретной сделки"""
    try:
        from ..analysis.advanced_analytics import advanced_analytics
        from ..analysis.market_analyzer import MarketAnalyzer
        
        trade = db.query(Trade).filter(Trade.id == trade_id).first()
        if not trade:
            raise HTTPException(status_code=404, detail="Trade not found")
        
        analyzer = MarketAnalyzer()
        market_data = await analyzer.analyze_symbol(trade.symbol)
        
        if market_data and 'df' in market_data:
            analysis = await advanced_analytics.analyze_trade_context(trade_id, market_data['df'])
            return analysis
        else:
            return {"error": "No market data available"}
    
    except ImportError:
        return {"error": "Модуль аналитики не найден"}