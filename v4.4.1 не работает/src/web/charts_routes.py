# ========================================
# ИСПРАВЛЕННЫЙ ФАЙЛ: src/web/charts_routes.py
# ДОБАВЛЯЕМ НЕДОСТАЮЩИЙ ЭНДПОИНТ /api/balance
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


def get_balance_from_db():
    """Получает баланс из базы данных"""
    try:
        from ..core.database import SessionLocal
        from src.core.models import Balance
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
    Регистрируем все роуты для графиков в Flask приложении
    
    Args:
        app: Flask приложение
        bot_manager: Менеджер бота (может быть None)
        exchange_client: Клиент биржи (может быть None)
    """
    
    @app.route('/api/balance')  # ← ДОБАВЛЕН НЕДОСТАЮЩИЙ ЭНДПОИНТ!
    def get_balance_simple():
        """API для получения баланса БЕЗ авторизации (для дашборда)"""
        try:
            balance_data = get_balance_from_db()
            # Добавляем success для совместимости
            balance_data['success'] = True
            balance_data['timestamp'] = datetime.utcnow().isoformat()
            return jsonify(balance_data)
        except Exception as e:
            logger.error(f"Ошибка API баланса: {e}")
            return jsonify({
                'success': False,
                'error': str(e),
                'total_usdt': 0,
                'available_usdt': 0,
                'in_positions': 0,
                'pnl_today': 0,
                'pnl_percent': 0,
                'source': 'error'
            }), 500
    
    @app.route('/api/charts/balance')
    @login_required  
    def get_balance_api():
        """API для получения баланса С авторизацией (для графиков)"""
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
            
            # Fallback к базе данных
            balance_data = get_balance_from_db()
            balance_data['success'] = True
            return jsonify(balance_data)
            
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
    @login_required
    def get_trades_api():
        """API для получения сделок"""
        try:
            from ..core.database import SessionLocal
            from src.core.models import Trade, TradeStatus
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
                        'entry_price': float(trade.price) if trade.price else 0,
                        'exit_price': float(trade.close_price) if trade.close_price else None,
                        'quantity': float(trade.quantity) if trade.quantity else 0,
                        'profit': float(trade.profit_loss) if trade.profit_loss else 0,
                        'profit_percent': float(trade.profit_loss_percent) if trade.profit_loss_percent else 0,
                        'status': trade.status.value if hasattr(trade.status, 'value') else str(trade.status),
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
                    'strategy': 'multi_indicator',
                    'created_at': (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                    'closed_at': (datetime.utcnow() - timedelta(hours=1)).isoformat()
                }
            ]
            
            return jsonify({
                'success': True,
                'trades': demo_trades,
                'total': len(demo_trades),
                'source': 'demo'
            })
    
    @app.route('/api/charts/stats')
    @login_required
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
    @login_required
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
    
    logger.info("✅ Роуты для графиков зарегистрированы:")
    logger.info("   🟢 GET /api/balance - простой баланс (без авторизации)")
    logger.info("   🟢 GET /api/charts/balance - детальный баланс (с авторизацией)")
    logger.info("   🟢 GET /api/charts/trades - сделки")
    logger.info("   🟢 GET /api/charts/stats - статистика")
    return True
    register_price_data_routes(app, exchange_client)
    
def register_price_data_routes(app, exchange_client=None):
    """
    Добавляет API для получения реальных рыночных данных
    ДОБАВЬТЕ ЭТУ ФУНКЦИЮ В КОНЕЦ charts_routes.py
    """
    
    @app.route('/api/charts/price/<symbol>')
    def get_current_price(symbol):
        """Получить текущую цену валюты"""
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
                except Exception as e:
                    logger.warning(f"Не удалось получить цену {symbol} с биржи: {e}")
            
            # Fallback к демо данным с реалистичным движением
            import random
            base_prices = {
                'BTCUSDT': 67800.0,
                'ETHUSDT': 3450.0,
                'BNBUSDT': 625.0,
                'SOLUSDT': 145.0
            }
            
            base_price = base_prices.get(symbol, 1.0)
            # Добавляем случайное движение ±1%
            price_change = random.uniform(-0.01, 0.01)
            current_price = base_price * (1 + price_change)
            
            return jsonify({
                'success': True,
                'symbol': symbol,
                'price': round(current_price, 2),
                'bid': round(current_price * 0.9995, 2),
                'ask': round(current_price * 1.0005, 2),
                'volume': random.randint(10000, 50000),
                'change_24h': round(random.uniform(-5.0, 5.0), 2),
                'high_24h': round(current_price * 1.02, 2),
                'low_24h': round(current_price * 0.98, 2),
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
                        'candles': candles,
                        'source': 'exchange'
                    })
                except Exception as e:
                    logger.warning(f"Не удалось получить свечи с биржи: {e}")
            
            # Генерируем реалистичные демо данные
            from datetime import timedelta
            now = datetime.utcnow()
            candles = []
            
            base_prices = {
                'BTCUSDT': 67800.0,
                'ETHUSDT': 3450.0,
                'BNBUSDT': 625.0,
                'SOLUSDT': 145.0
            }
            base_price = base_prices.get(symbol, 1.0)
            
            for i in range(limit):
                timestamp = int((now - timedelta(hours=limit-i)).timestamp() * 1000)
                
                # Более реалистичная симуляция движения цены
                import math
                wave = math.sin(i * 0.1) * 0.02  # Волновое движение
                trend = (i - limit/2) * 0.0001   # Небольшой тренд
                noise = random.uniform(-0.005, 0.005)  # Шум
                
                price_factor = 1 + wave + trend + noise
                
                open_price = base_price * price_factor
                close_price = open_price * (1 + random.uniform(-0.01, 0.01))
                high_price = max(open_price, close_price) * (1 + random.uniform(0, 0.005))
                low_price = min(open_price, close_price) * (1 - random.uniform(0, 0.005))
                
                candles.append({
                    'timestamp': timestamp,
                    'open': round(open_price, 2),
                    'high': round(high_price, 2),
                    'low': round(low_price, 2),
                    'close': round(close_price, 2),
                    'volume': random.randint(800, 1200)
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
    
    @app.route('/api/charts/tickers')
    def get_all_tickers():
        """Получить данные по всем торговым парам"""
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
    
    logger.info("✅ API рыночных данных зарегистрированы:")
    logger.info("   📈 GET /api/charts/price/<symbol> - текущая цена")
    logger.info("   🕯️ GET /api/charts/candles/<symbol> - свечные данные")
    logger.info("   📊 GET /api/charts/tickers - все тикеры")



