"""
API роуты для графиков и данных торговли - ИСПРАВЛЕННАЯ ВЕРСИЯ
Файл: src/web/charts_routes.py

ИСПРАВЛЕНИЯ:
✅ Функция get_trading_pairs переименована в get_chart_trading_pairs
✅ Убраны дублирования с trading_api.py
✅ Четкое разделение функций для графиков
✅ Уникальные имена всех функций
"""

from flask import jsonify, request
from flask_login import login_required
from datetime import datetime, timedelta
import logging
import random
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

# Проверяем доступность core модулей
try:
    from ..core.database import SessionLocal
    from ..core.models import Trade, Balance, TradeStatus
    from sqlalchemy import desc
    CORE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Core модули недоступны: {e}")
    CORE_AVAILABLE = False
    SessionLocal = None
    Trade = None
    Balance = None
    TradeStatus = None


def get_balance_from_db():
    """Получает баланс из базы данных"""
    try:
        if not CORE_AVAILABLE or not Balance or not SessionLocal:
            return {
                'total_usdt': 1000.0,
                'available_usdt': 950.0,
                'in_positions': 50.0,
                'pnl_today': 25.50,
                'pnl_percent': 2.5,
                'source': 'demo_no_db'
            }
        
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
    def get_chart_balance_simple():
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
    def get_chart_balance_detailed():
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
    
    @app.route('/api/charts/trades')
    @login_required
    def get_chart_trades_api():
        """API для получения сделок для графиков"""
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
            logger.error(f"Ошибка API сделок для графиков: {e}")
            return _get_demo_trades()
    
    # =================================================================
    # СТАТИСТИКА И АНАЛИТИКА
    # =================================================================
    
    @app.route('/api/charts/stats')
    @login_required
    def get_chart_stats_api():
        """API для получения статистики"""
        try:
            if bot_manager:
                status = bot_manager.get_status()
                
                return jsonify({
                    'success': True,
                    'active_pairs': len(status.get('active_pairs', [])),
                    'open_positions': status.get('open_positions', 0),
                    'trades_today': status.get('trades_today', 0),
                    'cycles_completed': status.get('cycles_completed', 0),
                    'uptime': status.get('uptime', 0),
                    'bot_status': status.get('status', 'stopped'),
                    'start_time': status.get('start_time')
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
                    'source': 'demo'
                })
                
        except Exception as e:
            logger.error(f"Ошибка получения статистики: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/charts/indicators/<symbol>')
    @login_required
    def get_chart_indicators_api(symbol):
        """API для получения технических индикаторов"""
        try:
            # Пока возвращаем демо индикаторы
            # В будущем можно подключить реальные расчеты
            
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
    # ТОРГОВЫЕ ПАРЫ (ПЕРЕИМЕНОВАННАЯ ФУНКЦИЯ)
    # =================================================================
    
    @app.route('/api/charts/pairs')
    def get_chart_trading_pairs():
        """
        ПЕРЕИМЕНОВАННАЯ ФУНКЦИЯ: Получить список торговых пар для графиков
        (была get_trading_pairs - конфликтовала с trading_api.py)
        """
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
            logger.error(f"Ошибка получения торговых пар для графиков: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # =================================================================
    # РЫНОЧНЫЕ ДАННЫЕ
    # =================================================================
    
    @app.route('/api/charts/price/<symbol>')
    def get_chart_current_price(symbol):
        """Получить текущую цену валюты для графиков"""
        try:
            if exchange_client:
                import asyncio
                try:
                    # Получаем тикер с биржи
                    ticker = asyncio.run(exchange_client.fetch_ticker(symbol))
                    
                    return jsonify({
                        'success': True,
                        'symbol': symbol,
                        'price': float(ticker.get('last', 0)),
                        'bid': float(ticker.get('bid', 0)),
                        'ask': float(ticker.get('ask', 0)),
                        'volume': float(ticker.get('baseVolume', 0)),
                        'change_24h': float(ticker.get('percentage', 0)),
                        'high_24h': float(ticker.get('high', 0)),
                        'low_24h': float(ticker.get('low', 0)),
                        'source': 'exchange',
                        'timestamp': datetime.utcnow().isoformat()
                    })
                except Exception as api_error:
                    logger.warning(f"Ошибка API биржи для {symbol}: {api_error}")
                    # Возвращаем демо данные при ошибке API
                    pass
            
            # Демо данные
            base_prices = {
                'BTCUSDT': 67800.0,
                'ETHUSDT': 3450.0,
                'BNBUSDT': 625.0,
                'SOLUSDT': 145.0,
                'ADAUSDT': 1.45
            }
            
            base_price = base_prices.get(symbol, 1.0)
            price_change = random.uniform(-0.01, 0.01)
            
            return jsonify({
                'success': True,
                'symbol': symbol,
                'price': round(base_price * (1 + price_change), 2),
                'bid': round(base_price * (1 + price_change - 0.001), 2),
                'ask': round(base_price * (1 + price_change + 0.001), 2),
                'volume': random.randint(10000, 50000),
                'change_24h': round(random.uniform(-5.0, 5.0), 2),
                'high_24h': round(base_price * 1.05, 2),
                'low_24h': round(base_price * 0.95, 2),
                'source': 'demo',
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Ошибка получения цены {symbol}: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/charts/candles/<symbol>')
    def get_chart_candles(symbol):
        """Получить свечные данные для графиков"""
        try:
            # Параметры
            timeframe = request.args.get('timeframe', '1h')
            limit = min(request.args.get('limit', 100, type=int), 500)
            
            if exchange_client:
                import asyncio
                try:
                    # Получаем свечи с биржи
                    ohlcv = asyncio.run(exchange_client.fetch_ohlcv(symbol, timeframe, limit=limit))
                    
                    candles = []
                    for kline in ohlcv:
                        candles.append({
                            'timestamp': kline[0],
                            'open': float(kline[1]),
                            'high': float(kline[2]),
                            'low': float(kline[3]),
                            'close': float(kline[4]),
                            'volume': float(kline[5])
                        })
                    
                    return jsonify({
                        'success': True,
                        'symbol': symbol,
                        'timeframe': timeframe,
                        'candles': candles,
                        'count': len(candles),
                        'source': 'exchange'
                    })
                except Exception as api_error:
                    logger.warning(f"Ошибка API свечей для {symbol}: {api_error}")
                    # Возвращаем демо данные при ошибке
                    pass
            
            # Генерируем демо свечи
            base_price = 67800.0 if symbol == 'BTCUSDT' else 3450.0
            candles = []
            
            for i in range(limit):
                timestamp = int((datetime.utcnow() - timedelta(hours=limit-i)).timestamp() * 1000)
                price_change = random.uniform(-0.02, 0.02)
                current_price = base_price * (1 + price_change)
                
                candle_range = current_price * 0.01  # 1% диапазон свечи
                open_price = current_price + random.uniform(-candle_range/2, candle_range/2)
                close_price = current_price + random.uniform(-candle_range/2, candle_range/2)
                high_price = max(open_price, close_price) + random.uniform(0, candle_range/4)
                low_price = min(open_price, close_price) - random.uniform(0, candle_range/4)
                
                candles.append({
                    'timestamp': timestamp,
                    'open': round(open_price, 2),
                    'high': round(high_price, 2),
                    'low': round(low_price, 2),
                    'close': round(close_price, 2),
                    'volume': random.randint(1000, 10000)
                })
            
            return jsonify({
                'success': True,
                'symbol': symbol,
                'timeframe': timeframe,
                'candles': candles,
                'count': len(candles),
                'source': 'demo'
            })
            
        except Exception as e:
            logger.error(f"Ошибка получения свечей для {symbol}: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/charts/tickers')
    def get_chart_all_tickers():
        """Получить данные по всем торговым парам для графиков"""
        try:
            symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT']
            tickers = {}
            
            for symbol in symbols:
                if exchange_client:
                    try:
                        import asyncio
                        ticker = asyncio.run(exchange_client.fetch_ticker(symbol))
                        tickers[symbol] = {
                            'price': float(ticker.get('last', 0)),
                            'change_24h': float(ticker.get('percentage', 0)),
                            'volume': float(ticker.get('baseVolume', 0))
                        }
                        continue
                    except:
                        pass
                
                # Демо данные
                base_prices = {
                    'BTCUSDT': 67800.0,
                    'ETHUSDT': 3450.0,
                    'BNBUSDT': 625.0,
                    'SOLUSDT': 145.0
                }
                base_price = base_prices.get(symbol, 1.0)
                price_change = random.uniform(-0.01, 0.01)
                
                tickers[symbol] = {
                    'price': round(base_price * (1 + price_change), 2),
                    'change_24h': round(random.uniform(-5.0, 5.0), 2),
                    'volume': random.randint(10000, 50000)
                }
            
            return jsonify({
                'success': True,
                'tickers': tickers,
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Ошибка получения тикеров: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # =================================================================
    # ЛОГИРОВАНИЕ РЕЗУЛЬТАТОВ
    # =================================================================
    
    logger.info("✅ Роуты для графиков зарегистрированы:")
    logger.info("   🟢 GET /api/balance - простой баланс (без авторизации)")
    logger.info("   🟢 GET /api/charts/balance - детальный баланс (с авторизацией)")
    logger.info("   🟢 GET /api/charts/trades - сделки")
    logger.info("   🟢 GET /api/charts/stats - статистика")
    logger.info("   🟢 GET /api/charts/indicators/<symbol> - технические индикаторы")
    logger.info("   🟢 GET /api/charts/candles/<symbol> - свечные данные")
    logger.info("   🟢 GET /api/charts/pairs - торговые пары")
    logger.info("   🟢 GET /api/charts/price/<symbol> - текущая цена")
    logger.info("   🟢 GET /api/charts/tickers - все тикеры")
    
    return True

# Экспорт
__all__ = ['register_chart_routes']