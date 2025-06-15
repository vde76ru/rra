"""
API для графиков и реального времени
Файл: src/web/chart_api.py
"""
from flask import jsonify, request, render_template
from flask_socketio import emit, join_room, leave_room
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from typing import Dict, List, Any, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor

from ..core.database import SessionLocal
from ..core.models import Trade, Signal, Order, Strategy, StrategyPerformance
from ..exchange.client import ExchangeClient
from ..logging.smart_logger import SmartLogger
from sqlalchemy import and_, func, desc
from sqlalchemy.orm import Session

logger = SmartLogger(__name__)

# Thread pool для асинхронных операций
executor = ThreadPoolExecutor(max_workers=4)


class ChartAPI:
    """
    API для работы с графиками и real-time данными
    """
    
    def __init__(self, app, socketio, exchange_client: ExchangeClient):
        self.app = app
        self.socketio = socketio
        self.exchange_client = exchange_client
        
        # Кеш для данных
        self.price_cache = {}
        self.balance_cache = None
        self.last_balance_update = None
        
        # Регистрация роутов
        self._register_routes()
        self._register_socketio_handlers()
        
        # Фоновые задачи
        self.background_tasks = []
    
    def _register_routes(self):
        """Регистрирует HTTP роуты"""
        
        @self.app.route('/api/balance')
        def get_balance():
            """Получает текущий баланс"""
            try:
                # Проверяем кеш
                if (self.balance_cache and self.last_balance_update and 
                    (datetime.utcnow() - self.last_balance_update).seconds < 5):
                    return jsonify(self.balance_cache)
                
                # Получаем баланс из exchange
                balance_info = asyncio.run(self.exchange_client.get_account_balance())
                
                # Форматируем данные
                formatted_balance = {
                    'total_usdt': float(balance_info.get('totalWalletBalance', 0)),
                    'available_usdt': float(balance_info.get('availableBalance', 0)),
                    'unrealized_pnl': float(balance_info.get('totalUnrealizedProfit', 0)),
                    'margin_used': float(balance_info.get('totalMarginBalance', 0)),
                    'positions': []
                }
                
                # Добавляем позиции
                for position in balance_info.get('positions', []):
                    if float(position.get('positionAmt', 0)) != 0:
                        formatted_balance['positions'].append({
                            'symbol': position.get('symbol'),
                            'side': 'LONG' if float(position['positionAmt']) > 0 else 'SHORT',
                            'quantity': abs(float(position['positionAmt'])),
                            'entry_price': float(position.get('entryPrice', 0)),
                            'mark_price': float(position.get('markPrice', 0)),
                            'pnl': float(position.get('unrealizedProfit', 0)),
                            'pnl_percent': float(position.get('percentage', 0))
                        })
                
                # Обновляем кеш
                self.balance_cache = formatted_balance
                self.last_balance_update = datetime.utcnow()
                
                return jsonify(formatted_balance)
                
            except Exception as e:
                logger.error(f"Ошибка получения баланса: {str(e)}", category='api')
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/chart-data/<symbol>')
        def get_chart_data(symbol):
            """Получает данные для графика"""
            try:
                timeframe = request.args.get('timeframe', '1h')
                limit = int(request.args.get('limit', 500))
                
                # Получаем исторические данные
                klines = asyncio.run(
                    self.exchange_client.get_historical_klines(
                        symbol, timeframe, limit
                    )
                )
                
                # Форматируем для TradingView
                chart_data = {
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'data': []
                }
                
                for kline in klines:
                    chart_data['data'].append({
                        'time': int(kline[0] / 1000),  # timestamp в секундах
                        'open': float(kline[1]),
                        'high': float(kline[2]),
                        'low': float(kline[3]),
                        'close': float(kline[4]),
                        'volume': float(kline[5])
                    })
                
                return jsonify(chart_data)
                
            except Exception as e:
                logger.error(f"Ошибка получения данных графика: {str(e)}", category='api')
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/trades')
        def get_trades():
            """Получает историю сделок"""
            try:
                db = SessionLocal()
                
                # Параметры пагинации
                page = int(request.args.get('page', 1))
                per_page = int(request.args.get('per_page', 20))
                symbol = request.args.get('symbol')
                
                # Базовый запрос
                query = db.query(Trade)
                
                # Фильтры
                if symbol:
                    query = query.filter(Trade.symbol == symbol)
                
                # Получаем данные
                total = query.count()
                trades = query.order_by(desc(Trade.created_at))\
                            .offset((page - 1) * per_page)\
                            .limit(per_page)\
                            .all()
                
                # Форматируем результат
                result = {
                    'total': total,
                    'page': page,
                    'per_page': per_page,
                    'trades': [{
                        'id': trade.id,
                        'symbol': trade.symbol,
                        'side': trade.side.value,
                        'quantity': float(trade.quantity),
                        'entry_price': float(trade.entry_price),
                        'exit_price': float(trade.exit_price) if trade.exit_price else None,
                        'profit': float(trade.profit) if trade.profit else None,
                        'profit_percent': float(trade.profit_percent) if trade.profit_percent else None,
                        'status': trade.status.value,
                        'strategy': trade.strategy,
                        'created_at': trade.created_at.isoformat(),
                        'closed_at': trade.closed_at.isoformat() if trade.closed_at else None
                    } for trade in trades]
                }
                
                db.close()
                return jsonify(result)
                
            except Exception as e:
                logger.error(f"Ошибка получения сделок: {str(e)}", category='api')
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/analytics/performance')
        def get_performance_analytics():
            """Получает аналитику производительности"""
            try:
                db = SessionLocal()
                
                # Период анализа
                days = int(request.args.get('days', 30))
                start_date = datetime.utcnow() - timedelta(days=days)
                
                # Общая статистика
                total_trades = db.query(Trade).filter(
                    Trade.created_at >= start_date
                ).count()
                
                profitable_trades = db.query(Trade).filter(
                    and_(
                        Trade.created_at >= start_date,
                        Trade.profit > 0
                    )
                ).count()
                
                # Прибыль по дням
                daily_pnl = db.query(
                    func.date(Trade.closed_at).label('date'),
                    func.sum(Trade.profit).label('profit')
                ).filter(
                    and_(
                        Trade.closed_at >= start_date,
                        Trade.status == 'CLOSED'
                    )
                ).group_by(func.date(Trade.closed_at)).all()
                
                # Производительность по стратегиям
                strategy_stats = db.query(
                    Trade.strategy,
                    func.count(Trade.id).label('count'),
                    func.avg(Trade.profit_percent).label('avg_profit'),
                    func.sum(Trade.profit).label('total_profit')
                ).filter(
                    and_(
                        Trade.created_at >= start_date,
                        Trade.status == 'CLOSED'
                    )
                ).group_by(Trade.strategy).all()
                
                # Форматируем результат
                result = {
                    'summary': {
                        'total_trades': total_trades,
                        'profitable_trades': profitable_trades,
                        'win_rate': profitable_trades / total_trades if total_trades > 0 else 0,
                        'period_days': days
                    },
                    'daily_pnl': [{
                        'date': day.date.isoformat() if day.date else None,
                        'profit': float(day.profit) if day.profit else 0
                    } for day in daily_pnl],
                    'strategy_performance': [{
                        'strategy': stat.strategy,
                        'trades': stat.count,
                        'avg_profit_percent': float(stat.avg_profit) if stat.avg_profit else 0,
                        'total_profit': float(stat.total_profit) if stat.total_profit else 0
                    } for stat in strategy_stats]
                }
                
                db.close()
                return jsonify(result)
                
            except Exception as e:
                logger.error(f"Ошибка получения аналитики: {str(e)}", category='api')
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/market/indicators/<symbol>')
        def get_market_indicators(symbol):
            """Получает текущие индикаторы рынка"""
            try:
                # Получаем последние данные
                klines = asyncio.run(
                    self.exchange_client.get_historical_klines(
                        symbol, '1h', 100
                    )
                )
                
                # Конвертируем в DataFrame
                df = pd.DataFrame(klines, columns=[
                    'timestamp', 'open', 'high', 'low', 'close', 'volume',
                    'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                    'taker_buy_quote', 'ignore'
                ])
                
                df['close'] = df['close'].astype(float)
                df['high'] = df['high'].astype(float)
                df['low'] = df['low'].astype(float)
                df['volume'] = df['volume'].astype(float)
                
                # Вычисляем индикаторы
                from ..ml.features.feature_engineering import FeatureEngineer
                fe = FeatureEngineer()
                
                # RSI
                rsi = fe._calculate_rsi(df['close'], 14)
                
                # MACD
                exp1 = df['close'].ewm(span=12, adjust=False).mean()
                exp2 = df['close'].ewm(span=26, adjust=False).mean()
                macd = exp1 - exp2
                signal = macd.ewm(span=9, adjust=False).mean()
                
                # Bollinger Bands
                sma = df['close'].rolling(20).mean()
                std = df['close'].rolling(20).std()
                upper_band = sma + 2 * std
                lower_band = sma - 2 * std
                
                # Текущие значения
                current_indicators = {
                    'rsi': float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else None,
                    'macd': {
                        'macd': float(macd.iloc[-1]) if not pd.isna(macd.iloc[-1]) else None,
                        'signal': float(signal.iloc[-1]) if not pd.isna(signal.iloc[-1]) else None,
                        'histogram': float(macd.iloc[-1] - signal.iloc[-1]) if not pd.isna(macd.iloc[-1]) else None
                    },
                    'bollinger': {
                        'upper': float(upper_band.iloc[-1]) if not pd.isna(upper_band.iloc[-1]) else None,
                        'middle': float(sma.iloc[-1]) if not pd.isna(sma.iloc[-1]) else None,
                        'lower': float(lower_band.iloc[-1]) if not pd.isna(lower_band.iloc[-1]) else None
                    },
                    'price': float(df['close'].iloc[-1]),
                    'volume_24h': float(df['volume'].sum()),
                    'price_change_24h': float((df['close'].iloc[-1] - df['close'].iloc[-24]) / df['close'].iloc[-24] * 100)
                }
                
                return jsonify(current_indicators)
                
            except Exception as e:
                logger.error(f"Ошибка получения индикаторов: {str(e)}", category='api')
                return jsonify({'error': str(e)}), 500
        
        # Страницы дашборда
        @self.app.route('/charts')
        def charts_page():
            """Страница с графиками"""
            return render_template('charts.html')
        
        @self.app.route('/analytics')
        def analytics_page():
            """Страница аналитики"""
            return render_template('analytics.html')
    
    def _register_socketio_handlers(self):
        """Регистрирует WebSocket обработчики"""
        
        @self.socketio.on('subscribe_price')
        def handle_price_subscription(data):
            """Подписка на обновления цены"""
            symbol = data.get('symbol')
            if symbol:
                join_room(f"price_{symbol}")
                emit('subscription_confirmed', {'symbol': symbol})
                logger.info(f"Клиент подписан на цену {symbol}", category='websocket')
        
        @self.socketio.on('unsubscribe_price')
        def handle_price_unsubscription(data):
            """Отписка от обновлений цены"""
            symbol = data.get('symbol')
            if symbol:
                leave_room(f"price_{symbol}")
                emit('unsubscription_confirmed', {'symbol': symbol})
        
        @self.socketio.on('subscribe_trades')
        def handle_trades_subscription():
            """Подписка на обновления сделок"""
            join_room('trades')
            emit('subscription_confirmed', {'channel': 'trades'})
        
        @self.socketio.on('subscribe_balance')
        def handle_balance_subscription():
            """Подписка на обновления баланса"""
            join_room('balance')
            emit('subscription_confirmed', {'channel': 'balance'})
            
            # Отправляем текущий баланс
            if self.balance_cache:
                emit('balance_update', self.balance_cache)
    
    async def start_real_time_updates(self):
        """Запускает real-time обновления"""
        # Запускаем задачи обновления
        self.background_tasks.append(
            asyncio.create_task(self._price_update_loop())
        )
        self.background_tasks.append(
            asyncio.create_task(self._balance_update_loop())
        )
        self.background_tasks.append(
            asyncio.create_task(self._trades_update_loop())
        )
        
        logger.info("Real-time обновления запущены", category='websocket')
    
    async def _price_update_loop(self):
        """Цикл обновления цен"""
        while True:
            try:
                # Получаем активные символы из подписок
                active_symbols = set()
                for room in self.socketio.server.manager.rooms:
                    if room.startswith('price_'):
                        active_symbols.add(room.replace('price_', ''))
                
                # Обновляем цены для активных символов
                for symbol in active_symbols:
                    try:
                        ticker = await self.exchange_client.get_ticker(symbol)
                        
                        price_data = {
                            'symbol': symbol,
                            'price': float(ticker['lastPrice']),
                            'change_24h': float(ticker['priceChangePercent']),
                            'volume_24h': float(ticker['volume']),
                            'high_24h': float(ticker['highPrice']),
                            'low_24h': float(ticker['lowPrice']),
                            'timestamp': datetime.utcnow().isoformat()
                        }
                        
                        # Отправляем обновление
                        self.socketio.emit(
                            'price_update',
                            price_data,
                            room=f'price_{symbol}'
                        )
                        
                        # Обновляем кеш
                        self.price_cache[symbol] = price_data
                        
                    except Exception as e:
                        logger.error(f"Ошибка обновления цены {symbol}: {e}")
                
                await asyncio.sleep(1)  # Обновление каждую секунду
                
            except Exception as e:
                logger.error(f"Ошибка в price update loop: {e}")
                await asyncio.sleep(5)
    
    async def _balance_update_loop(self):
        """Цикл обновления баланса"""
        while True:
            try:
                # Обновляем баланс каждые 5 секунд
                balance_info = await self.exchange_client.get_account_balance()
                
                formatted_balance = {
                    'total_usdt': float(balance_info.get('totalWalletBalance', 0)),
                    'available_usdt': float(balance_info.get('availableBalance', 0)),
                    'unrealized_pnl': float(balance_info.get('totalUnrealizedProfit', 0)),
                    'margin_used': float(balance_info.get('totalMarginBalance', 0)),
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                # Проверяем изменения
                if (not self.balance_cache or 
                    self.balance_cache['total_usdt'] != formatted_balance['total_usdt'] or
                    self.balance_cache['unrealized_pnl'] != formatted_balance['unrealized_pnl']):
                    
                    # Обновляем кеш
                    self.balance_cache = formatted_balance
                    self.last_balance_update = datetime.utcnow()
                    
                    # Отправляем обновление
                    self.socketio.emit(
                        'balance_update',
                        formatted_balance,
                        room='balance'
                    )
                
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Ошибка в balance update loop: {e}")
                await asyncio.sleep(10)
    
    async def _trades_update_loop(self):
        """Цикл обновления сделок"""
        last_trade_id = None
        
        while True:
            try:
                db = SessionLocal()
                
                # Получаем новые сделки
                query = db.query(Trade).order_by(desc(Trade.id))
                
                if last_trade_id:
                    query = query.filter(Trade.id > last_trade_id)
                
                new_trades = query.limit(10).all()
                
                if new_trades:
                    # Обновляем последний ID
                    last_trade_id = new_trades[0].id
                    
                    # Форматируем и отправляем
                    for trade in new_trades:
                        trade_data = {
                            'id': trade.id,
                            'symbol': trade.symbol,
                            'side': trade.side.value,
                            'quantity': float(trade.quantity),
                            'entry_price': float(trade.entry_price),
                            'status': trade.status.value,
                            'strategy': trade.strategy,
                            'created_at': trade.created_at.isoformat()
                        }
                        
                        self.socketio.emit(
                            'new_trade',
                            trade_data,
                            room='trades'
                        )
                
                db.close()
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Ошибка в trades update loop: {e}")
                await asyncio.sleep(5)
    
    def stop_real_time_updates(self):
        """Останавливает real-time обновления"""
        for task in self.background_tasks:
            task.cancel()
        
        logger.info("Real-time обновления остановлены", category='websocket')


# Вспомогательные функции для анализа
def calculate_sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.02) -> float:
    """Вычисляет коэффициент Шарпа"""
    excess_returns = returns - risk_free_rate / 365
    return np.sqrt(365) * excess_returns.mean() / excess_returns.std()


def calculate_max_drawdown(equity_curve: pd.Series) -> float:
    """Вычисляет максимальную просадку"""
    cumulative = (1 + equity_curve).cumprod()
    running_max = cumulative.expanding().max()
    drawdown = (cumulative - running_max) / running_max
    return drawdown.min()


def calculate_win_rate(trades: List[Trade]) -> float:
    """Вычисляет win rate"""
    if not trades:
        return 0.0
    
    winning_trades = sum(1 for t in trades if t.profit and t.profit > 0)
    return winning_trades / len(trades)


def calculate_profit_factor(trades: List[Trade]) -> float:
    """Вычисляет profit factor"""
    gross_profit = sum(t.profit for t in trades if t.profit and t.profit > 0)
    gross_loss = abs(sum(t.profit for t in trades if t.profit and t.profit < 0))
    
    if gross_loss == 0:
        return float('inf') if gross_profit > 0 else 0
    
    return gross_profit / gross_loss