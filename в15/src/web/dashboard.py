"""
HTML дашборд
Путь: /var/www/www-root/data/www/systemetech.ru/src/web/dashboard.py
"""

def get_dashboard_html() -> str:
    """Возвращает HTML код дашборда"""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Crypto Trading Bot Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0a0e27;
            color: #fff;
            line-height: 1.6;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        header {
            background: rgba(255,255,255,0.05);
            padding: 20px 0;
            margin-bottom: 30px;
            border-radius: 10px;
        }
        
        .header-content {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0 30px;
        }
        
        h1 {
            font-size: 28px;
            background: linear-gradient(45deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .user-info {
            display: flex;
            align-items: center;
            gap: 20px;
        }
        
        .btn {
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            transition: transform 0.2s;
        }
        
        .btn:hover {
            transform: translateY(-2px);
        }
        
        .btn-danger {
            background: linear-gradient(45deg, #f093fb, #f5576c);
        }
        
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .card {
            background: rgba(255,255,255,0.05);
            border-radius: 10px;
            padding: 25px;
            border: 1px solid rgba(255,255,255,0.1);
            transition: transform 0.2s;
        }
        
        .card:hover {
            transform: translateY(-5px);
            border-color: rgba(102, 126, 234, 0.5);
        }
        
        .card h3 {
            font-size: 14px;
            color: #888;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .metric {
            font-size: 32px;
            font-weight: 700;
            margin-bottom: 5px;
        }
        
        .positive {
            color: #4ade80;
        }
        
        .negative {
            color: #f87171;
        }
        
        .status-badge {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
        }
        
        .status-running {
            background: rgba(74, 222, 128, 0.2);
            color: #4ade80;
        }
        
        .status-stopped {
            background: rgba(248, 113, 113, 0.2);
            color: #f87171;
        }
        
        .controls {
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }
        
        .table-container {
            background: rgba(255,255,255,0.05);
            border-radius: 10px;
            padding: 20px;
            overflow-x: auto;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
        }
        
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        
        th {
            font-weight: 600;
            color: #888;
            text-transform: uppercase;
            font-size: 12px;
            letter-spacing: 1px;
        }
        
        .pairs-selector {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
            gap: 10px;
            margin: 20px 0;
        }
        
        .pair-checkbox {
            display: flex;
            align-items: center;
            padding: 10px;
            background: rgba(255,255,255,0.05);
            border-radius: 5px;
            cursor: pointer;
        }
        
        .pair-checkbox:hover {
            background: rgba(255,255,255,0.1);
        }
        
        .pair-checkbox input {
            margin-right: 8px;
        }
        
        #connection-status {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: #f87171;
            display: inline-block;
            margin-right: 5px;
        }
        
        #connection-status.connected {
            background: #4ade80;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0% {
                box-shadow: 0 0 0 0 rgba(74, 222, 128, 0.7);
            }
            70% {
                box-shadow: 0 0 0 10px rgba(74, 222, 128, 0);
            }
            100% {
                box-shadow: 0 0 0 0 rgba(74, 222, 128, 0);
            }
        }
        
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.8);
        }
        
        .modal-content {
            background: #1a1f36;
            margin: 5% auto;
            padding: 30px;
            width: 90%;
            max-width: 500px;
            border-radius: 10px;
            position: relative;
        }
        
        .close {
            position: absolute;
            right: 20px;
            top: 20px;
            font-size: 28px;
            cursor: pointer;
            color: #888;
        }
        
        .close:hover {
            color: #fff;
        }
        
        .login-form {
            display: flex;
            flex-direction: column;
            gap: 15px;
        }
        
        .login-form input {
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            padding: 12px;
            border-radius: 5px;
            color: #fff;
            font-size: 16px;
        }
        
        .login-form input:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .chart-container {
            height: 400px;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="header-content">
                <h1>🤖 Crypto Trading Bot</h1>
                <div class="user-info">
                    <span id="connection-status"></span>
                    <span id="username">Not logged in</span>
                    <button class="btn" onclick="logout()">Logout</button>
                </div>
            </div>
        </header>
        
        <div class="grid">
            <div class="card">
                <h3>Bot Status</h3>
                <div id="bot-status" class="status-badge status-stopped">Stopped</div>
                <div class="controls">
                    <button id="start-btn" class="btn" onclick="startBot()">Start Bot</button>
                    <button id="stop-btn" class="btn btn-danger" onclick="stopBot()" style="display:none;">Stop Bot</button>
                </div>
            </div>
            
            <div class="card">
                <h3>Balance (USDT)</h3>
                <div id="balance" class="metric">$0.00</div>
                <small id="balance-change">+0.00%</small>
            </div>
            
            <div class="card">
                <h3>Daily P&L</h3>
                <div id="daily-pnl" class="metric">$0.00</div>
                <small id="pnl-percent">+0.00%</small>
            </div>
            
            <div class="card">
                <h3>Open Positions</h3>
                <div id="open-positions" class="metric">0</div>
                <small>Active trades</small>
            </div>
            
            <div class="card">
                <h3>Win Rate</h3>
                <div id="win-rate" class="metric">0%</div>
                <small id="total-trades">0 trades today</small>
            </div>
            
            <div class="card">
                <h3>Active Pairs</h3>
                <div id="active-pairs" class="metric">0</div>
                <small>Trading pairs</small>
            </div>
        </div>
        
        <div class="card">
            <h3>Trading Pairs</h3>
            <div class="pairs-selector" id="pairs-selector"></div>
            <button class="btn" onclick="updatePairs()">Update Pairs</button>
        </div>
        
        <div class="table-container">
            <h3>Recent Trades</h3>
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
        
        <div class="table-container" style="margin-top: 20px;">
            <h3>Recent Signals</h3>
            <table id="signals-table">
                <thead>
                    <tr>
                        <th>Time</th>
                        <th>Pair</th>
                        <th>Action</th>
                        <th>Confidence</th>
                        <th>Reason</th>
                    </tr>
                </thead>
                <tbody id="signals-tbody">
                </tbody>
            </table>
        </div>
    </div>
    
    <!-- Login Modal -->
    <div id="loginModal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="closeLoginModal()">&times;</span>
            <h2>Login</h2>
            <form class="login-form" onsubmit="login(event)">
                <input type="text" id="login-username" placeholder="Username" required>
                <input type="password" id="login-password" placeholder="Password" required>
                <button type="submit" class="btn">Login</button>
            </form>
        </div>
    </div>
    
    <script>
        let ws = null;
        let token = localStorage.getItem('token');
        const API_URL = window.location.origin;
        
        // Проверка авторизации при загрузке
        window.onload = async function() {
            if (!token) {
                showLoginModal();
            } else {
                await checkAuth();
                connectWebSocket();
                loadDashboardData();
            }
        };
        
        function showLoginModal() {
            document.getElementById('loginModal').style.display = 'block';
        }
        
        function closeLoginModal() {
            document.getElementById('loginModal').style.display = 'none';
        }
        
        async function login(event) {
            event.preventDefault();
            
            const username = document.getElementById('login-username').value;
            const password = document.getElementById('login-password').value;
            
            const formData = new FormData();
            formData.append('username', username);
            formData.append('password', password);
            
            try {
                const response = await fetch(`${API_URL}/auth/token`, {
                    method: 'POST',
                    body: formData
                });
                
                if (response.ok) {
                    const data = await response.json();
                    token = data.access_token;
                    localStorage.setItem('token', token);
                    closeLoginModal();
                    document.getElementById('username').textContent = username;
                    connectWebSocket();
                    loadDashboardData();
                } else {
                    alert('Login failed');
                }
            } catch (error) {
                alert('Connection error');
            }
        }
        
        async function checkAuth() {
            try {
                const response = await fetch(`${API_URL}/auth/me`, {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
                
                if (response.ok) {
                    const user = await response.json();
                    document.getElementById('username').textContent = user.username;
                } else {
                    showLoginModal();
                }
            } catch (error) {
                showLoginModal();
            }
        }
        
        function logout() {
            localStorage.removeItem('token');
            if (ws) ws.close();
            window.location.reload();
        }
        
        function connectWebSocket() {
            const wsUrl = `ws://${window.location.host}/ws/${generateClientId()}`;
            ws = new WebSocket(wsUrl);
            
            ws.onopen = () => {
                document.getElementById('connection-status').classList.add('connected');
            };
            
            ws.onclose = () => {
                document.getElementById('connection-status').classList.remove('connected');
                // Переподключение через 5 секунд
                setTimeout(connectWebSocket, 5000);
            };
            
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.type === 'update') {
                    updateDashboard(data.data);
                }
            };
        }
        
        function generateClientId() {
            return Math.random().toString(36).substr(2, 9);
        }
        
        async function loadDashboardData() {
            try {
                const response = await fetch(`${API_URL}/api/dashboard`, {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
                
                if (response.ok) {
                    const data = await response.json();
                    updateFromApiData(data);
                }
            } catch (error) {
                console.error('Error loading dashboard data:', error);
            }
            
            // Загружаем список пар
            loadTradingPairs();
        }
        
        async function loadTradingPairs() {
            try {
                const response = await fetch(`${API_URL}/api/pairs`, {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
                
                if (response.ok) {
                    const pairs = await response.json();
                    displayTradingPairs(pairs);
                }
            } catch (error) {
                console.error('Error loading pairs:', error);
            }
        }
        
        function displayTradingPairs(pairs) {
            const container = document.getElementById('pairs-selector');
            container.innerHTML = '';
            
            const allPairs = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'ADAUSDT', 'XRPUSDT', 'DOTUSDT', 'DOGEUSDT'];
            
            allPairs.forEach(symbol => {
                const pairDiv = document.createElement('div');
                pairDiv.className = 'pair-checkbox';
                
                const isActive = pairs.some(p => p.symbol === symbol && p.is_active);
                
                pairDiv.innerHTML = `
                    <input type="checkbox" id="pair-${symbol}" value="${symbol}" ${isActive ? 'checked' : ''}>
                    <label for="pair-${symbol}">${symbol}</label>
                `;
                
                container.appendChild(pairDiv);
            });
        }
        
        function updateFromApiData(data) {
            const { bot_status, balance, statistics, recent_trades, recent_signals } = data;
            
            // Обновляем статус бота
            if (bot_status) {
                updateBotStatus(bot_status.is_running);
                document.getElementById('active-pairs').textContent = bot_status.active_pairs.length;
                document.getElementById('open-positions').textContent = bot_status.open_positions;
            }
            
            // Обновляем баланс
            if (balance && balance.USDT) {
                document.getElementById('balance').textContent = `$${balance.USDT.total.toFixed(2)}`;
            }
            
            // Обновляем статистику
            if (statistics) {
                document.getElementById('daily-pnl').textContent = `$${statistics.total_profit.toFixed(2)}`;
                document.getElementById('daily-pnl').className = statistics.total_profit >= 0 ? 'metric positive' : 'metric negative';
                
                const pnlPercent = statistics.total_profit / (balance?.USDT?.total || 1000) * 100;
                document.getElementById('pnl-percent').textContent = `${pnlPercent >= 0 ? '+' : ''}${pnlPercent.toFixed(2)}%`;
                
                document.getElementById('win-rate').textContent = `${statistics.win_rate.toFixed(1)}%`;
                document.getElementById('total-trades').textContent = `${statistics.total_trades} trades today`;
            }
            
            // Обновляем таблицы
            if (recent_trades) updateTradesTable(recent_trades);
            if (recent_signals) updateSignalsTable(recent_signals);
        }
        
        function updateDashboard(data) {
            // Обновление от WebSocket
            if (data.bot_status) {
                updateBotStatus(data.bot_status.is_running);
            }
            
            if (data.balance) {
                document.getElementById('balance').textContent = `$${data.balance.total.toFixed(2)}`;
            }
            
            if (data.recent_trades) {
                updateTradesTable(data.recent_trades);
            }
            
            if (data.recent_signals) {
                updateSignalsTable(data.recent_signals);
            }
        }
        
        function updateBotStatus(isRunning) {
            const statusEl = document.getElementById('bot-status');
            const startBtn = document.getElementById('start-btn');
            const stopBtn = document.getElementById('stop-btn');
            
            if (isRunning) {
                statusEl.textContent = 'Running';
                statusEl.className = 'status-badge status-running';
                startBtn.style.display = 'none';
                stopBtn.style.display = 'block';
            } else {
                statusEl.textContent = 'Stopped';
                statusEl.className = 'status-badge status-stopped';
                startBtn.style.display = 'block';
                stopBtn.style.display = 'none';
            }
        }
        
        function updateTradesTable(trades) {
            const tbody = document.getElementById('trades-tbody');
            tbody.innerHTML = '';
            
            trades.slice(0, 10).forEach(trade => {
                const row = tbody.insertRow();
                row.insertCell(0).textContent = new Date(trade.created_at).toLocaleString();
                row.insertCell(1).textContent = trade.symbol;
                row.insertCell(2).textContent = trade.side;
                row.insertCell(3).textContent = `$${trade.entry_price.toFixed(2)}`;
                row.insertCell(4).textContent = trade.exit_price ? `$${trade.exit_price.toFixed(2)}` : '-';
                
                const profitCell = row.insertCell(5);
                if (trade.profit !== null) {
                    profitCell.textContent = `$${trade.profit.toFixed(2)}`;
                    profitCell.className = trade.profit >= 0 ? 'positive' : 'negative';
                } else {
                    profitCell.textContent = '-';
                }
                
                row.insertCell(6).textContent = trade.status;
            });
        }
        
        function updateSignalsTable(signals) {
            const tbody = document.getElementById('signals-tbody');
            tbody.innerHTML = '';
            
            signals.slice(0, 10).forEach(signal => {
                const row = tbody.insertRow();
                row.insertCell(0).textContent = new Date(signal.created_at).toLocaleString();
                row.insertCell(1).textContent = signal.symbol;
                row.insertCell(2).textContent = signal.action;
                row.insertCell(3).textContent = `${(signal.confidence * 100).toFixed(1)}%`;
                row.insertCell(4).textContent = signal.reason || '-';
            });
        }
        
        async function startBot() {
            try {
                const response = await fetch(`${API_URL}/api/bot/start`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
                
                if (response.ok) {
                    alert('Bot started successfully');
                    loadDashboardData();
                } else {
                    const error = await response.json();
                    alert(`Failed to start bot: ${error.detail}`);
                }
            } catch (error) {
                alert('Connection error');
            }
        }
        
        async function stopBot() {
            try {
                const response = await fetch(`${API_URL}/api/bot/stop`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
                
                if (response.ok) {
                    alert('Bot stopped successfully');
                    loadDashboardData();
                } else {
                    const error = await response.json();
                    alert(`Failed to stop bot: ${error.detail}`);
                }
            } catch (error) {
                alert('Connection error');
            }
        }
        
        async function updatePairs() {
            const checkboxes = document.querySelectorAll('#pairs-selector input[type="checkbox"]:checked');
            const pairs = Array.from(checkboxes).map(cb => cb.value);
            
            if (pairs.length === 0) {
                alert('Please select at least one trading pair');
                return;
            }
            
            try {
                const response = await fetch(`${API_URL}/api/pairs`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(pairs)
                });
                
                if (response.ok) {
                    alert('Trading pairs updated successfully');
                    loadDashboardData();
                } else {
                    const error = await response.json();
                    alert(`Failed to update pairs: ${error.detail}`);
                }
            } catch (error) {
                alert('Connection error');
            }
        }
        
        // Обновление данных каждые 30 секунд
        setInterval(loadDashboardData, 30000);
    </script>
</body>
</html>
    """
    
def get_dashboard_html() -> str:
    """Возвращает HTML код дашборда"""
    return """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Crypto Trading Bot Dashboard</title>
    <!-- Стили остаются те же... -->
</head>
<body>
    <!-- HTML остается тот же до скриптов... -->
    
    <script>
        let ws = null;
        let token = localStorage.getItem('token');
        const API_URL = window.location.origin;
        
        // ✅ ИСПРАВЛЕНИЕ: Правильная функция логина
        async function login(event) {
            event.preventDefault();
            
            const username = document.getElementById('login-username').value;
            const password = document.getElementById('login-password').value;
            
            try {
                // ✅ ИСПРАВЛЕНИЕ: Используем правильный endpoint и JSON
                const response = await fetch(`${API_URL}/api/login`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'  // ✅ JSON, не FormData
                    },
                    body: JSON.stringify({
                        username: username,
                        password: password
                    })
                });
                
                if (response.ok) {
                    const data = await response.json();
                    token = data.access_token;
                    localStorage.setItem('token', token);
                    closeLoginModal();
                    document.getElementById('username').textContent = username;
                    connectWebSocket();
                    loadDashboardData();
                } else {
                    const errorData = await response.json();
                    alert(`Login failed: ${errorData.detail || 'Unknown error'}`);
                }
            } catch (error) {
                console.error('Login error:', error);
                alert('Connection error');
            }
        }
        
        // ✅ ИСПРАВЛЕНИЕ: Функция проверки авторизации
        async function checkAuth() {
            try {
                // ✅ Используем правильный endpoint для проверки пользователя
                const response = await fetch(`${API_URL}/api/user/me`, {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
                
                if (response.ok) {
                    const user = await response.json();
                    document.getElementById('username').textContent = user.username;
                } else {
                    showLoginModal();
                }
            } catch (error) {
                console.error('Auth check error:', error);
                showLoginModal();
            }
        }
        
        // Остальной JavaScript остается тот же...
    </script>
</body>
</html>
    """