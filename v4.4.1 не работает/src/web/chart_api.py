"""
API для графиков и реального времени - ПОЛНОСТЬЮ ИСПРАВЛЕННАЯ ВЕРСИЯ
Файл: src/web/chart_api.py
"""
from flask import jsonify, request, render_template
from flask_socketio import emit, join_room, leave_room
from flask_login import login_required
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from typing import Dict, List, Any, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor

# ИСПРАВЛЕНИЕ: Правильные импорты из core.models
from ..core.database import SessionLocal
from src.core.models import (
    Trade, Signal, Order, 
    StrategyPerformance,  # Вместо Strategy
    TradingPair, Balance, BotState
)
from src.exchange.client import ExchangeClient
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
        
        @self.app.route('/api/chart/balance')
        @login_required
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
        @login_required
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
        @login_required
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
                        'side': trade.side.value if hasattr(trade.side, 'value') else str(trade.side),
                        'quantity': float(trade.quantity),
                        'entry_price': float(trade.entry_price),
                        'exit_price': float(trade.exit_price) if trade.exit_price else None,
                        'profit': float(trade.profit) if trade.profit else None,
                        'profit_percent': float(trade.profit_percent) if trade.profit_percent else None,
                        'status': trade.status.value if hasattr(trade.status, 'value') else str(trade.status),
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
        @login_required
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
                    and_(Trade.created_at >= start_date,
                         Trade.profit > 0)
                ).count()
                
                total_profit = db.query(func.sum(Trade.profit)).filter(
                    Trade.created_at >= start_date
                ).scalar() or 0
                
                # Статистика по стратегиям
                strategy_stats = db.query(
                    StrategyPerformance.strategy_name,
                    func.count(StrategyPerformance.id).label('trades_count'),
                    func.sum(StrategyPerformance.profit).label('total_profit')
                ).filter(
                    StrategyPerformance.created_at >= start_date
                ).group_by(
                    StrategyPerformance.strategy_name
                ).all()
                
                result = {
                    'period_days': days,
                    'total_trades': total_trades,
                    'profitable_trades': profitable_trades,
                    'win_rate': (profitable_trades / total_trades * 100) if total_trades > 0 else 0,
                    'total_profit': float(total_profit),
                    'strategies': [{
                        'name': stat.strategy_name,
                        'trades': stat.trades_count,
                        'profit': float(stat.total_profit) if stat.total_profit else 0
                    } for stat in strategy_stats]
                }
                
                db.close()
                return jsonify(result)
                
            except Exception as e:
                logger.error(f"Ошибка получения аналитики: {str(e)}", category='api')
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/market/indicators/<symbol>')
        @login_required
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
                
                # Вычисляем индикаторы (используем pandas_ta если доступна)
                try:
                    import pandas_ta as ta
                    df['rsi'] = ta.rsi(df['close'], length=14)
                    macd_data = ta.macd(df['close'], fast=12, slow=26, signal=9)
                    if macd_data is not None:
                        df['macd'] = macd_data.iloc[:, 0]
                        df['macd_signal'] = macd_data.iloc[:, 1]
                        df['macd_diff'] = macd_data.iloc[:, 2]
                    
                    bb_data = ta.bbands(df['close'], length=20, std=2)
                    if bb_data is not None:
                        df['bb_lower'] = bb_data.iloc[:, 0]
                        df['bb_middle'] = bb_data.iloc[:, 1]
                        df['bb_upper'] = bb_data.iloc[:, 2]
                except:
                    # Fallback на ручные расчеты
                    df['rsi'] = self._calculate_rsi(df['close'], 14)
                    
                    exp1 = df['close'].ewm(span=12, adjust=False).mean()
                    exp2 = df['close'].ewm(span=26, adjust=False).mean()
                    df['macd'] = exp1 - exp2
                    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
                    df['macd_diff'] = df['macd'] - df['macd_signal']
                    
                    sma = df['close'].rolling(20).mean()
                    std = df['close'].rolling(20).std()
                    df['bb_upper'] = sma + 2 * std
                    df['bb_middle'] = sma
                    df['bb_lower'] = sma - 2 * std
                
                # Текущие значения
                current_indicators = {
                    'rsi': float(df['rsi'].iloc[-1]) if not pd.isna(df['rsi'].iloc[-1]) else None,
                    'macd': {
                        'macd': float(df['macd'].iloc[-1]) if not pd.isna(df['macd'].iloc[-1]) else None,
                        'signal': float(df['macd_signal'].iloc[-1]) if not pd.isna(df['macd_signal'].iloc[-1]) else None,
                        'histogram': float(df['macd_diff'].iloc[-1]) if not pd.isna(df['macd_diff'].iloc[-1]) else None
                    },
                    'bollinger': {
                        'upper': float(df['bb_upper'].iloc[-1]) if not pd.isna(df['bb_upper'].iloc[-1]) else None,
                        'middle': float(df['bb_middle'].iloc[-1]) if not pd.isna(df['bb_middle'].iloc[-1]) else None,
                        'lower': float(df['bb_lower'].iloc[-1]) if not pd.isna(df['bb_lower'].iloc[-1]) else None
                    },
                    'price': float(df['close'].iloc[-1]),
                    'volume_24h': float(df['volume'].sum()),
                    'high_24h': float(df['high'].max()),
                    'low_24h': float(df['low'].min())
                }
                
                return jsonify(current_indicators)
                
            except Exception as e:
                logger.error(f"Ошибка получения индикаторов: {str(e)}", category='api')
                return jsonify({'error': str(e)}), 500
    
    def _calculate_rsi(self, prices, period=14):
        """Ручной расчет RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _register_socketio_handlers(self):
        """Регистрирует обработчики WebSocket"""
        
        @self.socketio.on('subscribe_prices')
        def handle_price_subscription(data):
            """Подписка на обновления цен"""
            symbols = data.get('symbols', [])
            room = data.get('room', 'prices')
            
            join_room(room)
            
            # Отправляем текущие цены
            current_prices = {}
            for symbol in symbols:
                if symbol in self.price_cache:
                    current_prices[symbol] = self.price_cache[symbol]
            
            emit('price_update', current_prices, room=room)
        
        @self.socketio.on('unsubscribe_prices')
        def handle_price_unsubscription(data):
            """Отписка от обновлений цен"""
            room = data.get('room', 'prices')
            leave_room(room)
    
    async def start_price_updates(self, symbols: List[str], interval: int = 1):
        """Запускает обновление цен в реальном времени"""
        while True:
            try:
                for symbol in symbols:
                    # Получаем текущую цену
                    ticker = await self.exchange_client.get_ticker(symbol)
                    
                    if ticker:
                        price_data = {
                            'symbol': symbol,
                            'price': float(ticker.get('last', 0)),
                            'change_24h': float(ticker.get('percentage', 0)),
                            'volume_24h': float(ticker.get('baseVolume', 0)),
                            'timestamp': datetime.utcnow().isoformat()
                        }
                        
                        # Обновляем кеш
                        self.price_cache[symbol] = price_data
                        
                        # Отправляем через WebSocket
                        self.socketio.emit('price_update', {symbol: price_data}, room='prices')
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Ошибка обновления цен: {str(e)}", category='websocket')
                await asyncio.sleep(5)  # Пауза при ошибке
    
    def stop_background_tasks(self):
        """Останавливает фоновые задачи"""
        for task in self.background_tasks:
            task.cancel()
        self.background_tasks = []