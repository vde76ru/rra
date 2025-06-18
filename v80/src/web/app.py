"""
Flask веб-приложение для Crypto Trading Bot - ИСПРАВЛЕННАЯ ВЕРСИЯ
Файл: src/web/app.py
"""
import os
from datetime import datetime
from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_socketio import SocketIO, emit
import asyncio
from functools import wraps
from collections import deque

# ИСПРАВЛЕНИЕ: Правильные импорты из core.models
from ..core.database import SessionLocal
from ..core.models import (
    User, Trade, Signal, Order,
    StrategyPerformance,  # Вместо Strategy
    BotState, Balance, TradingPair
)
from ..bot.manager import BotManager
from ..logging.smart_logger import SmartLogger
from ..logging.analytics_collector import AnalyticsCollector

# Условный импорт ChartAPI
try:
    from .chart_api import ChartAPI
    CHART_API_AVAILABLE = True
except ImportError:
    CHART_API_AVAILABLE = False
    ChartAPI = None

# Инициализация логгера
smart_logger = SmartLogger(__name__)
logger = smart_logger

# Глобальные переменные
bot_manager = None
analytics_collector = None
socketio = None


def create_app():
    """Создание и настройка Flask приложения"""
    app = Flask(__name__, 
                template_folder='templates',
                static_folder='static')
    
    # Конфигурация
    app.config['SECRET_KEY'] = os.getenv('APP_SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SESSION_TYPE'] = 'filesystem'
    
    # Инициализация SocketIO
    global socketio
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
    
    # Инициализация LoginManager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    
    # Инициализация компонентов
    global bot_manager, analytics_collector
    bot_manager = BotManager()
    analytics_collector = AnalyticsCollector()
    
    # Chart API только если доступен
    chart_api = ChartAPI() if CHART_API_AVAILABLE else None
    
    @login_manager.user_loader
    def load_user(user_id):
        db = SessionLocal()
        try:
            return db.query(User).filter(User.id == int(user_id)).first()
        finally:
            db.close()
    
    # Декоратор для async routes
    def async_route(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(f(*args, **kwargs))
            finally:
                loop.close()
        return wrapper
    
    # ====================
    # МАРШРУТЫ
    # ====================
    
    @app.route('/')
    @login_required
    def index():
        """Главная страница дашборда"""
        return render_template('dashboard.html')
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """Страница входа"""
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            db = SessionLocal()
            try:
                user = db.query(User).filter(User.username == username).first()
                
                if user and user.check_password(password):
                    login_user(user)
                    logger.info(f"Успешный вход пользователя: {username}")
                    return redirect(url_for('index'))
                else:
                    logger.warning(f"Неудачная попытка входа: {username}")
                    return render_template('login.html', error="Неверное имя пользователя или пароль")
            finally:
                db.close()
        
        return render_template('login.html')
    
    @app.route('/logout')
    @login_required
    def logout():
        """Выход из системы"""
        logout_user()
        return redirect(url_for('login'))
    
    # ====================
    # API ENDPOINTS
    # ====================
    
    @app.route('/api/status')
    @login_required
    def get_status():
        """Получить статус бота"""
        try:
            status = bot_manager.get_status()
            return jsonify(status)
        except Exception as e:
            logger.error(f"Ошибка получения статуса: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/balance')
    @login_required
    @async_route
    async def get_balance():
        """Получить текущий баланс"""
        try:
            balance = await bot_manager.get_balance_info()
            return jsonify(balance)
        except Exception as e:
            logger.error(f"Ошибка получения баланса: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/trades')
    @login_required
    def get_trades():
        """Получить список сделок"""
        limit = request.args.get('limit', 50, type=int)
        
        db = SessionLocal()
        try:
            trades = db.query(Trade).order_by(Trade.created_at.desc()).limit(limit).all()
            
            trades_data = []
            for trade in trades:
                trades_data.append({
                    'id': trade.id,
                    'symbol': trade.symbol,
                    'side': trade.side,
                    'price': float(trade.price),
                    'quantity': float(trade.quantity),
                    'status': trade.status,
                    'profit': float(trade.profit) if trade.profit else 0,
                    'created_at': trade.created_at.isoformat()
                })
            
            return jsonify(trades_data)
        finally:
            db.close()
    
    @app.route('/api/strategies')
    @login_required
    def get_strategies():
        """Получить информацию о стратегиях"""
        db = SessionLocal()
        try:
            # Получаем производительность стратегий
            performances = db.query(StrategyPerformance).all()
            
            strategies_data = []
            for perf in performances:
                strategies_data.append({
                    'name': perf.strategy_name,
                    'trades_count': perf.trades_count,
                    'win_rate': float(perf.win_rate),
                    'profit_factor': float(perf.profit_factor),
                    'sharpe_ratio': float(perf.sharpe_ratio) if perf.sharpe_ratio else 0,
                    'total_profit': float(perf.total_profit),
                    'updated_at': perf.updated_at.isoformat()
                })
            
            return jsonify(strategies_data)
        finally:
            db.close()
    
    @app.route('/api/bot/start', methods=['POST'])
    @login_required
    @async_route
    async def start_bot():
        """Запустить бота"""
        try:
            success, message = await bot_manager.start()
            return jsonify({
                'success': success,
                'message': message
            })
        except Exception as e:
            logger.error(f"Ошибка запуска бота: {e}")
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500
    
    @app.route('/api/bot/stop', methods=['POST'])
    @login_required
    @async_route
    async def stop_bot():
        """Остановить бота"""
        try:
            success, message = await bot_manager.stop()
            return jsonify({
                'success': success,
                'message': message
            })
        except Exception as e:
            logger.error(f"Ошибка остановки бота: {e}")
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500
    
    # ====================
    # WEBSOCKET EVENTS
    # ====================
    
    @socketio.on('connect')
    @login_required
    def handle_connect():
        """Обработка подключения WebSocket"""
        logger.info(f"WebSocket подключен: {current_user.username}")
        emit('connected', {'data': 'Connected'})
    
    @socketio.on('disconnect')
    @login_required
    def handle_disconnect():
        """Обработка отключения WebSocket"""
        logger.info(f"WebSocket отключен: {current_user.username}")
    
    @socketio.on('subscribe_updates')
    @login_required
    def handle_subscribe():
        """Подписка на обновления"""
        # Отправляем начальный статус
        status = bot_manager.get_status()
        emit('status_update', status)
    
    # ====================
    # ОБРАБОТКА ОШИБОК
    # ====================
    
    @app.errorhandler(404)
    def not_found(error):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Внутренняя ошибка сервера: {error}")
        return render_template('500.html'), 500
    
    return app, socketio


# Создаем приложение
app, socketio = create_app()

# Экспортируем для использования в других модулях
__all__ = ['app', 'socketio']