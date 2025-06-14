"""
Веб-интерфейс для Crypto Trading Bot
"""
from fastapi import FastAPI, Depends, HTTPException, WebSocket, status
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List, Dict, Any
import logging

from ..core.database import get_db, SessionLocal
from ..core.models import User, Trade, Signal, TradingPair
from ..bot.manager import bot_manager
from .auth import get_current_user, create_access_token, auth_service
from .websocket import websocket_endpoint
from .dashboard import get_dashboard_html

logger = logging.getLogger(__name__)

# Создаем приложение
app = FastAPI(
    title="Crypto Trading Bot",
    version="3.0",
    description="Professional Crypto Trading Bot with Web Interface"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Модели для API
class LoginRequest(BaseModel):
    username: str
    password: str

class BotActionRequest(BaseModel):
    action: str  # start, stop

class PairsUpdateRequest(BaseModel):
    pairs: List[str]

# === API Endpoints ===

@app.get("/", response_class=HTMLResponse)
async def root():
    """Главная страница с дашбордом"""
    return get_dashboard_html()

# ✅ ИСПРАВЛЕНИЕ: Добавляем стандартный OAuth2 endpoint
@app.post("/auth/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 совместимый endpoint для получения токена
    Используется стандартными клиентами
    """
    db = SessionLocal()
    try:
        user = await auth_service.authenticate_user(db, form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token = create_access_token(data={"sub": user.username})
        return {"access_token": access_token, "token_type": "bearer"}
    finally:
        db.close()

# ✅ ДОПОЛНИТЕЛЬНО: JSON endpoint для веб-интерфейса
@app.post("/api/login")
async def login_json(request: LoginRequest):
    """JSON endpoint для веб-интерфейса"""
    db = SessionLocal()
    try:
        user = await auth_service.authenticate_user(db, request.username, request.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверные учетные данные"
            )
        
        access_token = create_access_token(data={"sub": user.username})
        return {
            "access_token": access_token, 
            "token_type": "bearer",
            "user": {
                "username": user.username,
                "is_admin": user.is_admin
            }
        }
    finally:
        db.close()

# ✅ ДОБАВЛЯЕМ: Endpoint для получения информации о текущем пользователе
@app.get("/api/user/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Получить информацию о текущем пользователе"""
    return {
        "username": current_user.username,
        "email": current_user.email,
        "is_admin": current_user.is_admin,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at,
        "last_login": current_user.last_login
    }

@app.get("/api/bot/status")
async def get_bot_status(current_user: User = Depends(get_current_user)):
    """Получить статус бота"""
    return bot_manager.get_status()

@app.post("/api/bot/action")
async def bot_action(
    request: BotActionRequest, 
    current_user: User = Depends(get_current_user)
):
    """Управление ботом"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Только администраторы могут управлять ботом"
        )
    
    if request.action == "start":
        success, message = await bot_manager.start()
        if not success:
            raise HTTPException(status_code=400, detail=message)
        return {"status": "started", "message": message}
    
    elif request.action == "stop":
        success, message = await bot_manager.stop()
        return {"status": "stopped", "message": message}
    
    else:
        raise HTTPException(status_code=400, detail="Invalid action")

# Остальные endpoints остаются теми же...
@app.get("/api/balance")
async def get_balance(current_user: User = Depends(get_current_user)):
    """Получить баланс"""
    try:
        balance = await bot_manager.exchange.fetch_balance()
        return {
            "USDT": balance.get("USDT", {}).get("free", 0),
            "total": balance.get("USDT", {}).get("total", 0)
        }
    except Exception as e:
        logger.error(f"Ошибка получения баланса: {e}")
        return {"USDT": 0, "total": 0}

@app.get("/api/trades")
async def get_trades(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Получить историю сделок"""
    trades = db.query(Trade).order_by(Trade.created_at.desc()).limit(limit).all()
    return trades

@app.get("/api/pairs")
async def get_pairs(
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Получить список торговых пар"""
    pairs = db.query(TradingPair).all()
    return pairs

@app.post("/api/pairs")
async def update_pairs(
    request: PairsUpdateRequest,
    current_user: User = Depends(get_current_user)
):
    """Обновить торговые пары"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Только администраторы могут изменять настройки"
        )
    
    success, message = await bot_manager.update_pairs(request.pairs)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"status": "updated", "pairs": request.pairs}

# ✅ ДОБАВЛЯЕМ: Endpoint для дашборда
@app.get("/api/dashboard")
async def get_dashboard_data(
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Получить все данные для дашборда"""
    try:
        # Статус бота
        bot_status = bot_manager.get_status()
        
        # Баланс
        try:
            balance_data = await get_balance(current_user)
        except:
            balance_data = {"USDT": 0, "total": 0}
        
        # Статистика
        from datetime import datetime, timedelta
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        recent_trades = db.query(Trade).order_by(Trade.created_at.desc()).limit(10).all()
        recent_signals = db.query(Signal).order_by(Signal.created_at.desc()).limit(10).all()
        
        # Считаем статистику за день
        today_trades = db.query(Trade).filter(Trade.created_at >= today_start).all()
        total_profit = sum(t.profit or 0 for t in today_trades)
        profitable_trades = len([t for t in today_trades if t.profit and t.profit > 0])
        win_rate = (profitable_trades / len(today_trades) * 100) if today_trades else 0
        
        return {
            "bot_status": bot_status,
            "balance": balance_data,
            "statistics": {
                "total_trades": len(today_trades),
                "profitable_trades": profitable_trades,
                "total_profit": total_profit,
                "win_rate": win_rate
            },
            "recent_trades": [
                {
                    "id": t.id,
                    "symbol": t.symbol,
                    "side": t.side.value if hasattr(t.side, 'value') else str(t.side),
                    "entry_price": float(t.entry_price) if t.entry_price else 0,
                    "exit_price": float(t.exit_price) if t.exit_price else None,
                    "profit": float(t.profit) if t.profit else None,
                    "status": t.status.value if hasattr(t.status, 'value') else str(t.status),
                    "created_at": t.created_at.isoformat()
                } for t in recent_trades
            ],
            "recent_signals": [
                {
                    "id": s.id,
                    "symbol": s.symbol,
                    "action": s.action,
                    "confidence": float(s.confidence) if s.confidence else 0,
                    "reason": s.reason,
                    "created_at": s.created_at.isoformat()
                } for s in recent_signals
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Ошибка получения данных дашборда: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения данных")

# WebSocket endpoint
app.websocket("/ws")(websocket_endpoint)

# HTML дашборд
dashboard_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Crypto Trading Bot</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0f0f0f;
            color: #fff;
            line-height: 1.6;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        .status-bar {
            display: flex;
            gap: 20px;
            align-items: center;
            font-size: 1.1em;
        }
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .status-indicator.online { background: #4ade80; }
        .status-indicator.offline { background: #f87171; }
        
        .dashboard {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .card {
            background: #1a1a1a;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
            transition: transform 0.3s;
        }
        .card:hover {
            transform: translateY(-5px);
        }
        .card h3 {
            color: #9ca3af;
            font-size: 0.9em;
            text-transform: uppercase;
            margin-bottom: 10px;
        }
        .metric {
            font-size: 2em;
            font-weight: 700;
            color: #fff;
        }
        .positive { color: #4ade80; }
        .negative { color: #f87171; }
        
        .controls {
            display: flex;
            gap: 15px;
            margin-bottom: 30px;
        }
        .btn {
            padding: 12px 30px;
            border: none;
            border-radius: 8px;
            font-size: 1em;
            cursor: pointer;
            transition: all 0.3s;
            font-weight: 600;
        }
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .btn-danger {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        }
        
        .table-container {
            background: #1a1a1a;
            border-radius: 15px;
            padding: 25px;
            overflow-x: auto;
            margin-bottom: 30px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            padding: 15px;
            text-align: left;
            border-bottom: 1px solid #2a2a2a;
        }
        th {
            color: #9ca3af;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.85em;
        }
        
        #ws-status {
            position: fixed;
            bottom: 20px;
            right: 20px;
            padding: 10px 20px;
            background: #1a1a1a;
            border-radius: 20px;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Crypto Trading Bot</h1>
            <div class="status-bar">
                <span>
                    <span id="bot-status-indicator" class="status-indicator offline"></span>
                    Bot: <span id="bot-status">Offline</span>
                </span>
                <span>
                    <span id="ws-indicator" class="status-indicator offline"></span>
                    WebSocket: <span id="ws-status-text">Disconnected</span>
                </span>
            </div>
        </div>
        
        <div class="controls">
            <button id="start-btn" class="btn btn-primary" onclick="startBot()">▶️ Start Bot</button>
            <button id="stop-btn" class="btn btn-danger" onclick="stopBot()" style="display:none">⏹️ Stop Bot</button>
            <button class="btn btn-primary" onclick="refreshData()">🔄 Refresh</button>
        </div>
        
        <div class="dashboard">
            <div class="card">
                <h3>Balance</h3>
                <div id="balance" class="metric">$0.00</div>
            </div>
            <div class="card">
                <h3>Daily P&L</h3>
                <div id="daily-pnl" class="metric">$0.00</div>
            </div>
            <div class="card">
                <h3>Win Rate</h3>
                <div id="win-rate" class="metric">0%</div>
            </div>
            <div class="card">
                <h3>Active Positions</h3>
                <div id="positions" class="metric">0</div>
            </div>
        </div>
        
        <div class="table-container">
            <h3>Recent Trades</h3>
            <table>
                <thead>
                    <tr>
                        <th>Time</th>
                        <th>Symbol</th>
                        <th>Side</th>
                        <th>Entry</th>
                        <th>Exit</th>
                        <th>Profit</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody id="trades-tbody">
                    <tr><td colspan="7" style="text-align:center">No trades yet</td></tr>
                </tbody>
            </table>
        </div>
    </div>
    
    <div id="ws-status">
        <span id="ws-status">⚡ Connecting...</span>
    </div>
    
    <script>
        let ws = null;
        let token = localStorage.getItem('token');
        
        // Если нет токена, перенаправляем на логин
        if (!token) {
            // Простая форма логина
            document.body.innerHTML = `
                <div style="display:flex;align-items:center;justify-content:center;height:100vh">
                    <div class="card" style="width:400px">
                        <h2 style="margin-bottom:20px">Login</h2>
                        <input type="text" id="username" placeholder="Username" style="width:100%;padding:10px;margin-bottom:10px;background:#2a2a2a;border:none;border-radius:5px;color:white">
                        <input type="password" id="password" placeholder="Password" style="width:100%;padding:10px;margin-bottom:20px;background:#2a2a2a;border:none;border-radius:5px;color:white">
                        <button class="btn btn-primary" onclick="login()" style="width:100%">Login</button>
                    </div>
                </div>
            `;
        } else {
            connectWebSocket();
            refreshData();
        }
        
        async function login() {
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            
            try {
                const response = await fetch('/api/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password })
                });
                
                if (response.ok) {
                    const data = await response.json();
                    localStorage.setItem('token', data.access_token);
                    location.reload();
                } else {
                    alert('Invalid credentials');
                }
            } catch (error) {
                alert('Connection error');
            }
        }
        
        function connectWebSocket() {
            ws = new WebSocket(`ws://${window.location.host}/ws`);
            
            ws.onopen = () => {
                document.getElementById('ws-indicator').classList.add('online');
                document.getElementById('ws-status-text').textContent = 'Connected';
                document.getElementById('ws-status').textContent = '⚡ Connected';
            };
            
            ws.onclose = () => {
                document.getElementById('ws-indicator').classList.remove('online');
                document.getElementById('ws-status-text').textContent = 'Disconnected';
                document.getElementById('ws-status').textContent = '⚡ Reconnecting...';
                // Переподключение через 5 секунд
                setTimeout(connectWebSocket, 5000);
            };
            
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                updateDashboard(data.data);
            };
        }
        
        async function refreshData() {
            try {
                // Статус бота
                const statusRes = await fetch('/api/bot/status', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (statusRes.ok) {
                    const status = await statusRes.json();
                    updateBotStatus(status);
                }
                
                // Баланс
                const balanceRes = await fetch('/api/balance', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (balanceRes.ok) {
                    const balance = await balanceRes.json();
                    document.getElementById('balance').textContent = `$${balance.USDT.toFixed(2)}`;
                }
                
                // Сделки
                const tradesRes = await fetch('/api/trades?limit=10', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (tradesRes.ok) {
                    const trades = await tradesRes.json();
                    updateTradesTable(trades);
                }
            } catch (error) {
                console.error('Error refreshing data:', error);
            }
        }
        
        function updateDashboard(data) {
            if (data.bot_status) {
                updateBotStatus(data.bot_status);
            }
            if (data.balance) {
                document.getElementById('balance').textContent = `$${data.balance.USDT.toFixed(2)}`;
            }
            if (data.recent_trades) {
                updateTradesTable(data.recent_trades);
            }
        }
        
        function updateBotStatus(status) {
            const isRunning = status.is_running;
            document.getElementById('bot-status').textContent = isRunning ? 'Running' : 'Stopped';
            document.getElementById('bot-status-indicator').classList.toggle('online', isRunning);
            document.getElementById('bot-status-indicator').classList.toggle('offline', !isRunning);
            
            document.getElementById('start-btn').style.display = isRunning ? 'none' : 'block';
            document.getElementById('stop-btn').style.display = isRunning ? 'block' : 'none';
            
            if (status.open_positions !== undefined) {
                document.getElementById('positions').textContent = status.open_positions;
            }
        }
        
        function updateTradesTable(trades) {
            const tbody = document.getElementById('trades-tbody');
            if (trades.length === 0) {
                tbody.innerHTML = '<tr><td colspan="7" style="text-align:center">No trades yet</td></tr>';
                return;
            }
            
            tbody.innerHTML = trades.map(trade => `
                <tr>
                    <td>${new Date(trade.created_at).toLocaleString()}</td>
                    <td>${trade.symbol}</td>
                    <td>${trade.side}</td>
                    <td>$${trade.entry_price.toFixed(2)}</td>
                    <td>${trade.exit_price ? `$${trade.exit_price.toFixed(2)}` : '-'}</td>
                    <td class="${trade.profit >= 0 ? 'positive' : 'negative'}">
                        ${trade.profit ? `$${trade.profit.toFixed(2)}` : '-'}
                    </td>
                    <td>${trade.status}</td>
                </tr>
            `).join('');
        }
        
        async function startBot() {
            try {
                const response = await fetch('/api/bot/action', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ action: 'start' })
                });
                
                if (response.ok) {
                    alert('Bot started successfully');
                    refreshData();
                } else {
                    const error = await response.json();
                    alert(`Failed to start bot: ${error.detail}`);
                }
            } catch (error) {
                alert('Connection error');
            }
        }
        
        async function stopBot() {
            if (!confirm('Are you sure you want to stop the bot?')) return;
            
            try {
                const response = await fetch('/api/bot/action', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ action: 'stop' })
                });
                
                if (response.ok) {
                    alert('Bot stopped successfully');
                    refreshData();
                } else {
                    alert('Failed to stop bot');
                }
            } catch (error) {
                alert('Connection error');
            }
        }
        
        // Обновление данных каждые 10 секунд
        setInterval(refreshData, 10000);
    </script>
</body>
</html>
"""