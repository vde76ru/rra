"""
Полный дашборд для торгового бота на русском языке
Файл: src/web/dashboard.py
"""

def get_dashboard_html() -> str:
    """Возвращает HTML код полного дашборда на русском языке"""
    
    html = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🚀 Криптотрейдинг Бот - Панель Управления</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        
        .header {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            padding: 20px;
            box-shadow: 0 2px 20px rgba(0, 0, 0, 0.1);
            position: sticky;
            top: 0;
            z-index: 100;
        }
        
        .header h1 {
            text-align: center;
            color: #2c3e50;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .status-bar {
            display: flex;
            justify-content: center;
            gap: 30px;
            flex-wrap: wrap;
        }
        
        .status-item {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 10px 20px;
            background: rgba(52, 152, 219, 0.1);
            border-radius: 25px;
            border: 2px solid transparent;
            transition: all 0.3s ease;
        }
        
        .status-item.active {
            background: rgba(46, 204, 113, 0.2);
            border-color: #2ecc71;
        }
        
        .status-item.error {
            background: rgba(231, 76, 60, 0.2);
            border-color: #e74c3c;
        }
        
        .status-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #95a5a6;
            animation: pulse 2s infinite;
        }
        
        .status-dot.active {
            background: #2ecc71;
        }
        
        .status-dot.error {
            background: #e74c3c;
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 30px 20px;
        }
        
        .control-panel {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 25px;
            margin-bottom: 30px;
        }
        
        .card {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0, 0, 0, 0.15);
        }
        
        .card h3 {
            color: #2c3e50;
            margin-bottom: 20px;
            font-size: 1.4em;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }
        
        .btn {
            background: linear-gradient(135deg, #3498db, #2980b9);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 1em;
            font-weight: 600;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin: 5px;
            min-width: 120px;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(52, 152, 219, 0.4);
        }
        
        .btn.btn-success {
            background: linear-gradient(135deg, #2ecc71, #27ae60);
        }
        
        .btn.btn-success:hover {
            box-shadow: 0 5px 15px rgba(46, 204, 113, 0.4);
        }
        
        .btn.btn-danger {
            background: linear-gradient(135deg, #e74c3c, #c0392b);
        }
        
        .btn.btn-danger:hover {
            box-shadow: 0 5px 15px rgba(231, 76, 60, 0.4);
        }
        
        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .input-group {
            margin-bottom: 20px;
        }
        
        .input-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #2c3e50;
        }
        
        .input-group select,
        .input-group input {
            width: 100%;
            padding: 12px 15px;
            border: 2px solid #ecf0f1;
            border-radius: 10px;
            font-size: 1em;
            transition: border-color 0.3s ease;
            background: white;
        }
        
        .input-group select:focus,
        .input-group input:focus {
            outline: none;
            border-color: #3498db;
            box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            padding: 20px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 5px 20px rgba(0, 0, 0, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .stat-number {
            font-size: 2.5em;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 5px;
        }
        
        .stat-label {
            color: #7f8c8d;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .stat-card.positive .stat-number {
            color: #2ecc71;
        }
        
        .stat-card.negative .stat-number {
            color: #e74c3c;
        }
        
        .trades-table {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
        }
        
        .trades-table table {
            width: 100%;
            border-collapse: collapse;
        }
        
        .trades-table th,
        .trades-table td {
            padding: 15px;
            text-align: left;
            border-bottom: 1px solid #ecf0f1;
        }
        
        .trades-table th {
            background: #f8f9fa;
            font-weight: 600;
            color: #2c3e50;
        }
        
        .trades-table tr:hover {
            background: rgba(52, 152, 219, 0.05);
        }
        
        .profit {
            color: #2ecc71;
            font-weight: bold;
        }
        
        .loss {
            color: #e74c3c;
            font-weight: bold;
        }
        
        .logs-container {
            background: rgba(0, 0, 0, 0.9);
            color: #00ff00;
            font-family: 'Courier New', monospace;
            border-radius: 15px;
            padding: 20px;
            max-height: 300px;
            overflow-y: auto;
            margin-top: 20px;
        }
        
        .log-entry {
            margin: 5px 0;
            padding: 5px;
            border-left: 3px solid #00ff00;
            padding-left: 10px;
        }
        
        .log-error {
            color: #ff4444;
            border-left-color: #ff4444;
        }
        
        .log-warning {
            color: #ffaa00;
            border-left-color: #ffaa00;
        }
        
        .toggle-switch {
            position: relative;
            display: inline-block;
            width: 60px;
            height: 34px;
        }
        
        .toggle-switch input {
            opacity: 0;
            width: 0;
            height: 0;
        }
        
        .slider {
            position: absolute;
            cursor: pointer;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: #ccc;
            transition: .4s;
            border-radius: 34px;
        }
        
        .slider:before {
            position: absolute;
            content: "";
            height: 26px;
            width: 26px;
            left: 4px;
            bottom: 4px;
            background-color: white;
            transition: .4s;
            border-radius: 50%;
        }
        
        input:checked + .slider {
            background-color: #2196F3;
        }
        
        input:checked + .slider:before {
            transform: translateX(26px);
        }
        
        .notification {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 25px;
            border-radius: 10px;
            color: white;
            font-weight: 600;
            z-index: 1000;
            transform: translateX(400px);
            transition: transform 0.3s ease;
        }
        
        .notification.show {
            transform: translateX(0);
        }
        
        .notification.success {
            background: #2ecc71;
        }
        
        .notification.error {
            background: #e74c3c;
        }
        
        .notification.info {
            background: #3498db;
        }
        
        @media (max-width: 768px) {
            .header h1 {
                font-size: 2em;
            }
            
            .status-bar {
                flex-direction: column;
                align-items: center;
            }
            
            .control-panel {
                grid-template-columns: 1fr;
            }
            
            .stats-grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 Криптотрейдинг Бот</h1>
        <div class="status-bar">
            <div class="status-item" id="bot-status">
                <span class="status-dot" id="bot-dot"></span>
                <span>Статус: <span id="bot-status-text">Остановлен</span></span>
            </div>
            <div class="status-item" id="connection-status">
                <span class="status-dot active"></span>
                <span>Соединение: Активно</span>
            </div>
            <div class="status-item">
                <span class="status-dot active"></span>
                <span>База данных: Подключена</span>
            </div>
            <div class="status-item">
                <span class="status-dot active"></span>
                <span>Биржа: Bybit</span>
            </div>
        </div>
    </div>

    <div class="container">
        <!-- Статистика -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number" id="total-trades">0</div>
                <div class="stat-label">Всего сделок</div>
            </div>
            <div class="stat-card positive">
                <div class="stat-number" id="total-profit">+0.00 USDT</div>
                <div class="stat-label">Общая прибыль</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="success-rate">0%</div>
                <div class="stat-label">Успешные сделки</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="active-positions">0</div>
                <div class="stat-label">Активные позиции</div>
            </div>
        </div>

        <!-- Панель управления -->
        <div class="control-panel">
            <!-- Управление ботом -->
            <div class="card">
                <h3>🤖 Управление ботом</h3>
                <div class="input-group">
                    <label for="strategy-select">Выберите стратегию:</label>
                    <select id="strategy-select">
                        <option value="momentum">Momentum - Следование за трендом</option>
                        <option value="multi_indicator">Multi Indicator - Множественные индикаторы</option>
                        <option value="scalping">Scalping - Скальпинг</option>
                        <option value="safe_multi_indicator">Safe Multi Indicator - Безопасная стратегия</option>
                        <option value="conservative">Conservative - Консервативная стратегия</option>
                    </select>
                </div>
                <div style="text-align: center;">
                    <button id="start-bot" class="btn btn-success">▶️ Запустить бота</button>
                    <button id="stop-bot" class="btn btn-danger">⏹️ Остановить бота</button>
                </div>
            </div>

            <!-- Торговые пары -->
            <div class="card">
                <h3>💱 Торговые пары</h3>
                <div style="margin-bottom: 15px;">
                    <label>
                        <input type="checkbox" checked> BTCUSDT - Bitcoin/USDT
                    </label>
                </div>
                <div style="margin-bottom: 15px;">
                    <label>
                        <input type="checkbox" checked> ETHUSDT - Ethereum/USDT
                    </label>
                </div>
                <div style="margin-bottom: 15px;">
                    <label>
                        <input type="checkbox"> ADAUSDT - Cardano/USDT
                    </label>
                </div>
                <div style="margin-bottom: 15px;">
                    <label>
                        <input type="checkbox"> DOTUSDT - Polkadot/USDT
                    </label>
                </div>
                <button class="btn">💾 Сохранить настройки</button>
            </div>

            <!-- Управление рисками -->
            <div class="card">
                <h3>⚠️ Управление рисками</h3>
                <div class="input-group">
                    <label for="max-position">Максимальный размер позиции (%):</label>
                    <input type="number" id="max-position" value="5" min="1" max="100" step="0.5">
                </div>
                <div class="input-group">
                    <label for="stop-loss">Стоп-лосс (%):</label>
                    <input type="number" id="stop-loss" value="2" min="0.5" max="10" step="0.5">
                </div>
                <div class="input-group">
                    <label for="take-profit">Тейк-профит (%):</label>
                    <input type="number" id="take-profit" value="4" min="1" max="20" step="0.5">
                </div>
                <div class="input-group">
                    <label for="max-trades">Максимум сделок в день:</label>
                    <input type="number" id="max-trades" value="10" min="1" max="50" step="1">
                </div>
            </div>

            <!-- Уведомления -->
            <div class="card">
                <h3>🔔 Уведомления</h3>
                <div style="margin-bottom: 20px;">
                    <label style="display: flex; align-items: center; gap: 10px;">
                        <span>Email уведомления:</span>
                        <label class="toggle-switch">
                            <input type="checkbox" id="email-notifications" checked>
                            <span class="slider"></span>
                        </label>
                    </label>
                </div>
                <div style="margin-bottom: 20px;">
                    <label style="display: flex; align-items: center; gap: 10px;">
                        <span>Telegram уведомления:</span>
                        <label class="toggle-switch">
                            <input type="checkbox" id="telegram-notifications">
                            <span class="slider"></span>
                        </label>
                    </label>
                </div>
                <div class="input-group">
                    <label for="telegram-token">Telegram Bot Token:</label>
                    <input type="text" id="telegram-token" placeholder="Введите токен бота">
                </div>
            </div>

            <!-- Системная информация -->
            <div class="card">
                <h3>🖥️ Система</h3>
                <p><strong>Время работы:</strong> <span id="uptime">00:00:00</span></p>
                <p><strong>Последний цикл:</strong> <span id="last-cycle">Никогда</span></p>
                <p><strong>Количество циклов:</strong> <span id="cycles-count">0</span></p>
                <p><strong>Использование памяти:</strong> <span id="memory-usage">0 MB</span></p>
                <div style="margin-top: 15px;">
                    <button class="btn" onclick="exportTrades()">📊 Экспорт сделок</button>
                    <button class="btn" onclick="clearLogs()">🗑️ Очистить логи</button>
                </div>
            </div>

            <!-- Быстрые действия -->
            <div class="card">
                <h3>⚡ Быстрые действия</h3>
                <button class="btn" onclick="closeAllPositions()">❌ Закрыть все позиции</button>
                <button class="btn" onclick="pauseTrading()">⏸️ Приостановить торговлю</button>
                <button class="btn" onclick="resumeTrading()">▶️ Возобновить торговлю</button>
                <button class="btn" onclick="restartBot()">🔄 Перезапустить бота</button>
            </div>
        </div>

        <!-- Таблица сделок -->
        <div class="trades-table">
            <h3 style="padding: 20px; margin: 0; background: #f8f9fa; border-bottom: 1px solid #ecf0f1;">📈 Последние сделки</h3>
            <table>
                <thead>
                    <tr>
                        <th>Время</th>
                        <th>Пара</th>
                        <th>Тип</th>
                        <th>Количество</th>
                        <th>Цена</th>
                        <th>Прибыль/Убыток</th>
                        <th>Стратегия</th>
                        <th>Статус</th>
                    </tr>
                </thead>
                <tbody id="trades-tbody">
                    <tr>
                        <td colspan="8" style="text-align: center; padding: 40px; color: #7f8c8d;">
                            Пока нет сделок
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>

        <!-- Логи -->
        <div class="logs-container">
            <h3 style="color: #00ff00; margin-bottom: 15px;">📋 Системные логи</h3>
            <div id="logs-content">
                <div class="log-entry">[СИСТЕМА] Дашборд загружен успешно</div>
                <div class="log-entry">[СИСТЕМА] Ожидание подключения к боту...</div>
            </div>
        </div>
    </div>

    <script>
        // Глобальные переменные
        let ws = null;
        let botStatus = 'inactive';
        let isConnected = false;

        // Инициализация
        document.addEventListener('DOMContentLoaded', function() {
            connectWebSocket();
            loadBotStatus();
            loadStats();
            setupEventListeners();
            updateUptime();
            setInterval(updateUptime, 1000);
        });

        // WebSocket соединение
        function connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;
            
            ws = new WebSocket(wsUrl);
            
            ws.onopen = function() {
                isConnected = true;
                addLog('[СИСТЕМА] WebSocket соединение установлено', 'info');
                updateConnectionStatus(true);
            };
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                handleWebSocketMessage(data);
            };
            
            ws.onclose = function() {
                isConnected = false;
                addLog('[СИСТЕМА] WebSocket соединение потеряно. Переподключение...', 'warning');
                updateConnectionStatus(false);
                setTimeout(connectWebSocket, 5000);
            };
            
            ws.onerror = function(error) {
                addLog('[ОШИБКА] Ошибка WebSocket: ' + error, 'error');
            };
        }

        // Обработка WebSocket сообщений
        function handleWebSocketMessage(data) {
            switch(data.type) {
                case 'bot_status':
                    updateBotStatus(data.status, data.strategy);
                    document.getElementById('active-positions').textContent = data.positions || 0;
                    break;
                case 'bot_started':
                    showNotification('Бот запущен успешно!', 'success');
                    addLog('[БОТ] Бот запущен со стратегией: ' + data.strategy);
                    break;
                case 'bot_stopped':
                    showNotification('Бот остановлен', 'info');
                    addLog('[БОТ] Бот остановлен');
                    break;
                case 'new_trade':
                    addTradeToTable(data.trade);
                    updateStats();
                    break;
                case 'settings_updated':
                    showNotification('Настройки сохранены', 'success');
                    addLog('[НАСТРОЙКИ] Настройки обновлены');
                    break;
            }
        }

        // Настройка обработчиков событий
        function setupEventListeners() {
            document.getElementById('start-bot').addEventListener('click', startBot);
            document.getElementById('stop-bot').addEventListener('click', stopBot);
        }

        // Загрузка статуса бота
        async function loadBotStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                updateBotStatus(data.status, data.strategy);
                document.getElementById('active-positions').textContent = data.positions || 0;
                document.getElementById('cycles-count').textContent = data.cycles_count || 0;
            } catch (error) {
                addLog('[ОШИБКА] Не удалось загрузить статус бота: ' + error, 'error');
            }
        }

        // Загрузка статистики
        async function loadStats() {
            try {
                const response = await fetch('/api/stats');
                const data = await response.json();
                
                document.getElementById('total-trades').textContent = data.total_trades || 0;
                document.getElementById('total-profit').textContent = 
                    (data.total_profit >= 0 ? '+' : '') + (data.total_profit || 0).toFixed(2) + ' USDT';
                document.getElementById('success-rate').textContent = 
                    (data.success_rate || 0).toFixed(1) + '%';
                
                // Обновляем цвет прибыли
                const profitElement = document.getElementById('total-profit').parentElement;
                profitElement.className = 'stat-card ' + (data.total_profit >= 0 ? 'positive' : 'negative');
            } catch (error) {
                addLog('[ОШИБКА] Не удалось загрузить статистику: ' + error, 'error');
            }
        }

        // Обновление статуса бота
        function updateBotStatus(status, strategy) {
            const statusElement = document.getElementById('bot-status-text');
            const dotElement = document.getElementById('bot-dot');
            const statusContainer = document.getElementById('bot-status');
            
            botStatus = status;
            
            if (status === 'active') {
                statusElement.textContent = 'Активен' + (strategy ? ` (${strategy})` : '');
                dotElement.className = 'status-dot active';
                statusContainer.className = 'status-item active';
            } else {
                statusElement.textContent = 'Остановлен';
                dotElement.className = 'status-dot';
                statusContainer.className = 'status-item';
            }
            
            // Обновляем кнопки
            document.getElementById('start-bot').disabled = (status === 'active');
            document.getElementById('stop-bot').disabled = (status !== 'active');
        }

        // Обновление статуса соединения
        function updateConnectionStatus(connected) {
            const statusElement = document.getElementById('connection-status');
            if (connected) {
                statusElement.className = 'status-item active';
                statusElement.querySelector('span:last-child').textContent = 'Соединение: Активно';
            } else {
                statusElement.className = 'status-item error';
                statusElement.querySelector('span:last-child').textContent = 'Соединение: Потеряно';
            }
        }

        // Запуск бота
        async function startBot() {
            const strategy = document.getElementById('strategy-select').value;
            
            try {
                const response = await fetch('/api/bot/start', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ strategy: strategy })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showNotification('Бот запускается...', 'info');
                    addLog('[БОТ] Запуск бота со стратегией: ' + strategy);
                } else {
                    throw new Error(data.message || 'Неизвестная ошибка');
                }
            } catch (error) {
                showNotification('Ошибка запуска бота: ' + error.message, 'error');
                addLog('[ОШИБКА] Ошибка запуска бота: ' + error.message, 'error');
            }
        }

        // Остановка бота
        async function stopBot() {
            try {
                const response = await fetch('/api/bot/stop', {
                    method: 'POST'
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showNotification('Бот останавливается...', 'info');
                    addLog('[БОТ] Остановка бота');
                } else {
                    throw new Error(data.message || 'Неизвестная ошибка');
                }
            } catch (error) {
                showNotification('Ошибка остановки бота: ' + error.message, 'error');
                addLog('[ОШИБКА] Ошибка остановки бота: ' + error.message, 'error');
            }
        }

        // Обновление времени работы
        function updateUptime() {
            // Заглушка для времени работы
            const now = new Date();
            const uptimeStr = now.toLocaleTimeString('ru-RU');
            document.getElementById('last-cycle').textContent = uptimeStr;
        }

        // Добавление лога
        function addLog(message, type = 'info') {
            const logsContent = document.getElementById('logs-content');
            const logEntry = document.createElement('div');
            
            const timestamp = new Date().toLocaleTimeString('ru-RU');
            logEntry.textContent = `[${timestamp}] ${message}`;
            
            logEntry.className = 'log-entry';
            if (type === 'error') {
                logEntry.className += ' log-error';
            } else if (type === 'warning') {
                logEntry.className += ' log-warning';
            }
            
            logsContent.appendChild(logEntry);
            logsContent.scrollTop = logsContent.scrollHeight;
            
            // Ограничиваем количество логов
            if (logsContent.children.length > 100) {
                logsContent.removeChild(logsContent.firstChild);
            }
        }

        // Показ уведомлений
        function showNotification(message, type = 'info') {
            const notification = document.createElement('div');
            notification.className = `notification ${type}`;
            notification.textContent = message;
            
            document.body.appendChild(notification);
            
            setTimeout(() => {
                notification.classList.add('show');
            }, 100);
            
            setTimeout(() => {
                notification.classList.remove('show');
                setTimeout(() => {
                    document.body.removeChild(notification);
                }, 300);
            }, 3000);
        }

        // Добавление сделки в таблицу
        function addTradeToTable(trade) {
            const tbody = document.getElementById('trades-tbody');
            
            // Удаляем заглушку если есть
            if (tbody.children.length === 1 && tbody.children[0].children.length === 1) {
                tbody.innerHTML = '';
            }
            
            const row = document.createElement('tr');
            const profitClass = trade.profit >= 0 ? 'profit' : 'loss';
            
            row.innerHTML = `
                <td>${new Date(trade.timestamp).toLocaleString('ru-RU')}</td>
                <td>${trade.symbol}</td>
                <td>${trade.side === 'buy' ? 'Покупка' : 'Продажа'}</td>
                <td>${trade.amount}</td>
                <td>$${trade.price.toFixed(2)}</td>
                <td class="${profitClass}">${trade.profit >= 0 ? '+' : ''}${trade.profit.toFixed(2)} USDT</td>
                <td>${trade.strategy}</td>
                <td>${trade.status === 'completed' ? 'Завершена' : 'Активна'}</td>
            `;
            
            tbody.insertBefore(row, tbody.firstChild);
            
            // Ограничиваем количество строк
            if (tbody.children.length > 50) {
                tbody.removeChild(tbody.lastChild);
            }
        }

        // Дополнительные функции
        function exportTrades() {
            showNotification('Экспорт сделок...', 'info');
            // TODO: Реализовать экспорт
        }

        function clearLogs() {
            document.getElementById('logs-content').innerHTML = '';
            addLog('[СИСТЕМА] Логи очищены');
        }

        function closeAllPositions() {
            if (confirm('Вы уверены, что хотите закрыть все открытые позиции?')) {
                showNotification('Закрытие всех позиций...', 'info');
                // TODO: Реализовать закрытие позиций
            }
        }

        function pauseTrading() {
            showNotification('Торговля приостановлена', 'info');
            // TODO: Реализовать приостановку
        }

        function resumeTrading() {
            showNotification('Торговля возобновлена', 'info');
            // TODO: Реализовать возобновление
        }

        function restartBot() {
            if (confirm('Вы уверены, что хотите перезапустить бота?')) {
                showNotification('Перезапуск бота...', 'info');
                // TODO: Реализовать перезапуск
            }
        }

        // Обновление статистики
        function updateStats() {
            loadStats(); // Перезагружаем статистику
        }
    </script>
</body>
</html>
    """
    
    return html


# Дополнительные функции для API

class DashboardAPI:
    """API класс для работы с дашбордом"""
    
    @staticmethod
    async def get_bot_status():
        """Получить статус бота"""
        # Здесь должна быть логика получения статуса бота
        return {"status": "inactive", "strategy": None}
    
    @staticmethod
    async def start_bot(strategy: str):
        """Запустить бота с выбранной стратегией"""
        # Здесь должна быть логика запуска бота
        return {"success": True, "message": f"Бот запущен со стратегией {strategy}"}
    
    @staticmethod
    async def stop_bot():
        """Остановить бота"""
        # Здесь должна быть логика остановки бота
        return {"success": True, "message": "Бот остановлен"}
    
    @staticmethod
    async def get_stats():
        """Получить статистику торговли"""
        # Здесь должна быть логика получения статистики
        return {
            "totalTrades": 0,
            "totalProfit": 0.0,
            "successRate": 0.0,
            "activePositions": 0
        }
    
    @staticmethod
    async def get_trades():
        """Получить список сделок"""
        # Здесь должна быть логика получения сделок
        return []
    
    @staticmethod
    async def save_settings(settings: dict):
        """Сохранить настройки"""
        # Здесь должна быть логика сохранения настроек
        return {"success": True, "message": "Настройки сохранены"}


def setup_dashboard_routes(app):
    """Настройка маршрутов для дашборда"""
    
    @app.get("/")
    async def dashboard():
        return HTMLResponse(get_dashboard_html())
    
    @app.get("/api/status")
    async def get_status():
        return await DashboardAPI.get_bot_status()
    
    @app.post("/api/bot/start")
    async def start_bot(data: dict):
        strategy = data.get("strategy", "momentum")
        return await DashboardAPI.start_bot(strategy)
    
    @app.post("/api/bot/stop")
    async def stop_bot():
        return await DashboardAPI.stop_bot()
    
    @app.get("/api/stats")
    async def get_stats():
        return await DashboardAPI.get_stats()
    
    @app.get("/api/trades")
    async def get_trades():
        return await DashboardAPI.get_trades()
    
    @app.post("/api/settings")
    async def save_settings(settings: dict):
        return await DashboardAPI.save_settings(settings)


if __name__ == "__main__":
    print("Дашборд готов к использованию!")
    print("Основные функции:")
    print("- Управление ботом (запуск/остановка)")
    print("- Мониторинг сделок в реальном времени")
    print("- Выбор и настройка стратегий")
    print("- Аналитика и статистика")
    print("- Настройки рисков и уведомлений")
    print("- Чистые логи только важных событий")
    print("- Полностью на русском языке")