"""
Flask веб-приложение для Crypto Trading Bot
Файл: src/web/app.py
"""
import os
from datetime import datetime
from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_socketio import SocketIO, emit
import asyncio
from functools import wraps

from ..core.database import SessionLocal
from ..core.models import User, Trade, Signal, Order
from ..bot.manager import BotManager
from ..logging.smart_logger import SmartLogger
from ..logging.analytics_collector import AnalyticsCollector
from .chart_api import ChartAPI

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
    
    # Chart API
    chart_api = ChartAPI()
    
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
    
    # ===== ROUTES =====
    
    @app.route('/')
    def index():
        """Главная страница"""
        return redirect(url_for('dashboard'))
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """Страница входа"""
        if request.method == 'POST':
            # Простая авторизация для демо
            username = request.form.get('username')
            password = request.form.get('password')
            
            if username == 'admin' and password == 'admin':
                # Создаем или получаем пользователя
                db = SessionLocal()
                try:
                    user = db.query(User).filter(User.username == username).first()
                    if not user:
                        user = User(username=username, email='admin@example.com')
                        db.add(user)
                        db.commit()
                    
                    login_user(user)
                    return redirect(url_for('dashboard'))
                finally:
                    db.close()
            else:
                return render_template('login.html', error='Неверные учетные данные')
        
        return render_template('login.html')
    
    @app.route('/logout')
    @login_required
    def logout():
        """Выход из системы"""
        logout_user()
        return redirect(url_for('login'))
    
    @app.route('/dashboard')
    @login_required
    @async_route
    async def dashboard():
        """Главный дашборд"""
        try:
            # Получаем статистику
            stats = await bot_manager.get_statistics() if bot_manager else {}
            
            # Получаем последние сделки
            db = SessionLocal()
            try:
                recent_trades = db.query(Trade).order_by(Trade.created_at.desc()).limit(10).all()
                active_positions = db.query(Trade).filter(Trade.status == 'open').all()
            finally:
                db.close()
            
            return render_template('dashboard.html',
                                 stats=stats,
                                 recent_trades=recent_trades,
                                 active_positions=active_positions,
                                 bot_status=bot_manager.is_running if bot_manager else False)
        except Exception as e:
            logger.error(f"Ошибка загрузки дашборда: {e}", category='error')
            return render_template('error.html', error=str(e))
    
    @app.route('/charts')
    @login_required
    def charts():
        """Страница с графиками"""
        return render_template('charts.html')
    
    @app.route('/analytics')
    @login_required
    @async_route
    async def analytics():
        """Страница аналитики"""
        try:
            # Получаем аналитику
            analytics_data = await analytics_collector.get_comprehensive_analytics()
            return render_template('analytics.html', analytics=analytics_data)
        except Exception as e:
            logger.error(f"Ошибка загрузки аналитики: {e}", category='error')
            return render_template('error.html', error=str(e))
    
    @app.route('/news')
    @login_required
    def news():
        """Страница новостей и соцсигналов"""
        return render_template('news.html')
    
    # ===== API ENDPOINTS =====
    
    @app.route('/api/bot/start', methods=['POST'])
    @login_required
    @async_route
    async def start_bot():
        """Запуск бота"""
        try:
            if not bot_manager.is_running:
                await bot_manager.start()
                socketio.emit('bot_status', {'status': 'running'})
                return jsonify({'success': True, 'message': 'Бот успешно запущен'})
            else:
                return jsonify({'success': False, 'message': 'Бот уже запущен'})
        except Exception as e:
            logger.error(f"Ошибка запуска бота: {e}", category='error')
            return jsonify({'success': False, 'message': str(e)})
    
    @app.route('/api/bot/stop', methods=['POST'])
    @login_required
    @async_route
    async def stop_bot():
        """Остановка бота"""
        try:
            if bot_manager.is_running:
                await bot_manager.stop()
                socketio.emit('bot_status', {'status': 'stopped'})
                return jsonify({'success': True, 'message': 'Бот успешно остановлен'})
            else:
                return jsonify({'success': False, 'message': 'Бот не запущен'})
        except Exception as e:
            logger.error(f"Ошибка остановки бота: {e}", category='error')
            return jsonify({'success': False, 'message': str(e)})
    
    @app.route('/api/bot/status')
    @login_required
    def bot_status():
        """Статус бота"""
        return jsonify({
            'running': bot_manager.is_running if bot_manager else False,
            'uptime': bot_manager.get_uptime() if bot_manager and bot_manager.is_running else 0
        })
    
    @app.route('/api/balance')
    @login_required
    @async_route
    async def get_balance():
        """Получение баланса"""
        try:
            balance = await bot_manager.get_balance() if bot_manager else {}
            return jsonify(balance)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/trades/recent')
    @login_required
    def get_recent_trades():
        """Получение последних сделок"""
        db = SessionLocal()
        try:
            limit = request.args.get('limit', 20, type=int)
            trades = db.query(Trade).order_by(Trade.created_at.desc()).limit(limit).all()
            
            return jsonify([{
                'id': t.id,
                'symbol': t.symbol,
                'side': t.side.value,
                'quantity': float(t.quantity),
                'entry_price': float(t.entry_price),
                'exit_price': float(t.exit_price) if t.exit_price else None,
                'profit': float(t.profit) if t.profit else None,
                'status': t.status.value,
                'created_at': t.created_at.isoformat()
            } for t in trades])
        finally:
            db.close()
    
    @app.route('/api/performance/summary')
    @login_required
    @async_route
    async def get_performance_summary():
        """Сводка производительности"""
        try:
            summary = await analytics_collector.get_performance_summary()
            return jsonify(summary)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/strategies')
    @login_required
    def get_strategies():
        """Получение списка стратегий"""
        strategies = bot_manager.get_available_strategies() if bot_manager else []
        return jsonify(strategies)
    
    @app.route('/api/strategies/toggle', methods=['POST'])
    @login_required
    def toggle_strategy():
        """Включение/выключение стратегии"""
        data = request.json
        strategy_name = data.get('strategy')
        enabled = data.get('enabled')
        
        if bot_manager:
            bot_manager.toggle_strategy(strategy_name, enabled)
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Bot manager not initialized'})
    
    # ===== WebSocket Events =====
    
    @socketio.on('connect')
    def handle_connect():
        """Подключение клиента"""
        logger.info(f"WebSocket клиент подключен", category='websocket')
        emit('connected', {'data': 'Connected to server'})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Отключение клиента"""
        logger.info(f"WebSocket клиент отключен", category='websocket')
    
    @socketio.on('subscribe_updates')
    def handle_subscribe(data):
        """Подписка на обновления"""
        channel = data.get('channel', 'all')
        logger.info(f"Клиент подписался на канал: {channel}", category='websocket')
        emit('subscribed', {'channel': channel})
    
    # ===== Error Handlers =====
    
    @app.errorhandler(404)
    def not_found(error):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}", category='error')
        return render_template('500.html'), 500
    
    return app


# Функция для запуска в режиме разработки
if __name__ == '__main__':
    app = create_app()
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)