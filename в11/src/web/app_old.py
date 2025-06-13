from fastapi import FastAPI, WebSocket, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import json
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
import jwt
import os
import logging
from dotenv import load_dotenv

# ✅ ИСПРАВЛЕНИЕ: Импорты из проекта - используем единый менеджер
from src.core.database import SessionLocal, get_db
from src.core.models import Trade, User, BotState, TradingPair, Signal, TradeStatus, OrderSide
from src.core.unified_bot_manager import unified_bot_manager
from src.core.state_manager import state_manager
from src.web.auth import auth_service, ACCESS_TOKEN_EXPIRE_MINUTES, SECRET_KEY, ALGORITHM
from src.exchange.bybit_client import HumanizedBybitClient

load_dotenv()

# Настройка логирования
logger = logging.getLogger(__name__)

app = FastAPI(title="Crypto Trading Bot", version="3.0")

# CORS для API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Клиент для получения данных
exchange_client = HumanizedBybitClient()

# HTML страница входа
login_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Crypto Bot - Login</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
            color: #fff;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }
        .login-container {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.37);
            border: 1px solid rgba(255, 255, 255, 0.18);
            width: 100%;
            max-width: 400px;
        }
        h2 {
            text-align: center;
            margin-bottom: 30px;
            font-size: 28px;
            font-weight: 600;
        }
        .logo {
            text-align: center;
            font-size: 48px;
            margin-bottom: 20px;
        }
        input {
            width: 100%;
            padding: 15px;
            margin: 10px 0;
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 10px;
            color: #fff;
            font-size: 16px;
            transition: all 0.3s;
        }
        input:focus {
            outline: none;
            border-color: #4CAF50;
            background: rgba(255, 255, 255, 0.15);
        }
        input::placeholder {
            color: rgba(255, 255, 255, 0.6);
        }
        button {
            width: 100%;
            padding: 15px;
            margin-top: 20px;
            background: linear-gradient(45deg, #4CAF50, #45a049);
            color: white;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            font-size: 18px;
            font-weight: 600;
            transition: all 0.3s;
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(76, 175, 80, 0.4);
        }
        .error {
            color: #ff6b6b;
            text-align: center;
            margin-top: 15px;
            padding: 10px;
            background: rgba(255, 107, 107, 0.1);
            border-radius: 5px;
            display: none;
        }
        .loading {
            display: none;
            text-align: center;
            margin-top: 20px;
        }
        .spinner {
            border: 3px solid rgba(255, 255, 255, 0.3);
            border-top: 3px solid #4CAF50;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="logo">🤖</div>
        <h2>Crypto Trading Bot</h2>
        <form id="loginForm">
            <input type="text" id="username" placeholder="Username" required autocomplete="username">
            <input type="password" id="password" placeholder="Password" required autocomplete="current-password">
            <button type="submit">Login</button>
            <div id="error" class="error"></div>
            <div id="loading" class="loading">
                <div class="spinner"></div>
                <p>Logging in...</p>
            </div>
        </form>
    </div>
    
    <script>
        document.getElementById('loginForm').onsubmit = async (e) => {
            e.preventDefault();
            
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            const errorDiv = document.getElementById('error');
            const loadingDiv = document.getElementById('loading');
            const submitButton = e.target.querySelector('button');
            
            // Reset error
            errorDiv.style.display = 'none';
            errorDiv.textContent = '';
            
            // Show loading
            loadingDiv.style.display = 'block';
            submitButton.disabled = true;
            
            const formData = new FormData();
            formData.append('username', username);
            formData.append('password', password);
            
            try {
                const response = await fetch('/token', {
                    method: 'POST',
                    body: formData
                });
                
                if (response.ok) {
                    const data = await response.json();
                    localStorage.setItem('access_token', data.access_token);
                    localStorage.setItem('username', username);
                    window.location.href = '/dashboard';
                } else {
                    const error = await response.json();
                    errorDiv.textContent = error.detail || 'Login failed';
                    errorDiv.style.display = 'block';
                }
            } catch (error) {
                errorDiv.textContent = 'Connection error. Please try again.';
                errorDiv.style.display = 'block';
            } finally {
                loadingDiv.style.display = 'none';
                submitButton.disabled = false;
            }
        };
    </script>
</body>
</html>
"""

# ✅ ИСПРАВЛЕННЫЙ дашборд с индикаторами синхронизации
dashboard_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Crypto Trading Bot Dashboard</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/luxon@3.3.0/build/global/luxon.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-luxon@1.3.1/dist/chartjs-adapter-luxon.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: #0a0a0a;
            color: #e0e0e0;
            overflow-x: hidden;
        }
        .header {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            padding: 20px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.5);
            position: sticky;
            top: 0;
            z-index: 100;
        }
        .header h1 {
            font-size: 24px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .header-controls {
            display: flex;
            align-items: center;
            gap: 15px;
            flex-wrap: wrap;
        }
        .user-info {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 8px 16px;
            background: rgba(255,255,255,0.1);
            border-radius: 20px;
        }
        .container {
            max-width: 1600px;
            margin: 0 auto;
            padding: 20px;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .card {
            background: linear-gradient(135deg, #1e1e2e 0%, #252535 100%);
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            border: 1px solid rgba(255,255,255,0.05);
            transition: transform 0.3s, box-shadow 0.3s;
        }
        .card:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 30px rgba(0,0,0,0.4);
        }
        .card h3 {
            font-size: 14px;
            font-weight: 500;
            color: #888;
            margin-bottom: 15px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .metric-value {
            font-size: 28px;
            font-weight: 700;
        }
        .metric-change {
            font-size: 14px;
            margin-top: 5px;
            opacity: 0.8;
        }
        .profit { color: #4caf50; }
        .loss { color: #f44336; }
        .neutral { color: #ffc107; }
        .btn {
            background: linear-gradient(45deg, #4CAF50, #45a049);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-size: 12px;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(76, 175, 80, 0.4);
        }
        .btn:disabled {
            background: #444;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }
        .btn-danger {
            background: linear-gradient(45deg, #f44336, #d32f2f);
        }
        .btn-danger:hover {
            box-shadow: 0 5px 20px rgba(244, 67, 54, 0.4);
        }
        .btn-secondary {
            background: linear-gradient(45deg, #666, #555);
        }
        .status {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .status-active {
            background: rgba(76, 175, 80, 0.2);
            color: #4caf50;
        }
        .status-inactive {
            background: rgba(244, 67, 54, 0.2);
            color: #f44336;
        }
        .status-warning {
            background: rgba(255, 193, 7, 0.2);
            color: #ffc107;
        }
        .pulse {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        .pulse.active {
            background: #4caf50;
        }
        .pulse.inactive {
            background: #f44336;
        }
        .pulse.warning {
            background: #ffc107;
        }
        @keyframes pulse {
            0% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.5; transform: scale(1.1); }
            100% { opacity: 1; transform: scale(1); }
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            background: #1e1e2e;
            border-radius: 10px;
            overflow: hidden;
        }
        th, td {
            padding: 15px;
            text-align: left;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }
        th {
            background-color: #252535;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 12px;
            letter-spacing: 1px;
            color: #888;
        }
        tr:hover {
            background: rgba(255,255,255,0.02);
        }
        .pair-selector {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
            margin: 20px 0;
        }
        .pair-checkbox {
            display: flex;
            align-items: center;
            padding: 10px 15px;
            background: rgba(255,255,255,0.05);
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
        }
        .pair-checkbox:hover {
            background: rgba(255,255,255,0.1);
        }
        .pair-checkbox input[type="checkbox"] {
            margin-right: 8px;
            cursor: pointer;
        }
        .controls-section {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin: 20px 0;
        }
        .chart-container {
            position: relative;
            height: 400px;
            margin-top: 20px;
        }
        .positions-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        .position-card {
            background: rgba(255,255,255,0.05);
            padding: 20px;
            border-radius: 10px;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .position-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        .position-symbol {
            font-size: 18px;
            font-weight: 600;
        }
        .position-side {
            padding: 4px 12px;
            border-radius: 15px;
            font-size: 12px;
            font-weight: 600;
        }
        .position-side.buy {
            background: rgba(76, 175, 80, 0.2);
            color: #4caf50;
        }
        .position-side.sell {
            background: rgba(244, 67, 54, 0.2);
            color: #f44336;
        }
        .position-details {
            display: grid;
            gap: 10px;
            font-size: 14px;
        }
        .position-detail {
            display: flex;
            justify-content: space-between;
            color: #aaa;
        }
        .position-detail strong {
            color: #e0e0e0;
        }
        .notification {
            position: fixed;
            top: 80px;
            right: 20px;
            background: #333;
            padding: 15px 20px;
            border-radius: 10px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            display: none;
            animation: slideIn 0.3s ease-out;
            z-index: 1000;
            max-width: 300px;
        }
        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        .notification.success {
            background: linear-gradient(135deg, #1b5e20, #2e7d32);
        }
        .notification.error {
            background: linear-gradient(135deg, #b71c1c, #c62828);
        }
        .notification.info {
            background: linear-gradient(135deg, #0d47a1, #1565c0);
        }
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.8);
            animation: fadeIn 0.3s;
        }
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        .modal-content {
            background-color: #1e1e2e;
            margin: 5% auto;
            padding: 30px;
            border: 1px solid rgba(255,255,255,0.1);
            width: 90%;
            max-width: 600px;
            border-radius: 15px;
            animation: slideDown 0.3s;
        }
        @keyframes slideDown {
            from {
                transform: translateY(-50px);
                opacity: 0;
            }
            to {
                transform: translateY(0);
                opacity: 1;
            }
        }
        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        .modal-header h2 {
            font-size: 24px;
            font-weight: 600;
        }
        .close {
            color: #aaa;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
            transition: color 0.3s;
        }
        .close:hover {
            color: #fff;
        }
        .loading-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.7);
            display: none;
            justify-content: center;
            align-items: center;
            z-index: 9999;
        }
        .loading-spinner {
            border: 4px solid rgba(255,255,255,0.3);
            border-top: 4px solid #4CAF50;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        @media (max-width: 768px) {
            .header {
                flex-direction: column;
                gap: 15px;
            }
            .header-controls {
                justify-content: center;
            }
            .grid {
                grid-template-columns: 1fr;
            }
            .controls-section {
                flex-direction: column;
            }
            .btn {
                width: 100%;
            }
        }
    </style>
</head>
<body>
    <div class="loading-overlay" id="loadingOverlay">
        <div class="loading-spinner"></div>
    </div>
    
    <div class="notification" id="notification"></div>
    
    <div class="header">
        <h1>🤖 Crypto Trading Bot</h1>
        <div class="header-controls">
            <div class="user-info">
                <span>👤 <span id="username">User</span></span>
            </div>
            <div id="connection-status" class="status status-inactive">
                <span class="pulse inactive"></span>
                <span>Disconnected</span>
            </div>
            <div id="sync-status" class="status status-warning" style="display: none;">
                <span class="pulse warning"></span>
                <span>Desynchronized</span>
            </div>
            <button id="sync-btn" class="btn btn-secondary" onclick="syncState()" style="display: none;">
                🔄 Sync
            </button>
            <button onclick="logout()" class="btn btn-danger">Logout</button>
        </div>
    </div>
    
    <div class="container">
        <!-- Метрики -->
        <div class="grid">
            <div class="card">
                <h3>💰 Total Balance</h3>
                <div class="metric">
                    <div>
                        <div class="metric-value" id="balance">$0.00</div>
                        <div class="metric-change" id="balance-change">+0.00%</div>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h3>📈 Daily P&L</h3>
                <div class="metric">
                    <div>
                        <div class="metric-value" id="daily-pnl">$0.00</div>
                        <div class="metric-change" id="daily-pnl-percent">+0.00%</div>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h3>📊 Open Positions</h3>
                <div class="metric">
                    <div>
                        <div class="metric-value" id="open-positions">0</div>
                        <div class="metric-change">of <span id="max-positions">3</span> max</div>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h3>🎯 Win Rate</h3>
                <div class="metric">
                    <div>
                        <div class="metric-value" id="win-rate">0%</div>
                        <div class="metric-change"><span id="total-trades">0</span> trades</div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Управление -->
        <div class="card">
            <h3>🎮 Bot Control</h3>
            <div class="controls-section">
                <button id="start-bot" class="btn" onclick="controlBot('start')">
                    ▶️ Start Bot
                </button>
                <button id="stop-bot" class="btn btn-danger" onclick="controlBot('stop')" style="display:none;">
                    ⏹️ Stop Bot
                </button>
                <button class="btn btn-secondary" onclick="showSettings()">
                    ⚙️ Settings
                </button>
                <button class="btn btn-secondary" onclick="refreshData()">
                    🔄 Refresh
                </button>
            </div>
        </div>
        
        <!-- Выбор валютных пар -->
        <div class="card">
            <h3>💱 Trading Pairs</h3>
            <div class="pair-selector" id="pair-selector">
                <!-- Динамически заполняется -->
            </div>
            <button class="btn" onclick="updatePairs()">Update Pairs</button>
        </div>
        
        <!-- Открытые позиции -->
        <div class="card" id="positions-section" style="display:none;">
            <h3>💼 Open Positions</h3>
            <div class="positions-grid" id="positions-grid">
                <!-- Динамически заполняется -->
            </div>
        </div>
        
        <!-- График -->
        <div class="card">
            <h3>📈 Performance Chart</h3>
            <div class="chart-container">
                <canvas id="performance-chart"></canvas>
            </div>
        </div>
        
        <!-- Таблица сделок -->
        <div class="card">
            <h3>📜 Recent Trades</h3>
            <div style="overflow-x: auto;">
                <table id="trades-table">
                    <thead>
                        <tr>
                            <th>Time</th>
                            <th>Pair</th>
                            <th>Side</th>
                            <th>Entry</th>
                            <th>Exit</th>
                            <th>Quantity</th>
                            <th>Profit</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody id="trades-tbody">
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    
    <!-- Settings Modal -->
    <div id="settingsModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2>⚙️ Bot Settings</h2>
                <span class="close" onclick="closeSettings()">&times;</span>
            </div>
            <div id="settings-content">
                <!-- Динамически заполняется -->
            </div>
        </div>
    </div>
    
    <script>
        let ws = null;
        let chart = null;
        let reconnectInterval = null;
        const token = localStorage.getItem('access_token');
        const username = localStorage.getItem('username') || 'User';
        
        if (!token) {
            window.location.href = '/';
        }
        
        document.getElementById('username').textContent = username;
        
        // WebSocket подключение
        function connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            ws = new WebSocket(`${protocol}//${window.location.host}/ws?token=${token}`);
            
            ws.onopen = () => {
                console.log('WebSocket connected');
                updateConnectionStatus(true);
                clearInterval(reconnectInterval);
            };
            
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                updateDashboard(data);
            };
            
            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };
            
            ws.onclose = () => {
                console.log('WebSocket disconnected');
                updateConnectionStatus(false);
                // Переподключение каждые 5 секунд
                if (!reconnectInterval) {
                    reconnectInterval = setInterval(connectWebSocket, 5000);
                }
            };
        }
        
        function updateConnectionStatus(connected) {
            const statusEl = document.getElementById('connection-status');
            const pulseEl = statusEl.querySelector('.pulse');
            const textEl = statusEl.querySelector('span:last-child');
            
            if (connected) {
                statusEl.className = 'status status-active';
                pulseEl.className = 'pulse active';
                textEl.textContent = 'Connected';
            } else {
                statusEl.className = 'status status-inactive';
                pulseEl.className = 'pulse inactive';
                textEl.textContent = 'Disconnected';
            }
        }
        
        // ✅ ИСПРАВЛЕННОЕ обновление дашборда с индикатором синхронизации
        function updateDashboard(data) {
            // Баланс
            const balance = data.balance || 0;
            const balanceChange = data.balance_change || 0;
            document.getElementById('balance').textContent = `$${balance.toFixed(2)}`;
            const balanceChangeEl = document.getElementById('balance-change');
            balanceChangeEl.textContent = `${balanceChange >= 0 ? '+' : ''}${balanceChange.toFixed(2)}%`;
            balanceChangeEl.className = `metric-change ${balanceChange >= 0 ? 'profit' : 'loss'}`;
            
            // Daily P&L
            const dailyPnl = data.daily_pnl || 0;
            const dailyPnlPercent = data.daily_pnl_percent || 0;
            document.getElementById('daily-pnl').textContent = `$${dailyPnl.toFixed(2)}`;
            document.getElementById('daily-pnl').className = `metric-value ${dailyPnl >= 0 ? 'profit' : 'loss'}`;
            const pnlPercentEl = document.getElementById('daily-pnl-percent');
            pnlPercentEl.textContent = `${dailyPnlPercent >= 0 ? '+' : ''}${dailyPnlPercent.toFixed(2)}%`;
            pnlPercentEl.className = `metric-change ${dailyPnlPercent >= 0 ? 'profit' : 'loss'}`;
            
            // Позиции
            document.getElementById('open-positions').textContent = data.open_positions || 0;
            document.getElementById('max-positions').textContent = data.max_positions || 3;
            
            // Win rate
            document.getElementById('win-rate').textContent = `${(data.win_rate || 0).toFixed(1)}%`;
            document.getElementById('total-trades').textContent = data.total_trades || 0;
            
            // ✅ НОВОЕ: Статус бота с проверкой синхронизации
            updateBotStatus(data.bot_running, data.manager_running);
            
            // ✅ НОВОЕ: Индикатор синхронизации
            updateSyncStatus(data.synchronized);
            
            // Активные пары
            if (data.active_pairs) {
                updatePairSelector(data.active_pairs);
            }
            
            // Открытые позиции
            if (data.positions && data.positions.length > 0) {
                updatePositions(data.positions);
            } else {
                document.getElementById('positions-section').style.display = 'none';
            }
            
            // Таблица сделок
            if (data.recent_trades) {
                updateTradesTable(data.recent_trades);
            }
            
            // График
            if (data.chart_data) {
                updateChart(data.chart_data);
            }
        }
        
        // ✅ УЛУЧШЕННАЯ функция обновления статуса бота
        function updateBotStatus(botRunning, managerRunning) {
            const startBtn = document.getElementById('start-bot');
            const stopBtn = document.getElementById('stop-bot');
            
            // Используем статус процесса как основной
            const isRunning = botRunning || false;
            
            if (isRunning) {
                startBtn.style.display = 'none';
                stopBtn.style.display = 'inline-block';
            } else {
                startBtn.style.display = 'inline-block';
                stopBtn.style.display = 'none';
            }
        }
        
        // ✅ НОВАЯ функция для обновления статуса синхронизации
        function updateSyncStatus(synchronized) {
            const syncStatus = document.getElementById('sync-status');
            const syncBtn = document.getElementById('sync-btn');
            
            if (synchronized === false) {
                syncStatus.style.display = 'flex';
                syncBtn.style.display = 'inline-block';
            } else {
                syncStatus.style.display = 'none';
                syncBtn.style.display = 'none';
            }
        }
        
        function updatePairSelector(activePairs) {
            const container = document.getElementById('pair-selector');
            const allPairs = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'ADAUSDT', 'DOGEUSDT', 'XRPUSDT', 'DOTUSDT'];
            
            container.innerHTML = allPairs.map(pair => `
                <label class="pair-checkbox">
                    <input type="checkbox" value="${pair}" ${activePairs.includes(pair) ? 'checked' : ''}>
                    <span>${pair.replace('USDT', '/USDT')}</span>
                </label>
            `).join('');
        }
        
        function updatePositions(positions) {
            const section = document.getElementById('positions-section');
            const grid = document.getElementById('positions-grid');
            
            section.style.display = 'block';
            
            grid.innerHTML = positions.map(pos => `
                <div class="position-card">
                    <div class="position-header">
                        <span class="position-symbol">${pos.symbol}</span>
                        <span class="position-side ${pos.side.toLowerCase()}">${pos.side}</span>
                    </div>
                    <div class="position-details">
                        <div class="position-detail">
                            <span>Entry Price:</span>
                            <strong>$${pos.entry_price.toFixed(2)}</strong>
                        </div>
                        <div class="position-detail">
                            <span>Current Price:</span>
                            <strong>$${pos.current_price.toFixed(2)}</strong>
                        </div>
                        <div class="position-detail">
                            <span>Quantity:</span>
                            <strong>${pos.quantity.toFixed(4)}</strong>
                        </div>
                        <div class="position-detail">
                            <span>P&L:</span>
                            <strong class="${pos.pnl >= 0 ? 'profit' : 'loss'}">
                                $${pos.pnl.toFixed(2)} (${pos.pnl_percent.toFixed(2)}%)
                            </strong>
                        </div>
                    </div>
                    <button class="btn btn-danger" style="width:100%; margin-top:15px;" 
                            onclick="closePosition('${pos.symbol}')">
                        Close Position
                    </button>
                </div>
            `).join('');
        }
        
        // Управление ботом
        async function controlBot(action) {
            showLoading();
            try {
                const response = await fetch(`/api/bot/${action}`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
                
                if (response.ok) {
                    const data = await response.json();
                    showNotification(data.message || `Bot ${action}ed successfully`, 'success');
                    
                    // Обновляем статус кнопок
                    updateBotStatus(action === 'start', action === 'start');
                    
                    // Обновляем данные
                    setTimeout(refreshData, 2000);
                } else {
                    const error = await response.json();
                    showNotification(error.detail || `Failed to ${action} bot`, 'error');
                }
            } catch (error) {
                showNotification('Connection error', 'error');
            } finally {
                hideLoading();
            }
        }
        
        // ✅ НОВАЯ функция синхронизации состояния
        async function syncState() {
            showLoading();
            try {
                const response = await fetch('/api/bot/sync', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
                
                if (response.ok) {
                    const data = await response.json();
                    showNotification(data.message, 'success');
                    
                    // Скрываем индикатор рассинхронизации
                    updateSyncStatus(true);
                    
                    // Обновляем данные
                    setTimeout(refreshData, 1000);
                } else {
                    const error = await response.json();
                    showNotification(error.detail || 'Sync failed', 'error');
                }
            } catch (error) {
                showNotification('Connection error', 'error');
            } finally {
                hideLoading();
            }
        }
        
        // Обновление торговых пар
        async function updatePairs() {
            const checkboxes = document.querySelectorAll('#pair-selector input[type="checkbox"]:checked');
            const pairs = Array.from(checkboxes).map(cb => cb.value);
            
            if (pairs.length === 0) {
                showNotification('Please select at least one trading pair', 'error');
                return;
            }
            
            showLoading();
            try {
                const response = await fetch('/api/pairs', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ pairs })
                });
                
                if (response.ok) {
                    showNotification('Trading pairs updated', 'success');
                } else {
                    const error = await response.json();
                    showNotification(error.detail || 'Failed to update pairs', 'error');
                }
            } catch (error) {
                showNotification('Connection error', 'error');
            } finally {
                hideLoading();
            }
        }
        
        // Закрытие позиции
        async function closePosition(symbol) {
            if (!confirm(`Are you sure you want to close the ${symbol} position?`)) {
                return;
            }
            
            showLoading();
            try {
                const response = await fetch(`/api/position/${symbol}/close`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
                
                if (response.ok) {
                    showNotification(`${symbol} position closed`, 'success');
                    setTimeout(refreshData, 1000);
                } else {
                    const error = await response.json();
                    showNotification(error.detail || 'Failed to close position', 'error');
                }
            } catch (error) {
                showNotification('Connection error', 'error');
            } finally {
                hideLoading();
            }
        }
        
        // Обновление данных
        async function refreshData() {
            try {
                const response = await fetch('/api/dashboard', {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
                
                if (response.ok) {
                    const data = await response.json();
                    updateDashboard(data);
                } else {
                    console.error('Failed to refresh data');
                }
            } catch (error) {
                console.error('Failed to refresh data:', error);
            }
        }
        
        // Настройки
        function showSettings() {
            document.getElementById('settingsModal').style.display = 'block';
            loadSettings();
        }
        
        function closeSettings() {
            document.getElementById('settingsModal').style.display = 'none';
        }
        
        async function loadSettings() {
            // Здесь будет загрузка настроек
            document.getElementById('settings-content').innerHTML = `
                <p>Settings functionality coming soon...</p>
            `;
        }
        
        // Выход
        function logout() {
            localStorage.removeItem('access_token');
            localStorage.removeItem('username');
            window.location.href = '/';
        }
        
        // Уведомления
        function showNotification(message, type = 'info') {
            const notification = document.getElementById('notification');
            notification.textContent = message;
            notification.className = `notification ${type}`;
            notification.style.display = 'block';
            
            setTimeout(() => {
                notification.style.display = 'none';
            }, 4000);
        }
        
        // Загрузка
        function showLoading() {
            document.getElementById('loadingOverlay').style.display = 'flex';
        }
        
        function hideLoading() {
            document.getElementById('loadingOverlay').style.display = 'none';
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
                    backgroundColor: 'rgba(76, 175, 80, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.05)'
                        },
                        ticks: {
                            color: '#888'
                        }
                    },
                    y: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.05)'
                        },
                        ticks: {
                            color: '#888',
                            callback: function(value) {
                                return '$' + value.toFixed(0);
                            }
                        }
                    }
                }
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
                
                const sideCell = row.insertCell(2);
                sideCell.innerHTML = `<span class="position-side ${trade.side.toLowerCase()}">${trade.side}</span>`;
                
                row.insertCell(3).textContent = `$${trade.entry_price.toFixed(2)}`;
                row.insertCell(4).textContent = trade.exit_price ? `$${trade.exit_price.toFixed(2)}` : '-';
                row.insertCell(5).textContent = trade.quantity.toFixed(4);
                
                const profitCell = row.insertCell(6);
                if (trade.profit !== null && trade.profit !== undefined) {
                    profitCell.innerHTML = `<span class="${trade.profit >= 0 ? 'profit' : 'loss'}">
                        $${trade.profit.toFixed(2)} (${trade.profit_percent?.toFixed(2) || 0}%)
                    </span>`;
                } else {
                    profitCell.textContent = '-';
                }
                
                const statusCell = row.insertCell(7);
                const statusClass = trade.status === 'CLOSED' ? 'neutral' : 'active';
                statusCell.innerHTML = `<span class="${statusClass}">${trade.status}</span>`;
            });
        }
        
        // Запуск
        connectWebSocket();
        refreshData();
        
        // Обработка клавиш
        window.onclick = function(event) {
            if (event.target.className === 'modal') {
                event.target.style.display = 'none';
            }
        }
        
        // Периодическое обновление
        setInterval(refreshData, 30000); // каждые 30 секунд
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

@app.get("/api/dashboard")
async def get_dashboard_data(current_user: User = Depends(auth_service.get_current_user)):
    """Получение данных для дашборда"""
    return await get_dashboard_data_internal()

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
            data = await get_dashboard_data_internal()
            await websocket.send_json(data)
            await asyncio.sleep(5)
            
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await websocket.close()

# ✅ ИСПРАВЛЕННАЯ функция получения данных дашборда
async def get_dashboard_data_internal():
    """Получение данных для дашборда с использованием единого менеджера"""
    db = SessionLocal()
    
    try:
        # ✅ ИСПРАВЛЕНИЕ: Используем единый менеджер
        bot_status = unified_bot_manager.get_comprehensive_status()
        
        # Баланс
        try:
            balance_data = await exchange_client.fetch_balance()
            usdt_balance = balance_data.get('USDT', {}).get('total', 0)
        except Exception as e:
            logger.error(f"Ошибка получения баланса: {e}")
            usdt_balance = 10000  # Значение по умолчанию
        
        # Статистика сделок
        total_trades = db.query(Trade).count()
        open_positions = db.query(Trade).filter(Trade.status == TradeStatus.OPEN).all()
        
        # Дневная прибыль
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_trades = db.query(Trade).filter(
            Trade.status == TradeStatus.CLOSED,
            Trade.closed_at >= today_start
        ).all()
        
        daily_pnl = sum(trade.profit or 0 for trade in today_trades)
        daily_pnl_percent = (daily_pnl / usdt_balance * 100) if usdt_balance > 0 else 0
        
        # Win rate
        profitable_trades = len([t for t in today_trades if t.profit and t.profit > 0])
        total_closed_today = len(today_trades)
        win_rate = (profitable_trades / total_closed_today * 100) if total_closed_today > 0 else 0
        
        # Последние сделки
        recent_trades = db.query(Trade).order_by(Trade.created_at.desc()).limit(20).all()
        
        # График производительности
        chart_data = await get_performance_chart_data(db)
        
        # Подготовка позиций с текущими ценами
        positions_data = []
        for position in open_positions:
            try:
                ticker = await exchange_client.fetch_ticker(position.symbol)
                current_price = ticker['last']
                
                # Исправляем обращение к OrderSide
                if hasattr(position.side, 'value'):
                    side_value = position.side.value
                else:
                    side_value = str(position.side)
                
                if side_value == 'BUY':
                    pnl = (current_price - position.entry_price) * position.quantity
                else:
                    pnl = (position.entry_price - current_price) * position.quantity
                
                pnl_percent = (pnl / (position.entry_price * position.quantity)) * 100
                
                positions_data.append({
                    'symbol': position.symbol,
                    'side': side_value,
                    'entry_price': position.entry_price,
                    'current_price': current_price,
                    'quantity': position.quantity,
                    'pnl': pnl,
                    'pnl_percent': pnl_percent
                })
            except Exception as e:
                logger.error(f"Ошибка получения данных позиции {position.symbol}: {e}")
        
        return {
            'balance': usdt_balance,
            'balance_change': 0,  # TODO: Рассчитать изменение баланса
            'daily_pnl': daily_pnl,
            'daily_pnl_percent': daily_pnl_percent,
            'open_positions': len(open_positions),
            'max_positions': 3,  # Из настроек
            'total_trades': total_trades,
            'win_rate': win_rate,
            'bot_running': bot_status.get('process_running', False),  # ✅ Реальный статус процесса
            'manager_running': bot_status.get('manager_running', False),  # ✅ Статус менеджера
            'active_pairs': bot_status.get('active_pairs', []),
            'synchronized': bot_status.get('synchronized', True),  # ✅ Статус синхронизации
            'positions': positions_data,
            'recent_trades': [
                {
                    'created_at': trade.created_at.isoformat(),
                    'symbol': trade.symbol,
                    'side': trade.side.value if hasattr(trade.side, 'value') else str(trade.side),
                    'entry_price': trade.entry_price,
                    'exit_price': trade.exit_price,
                    'quantity': trade.quantity,
                    'profit': trade.profit,
                    'profit_percent': trade.profit_percent,
                    'status': trade.status.value if hasattr(trade.status, 'value') else str(trade.status)
                }
                for trade in recent_trades
            ],
            'chart_data': chart_data
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения данных дашборда: {e}")
        # Возвращаем базовые данные при ошибке
        return {
            'balance': 0,
            'balance_change': 0,
            'daily_pnl': 0,
            'daily_pnl_percent': 0,
            'open_positions': 0,
            'max_positions': 3,
            'total_trades': 0,
            'win_rate': 0,
            'bot_running': False,
            'manager_running': False,
            'active_pairs': [],
            'synchronized': False,
            'positions': [],
            'recent_trades': [],
            'chart_data': {'labels': [], 'values': []}
        }
    finally:
        db.close()

async def get_performance_chart_data(db):
    """Получение данных для графика производительности"""
    try:
        # Последние 24 часа
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=24)
        
        # Получаем все закрытые сделки за период
        trades = db.query(Trade).filter(
            Trade.closed_at >= start_time,
            Trade.closed_at <= end_time,
            Trade.status == TradeStatus.CLOSED
        ).order_by(Trade.closed_at).all()
        
        # Группируем по часам
        hourly_data = {}
        current_balance = 10000  # Начальный баланс (заменить на реальный)
        
        for trade in trades:
            hour = trade.closed_at.replace(minute=0, second=0, microsecond=0)
            if hour not in hourly_data:
                hourly_data[hour] = current_balance
            current_balance += trade.profit or 0
            hourly_data[hour] = current_balance
        
        # Заполняем пропущенные часы
        labels = []
        values = []
        current_hour = start_time.replace(minute=0, second=0, microsecond=0)
        last_value = current_balance
        
        while current_hour <= end_time:
            labels.append(current_hour.isoformat())
            if current_hour in hourly_data:
                last_value = hourly_data[current_hour]
            values.append(last_value)
            current_hour += timedelta(hours=1)
        
        return {
            'labels': labels,
            'values': values
        }
    except Exception as e:
        logger.error(f"Ошибка получения данных графика: {e}")
        return {
            'labels': [],
            'values': []
        }

# ✅ ИСПРАВЛЕННЫЕ API endpoints с единым менеджером
@app.post("/api/bot/{action}")
async def control_bot(action: str, current_user: User = Depends(auth_service.get_current_user)):
    """🎮 ИСПРАВЛЕННОЕ управление ботом с детальной обработкой ошибок"""
    try:
        logger.info(f"🎮 Получен запрос на {action} бота от пользователя {current_user.username}")
        
        if action == "start":
            result = await unified_bot_manager.start_bot()
            
            if result['success']:
                logger.info(f"✅ Бот успешно запущен: {result['message']}")
                return {
                    "status": "started", 
                    "message": result['message'], 
                    "pid": result.get('pid'),
                    "details": {
                        "already_running": result.get('already_running', False),
                        "status_summary": result.get('status', 'Запущен')
                    }
                }
            else:
                logger.warning(f"⚠️ Не удалось запустить бота: {result['message']}")
                raise HTTPException(
                    status_code=400, 
                    detail={
                        "message": result['message'],
                        "details": result.get('details', {}),
                        "already_running": result.get('already_running', False)
                    }
                )
                
        elif action == "stop":
            result = await unified_bot_manager.stop_bot()
            
            if result['success']:
                logger.info(f"✅ Бот успешно остановлен: {result['message']}")
                return {
                    "status": "stopped", 
                    "message": result['message'],
                    "details": {
                        "was_running": result.get('was_running', True),
                        "sync_needed": result.get('sync_needed', False),
                        "status_summary": result.get('status', 'Остановлен')
                    }
                }
            else:
                logger.error(f"❌ Не удалось остановить бота: {result['message']}")
                raise HTTPException(
                    status_code=400, 
                    detail={
                        "message": result['message'],
                        "details": result.get('details', {})
                    }
                )
        else:
            raise HTTPException(status_code=400, detail="Неподдерживаемое действие")
            
    except HTTPException:
        # Перебрасываем HTTP исключения как есть
        raise
    except Exception as e:
        error_msg = f"Критическая ошибка управления ботом: {str(e)}"
        logger.error(f"💥 {error_msg}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail={
                "message": "Внутренняя ошибка сервера",
                "error": error_msg,
                "action": action
            }
        )

@app.post("/api/bot/sync")
async def sync_bot_state(current_user: User = Depends(auth_service.get_current_user)):
    """🔄 ИСПРАВЛЕННАЯ синхронизация состояния бота"""
    try:
        logger.info(f"🔄 Запрос синхронизации от пользователя {current_user.username}")
        
        result = unified_bot_manager.sync_state()
        
        if result['success']:
            logger.info(f"✅ Синхронизация успешна: {result['message']}")
            return {
                "status": "synchronized", 
                "is_running": result['is_running'], 
                "message": result['message'],
                "details": {
                    "changed": result.get('changed', False),
                    "changes": result.get('changes', []),
                    "truth_source": result.get('truth_source', 'unknown')
                }
            }
        else:
            error_msg = result.get('error', 'Неизвестная ошибка синхронизации')
            logger.error(f"❌ Ошибка синхронизации: {error_msg}")
            raise HTTPException(
                status_code=500, 
                detail={
                    "message": "Ошибка синхронизации состояния",
                    "error": error_msg
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Критическая ошибка синхронизации: {str(e)}"
        logger.error(f"💥 {error_msg}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail={
                "message": "Внутренняя ошибка синхронизации",
                "error": error_msg
            }
        )

@app.post("/api/pairs")
async def update_trading_pairs(
    pairs: Dict[str, List[str]], 
    current_user: User = Depends(auth_service.get_current_user)
):
    """💱 ИСПРАВЛЕННОЕ обновление торговых пар"""
    try:
        pairs_list = pairs.get('pairs', [])
        logger.info(f"💱 Обновление торговых пар от {current_user.username}: {pairs_list}")
        
        if not pairs_list:
            raise HTTPException(
                status_code=400, 
                detail="Необходимо указать хотя бы одну торговую пару"
            )
        
        result = await unified_bot_manager.update_pairs(pairs_list)
        
        if result['success']:
            logger.info(f"✅ Торговые пары обновлены: {result['message']}")
            return {
                "status": "updated", 
                "pairs": result['pairs'],
                "message": result['message']
            }
        else:
            logger.error(f"❌ Ошибка обновления пар: {result['error']}")
            raise HTTPException(
                status_code=400, 
                detail={
                    "message": "Ошибка обновления торговых пар",
                    "error": result['error']
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Критическая ошибка обновления пар: {str(e)}"
        logger.error(f"💥 {error_msg}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail={
                "message": "Внутренняя ошибка обновления пар",
                "error": error_msg
            }
        )

@app.post("/api/position/{symbol}/close")
async def close_position(
    symbol: str,
    current_user: User = Depends(auth_service.get_current_user)
):
    """📤 ИСПРАВЛЕННОЕ закрытие позиции"""
    try:
        logger.info(f"📤 Запрос закрытия позиции {symbol} от {current_user.username}")
        
        result = await unified_bot_manager.close_position(symbol)
        
        if result['success']:
            logger.info(f"✅ Позиция закрыта: {result['message']}")
            return {
                "status": "closed", 
                "symbol": symbol,
                "message": result['message']
            }
        else:
            logger.warning(f"⚠️ Позиция не найдена: {symbol}")
            raise HTTPException(
                status_code=404, 
                detail={
                    "message": f"Позиция {symbol} не найдена",
                    "error": result.get('error', 'Position not found')
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Критическая ошибка закрытия позиции: {str(e)}"
        logger.error(f"💥 {error_msg}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail={
                "message": "Внутренняя ошибка закрытия позиции",
                "error": error_msg,
                "symbol": symbol
            }
        )
        
@app.post("/api/bot/force-sync")
async def force_sync(current_user: User = Depends(auth_service.get_current_user)):
    """🔄 Принудительная синхронизация состояний"""
    try:
        logger.info(f"🔄 Принудительная синхронизация от {current_user.username}")
        
        result = state_manager.sync_all_to_truth()
        
        if result['success']:
            return {
                'status': 'synchronized',
                'message': result['message'],
                'target_state': result['target_state']
            }
        else:
            raise HTTPException(status_code=500, detail=result['error'])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)