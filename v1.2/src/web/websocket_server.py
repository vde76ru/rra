"""
WebSocket сервер для real-time обновлений дашборда
"""
import asyncio
import json
from datetime import datetime
from typing import Dict, Set, Any
import aiohttp
from aiohttp import web
import weakref

from ..logging.smart_logger import SmartLogger
from ..core.database import SessionLocal

logger = SmartLogger(__name__)


class WebSocketManager:
    """Менеджер WebSocket соединений"""
    
    def __init__(self):
        self._connections: Set[web.WebSocketResponse] = weakref.WeakSet()
        self._subscriptions: Dict[str, Set[web.WebSocketResponse]] = {}
        
    async def add_connection(self, ws: web.WebSocketResponse):
        """Добавляет новое соединение"""
        self._connections.add(ws)
        logger.info(
            "Новое WebSocket соединение",
            category='websocket',
            total_connections=len(self._connections)
        )
        
        # Отправляем приветственное сообщение
        await ws.send_json({
            'type': 'connection',
            'status': 'connected',
            'timestamp': datetime.utcnow().isoformat()
        })
    
    def remove_connection(self, ws: web.WebSocketResponse):
        """Удаляет соединение"""
        # Удаляем из всех подписок
        for subscribers in self._subscriptions.values():
            subscribers.discard(ws)
        
        logger.info(
            "WebSocket соединение закрыто",
            category='websocket',
            remaining_connections=len(self._connections) - 1
        )
    
    async def subscribe(self, ws: web.WebSocketResponse, channel: str):
        """Подписывает соединение на канал"""
        if channel not in self._subscriptions:
            self._subscriptions[channel] = weakref.WeakSet()
        
        self._subscriptions[channel].add(ws)
        
        await ws.send_json({
            'type': 'subscription',
            'channel': channel,
            'status': 'subscribed',
            'timestamp': datetime.utcnow().isoformat()
        })
    
    async def unsubscribe(self, ws: web.WebSocketResponse, channel: str):
        """Отписывает соединение от канала"""
        if channel in self._subscriptions:
            self._subscriptions[channel].discard(ws)
        
        await ws.send_json({
            'type': 'subscription',
            'channel': channel,
            'status': 'unsubscribed',
            'timestamp': datetime.utcnow().isoformat()
        })
    
    async def broadcast(self, channel: str, data: Dict[str, Any]):
        """Отправляет данные всем подписчикам канала"""
        if channel not in self._subscriptions:
            return
        
        message = {
            'type': 'data',
            'channel': channel,
            'data': data,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Отправляем всем подписчикам
        tasks = []
        for ws in self._subscriptions[channel]:
            try:
                tasks.append(ws.send_json(message))
            except ConnectionResetError:
                pass
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def broadcast_all(self, data: Dict[str, Any]):
        """Отправляет данные всем соединениям"""
        message = {
            'type': 'broadcast',
            'data': data,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        tasks = []
        for ws in self._connections:
            try:
                tasks.append(ws.send_json(message))
            except ConnectionResetError:
                pass
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)


class RealtimeDataProvider:
    """Провайдер данных для real-time обновлений"""
    
    def __init__(self, ws_manager: WebSocketManager, bot_manager):
        self.ws_manager = ws_manager
        self.bot_manager = bot_manager
        self._running = False
        self._tasks = []
        
    async def start(self):
        """Запускает провайдер данных"""
        self._running = True
        
        # Запускаем фоновые задачи
        self._tasks = [
            asyncio.create_task(self._balance_updates()),
            asyncio.create_task(self._trades_updates()),
            asyncio.create_task(self._signals_updates()),
            asyncio.create_task(self._performance_updates()),
            asyncio.create_task(self._market_updates())
        ]
        
        logger.info("Realtime data provider запущен", category='websocket')
    
    async def stop(self):
        """Останавливает провайдер данных"""
        self._running = False
        
        for task in self._tasks:
            task.cancel()
        
        await asyncio.gather(*self._tasks, return_exceptions=True)
        logger.info("Realtime data provider остановлен", category='websocket')
    
    async def _balance_updates(self):
        """Отправляет обновления баланса"""
        while self._running:
            try:
                balance_data = await self.bot_manager.balance_manager.get_balance_info()
                
                await self.ws_manager.broadcast('balance', {
                    'total': balance_data['total'],
                    'available': balance_data['available'],
                    'in_orders': balance_data['in_orders'],
                    'profit_today': balance_data.get('profit_today', 0),
                    'profit_percent': balance_data.get('profit_percent', 0)
                })
                
                await asyncio.sleep(5)  # Обновляем каждые 5 секунд
                
            except Exception as e:
                logger.error(f"Ошибка обновления баланса: {e}", category='websocket')
                await asyncio.sleep(10)
    
    async def _trades_updates(self):
        """Отправляет обновления по сделкам"""
        last_trade_id = 0
        
        while self._running:
            try:
                # Получаем новые сделки
                db = SessionLocal()
                try:
                    trades = db.query(Trade).filter(
                        Trade.id > last_trade_id
                    ).order_by(Trade.id).limit(10).all()
                    
                    for trade in trades:
                        await self.ws_manager.broadcast('trades', {
                            'id': trade.id,
                            'symbol': trade.symbol,
                            'side': trade.side,
                            'quantity': trade.quantity,
                            'entry_price': trade.entry_price,
                            'current_price': trade.current_price,
                            'profit': trade.profit,
                            'profit_percent': trade.profit_percent,
                            'status': trade.status,
                            'strategy': trade.strategy,
                            'created_at': trade.created_at.isoformat()
                        })
                        
                        last_trade_id = trade.id
                        
                finally:
                    db.close()
                
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Ошибка обновления сделок: {e}", category='websocket')
                await asyncio.sleep(10)
    
    async def _signals_updates(self):
        """Отправляет обновления по сигналам"""
        last_signal_id = 0
        
        while self._running:
            try:
                # Получаем новые сигналы
                db = SessionLocal()
                try:
                    signals = db.query(Signal).filter(
                        Signal.id > last_signal_id
                    ).order_by(Signal.id).limit(10).all()
                    
                    for signal in signals:
                        await self.ws_manager.broadcast('signals', {
                            'id': signal.id,
                            'symbol': signal.symbol,
                            'action': signal.action,
                            'strategy': signal.strategy,
                            'confidence': signal.confidence,
                            'created_at': signal.created_at.isoformat()
                        })
                        
                        last_signal_id = signal.id
                        
                finally:
                    db.close()
                
                await asyncio.sleep(3)
                
            except Exception as e:
                logger.error(f"Ошибка обновления сигналов: {e}", category='websocket')
                await asyncio.sleep(10)
    
    async def _performance_updates(self):
        """Отправляет обновления производительности"""
        while self._running:
            try:
                # Получаем статистику
                stats = await self.bot_manager.get_performance_stats()
                
                await self.ws_manager.broadcast('performance', {
                    'total_trades': stats['total_trades'],
                    'win_rate': stats['win_rate'],
                    'profit_factor': stats['profit_factor'],
                    'sharpe_ratio': stats['sharpe_ratio'],
                    'max_drawdown': stats['max_drawdown'],
                    'best_strategy': stats['best_strategy'],
                    'worst_strategy': stats['worst_strategy']
                })
                
                await asyncio.sleep(30)  # Обновляем каждые 30 секунд
                
            except Exception as e:
                logger.error(f"Ошибка обновления производительности: {e}", category='websocket')
                await asyncio.sleep(60)
    
    async def _market_updates(self):
        """Отправляет обновления рынка"""
        while self._running:
            try:
                # Получаем данные по активным парам
                active_symbols = await self.bot_manager.get_active_symbols()
                
                for symbol in active_symbols:
                    ticker = await self.bot_manager.exchange.get_ticker(symbol)
                    
                    await self.ws_manager.broadcast(f'market:{symbol}', {
                        'symbol': symbol,
                        'price': ticker['last'],
                        'change_24h': ticker['percentage'],
                        'volume_24h': ticker['quoteVolume'],
                        'high_24h': ticker['high'],
                        'low_24h': ticker['low']
                    })
                
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Ошибка обновления рынка: {e}", category='websocket')
                await asyncio.sleep(10)


async def websocket_handler(request):
    """Обработчик WebSocket соединений"""
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    
    ws_manager = request.app['ws_manager']
    await ws_manager.add_connection(ws)
    
    try:
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                    
                    if data['type'] == 'subscribe':
                        await ws_manager.subscribe(ws, data['channel'])
                    
                    elif data['type'] == 'unsubscribe':
                        await ws_manager.unsubscribe(ws, data['channel'])
                    
                    elif data['type'] == 'ping':
                        await ws.send_json({
                            'type': 'pong',
                            'timestamp': datetime.utcnow().isoformat()
                        })
                        
                except json.JSONDecodeError:
                    await ws.send_json({
                        'type': 'error',
                        'message': 'Invalid JSON'
                    })
                    
            elif msg.type == aiohttp.WSMsgType.ERROR:
                logger.error(
                    f'WebSocket error: {ws.exception()}',
                    category='websocket'
                )
                
    except Exception as e:
        logger.error(f"WebSocket handler error: {e}", category='websocket')
        
    finally:
        ws_manager.remove_connection(ws)
        await ws.close()
    
    return ws


def setup_websocket(app: web.Application, bot_manager):
    """Настраивает WebSocket в приложении"""
    # Создаем менеджер
    ws_manager = WebSocketManager()
    app['ws_manager'] = ws_manager
    
    # Создаем провайдер данных
    data_provider = RealtimeDataProvider(ws_manager, bot_manager)
    app['data_provider'] = data_provider
    
    # Добавляем маршрут
    app.router.add_get('/ws', websocket_handler)
    
    # Добавляем startup/cleanup
    async def start_websocket(app):
        await app['data_provider'].start()
    
    async def stop_websocket(app):
        await app['data_provider'].stop()
    
    app.on_startup.append(start_websocket)
    app.on_cleanup.append(stop_websocket)
    
    logger.info("WebSocket настроен", category='websocket')