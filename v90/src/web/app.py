"""
Flask веб-приложение для Crypto Trading Bot - ПОЛНОСТЬЮ ИСПРАВЛЕННАЯ ВЕРСИЯ
Файл: src/web/app.py
"""
import os
import json
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import asyncio
from functools import wraps
from typing import Dict, Any, List, Optional
import logging

# Импорты из нашего проекта
from ..core.database import SessionLocal
from ..core.models import (
    User, Trade, Signal, Order, BotState, Balance, 
    TradingPair, StrategyPerformance, TradeStatus,
    OrderSide, SignalAction
)
from ..core.config import config
from ..exchange.client import ExchangeClient

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Глобальные переменные
app = None
socketio = None
bot_manager = None
exchange_client = None
login_manager = None

# Хранилище для WebSocket соединений
ws_clients = set()

def create_app():
    """Создание и настройка Flask приложения"""
    global app, socketio, bot_manager, exchange_client, login_manager
    
    # Создаем Flask приложение
    app = Flask(__name__, 
                template_folder='templates',
                static_folder='static')
    
    # Конфигурация
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
    
    # CORS
    CORS(app, resources={r"/*": {"origins": "*"}})
    
    # Инициализация SocketIO
    socketio = SocketIO(app, 
                       cors_allowed_origins="*", 
                       async_mode='threading',
                       logger=True,
                       engineio_logger=True)
    
    # Инициализация LoginManager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Пожалуйста, войдите в систему'
    
    # Инициализация компонентов
    try:
        from ..bot.manager import BotManager
        bot_manager = BotManager()
        logger.info("✅ BotManager инициализирован")
    except Exception as e:
        logger.warning(f"⚠️ Не удалось инициализировать BotManager: {e}")
        bot_manager = None
    
    try:
        exchange_client = ExchangeClient()
        logger.info("✅ ExchangeClient инициализирован")
    except Exception as e:
        logger.warning(f"⚠️ Не удалось инициализировать ExchangeClient: {e}")
        exchange_client = None
    
    @login_manager.user_loader
    def load_user(user_id):
        """Загрузка пользователя для Flask-Login"""
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == int(user_id)).first()
            return user
        finally:
            db.close()
    
    def async_route(f):
        """Декоратор для async маршрутов"""
        @wraps(f)
        def wrapper(*args, **kwargs):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(f(*args, **kwargs))
            finally:
                loop.close()
        return wrapper
    
    # ===== МАРШРУТЫ =====
    
    @app.route('/')
    def index():
        """Перенаправление на дашборд или логин"""
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return redirect(url_for('login'))
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """Страница входа"""
        if request.method == 'POST':
            data = request.get_json() if request.is_json else request.form
            username = data.get('username')
            password = data.get('password')
            
            db = SessionLocal()
            try:
                user = db.query(User).filter(User.username == username).first()
                
                if user and user.check_password(password):
                    # Проверяем блокировку
                    if user.is_blocked:
                        return jsonify({
                            'success': False,
                            'message': 'Аккаунт заблокирован. Обратитесь к администратору.'
                        }), 403
                    
                    # Успешный вход
                    login_user(user, remember=True)
                    user.last_login = datetime.utcnow()
                    user.failed_login_attempts = 0
                    db.commit()
                    
                    return jsonify({
                        'success': True,
                        'redirect': url_for('dashboard')
                    })
                else:
                    # Неудачная попытка
                    if user:
                        user.failed_login_attempts += 1
                        if user.failed_login_attempts >= 5:
                            user.is_blocked = True
                            user.blocked_at = datetime.utcnow()
                        db.commit()
                    
                    return jsonify({
                        'success': False,
                        'message': 'Неверное имя пользователя или пароль'
                    }), 401
                    
            finally:
                db.close()
        
        return render_template('login.html')
    
    @app.route('/logout')
    @login_required
    def logout():
        """Выход из системы"""
        logout_user()
        return redirect(url_for('login'))
    
    @app.route('/dashboard')
    @login_required
    def dashboard():
        """Главная страница дашборда"""
        db = SessionLocal()
        try:
            # Получаем статистику
            total_trades = db.query(Trade).count()
            active_trades = db.query(Trade).filter(
                Trade.status == TradeStatus.OPEN
            ).count()
            
            # Последние сделки
            recent_trades = db.query(Trade).order_by(
                Trade.created_at.desc()
            ).limit(10).all()
            
            # Статус бота
            bot_status = False
            if bot_manager:
                status = bot_manager.get_status()
                bot_status = status.get('is_running', False)
            
            return render_template('dashboard.html',
                total_trades=total_trades,
                active_trades=active_trades,
                recent_trades=recent_trades,
                bot_status=bot_status
            )
        finally:
            db.close()
    
    @app.route('/charts')
    @login_required
    def charts():
        """Страница с графиками"""
        return render_template('charts.html')
    
    @app.route('/analytics')
    @login_required
    def analytics():
        """Страница аналитики"""
        return render_template('analytics.html')
    
    @app.route('/news')
    @login_required
    def news():
        """Страница новостей"""
        return render_template('news.html')
    
    @app.route('/settings')
    @login_required
    def settings():
        """Страница настроек"""
        return render_template('settings.html')
    
    # ===== API ENDPOINTS =====
    
    @app.route('/api/status')
    @login_required
    def api_status():
        """Получить статус системы"""
        status = {
            'bot': {
                'running': False,
                'status': 'stopped'
            },
            'exchange': {
                'connected': False
            },
            'database': {
                'connected': True
            }
        }
        
        # Статус бота
        if bot_manager:
            bot_status = bot_manager.get_status()
            status['bot'] = bot_status
        
        # Статус биржи
        if exchange_client:
            status['exchange']['connected'] = True
        
        return jsonify(status)
    
    @app.route('/api/bot/start', methods=['POST'])
    @login_required
    @async_route
    async def start_bot():
        """Запустить бота"""
        if not bot_manager:
            return jsonify({
                'success': False,
                'message': 'Bot manager не инициализирован'
            }), 500
        
        try:
            await bot_manager.start()
            
            # Отправляем обновление через WebSocket
            socketio.emit('bot_status', {
                'status': 'running',
                'message': 'Бот запущен'
            })
            
            return jsonify({
                'success': True,
                'message': 'Бот успешно запущен'
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
        if not bot_manager:
            return jsonify({
                'success': False,
                'message': 'Bot manager не инициализирован'
            }), 500
        
        try:
            await bot_manager.stop()
            
            # Отправляем обновление через WebSocket
            socketio.emit('bot_status', {
                'status': 'stopped',
                'message': 'Бот остановлен'
            })
            
            return jsonify({
                'success': True,
                'message': 'Бот успешно остановлен'
            })
        except Exception as e:
            logger.error(f"Ошибка остановки бота: {e}")
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500
    
    @app.route('/api/balance')
    @login_required
    @async_route
    async def get_balance():
        """Получить баланс"""
        try:
            if not exchange_client:
                # Возвращаем тестовые данные
                return jsonify({
                    'total_usdt': 1000.0,
                    'available_usdt': 950.0,
                    'in_positions': 50.0,
                    'pnl_today': 12.5,
                    'pnl_percent': 1.25
                })
            
            balance = await exchange_client.get_account_balance()
            
            return jsonify({
                'total_usdt': float(balance.get('totalWalletBalance', 0)),
                'available_usdt': float(balance.get('availableBalance', 0)),
                'in_positions': float(balance.get('totalPositionValue', 0)),
                'pnl_today': float(balance.get('totalUnrealizedProfit', 0)),
                'pnl_percent': 0
            })
            
        except Exception as e:
            logger.error(f"Ошибка получения баланса: {e}")
            return jsonify({
                'error': str(e)
            }), 500
    
    @app.route('/api/trades')
    @login_required
    def get_trades():
        """Получить список сделок"""
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        db = SessionLocal()
        try:
            # Получаем сделки с пагинацией
            trades_query = db.query(Trade).order_by(Trade.created_at.desc())
            total = trades_query.count()
            
            trades = trades_query.offset((page - 1) * per_page).limit(per_page).all()
            
            return jsonify({
                'trades': [trade_to_dict(trade) for trade in trades],
                'total': total,
                'page': page,
                'per_page': per_page,
                'pages': (total + per_page - 1) // per_page
            })
        finally:
            db.close()
    
    @app.route('/api/signals')
    @login_required
    def get_signals():
        """Получить последние сигналы"""
        db = SessionLocal()
        try:
            signals = db.query(Signal).order_by(
                Signal.created_at.desc()
            ).limit(50).all()
            
            return jsonify({
                'signals': [signal_to_dict(signal) for signal in signals]
            })
        finally:
            db.close()
    
    @app.route('/api/analytics/summary')
    @login_required
    def get_analytics_summary():
        """Получить сводку аналитики"""
        db = SessionLocal()
        try:
            # Период анализа - последние 30 дней
            start_date = datetime.utcnow() - timedelta(days=30)
            
            # Статистика по сделкам
            trades = db.query(Trade).filter(
                Trade.created_at >= start_date,
                Trade.status == TradeStatus.CLOSED
            ).all()
            
            total_trades = len(trades)
            profitable_trades = len([t for t in trades if t.profit and t.profit > 0])
            total_profit = sum(t.profit or 0 for t in trades)
            
            # Статистика по стратегиям
            strategy_stats = {}
            for trade in trades:
                if trade.strategy:
                    if trade.strategy not in strategy_stats:
                        strategy_stats[trade.strategy] = {
                            'trades': 0,
                            'profit': 0,
                            'wins': 0
                        }
                    strategy_stats[trade.strategy]['trades'] += 1
                    strategy_stats[trade.strategy]['profit'] += trade.profit or 0
                    if trade.profit and trade.profit > 0:
                        strategy_stats[trade.strategy]['wins'] += 1
            
            return jsonify({
                'period_days': 30,
                'total_trades': total_trades,
                'profitable_trades': profitable_trades,
                'win_rate': round(profitable_trades / total_trades * 100, 2) if total_trades > 0 else 0,
                'total_profit': round(total_profit, 2),
                'strategies': strategy_stats
            })
        finally:
            db.close()
    
    # ===== WebSocket HANDLERS =====
    
    @socketio.on('connect')
    def handle_connect(auth=None):  # ИСПРАВЛЕНО: добавлен параметр auth
        """Обработка подключения WebSocket"""
        logger.info(f"WebSocket подключен: {request.sid}")
        ws_clients.add(request.sid)
        
        # Отправляем текущий статус
        if bot_manager:
            try:
                status = bot_manager.get_status()
                emit('bot_status', status)
            except Exception as e:
                logger.error(f"Ошибка получения статуса: {e}")
                emit('bot_status', {
                    'status': 'error',
                    'is_running': False,
                    'error': str(e)
                })
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Обработка отключения WebSocket"""
        logger.info(f"WebSocket отключен: {request.sid}")
        ws_clients.discard(request.sid)
    
    @socketio.on('get_status')
    def handle_get_status():
        """Получение статуса системы через WebSocket"""
        try:
            if bot_manager:
                status = bot_manager.get_status()
                emit('bot_status', status)
            else:
                emit('bot_status', {
                    'status': 'error',
                    'is_running': False,
                    'error': 'Bot manager не инициализирован'
                })
        except Exception as e:
            logger.error(f"Ошибка получения статуса: {e}")
            emit('bot_status', {
                'status': 'error',
                'is_running': False,
                'error': str(e)
            })
    
    @socketio.on('subscribe_updates')
    def handle_subscribe(data):
        """Подписка на обновления"""
        update_type = data.get('type', 'all')
        logger.info(f"Подписка на обновления: {update_type}")
        # Здесь можно реализовать логику подписок
    
    # ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====
    
    def trade_to_dict(trade: Trade) -> Dict[str, Any]:
        """Преобразование Trade в словарь"""
        return {
            'id': trade.id,
            'symbol': trade.symbol,
            'side': trade.side.value if trade.side else 'unknown',
            'entry_price': float(trade.entry_price) if trade.entry_price else 0,
            'exit_price': float(trade.exit_price) if trade.exit_price else 0,
            'quantity': float(trade.quantity) if trade.quantity else 0,
            'profit': float(trade.profit) if trade.profit else 0,
            'profit_percent': float(trade.profit_percent) if trade.profit_percent else 0,
            'status': trade.status.value if trade.status else 'unknown',
            'strategy': trade.strategy,
            'created_at': trade.created_at.isoformat() if trade.created_at else None,
            'closed_at': trade.closed_at.isoformat() if trade.closed_at else None
        }
    
    def signal_to_dict(signal: Signal) -> Dict[str, Any]:
        """Преобразование Signal в словарь"""
        return {
            'id': signal.id,
            'symbol': signal.symbol,
            'action': signal.action.value if signal.action else 'unknown',
            'price': float(signal.price) if signal.price else 0,
            'confidence': float(signal.confidence) if signal.confidence else 0,
            'strategy': signal.strategy,
            'indicators': signal.indicators,
            'created_at': signal.created_at.isoformat() if signal.created_at else None
        }
    
    # ===== ERROR HANDLERS =====
    
    @app.errorhandler(404)
    def not_found_error(error):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Endpoint not found'}), 404
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal error: {error}")
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Internal server error'}), 500
        return render_template('500.html'), 500
    
    @app.before_request
    def before_request():
        """Перед каждым запросом"""
        # Обновляем сессию
        session.permanent = True
        app.permanent_session_lifetime = timedelta(hours=24)
    
    return app, socketio

# Экспортируем функцию создания приложения
__all__ = ['create_app']