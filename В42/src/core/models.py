"""
Обновленный менеджер торгового бота с интеграцией всех компонентов
Путь: src/bot/manager.py
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional
from contextlib import asynccontextmanager

from sqlalchemy.orm import Session
from ..core.database import get_db
from ..core.models import BotState, Trade, Signal, TradingPair, TradingLog
from ..core.config import settings
from ..utils.smart_logger import SmartLogger

# ML компоненты
from ..ml.strategy_selector import MLStrategySelector
from ..ml.trainer import ModelTrainer
from ..ml.predictor import MarketPredictor

# Торговые компоненты
from ..bot.enhanced_executor import EnhancedTradeExecutor
from ..strategies.multi_indicator import MultiIndicatorStrategy
from ..strategies.scalping import ScalpingStrategy
from ..risk.manager import RiskManager

# Анализ новостей и соцсетей
from ..analysis.news.news_collector import NewsCollector
from ..analysis.social.twitter_monitor import TwitterMonitor
from ..analysis.social.reddit_monitor import RedditMonitor
from ..analysis.sentiment.analyzer import SentimentAnalyzer

# WebSocket и уведомления
from ..web.websocket_server import SocketIOManager
from ..notifications.telegram_bot import TelegramNotifier
from ..notifications.email_sender import EmailNotifier

# Мониторинг и метрики
from ..monitoring.performance_tracker import PerformanceTracker
from ..monitoring.system_monitor import SystemMonitor

class BotManager:
    """Главный менеджер торгового бота"""
    
    def __init__(self, app=None):
        self.app = app
        self.logger = SmartLogger(__name__)
        self.is_running = False
        self.start_time = None
        self.tasks = []
        
        # Инициализация компонентов
        self._initialize_components()
        
        # Состояние бота
        self.bot_state = None
        
    def _initialize_components(self):
        """Инициализация всех компонентов бота"""
        try:
            # ML компоненты
            self.ml_selector = MLStrategySelector()
            self.model_trainer = ModelTrainer()
            self.market_predictor = MarketPredictor()
            
            # Торговые компоненты
            self.trade_executor = EnhancedTradeExecutor()
            self.risk_manager = RiskManager()
            
            # Стратегии
            self.strategies = {
                'multi_indicator': MultiIndicatorStrategy(),
                'scalping': ScalpingStrategy()
            }
            
            # Анализ новостей и соцсетей
            self.news_collector = NewsCollector()
            self.twitter_monitor = TwitterMonitor()
            self.reddit_monitor = RedditMonitor()
            self.sentiment_analyzer = SentimentAnalyzer()
            
            # Уведомления
            self.telegram_notifier = TelegramNotifier()
            self.email_notifier = EmailNotifier()
            
            # Мониторинг
            self.performance_tracker = PerformanceTracker()
            self.system_monitor = SystemMonitor()
            
            # WebSocket (инициализируется позже с app)
            self.socketio_manager = None
            
            self.logger.info("Все компоненты успешно инициализированы")
            
        except Exception as e:
            self.logger.error(f"Ошибка инициализации компонентов: {e}")
            raise
    
    def initialize_websocket(self, app):
        """Инициализация WebSocket после создания app"""
        try:
            self.socketio_manager = SocketIOManager(app)
            self.logger.info("WebSocket менеджер инициализирован")
        except Exception as e:
            self.logger.error(f"Ошибка инициализации WebSocket: {e}")
    
    async def start(self):
        """Запуск торгового бота"""
        if self.is_running:
            self.logger.warning("Бот уже запущен")
            return
        
        try:
            self.logger.info("Запуск торгового бота...")
            self.start_time = datetime.utcnow()
            
            # Обновление состояния в БД
            await self._update_bot_state(is_running=True, start_time=self.start_time)
            
            # Запуск всех компонентов
            await self._start_all_components()
            
            # Основной торговый цикл
            self.tasks.append(asyncio.create_task(self._main_trading_loop()))
            
            self.is_running = True
            
            # Уведомления о запуске
            await self._send_startup_notifications()
            
            self.logger.info("Торговый бот успешно запущен")
            
        except Exception as e:
            self.logger.error(f"Ошибка запуска бота: {e}")
            await self.stop()
            raise
    
    async def stop(self):
        """Остановка торгового бота"""
        if not self.is_running:
            self.logger.warning("Бот уже остановлен")
            return
        
        try:
            self.logger.info("Остановка торгового бота...")
            
            # Отмена всех задач
            for task in self.tasks:
                if not task.done():
                    task.cancel()
            
            # Ожидание завершения задач
            if self.tasks:
                await asyncio.gather(*self.tasks, return_exceptions=True)
            
            # Остановка компонентов
            await self._stop_all_components()
            
            # Обновление состояния в БД
            await self._update_bot_state(
                is_running=False, 
                stop_time=datetime.utcnow()
            )
            
            self.is_running = False
            self.tasks.clear()
            
            # Уведомления об остановке
            await self._send_shutdown_notifications()
            
            self.logger.info("Торговый бот успешно остановлен")
            
        except Exception as e:
            self.logger.error(f"Ошибка остановки бота: {e}")
    
    async def _start_all_components(self):
        """Запуск всех компонентов"""
        # Запуск ML обучения
        self.tasks.append(asyncio.create_task(self._start_ml_training()))
        
        # Запуск мониторинга новостей
        self.tasks.append(asyncio.create_task(self._start_news_monitoring()))
        
        # Запуск мониторинга соцсетей
        self.tasks.append(asyncio.create_task(self._start_social_monitoring()))
        
        # Запуск системного мониторинга
        self.tasks.append(asyncio.create_task(self._start_system_monitoring()))
        
        # Запуск WebSocket сервера
        if self.socketio_manager:
            await self.socketio_manager.start()
        
        self.logger.info("Все компоненты запущены")
    
    async def _stop_all_components(self):
        """Остановка всех компонентов"""
        try:
            # Остановка WebSocket
            if self.socketio_manager:
                await self.socketio_manager.stop()
            
            # Остановка мониторинга
            await self.news_collector.stop()
            await self.twitter_monitor.stop()
            await self.reddit_monitor.stop()
            await self.system_monitor.stop()
            
            self.logger.info("Все компоненты остановлены")
            
        except Exception as e:
            self.logger.error(f"Ошибка остановки компонентов: {e}")
    
    async def _main_trading_loop(self):
        """Основной торговый цикл"""
        while self.is_running:
            try:
                # Получение активных торговых пар
                trading_pairs = await self._get_active_trading_pairs()
                
                for pair in trading_pairs:
                    await self._process_trading_pair(pair)
                
                # Обновление метрик производительности
                await self._update_performance_metrics()
                
                # Отправка обновлений через WebSocket
                await self._send_realtime_updates()
                
                # Пауза между циклами
                await asyncio.sleep(settings.TRADING_INTERVAL)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Ошибка в торговом цикле: {e}")
                await asyncio.sleep(60)  # Пауза при ошибке
    
    async def _process_trading_pair(self, pair: TradingPair):
        """Обработка торговой пары"""
        try:
            symbol = pair.symbol
            
            # Получение рыночных данных
            market_data = await self._get_market_data(symbol)
            
            # Анализ настроений
            sentiment_score = await self.sentiment_analyzer.analyze_symbol(symbol)
            
            # ML предсказание
            ml_prediction = await self.market_predictor.predict(symbol, market_data)
            
            # Выбор стратегии
            strategy_name = await self.ml_selector.select_strategy(
                symbol, market_data, sentiment_score, ml_prediction
            )
            
            # Получение сигнала от стратегии
            strategy = self.strategies.get(strategy_name)
            if strategy:
                signal = await strategy.generate_signal(symbol, market_data)
                
                if signal:
                    # Проверка риск-менеджмента
                    if await self.risk_manager.validate_signal(signal):
                        # Выполнение сделки
                        await self.trade_executor.execute_signal(signal)
                        
                        # Сохранение сигнала в БД
                        await self._save_signal(signal)
                        
                        # Уведомления
                        await self._send_trade_notification(signal)
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки пары {pair.symbol}: {e}")
    
    async def _start_ml_training(self):
        """Запуск ML обучения"""
        while self.is_running:
            try:
                # Переобучение моделей каждые 24 часа
                await self.model_trainer.train_all_models()
                await asyncio.sleep(24 * 3600)  # 24 часа
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Ошибка ML обучения: {e}")
                await asyncio.sleep(3600)  # Повтор через час
    
    async def _start_news_monitoring(self):
        """Запуск мониторинга новостей"""
        while self.is_running:
            try:
                await self.news_collector.collect_and_analyze()
                await asyncio.sleep(settings.NEWS_CHECK_INTERVAL)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Ошибка мониторинга новостей: {e}")
                await asyncio.sleep(300)  # 5 минут
    
    async def _start_social_monitoring(self):
        """Запуск мониторинга соцсетей"""
        tasks = [
            asyncio.create_task(self.twitter_monitor.start_monitoring()),
            asyncio.create_task(self.reddit_monitor.start_monitoring())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            for task in tasks:
                task.cancel()
        except Exception as e:
            self.logger.error(f"Ошибка мониторинга соцсетей: {e}")
    
    async def _start_system_monitoring(self):
        """Запуск системного мониторинга"""
        while self.is_running:
            try:
                system_stats = await self.system_monitor.get_system_stats()
                await self._check_system_health(system_stats)
                await asyncio.sleep(60)  # Каждую минуту
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Ошибка системного мониторинга: {e}")
                await asyncio.sleep(60)
    
    async def _get_active_trading_pairs(self) -> List[TradingPair]:
        """Получение активных торговых пар"""
        async with self._get_db_session() as db:
            return db.query(TradingPair).filter(TradingPair.is_active == True).all()
    
    async def _get_market_data(self, symbol: str) -> Dict:
        """Получение рыночных данных"""
        # Здесь должна быть логика получения данных с биржи
        # Возвращаем заглушку
        return {"symbol": symbol, "price": 0, "volume": 0}
    
    async def _save_signal(self, signal_data: Dict):
        """Сохранение сигнала в БД"""
        async with self._get_db_session() as db:
            signal = Signal(**signal_data)
            db.add(signal)
            await db.commit()
    
    async def _update_bot_state(self, **kwargs):
        """Обновление состояния бота в БД"""
        async with self._get_db_session() as db:
            bot_state = db.query(BotState).first()
            if not bot_state:
                bot_state = BotState()
                db.add(bot_state)
            
            for key, value in kwargs.items():
                setattr(bot_state, key, value)
            
            await db.commit()
    
    async def _update_performance_metrics(self):
        """Обновление метрик производительности"""
        try:
            await self.performance_tracker.update_metrics()
        except Exception as e:
            self.logger.error(f"Ошибка обновления метрик: {e}")
    
    async def _send_realtime_updates(self):
        """Отправка обновлений в реальном времени"""
        if self.socketio_manager:
            try:
                # Получение статистики
                stats = await self._get_bot_statistics()
                await self.socketio_manager.broadcast('bot_stats', stats)
            except Exception as e:
                self.logger.error(f"Ошибка отправки обновлений: {e}")
    
    async def _send_startup_notifications(self):
        """Отправка уведомлений о запуске"""
        message = f"🚀 Торговый бот запущен в {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}"
        
        await self.telegram_notifier.send_message(message)
        await self.email_notifier.send_notification("Бот запущен", message)
    
    async def _send_shutdown_notifications(self):
        """Отправка уведомлений об остановке"""
        stop_time = datetime.utcnow()
        runtime = stop_time - self.start_time if self.start_time else "Неизвестно"
        
        message = f"⏹️ Торговый бот остановлен в {stop_time.strftime('%Y-%m-%d %H:%M:%S')}\nВремя работы: {runtime}"
        
        await self.telegram_notifier.send_message(message)
        await self.email_notifier.send_notification("Бот остановлен", message)
    
    async def _send_trade_notification(self, signal_data: Dict):
        """Отправка уведомлений о сделке"""
        message = f"💰 Новый сигнал: {signal_data.get('action')} {signal_data.get('symbol')} по цене {signal_data.get('price')}"
        
        await self.telegram_notifier.send_message(message)
        
        if self.socketio_manager:
            await self.socketio_manager.broadcast('new_signal', signal_data)
    
    async def _check_system_health(self, stats: Dict):
        """Проверка состояния системы"""
        # Проверка загрузки CPU
        if stats.get('cpu_percent', 0) > 90:
            await self.telegram_notifier.send_message("⚠️ Высокая загрузка CPU!")
        
        # Проверка использования памяти
        if stats.get('memory_percent', 0) > 90:
            await self.telegram_notifier.send_message("⚠️ Высокое использование памяти!")
        
        # Проверка свободного места на диске
        if stats.get('disk_percent', 0) > 90:
            await self.telegram_notifier.send_message("⚠️ Мало свободного места на диске!")
    
    async def _get_bot_statistics(self) -> Dict:
        """Получение статистики бота"""
        async with self._get_db_session() as db:
            # Подсчет сделок
            total_trades = db.query(Trade).count()
            profitable_trades = db.query(Trade).filter(Trade.profit > 0).count()
            
            # Общая прибыль
            total_profit = db.query(Trade.profit).filter(Trade.profit.isnot(None)).scalar() or 0
            
            return {
                'is_running': self.is_running,
                'start_time': self.start_time.isoformat() if self.start_time else None,
                'total_trades': total_trades,
                'profitable_trades': profitable_trades,
                'total_profit': total_profit,
                'win_rate': (profitable_trades / total_trades * 100) if total_trades > 0 else 0
            }
    
    @asynccontextmanager
    async def _get_db_session(self):
        """Контекстный менеджер для работы с БД"""
        db = next(get_db())
        try:
            yield db
        finally:
            db.close()
    
    async def get_status(self) -> Dict:
        """Получение текущего статуса бота"""
        return {
            'is_running': self.is_running,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'components_status': {
                'ml_selector': bool(self.ml_selector),
                'trade_executor': bool(self.trade_executor),
                'news_collector': bool(self.news_collector),
                'websocket': bool(self.socketio_manager)
            }
        }
    
    async def restart(self):
        """Перезапуск бота"""
        self.logger.info("Перезапуск торгового бота...")
        await self.stop()
        await asyncio.sleep(5)  # Пауза между остановкой и запуском
        await self.start()

# Глобальный экземпляр менеджера
bot_manager = BotManager()