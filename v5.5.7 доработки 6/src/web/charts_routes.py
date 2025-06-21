"""
API роуты для графиков и данных торгового бота - ИСПРАВЛЕННАЯ ВЕРСИЯ
Файл: src/web/charts_routes.py

🎯 ИСПРАВЛЕНИЯ:
✅ Правильные импорты моделей из core
✅ Безопасный импорт с try/except
✅ Fallback для отсутствующих компонентов
✅ Полная совместимость с существующим кодом
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from flask import jsonify, request
from functools import wraps

# ИСПРАВЛЕННЫЕ ИМПОРТЫ - используем core.models
try:
    from ..core.models import Trade, Signal, Balance, TradingPair, Candle, TradeStatus, OrderSide
    from ..core.database import SessionLocal
    from ..core.config import config
    CORE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Не удалось импортировать core модули: {e}")
    # Fallback если импорты не работают
    SessionLocal = None
    Trade = Signal = Balance = TradingPair = Candle = None
    TradeStatus = OrderSide = None
    config = None
    CORE_AVAILABLE = False

logger = logging.getLogger(__name__)

def login_required(f):
    """Декоратор для проверки авторизации"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Упрощенная проверка авторизации для разработки
        # В production добавить полную проверку JWT токенов
        auth_header = request.headers.get('Authorization', '')
        if not auth_header and not request.cookies.get('session'):
            return jsonify({
                'success': False,
                'error': 'Authorization required'
            }), 401
        return f(*args, **kwargs)
    return decorated_function

def get_balance_from_db():
    """Получает баланс из базы данных"""
    try:
        if not CORE_AVAILABLE or not SessionLocal or not Balance:
            raise ImportError("Core модули недоступны")
            
        from sqlalchemy import desc
        
        db = SessionLocal()
        try:
            # Получаем последний баланс USDT
            latest_balance = db.query(Balance).filter(
                Balance.asset == 'USDT'
            ).order_by(desc(Balance.updated_at)).first()
            
            if latest_balance:
                return {
                    'total_usdt': float(latest_balance.total),
                    'available_usdt': float(latest_balance.free),
                    'in_positions': float(latest_balance.locked or 0),
                    'pnl_today': 0.0,  # Можно рассчитать из сделок
                    'pnl_percent': 0.0,
                    'source': 'database'
                }
            else:
                # Если нет записей, возвращаем тестовые данные
                return {
                    'total_usdt': 1000.0,
                    'available_usdt': 950.0,
                    'in_positions': 50.0,
                    'pnl_today': 25.50,
                    'pnl_percent': 2.5,
                    'source': 'demo'
                }
        finally:
            db.close()
            
    except Exception as e:
        logger.warning(f"Ошибка получения баланса из БД: {e}")
        # Возвращаем тестовые данные при ошибке
        return {
            'total_usdt': 1000.0,
            'available_usdt': 950.0,
            'in_positions': 50.0,
            'pnl_today': 25.50,
            'pnl_percent': 2.5,
            'source': 'demo_fallback'
        }

def register_chart_routes(app, bot_manager=None, exchange_client=None):
    """
    Регистрирует все API роуты для графиков и данных
    
    Args:
        app: Flask приложение
        bot_manager: Менеджер торгового бота
        exchange_client: Клиент биржи
    """
    
    logger.info("🔄 Регистрация API роутов для графиков...")
    
    # =================================================================
    # БАЗОВЫЕ API ENDPOINTS
    # =================================================================
    
    @app.route('/api/balance')
    def get_balance_simple():
        """Простой API для получения баланса (без авторизации для тестирования)"""
        try:
            if bot_manager and hasattr(bot_manager, 'get_balance'):
                balance_data = bot_manager.get_balance()
                return jsonify({
                    'success': True,
                    'balance': balance_data,
                    'timestamp': datetime.utcnow().isoformat()
                })
            else:
                # Используем функцию получения баланса из БД
                balance_data = get_balance_from_db()
                return jsonify({
                    'success': True,
                    'balance': balance_data,
                    'timestamp': datetime.utcnow().isoformat()
                })
                
        except Exception as e:
            logger.error(f"Ошибка API баланса: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/charts/balance')
    @login_required
    def get_balance_detailed():
        """Детальный API баланса с авторизацией"""
        try:
            balance_data = get_balance_from_db()
            
            # Добавляем дополнительную аналитику
            balance_data.update({
                'last_updated': datetime.utcnow().isoformat(),
                'risk_level': 'medium',
                'margin_ratio': 0.85,
                'free_margin': balance_data.get('available_usdt', 0)
            })
            
            return jsonify({
                'success': True,
                'balance': balance_data
            })
            
        except Exception as e:
            logger.error(f"Ошибка детального API баланса: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # =================================================================
    # TRADES И ПОЗИЦИИ
    # =================================================================
    
    @app.route('/api/charts/trades')
    @login_required
    def get_trades_api():
        """API для получения сделок"""
        try:
            if not CORE_AVAILABLE or not Trade or not SessionLocal:
                # Возвращаем демо данные если БД недоступна
                return _get_demo_trades()
            
            from sqlalchemy import desc
            
            limit = request.args.get('limit', 50, type=int)
            
            db = SessionLocal()
            try:
                trades = db.query(Trade).order_by(desc(Trade.created_at)).limit(limit).all()
                
                trades_data = []
                for trade in trades:
                    # Безопасное извлечение значений enum
                    side_value = trade.side.value if hasattr(trade.side, 'value') else str(trade.side)
                    status_value = trade.status.value if hasattr(trade.status, 'value') else str(trade.status)
                    
                    trades_data.append({
                        'id': trade.id,
                        'symbol': trade.symbol,
                        'side': side_value,
                        'entry_price': float(trade.price) if trade.price else 0,
                        'exit_price': float(trade.close_price) if trade.close_price else None,
                        'quantity': float(trade.quantity) if trade.quantity else 0,
                        'profit': float(trade.profit_loss) if trade.profit_loss else 0,
                        'profit_percent': float(trade.profit_loss_percent) if trade.profit_loss_percent else 0,
                        'status': status_value,
                        'strategy': trade.strategy,
                        'created_at': trade.created_at.isoformat() if trade.created_at else None,
                        'closed_at': trade.close_time.isoformat() if trade.close_time else None
                    })
                
                return jsonify({
                    'success': True,
                    'trades': trades_data,
                    'total': len(trades_data)
                })
                
            finally:
                db.close()
            
        except Exception as e:
            logger.error(f"Ошибка API сделок: {e}")
            return _get_demo_trades()
    
    def _get_demo_trades():
        """Возвращает демо сделки при ошибках"""
        demo_trades = [
            {
                'id': 1,
                'symbol': 'BTCUSDT',
                'side': 'BUY',
                'entry_price': 67500.0,
                'exit_price': 68200.0,
                'quantity': 0.01,
                'profit': 7.0,
                'profit_percent': 1.04,
                'status': 'CLOSED',
                'strategy': 'multi_indicator',
                'created_at': (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                'closed_at': (datetime.utcnow() - timedelta(hours=1)).isoformat()
            },
            {
                'id': 2,
                'symbol': 'ETHUSDT',
                'side': 'SELL',
                'entry_price': 3800.0,
                'exit_price': 3750.0,
                'quantity': 0.1,
                'profit': 5.0,
                'profit_percent': 1.32,
                'status': 'CLOSED',
                'strategy': 'momentum',
                'created_at': (datetime.utcnow() - timedelta(hours=4)).isoformat(),
                'closed_at': (datetime.utcnow() - timedelta(hours=3)).isoformat()
            }
        ]
        
        return jsonify({
            'success': True,
            'trades': demo_trades,
            'total': len(demo_trades),
            'source': 'demo'
        })
    
    # =================================================================
    # SIGNALS И СТРАТЕГИИ
    # =================================================================
    
    @app.route('/api/charts/signals')
    @login_required
    def get_signals_api():
        """API для получения торговых сигналов"""
        try:
            limit = int(request.args.get('limit', 20))
            symbol = request.args.get('symbol', '')
            
            if CORE_AVAILABLE and Signal and SessionLocal:
                # Получаем реальные сигналы из БД
                db = SessionLocal()
                try:
                    query = db.query(Signal)
                    
                    if symbol:
                        query = query.filter(Signal.symbol == symbol)
                    
                    signals = query.order_by(Signal.created_at.desc())\
                                  .limit(limit)\
                                  .all()
                    
                    signals_data = []
                    for signal in signals:
                        # Безопасное извлечение enum значений
                        signal_type = signal.signal_type.value if hasattr(signal.signal_type, 'value') else str(signal.signal_type)
                        action = signal.action.value if hasattr(signal.action, 'value') else str(signal.action)
                        
                        signals_data.append({
                            'id': signal.id,
                            'symbol': signal.symbol,
                            'type': signal_type,
                            'action': action,
                            'confidence': float(signal.confidence) if signal.confidence else 0,
                            'price': float(signal.price) if signal.price else 0,
                            'strategy': signal.strategy,
                            'created_at': signal.created_at.isoformat() if signal.created_at else None
                        })
                    
                    return jsonify({
                        'success': True,
                        'signals': signals_data,
                        'count': len(signals_data)
                    })
                    
                finally:
                    db.close()
            else:
                # Демо сигналы
                demo_signals = [
                    {
                        'id': 1,
                        'symbol': 'BTCUSDT',
                        'type': 'BUY',
                        'action': 'ENTRY',
                        'confidence': 0.75,
                        'price': 67650.0,
                        'strategy': 'multi_indicator',
                        'created_at': datetime.utcnow().isoformat()
                    },
                    {
                        'id': 2,
                        'symbol': 'ETHUSDT',
                        'type': 'SELL',
                        'action': 'EXIT',
                        'confidence': 0.68,
                        'price': 3795.0,
                        'strategy': 'momentum',
                        'created_at': (datetime.utcnow() - timedelta(minutes=15)).isoformat()
                    }
                ]
                
                return jsonify({
                    'success': True,
                    'signals': demo_signals,
                    'count': len(demo_signals),
                    'source': 'demo'
                })
                
        except Exception as e:
            logger.error(f"Ошибка API сигналов: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # =================================================================
    # СТАТИСТИКА И МОНИТОРИНГ
    # =================================================================
    
    @app.route('/api/charts/stats')
    @login_required
    def get_stats_api():
        """API для получения статистики бота"""
        try:
            if bot_manager and hasattr(bot_manager, 'get_status'):
                # Получаем реальную статистику от бота
                status = bot_manager.get_status()
                
                return jsonify({
                    'success': True,
                    'active_pairs': len(status.get('active_pairs', [])),
                    'open_positions': status.get('open_positions', 0),
                    'trades_today': status.get('trades_today', 0),
                    'cycles_completed': status.get('cycle_count', 0),
                    'uptime': status.get('uptime_seconds', 0),
                    'bot_status': status.get('status', 'unknown'),
                    'start_time': status.get('start_time', datetime.utcnow()).isoformat(),
                    'daily_pnl': status.get('daily_pnl', 0.0),
                    'win_rate': status.get('win_rate', 0.0),
                    'total_trades': status.get('total_trades', 0),
                    'source': 'real'
                })
            else:
                # Демо статистика
                return jsonify({
                    'success': True,
                    'active_pairs': 3,
                    'open_positions': 2,
                    'trades_today': 8,
                    'cycles_completed': 145,
                    'uptime': 7200,  # 2 часа в секундах
                    'bot_status': 'running',
                    'start_time': (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                    'daily_pnl': 15.75,
                    'win_rate': 67.5,
                    'total_trades': 24,
                    'source': 'demo'
                })
                
        except Exception as e:
            logger.error(f"Ошибка получения статистики: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # =================================================================
    # ТЕХНИЧЕСКИЕ ИНДИКАТОРЫ
    # =================================================================
    
    @app.route('/api/charts/indicators/<symbol>')
    @login_required
    def get_indicators_api(symbol):
        """API для получения технических индикаторов"""
        try:
            # В будущем можно подключить реальные расчеты от бота
            # Пока возвращаем демо индикаторы
            
            return jsonify({
                'success': True,
                'symbol': symbol,
                'rsi': 65.3,
                'macd': {
                    'histogram': 0.15,
                    'signal': 'bullish'
                },
                'sma_20': 67650.0,
                'sma_50': 67200.0,
                'bollinger_bands': {
                    'upper': 68200.0,
                    'middle': 67800.0,
                    'lower': 67400.0
                },
                'volume_sma': 1200000,
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Ошибка получения индикаторов для {symbol}: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # =================================================================
    # СВЕЧНЫЕ ДАННЫЕ
    # =================================================================
    
    @app.route('/api/charts/candles/<symbol>')
    def get_candles_api(symbol):
        """API для получения свечных данных"""
        try:
            timeframe = request.args.get('timeframe', '1h')
            limit = int(request.args.get('limit', 100))
            
            # Генерируем демо свечи (в реальности брать с биржи)
            candles = []
            base_price = 67800.0
            
            for i in range(limit):
                timestamp = datetime.utcnow() - timedelta(hours=limit-i)
                
                # Простая симуляция движения цены
                price_change = (i % 10 - 5) * 50
                open_price = base_price + price_change
                close_price = open_price + ((i % 7) - 3) * 30
                high_price = max(open_price, close_price) + abs((i % 3)) * 20
                low_price = min(open_price, close_price) - abs((i % 4)) * 15
                
                candles.append({
                    'timestamp': int(timestamp.timestamp() * 1000),
                    'open': round(open_price, 2),
                    'high': round(high_price, 2),
                    'low': round(low_price, 2),
                    'close': round(close_price, 2),
                    'volume': round(1000000 + (i % 5) * 200000)
                })
            
            return jsonify({
                'success': True,
                'symbol': symbol,
                'timeframe': timeframe,
                'candles': candles,
                'source': 'demo'
            })
                
        except Exception as e:
            logger.error(f"Ошибка получения свечей для {symbol}: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # =================================================================
    # ТОРГОВЫЕ ПАРЫ
    # =================================================================
    
    @app.route('/api/charts/pairs')
    def get_trading_pairs():
        """Получить список торговых пар"""
        try:
            if bot_manager and hasattr(bot_manager, 'get_status'):
                status = bot_manager.get_status()
                pairs = status.get('active_pairs', [])
                
                # Добавляем информацию о ценах
                pairs_data = []
                for pair in pairs:
                    pairs_data.append({
                        'symbol': pair,
                        'base': pair.replace('USDT', '').replace('BUSD', ''),
                        'quote': 'USDT',
                        'status': 'active'
                    })
                
                return jsonify({
                    'success': True,
                    'pairs': pairs_data,
                    'count': len(pairs_data)
                })
            else:
                # Демо пары
                demo_pairs = [
                    {'symbol': 'BTCUSDT', 'base': 'BTC', 'quote': 'USDT', 'status': 'active'},
                    {'symbol': 'ETHUSDT', 'base': 'ETH', 'quote': 'USDT', 'status': 'active'},
                    {'symbol': 'ADAUSDT', 'base': 'ADA', 'quote': 'USDT', 'status': 'active'}
                ]
                
                return jsonify({
                    'success': True,
                    'pairs': demo_pairs,
                    'count': len(demo_pairs),
                    'source': 'demo'
                })
                
        except Exception as e:
            logger.error(f"Ошибка получения торговых пар: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    logger.info("✅ Роуты для графиков зарегистрированы:")
    logger.info("   🟢 GET /api/balance - простой баланс (без авторизации)")
    logger.info("   🟢 GET /api/charts/balance - детальный баланс (с авторизацией)")
    logger.info("   🟢 GET /api/charts/trades - сделки")
    logger.info("   🟢 GET /api/charts/signals - торговые сигналы")
    logger.info("   🟢 GET /api/charts/stats - статистика")
    logger.info("   🟢 GET /api/charts/indicators/<symbol> - технические индикаторы")
    logger.info("   🟢 GET /api/charts/candles/<symbol> - свечные данные")
    logger.info("   🟢 GET /api/charts/pairs - торговые пары")
    
    return True