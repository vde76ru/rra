# ========================================
# ФАЙЛ: src/web/charts_routes.py
# Новый файл с API для графиков
# ========================================

"""
API роуты для графиков и данных торговли
"""

from flask import jsonify, request
from flask_login import login_required
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


def register_chart_routes(app, bot_manager=None, exchange_client=None):
    """
    Регистрируем все роуты для графиков в Flask приложении
    
    Args:
        app: Flask приложение
        bot_manager: Менеджер бота (может быть None)
        exchange_client: Клиент биржи (может быть None)
    """
    
    @app.route('/api/charts/balance')
    def get_balance_api():
        """API для получения баланса"""
        try:
            # Если есть exchange_client, получаем реальные данные
            if exchange_client:
                import asyncio
                try:
                    balance = asyncio.run(exchange_client.fetch_balance())
                    usdt_balance = balance.get('USDT', {})
                    
                    return jsonify({
                        'success': True,
                        'total_usdt': float(usdt_balance.get('total', 0)),
                        'available_usdt': float(usdt_balance.get('free', 0)),
                        'in_positions': float(usdt_balance.get('used', 0)),
                        'pnl_today': 0,
                        'pnl_percent': 0,
                        'source': 'exchange'
                    })
                except Exception as e:
                    logger.warning(f"Не удалось получить баланс с биржи: {e}")
            
            # Если нет exchange_client или ошибка, возвращаем тестовые данные
            return jsonify({
                'success': True,
                'total_usdt': 1000.0,
                'available_usdt': 950.0,
                'in_positions': 50.0,
                'pnl_today': 25.50,
                'pnl_percent': 2.5,
                'source': 'demo'
            })
            
        except Exception as e:
            logger.error(f"Ошибка API баланса: {e}")
            return jsonify({
                'success': False,
                'error': str(e),
                'total_usdt': 0,
                'available_usdt': 0,
                'in_positions': 0,
                'pnl_today': 0,
                'pnl_percent': 0
            }), 500
    
    @app.route('/api/charts/trades')
    def get_trades_api():
        """API для получения сделок"""
        try:
            from ..core.database import SessionLocal
            from ..core.models import Trade, TradeStatus
            from sqlalchemy import desc
            
            limit = request.args.get('limit', 50, type=int)
            
            db = SessionLocal()
            try:
                trades = db.query(Trade).order_by(desc(Trade.created_at)).limit(limit).all()
                
                trades_data = []
                for trade in trades:
                    trades_data.append({
                        'id': trade.id,
                        'symbol': trade.symbol,
                        'side': trade.side.value if hasattr(trade.side, 'value') else str(trade.side),
                        'entry_price': float(trade.entry_price) if trade.entry_price else 0,
                        'exit_price': float(trade.exit_price) if trade.exit_price else None,
                        'quantity': float(trade.quantity) if trade.quantity else 0,
                        'profit': float(trade.profit) if trade.profit else 0,
                        'profit_percent': float(trade.profit_percent) if trade.profit_percent else 0,
                        'status': trade.status.value if hasattr(trade.status, 'value') else str(trade.status),
                        'strategy': trade.strategy,
                        'created_at': trade.created_at.isoformat() if trade.created_at else None,
                        'closed_at': trade.closed_at.isoformat() if trade.closed_at else None
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
            # Возвращаем демо данные при ошибке
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
                    'strategy': 'momentum',
                    'created_at': (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                    'closed_at': (datetime.utcnow() - timedelta(hours=1)).isoformat()
                },
                {
                    'id': 2,
                    'symbol': 'ETHUSDT',
                    'side': 'SELL',
                    'entry_price': 3420.0,
                    'exit_price': 3380.0,
                    'quantity': 0.1,
                    'profit': 4.0,
                    'profit_percent': 1.17,
                    'status': 'CLOSED',
                    'strategy': 'scalping',
                    'created_at': (datetime.utcnow() - timedelta(hours=1)).isoformat(),
                    'closed_at': (datetime.utcnow() - timedelta(minutes=30)).isoformat()
                }
            ]
            
            return jsonify({
                'success': True,
                'trades': demo_trades,
                'total': len(demo_trades),
                'source': 'demo'
            })
    
    @app.route('/api/charts/price/<symbol>')
    def get_price_api(symbol):
        """API для получения текущей цены"""
        try:
            if exchange_client:
                import asyncio
                ticker = asyncio.run(exchange_client.fetch_ticker(symbol))
                
                return jsonify({
                    'success': True,
                    'symbol': symbol,
                    'price': float(ticker['last']),
                    'change_24h': float(ticker.get('percentage', 0)),
                    'volume_24h': float(ticker.get('quoteVolume', 0)),
                    'high_24h': float(ticker.get('high', 0)),
                    'low_24h': float(ticker.get('low', 0)),
                    'timestamp': datetime.utcnow().isoformat()
                })
            else:
                # Демо данные
                demo_prices = {
                    'BTCUSDT': 67800.0,
                    'ETHUSDT': 3450.0,
                    'BNBUSDT': 640.0
                }
                
                return jsonify({
                    'success': True,
                    'symbol': symbol,
                    'price': demo_prices.get(symbol, 50000.0),
                    'change_24h': 2.5,
                    'volume_24h': 1500000000,
                    'high_24h': demo_prices.get(symbol, 50000.0) * 1.03,
                    'low_24h': demo_prices.get(symbol, 50000.0) * 0.97,
                    'timestamp': datetime.utcnow().isoformat(),
                    'source': 'demo'
                })
                
        except Exception as e:
            logger.error(f"Ошибка получения цены {symbol}: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/charts/candles/<symbol>')
    def get_candles_api(symbol):
        """API для получения свечных данных"""
        try:
            interval = request.args.get('interval', '1h')
            limit = request.args.get('limit', 100, type=int)
            
            if exchange_client:
                import asyncio
                try:
                    klines = asyncio.run(exchange_client.fetch_ohlcv(symbol, interval, limit))
                    
                    candles = []
                    for kline in klines:
                        candles.append({
                            'timestamp': int(kline[0]),
                            'open': float(kline[1]),
                            'high': float(kline[2]),
                            'low': float(kline[3]),
                            'close': float(kline[4]),
                            'volume': float(kline[5])
                        })
                    
                    return jsonify({
                        'success': True,
                        'symbol': symbol,
                        'interval': interval,
                        'candles': candles
                    })
                except Exception as e:
                    logger.warning(f"Не удалось получить свечи с биржи: {e}")
            
            # Генерируем демо данные
            now = datetime.utcnow()
            candles = []
            base_price = 67800.0 if symbol == 'BTCUSDT' else 3450.0
            
            for i in range(limit):
                timestamp = int((now - timedelta(hours=limit-i)).timestamp() * 1000)
                # Простая симуляция движения цены
                price_change = (i % 10 - 5) * 0.01
                open_price = base_price * (1 + price_change)
                high_price = open_price * 1.005
                low_price = open_price * 0.995
                close_price = open_price * (1 + (i % 3 - 1) * 0.003)
                
                candles.append({
                    'timestamp': timestamp,
                    'open': round(open_price, 2),
                    'high': round(high_price, 2),
                    'low': round(low_price, 2),
                    'close': round(close_price, 2),
                    'volume': 1000 + (i % 100) * 10
                })
            
            return jsonify({
                'success': True,
                'symbol': symbol,
                'interval': interval,
                'candles': candles,
                'source': 'demo'
            })
            
        except Exception as e:
            logger.error(f"Ошибка получения свечей для {symbol}: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/charts/stats')
    def get_stats_api():
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
    def get_indicators_api(symbol):
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
    
    logger.info("✅ Роуты для графиков зарегистрированы")
    return True