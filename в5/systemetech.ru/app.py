from fastapi import FastAPI, WebSocket, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import json
from datetime import datetime, timedelta
import asyncio
from typing import List, Dict
from sqlalchemy.orm import Session
from src.core.database import SessionLocal, get_db
from src.core.models import Trade, User
from src.web.auth import auth_service, ACCESS_TOKEN_EXPIRE_MINUTES
from src.exchange.bybit_client import HumanizedBybitClient
from src.strategies.advanced_strategies import MultiIndicatorStrategy, SafeScalpingStrategy
from src.notifications.telegram_notifier import TelegramNotifier

app = FastAPI(title="Crypto Trading Bot", version="2.0")

# Статические файлы и шаблоны
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Инициализация компонентов
notifier = TelegramNotifier()
trading_pairs = []  # Активные торговые пары

# HTML страница входа
login_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Crypto Bot - Login</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #1a1a1a;
            color: #fff;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }
        .login-container {
            background: #2a2a2a;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(0,0,0,0.5);
            width: 300px;
        }
        h2 {
            text-align: center;
            margin-bottom: 20px;
        }
        input {
            width: 100%;
            padding: 10px;
            margin: 10px 0;
            background: #333;
            border: 1px solid #444;
            border-radius: 5px;
            color: #fff;
        }
        button {
            width: 100%;
            padding: 10px;
            background: #4CAF50;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
        }
        button:hover {
            background: #45a049;
        }uvicorn.run(app, host="0.0.0.0", port=8000)
        .error {
            color: #f44336;
            text-align: center;
            margin-top: 10px;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <h2>🔐 Crypto Trading Bot</h2>
        <form id="loginForm">
            <input type="text" id="username" placeholder="Username" required>
            <input type="password" id="password" placeholder="Password" required>
            <button type="submit">Login</button>
            <div id="error" class="error"></div>
        </form>
    </div>
    
    <script>
        document.getElementById('loginForm').onsubmit = async (e) => {
            e.preventDefault();
            
            const formData = new FormData();
            formData.append('username', document.getElementById('username').value);
            formData.append('password', document.getElementById('password').value);
            
            try {
                const response = await fetch('/token', {
                    method: 'POST',
                    body: formData
                });
                
                if (response.ok) {
                    const data = await response.json();
                    localStorage.setItem('access_token', data.access_token);
                    window.location.href = '/dashboard';
                } else {
                    const error = await response.json();
                    document.getElementById('error').textContent = error.detail;
                }
            } catch (error) {
                document.getElementById('error').textContent = 'Connection error';
            }
        };
    </script>
</body>
</html>
"""

# Улучшенный дашборд
dashboard_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Crypto Trading Bot Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #1a1a1a;
            color: #fff;
        }
        .header {
            background: #2a2a2a;
            padding: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .card {
            background: #2a2a2a;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.3);
        }
        .metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        .metric-value {
            font-size: 24px;
            font-weight: bold;
        }
        .profit { color: #4caf50; }
        .loss { color: #f44336; }
        .btn {
            background: #4CAF50;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            margin: 5px;
        }
        .btn:hover {
            background: #45a049;
        }
        .btn-danger {
            background: #f44336;
        }
        .btn-danger:hover {
            background: #da190b;
        }
        .status {
            display: inline-block;
            padding: 5px 10px;
            border-radius: 5px;
            font-size: 12px;
        }
        .status-active {
            background: #4caf50;
        }
        .status-inactive {
            background: #f44336;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #444;
        }
        th {
            background-color: #333;
        }
        .pair-selector {
            margin: 20px 0;
        }
        .pair-checkbox {
            margin: 5px 10px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 Crypto Trading Bot</h1>
        <div>
            <span id="connection-status" class="status status-inactive">Disconnected</span>
            <button onclick="logout()" class="btn btn-danger">Logout</button>
        </div>
    </div>
    
    <div class="container">
        <!-- Метрики -->
        <div class="grid">
            <div class="card">
                <h3>💰 Total Balance</h3>
                <div class="metric">
                    <span>USDT:</span>
                    <span class="metric-value" id="balance">$0.00</span>
                </div>
            </div>
            
            <div class="card">
                <h3>📈 Daily P&L</h3>
                <div class="metric">
                    <span>Today:</span>
                    <span class="metric-value" id="daily-pnl">$0.00</span>
                </div>
            </div>
            
            <div class="card">
                <h3>📊 Active Positions</h3>
                <div class="metric">
                    <span>Open:</span>
                    <span class="metric-value" id="open-positions">0</span>
                </div>
            </div>
            
            <div class="card">
                <h3>🎯 Win Rate</h3>
                <div class="metric">
                    <span>24h:</span>
                    <span class="metric-value" id="win-rate">0%</span>
                </div>
            </div>
        </div>
        
        <!-- Управление -->
        <div class="card">
            <h3>🎮 Bot Control</h3>
            <button id="start-bot" class="btn" onclick="controlBot('start')">▶️ Start Bot</button>
            <button id="stop-bot" class="btn btn-danger" onclick="controlBot('stop')">⏹️ Stop Bot</button>
            <button class="btn" onclick="runBacktest()">📊 Run Backtest</button>
            <button class="btn" onclick="showSettings()">⚙️ Settings</button>
        </div>
        
        <!-- Выбор валютных пар -->
        <div class="card">
            <h3>💱 Trading Pairs</h3>
            <div class="pair-selector">
                <label class="pair-checkbox">
                    <input type="checkbox" value="BTCUSDT" onchange="updatePairs(this)"> BTC/USDT
                </label>
                <label class="pair-checkbox">
                    <input type="checkbox" value="ETHUSDT" onchange="updatePairs(this)"> ETH/USDT
                </label>
                <label class="pair-checkbox">
                    <input type="checkbox" value="BNBUSDT" onchange="updatePairs(this)"> BNB/USDT
                </label>
                <label class="pair-checkbox">
                    <input type="checkbox" value="SOLUSDT" onchange="updatePairs(this)"> SOL/USDT
                </label>
                <label class="pair-checkbox">
                    <input type="checkbox" value="ADAUSDT" onchange="updatePairs(this)"> ADA/USDT
                </label>
            </div>
        </div>
        
        <!-- График -->
        <div class="card">
            <h3>📈 Performance Chart</h3>
            <canvas id="performance-chart" height="100"></canvas>
        </div>
        
        <!-- Таблица сделок -->
        <div class="card">
            <h3>📜 Recent Trades</h3>
            <table id="trades-table">
                <thead>
                    <tr>
                        <th>Time</th>
                        <th>Pair</th>
                        <th>Side</th>
                        <th>Entry</th>
                        <th>Exit</th>
                        <th>Profit</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody id="trades-tbody">
                </tbody>
            </table>
        </div>
    </div>
    
    <script>
        let ws = null;
        let chart = null;
        const token = localStorage.getItem('access_token');
        
        if (!token) {
            window.location.href = '/';
        }
        
        // WebSocket подключение
        function connectWebSocket() {
            ws = new WebSocket(`ws://${window.location.host}/ws?token=${token}`);
            
            ws.onopen = () => {
                document.getElementById('connection-status').textContent = 'Connected';
                document.getElementById('connection-status').className = 'status status-active';
            };
            
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                updateDashboard(data);
            };
            
            ws.onclose = () => {
                document.getElementById('connection-status').textContent = 'Disconnected';
                document.getElementById('connection-status').className = 'status status-inactive';
                setTimeout(connectWebSocket, 5000);
            };
        }
        
        connectWebSocket();
        
        // Обновление дашборда
        function updateDashboard(data) {
            document.getElementById('balance').textContent = `$${data.balance.toFixed(2)}`;
            document.getElementById('daily-pnl').textContent = `$${data.daily_pnl.toFixed(2)}`;
            document.getElementById('daily-pnl').className = data.daily_pnl >= 0 ? 'metric-value profit' : 'metric-value loss';
            document.getElementById('open-positions').textContent = data.open_positions;
            document.getElementById('win-rate').textContent = `${data.win_rate.toFixed(1)}%`;
            
            updateTradesTable(data.recent_trades);
            updateChart(data.chart_data);
        }
        
        // Управление ботом
        async function controlBot(action) {
            const response = await fetch(`/api/bot/${action}`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (response.ok) {
                alert(`Bot ${action}ed successfully`);
            }
        }
        
        // Обновление торговых пар
        async function updatePairs(checkbox) {
            const pairs = Array.from(document.querySelectorAll('.pair-checkbox input:checked'))
                .map(cb => cb.value);
            
            const response = await fetch('/api/pairs', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ pairs })
            });
        }
        
        // Выход
        function logout() {
            localStorage.removeItem('access_token');
            window.location.href = '/';
        }
        
        // Инициализация графика
        const ctx = document.getElementById('performance-chart').getContext('2d');
        chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Portfolio Value',
                    data: [],
                    borderColor: '#4caf50',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false
            }
        });
        
        function updateChart(data) {
            if (data && chart) {
                chart.data.labels = data.labels;
                chart.data.datasets[0].data = data.values;
                chart.update();
            }
        }
        
        function updateTradesTable(trades) {
            const tbody = document.getElementById('trades-tbody');
            tbody.innerHTML = '';
            
            trades.forEach(trade => {
                const row = tbody.insertRow();
                row.insertCell(0).textContent = new Date(trade.created_at).toLocaleString();
                row.insertCell(1).textContent = trade.symbol;
                row.insertCell(2).textContent = trade.side;
                row.insertCell(3).textContent = `$${trade.entry_price.toFixed(2)}`;
                row.insertCell(4).textContent = trade.exit_price ? `$${trade.exit_price.toFixed(2)}` : '-';
                
                const profitCell = row.insertCell(5);
                if (trade.profit !== null) {
                    profitCell.textContent = `$${trade.profit.toFixed(2)}`;
                    profitCell.className = trade.profit >= 0 ? 'profit' : 'loss';
                } else {
                    profitCell.textContent = '-';
                }
                
                row.insertCell(6).textContent = trade.status;
            });
        }
    </script>
</body>
</html>
"""

# API endpoints
@app.get("/")
async def login_page():
    return HTMLResponse(login_html)

@app.get("/dashboard")
async def dashboard_page():
    return HTMLResponse(dashboard_html)

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = await auth_service.authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth_service.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str):
    # Проверяем токен
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            await websocket.close()
            return
    except:
        await websocket.close()
        return
    
    await websocket.accept()
    
    try:
        while True:
            # Получаем данные для дашборда
            data = await get_dashboard_data()
            await websocket.send_json(data)
            await asyncio.sleep(5)
            
    except Exception as e:
        print(f"WebSocket error: {e}")

async def get_dashboard_data():
    """Получение данных для дашборда"""
    db = SessionLocal()
    client = HumanizedBybitClient()
    
    # Баланс
    balance_data = await client.fetch_balance()
    usdt_balance = balance_data.get('USDT', {}).get('total', 0)
    
    # Статистика сделок
    total_trades = db.query(Trade).count()
    open_positions = db.query(Trade).filter(Trade.status == 'OPEN').count()
    
    # Дневная прибыль
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_trades = db.query(Trade).filter(
        Trade.status == 'CLOSED',
        Trade.closed_at >= today_start
    ).all()
    
    daily_pnl = sum(trade.profit or 0 for trade in today_trades)
    
    # Win rate
    profitable_trades = len([t for t in today_trades if t.profit and t.profit > 0])
    total_closed_today = len(today_trades)
    win_rate = (profitable_trades / total_closed_today * 100) if total_closed_today > 0 else 0
    
    # Последние сделки
    recent_trades = db.query(Trade).order_by(Trade.created_at.desc()).limit(10).all()
    
    # График производительности (последние 24 часа)
    # Здесь должна быть логика для построения графика
    
    db.close()
    
    return {
        'balance': usdt_balance,
        'daily_pnl': daily_pnl,
        'open_positions': open_positions,
        'total_trades': total_trades,
        'win_rate': win_rate,
        'recent_trades': [
            {
                'created_at': trade.created_at.isoformat(),
                'symbol': trade.symbol,
                'side': trade.side,
                'entry_price': trade.entry_price,
                'exit_price': trade.exit_price,
                'profit': trade.profit,
                'status': trade.status
            }
            for trade in recent_trades
        ],
        'chart_data': {
            'labels': [],  # Временные метки
            'values': []   # Значения портфеля
        }
    }

# API для управления ботом
@app.post("/api/bot/{action}")
async def control_bot(action: str, current_user: User = Depends(auth_service.get_current_user)):
    global bot_instance
    
    if action == "start":
        # Запуск бота
        bot_instance.start()
        return {"status": "started"}
    elif action == "stop":
        # Остановка бота
        bot_instance.stop()
        return {"status": "stopped"}
    else:
        raise HTTPException(status_code=400, detail="Invalid action")

@app.post("/api/pairs")
async def update_trading_pairs(
    pairs: Dict[str, List[str]], 
    current_user: User = Depends(auth_service.get_current_user)
):
    global trading_pairs
    trading_pairs = pairs.get('pairs', [])
    return {"status": "updated", "pairs": trading_pairs}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)