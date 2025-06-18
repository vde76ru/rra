"""
Flask веб-приложение для Crypto Trading Bot - ПОЛНОСТЬЮ ИСПРАВЛЕННАЯ ВЕРСИЯ
Файл: src/web/app.py
"""
import os
from datetime import datetime
from flask import  Flask, render_template, jsonify, request, redirect, url_for, session, send_from_directory
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
from ..exchange.client import ExchangeClient

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

# Глобальные переменные - НЕ ИНИЦИАЛИЗИРУЕМ ЗДЕСЬ!
app = None
socketio = None
bot_manager = None
analytics_collector = None
exchange_client = None
chart_api = None


def create_app():
    """Создание и настройка Flask приложения"""
    global app, socketio, bot_manager, analytics_collector, exchange_client, chart_api
    
    app = Flask(__name__, 
                template_folder='templates',
                static_folder='static')
    
    # Конфигурация
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SESSION_TYPE'] = 'filesystem'
    
    # Инициализация SocketIO
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
    
    # Инициализация LoginManager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    
    # Инициализация компонентов
    bot_manager = BotManager()
    analytics_collector = AnalyticsCollector()
    exchange_client = ExchangeClient()
    
    # ИСПРАВЛЕНИЕ: Правильная инициализация ChartAPI с параметрами
    if CHART_API_AVAILABLE and ChartAPI:
        try:
            chart_api = ChartAPI(app, socketio, exchange_client)
            logger.info("✅ ChartAPI инициализирован")
        except Exception as e:
            logger.warning(f"⚠️ Не удалось инициализировать ChartAPI: {e}")
            chart_api = None
    
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
            """Безопасный декоратор для async функций в Flask"""
            try:
                return asyncio.run(f(*args, **kwargs))
            except Exception as e:
                logger.error(f"Ошибка в async_route: {e}", exc_info=True)
                return jsonify({
                    'success': False,
                    'message': f'Ошибка выполнения: {str(e)}'
                }), 500
        return wrapper
    
    # ====================
    # МАРШРУТЫ
    # ====================
    
    @app.route('/', endpoint='dashboard')
    @login_required
    def index():
        """Главная страница дашборда с данными для шаблона."""
        db = SessionLocal()
        try:
            # Собираем статистику (пример; вы можете здесь сделать более сложную логику)
            stats = {
                'total_trades': 0,
                'profitable_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0
            }
            # Если у бот-менеджера есть метод get_statistics, можно и так:
            # stats = bot_manager.get_statistics()

            # Активные позиции — предположим, что BotManager умеет их отдавать
            try:
                active_positions = bot_manager.get_active_positions()  # либо []
            except Exception:
                active_positions = []

            # Последние 10 сделок из БД
            try:
                recent_trades = db.query(Trade)\
                                  .order_by(Trade.created_at.desc())\
                                  .limit(10)\
                                  .all()
            except Exception:
                # если в схеме нет signal_id — просто не показываем истории
                recent_trades = []
                
        finally:
            db.close()

        status = bot_manager.get_status()
        bot_status = status.get('is_running', False) or status.get('running', False)

        return render_template(
            'dashboard.html',
            bot_status=bot_status,
            stats=stats,
            active_positions=active_positions,
            recent_trades=recent_trades
        )
    
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
    def api_status():
        """Получить статус системы"""
        try:
            status = bot_manager.get_status()
        except AttributeError as e:
            logger.error(f"❌ Ошибка получения статуса: {e}")
            status = { 'is_running': False, 'message': 'Status unavailable', 'active_pairs': [] }
        return jsonify(status)

    @app.route('/api/balance')
    @login_required
    def api_balance():
        """Получить баланс через ccxt (Bybit)."""
        result = { 'USDT': { 'total': 0, 'free': 0, 'used': 0 } }
        try:
            # если в BotManager есть exchange — ccxt.bybit()
            exch = getattr(bot_manager, 'exchange', None)
            if exch:
                # ccxt.fetch_balance() возвращает {'total': {...}, 'free': {...}, ...}
                bal = exch.fetch_balance()
                usdt = bal.get('total', {}).get('USDT', 0)
                free = bal.get('free', {}).get('USDT', 0)
                used = bal.get('used', {}).get('USDT', 0)
                result['USDT'] = {
                    'total': float(usdt),
                    'free': float(free),
                    'used': float(used)
                }
        except Exception as e:
            logger.error(f"❌ Ошибка получения баланса: {e}")
        return jsonify(result)
    
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
    
    # Роут /api/trades перенесен в ChartAPI для избежания конфликтов
    
    @app.route('/api/signals')
    @login_required
    def get_signals():
        """Получить список сигналов"""
        db = SessionLocal()
        try:
            signals = db.query(Signal)\
                       .order_by(Signal.created_at.desc())\
                       .limit(50)\
                       .all()
            
            # Создаём словари вручную, так как метода to_dict() нет
            signals_data = []
            for signal in signals:
                signal_dict = {
                    'id': signal.id,
                    'symbol': signal.symbol,
                    'strategy': signal.strategy,
                    'action': signal.action,
                    'price': float(signal.price) if signal.price else None,
                    'confidence': float(signal.confidence) if signal.confidence else 0.0,
                    'indicators': signal.indicators,
                    'reason': signal.reason,
                    'is_executed': bool(signal.is_executed),
                    'executed_at': signal.executed_at.isoformat() if signal.executed_at else None,
                    'created_at': signal.created_at.isoformat() if signal.created_at else None
                }
                signals_data.append(signal_dict)
            
            return jsonify({
                'success': True,
                'signals': signals_data,
                'count': len(signals_data)
            })
            
        except Exception as e:
            logger.error(f"Ошибка получения сигналов: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'message': 'Ошибка получения сигналов',
                'signals': []
            }), 500
        finally:
            db.close()
    
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
        """Обработчик ошибки 404"""
        try:
            return render_template('404.html'), 404
        except Exception:
            # Fallback на случай, если шаблон не найден
            return '''
            <!DOCTYPE html>
            <html>
            <head><title>404 - Страница не найдена</title></head>
            <body style="font-family: Arial; text-align: center; margin-top: 50px;">
                <h1>404 - Страница не найдена</h1>
                <p>Запрашиваемая страница не существует.</p>
                <a href="/">На главную</a>
            </body>
            </html>
            ''', 404
        
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Внутренняя ошибка сервера: {error}")
        return render_template('500.html'), 500
    
    @app.route('/favicon.ico')
    def favicon():
        """Маршрут для favicon"""
        return send_from_directory(
            os.path.join(app.root_path, 'static'),
            'favicon.ico',
            mimetype='image/vnd.microsoft.icon'
        )

    # === НОВЫЕ СТРАНИЦЫ ===

    @app.route('/charts', endpoint='charts')
    @login_required
    def charts():
        """Страница с графиками."""
        return render_template('charts.html')

    @app.route('/analytics', endpoint='analytics')
    @login_required
    def analytics():
        """Страница аналитики."""
        return render_template('analytics.html')

    @app.route('/news', endpoint='news')
    @login_required
    def news():
        """Страница новостей."""
        return render_template('news.html')

    return app, socketio


# НЕ создаем приложение при импорте!
# Это должно делаться явно через create_app()