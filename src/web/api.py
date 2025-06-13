"""
API endpoints для управления ботом
Путь: /var/www/www-root/data/www/systemetech.ru/src/web/api.py
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..core.database import get_db
from ..core.models import Trade, Signal, TradingPair, User, BotState, Balance
from ..bot.manager import bot_manager
from .auth import get_current_user

router = APIRouter()

@router.get("/status")
async def get_bot_status(current_user: User = Depends(get_current_user)):
    """Получить статус бота"""
    return bot_manager.get_status()

@router.post("/bot/start")
async def start_bot(current_user: User = Depends(get_current_user)):
    """Запустить бота"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Только администраторы могут управлять ботом")
    
    success, message = await bot_manager.start()
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {"status": "started", "message": message}

@router.post("/bot/stop")
async def stop_bot(current_user: User = Depends(get_current_user)):
    """Остановить бота"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Только администраторы могут управлять ботом")
    
    success, message = await bot_manager.stop()
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {"status": "stopped", "message": message}

@router.get("/pairs")
async def get_trading_pairs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить список торговых пар"""
    pairs = db.query(TradingPair).all()
    return pairs

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
    
    return {"status": "updated", "message": message, "pairs": pairs}

@router.get("/trades")
async def get_trades(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить список сделок"""
    trades = db.query(Trade).order_by(Trade.created_at.desc()).offset(skip).limit(limit).all()
    return trades

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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить список сигналов"""
    signals = db.query(Signal).order_by(Signal.created_at.desc()).offset(skip).limit(limit).all()
    return signals

@router.get("/balance")
async def get_balance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить текущий баланс"""
    # Последние балансы по каждой валюте
    subquery = db.query(
        Balance.currency,
        func.max(Balance.timestamp).label('max_timestamp')
    ).group_by(Balance.currency).subquery()
    
    balances = db.query(Balance).join(
        subquery,
        (Balance.currency == subquery.c.currency) & 
        (Balance.timestamp == subquery.c.max_timestamp)
    ).all()
    
    return {b.currency: {"total": b.total, "free": b.free, "used": b.used} for b in balances}

@router.get("/statistics")
async def get_statistics(
    period: str = "day",  # day, week, month, all
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить статистику торговли"""
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
    
    # Статистика по парам
    pair_stats = {}
    for trade in trades:
        if trade.symbol not in pair_stats:
            pair_stats[trade.symbol] = {
                'total': 0,
                'profitable': 0,
                'profit': 0
            }
        pair_stats[trade.symbol]['total'] += 1
        if trade.profit and trade.profit > 0:
            pair_stats[trade.symbol]['profitable'] += 1
        pair_stats[trade.symbol]['profit'] += trade.profit or 0
    
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
    recent_trades = await get_trades(0, 10, db, current_user)
    recent_signals = await get_signals(0, 10, db, current_user)
    
    return {
        'bot_status': bot_status,
        'balance': balance,
        'statistics': statistics,
        'recent_trades': recent_trades,
        'recent_signals': recent_signals,
        'timestamp': datetime.utcnow()
    }