"""
TRADING BOT INTEGRATION - Интеграция реальной торговли с основным ботом
Файл: src/bot/trading_integration.py

🎯 ПОЛНАЯ АВТОМАТИЗАЦИЯ ТОРГОВЛИ:
✅ Объединяет все компоненты: стратегии → исполнение → мониторинг
✅ Автоматический поиск торговых возможностей 24/7
✅ Интеллектуальный выбор стратегий для рыночных условий
✅ Управление несколькими позициями одновременно
✅ Экстренные остановки и безопасность
"""
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

from ..core.database import SessionLocal
from ..strategies.strategy_selector import get_strategy_selector
from ..bot.signal_processor import SignalProcessor
from ..logging.smart_logger import get_logger
from ..exchange.real_client import get_real_exchange_client
from ..exchange.position_manager import get_position_manager
from ..exchange.execution_engine import get_execution_engine

logger = get_logger(__name__)

class TradingBotWithRealTrading:
    """
    🔥 ОСНОВНОЙ ТОРГОВЫЙ БОТ С РЕАЛЬНОЙ ТОРГОВЛЕЙ
    
    Полная архитектура автоматизированной торговли:
    
    ┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
    │   СТРАТЕГИИ     │───▶│  РИСК-МЕНЕДЖМЕНТ │───▶│   ИСПОЛНЕНИЕ    │
    │   - Technical   │    │  - Position Size │    │   - Real Orders │
    │   - ML Models   │    │  - Correlation   │    │   - Stop/Loss   │
    │   - Market      │    │  - Drawdown      │    │   - Monitoring  │
    └─────────────────┘    └──────────────────┘    └─────────────────┘
             │                        │                        │
             ▼                        ▼                        ▼
    ┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
    │   DATA FEED     │    │   DATABASE       │    │   REPORTING     │
    │   - Price Data  │    │   - Trades       │    │   - Analytics   │
    │   - News/Social │    │   - Signals      │    │   - WebSocket   │
    │   - Sentiment   │    │   - Performance  │    │   - Telegram    │
    └─────────────────┘    └──────────────────┘    └─────────────────┘
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Инициализация торгового бота
        
        Args:
            config: Конфигурация бота
        """
        self.config = config
        
        # Компоненты торговой системы
        self.exchange = get_real_exchange_client()
        self.execution_engine = get_execution_engine()
        self.position_manager = get_position_manager()
        self.strategy_selector = get_strategy_selector()
        self.signal_processor = SignalProcessor()
        
        # Состояние бота
        self.is_running = False
        self.is_trading_enabled = config.get('trading_enabled', False)
        self.emergency_stop = False
        
        # Настройки циклов
        self.analysis_interval = config.get('analysis_interval_seconds', 60)
        self.position_check_interval = config.get('position_check_interval_seconds', 30)
        
        # Торговые параметры
        self.trading_pairs = config.get('trading_pairs', ['BTCUSDT'])
        self.max_concurrent_trades = config.get('max_concurrent_trades', 3)
        
        # Статистика
        self.cycle_count = 0
        self.signals_generated = 0
        self.trades_executed = 0
        self.last_activity = datetime.utcnow()
        
        logger.info(
            "🚀 TradingBot с реальной торговлей инициализирован",
            category='bot',
            trading_enabled=self.is_trading_enabled,
            pairs_count=len(self.trading_pairs),
            analysis_interval=self.analysis_interval
        )
    
    # =================================================================
    # ОСНОВНЫЕ МЕТОДЫ БОТА
    # =================================================================
    
    async def start(self):
        """Запуск торгового бота"""
        if self.is_running:
            logger.warning("Бот уже запущен")
            return
        
        try:
            # Проверяем подключения
            await self._validate_connections()
            
            self.is_running = True
            
            logger.info(
                "🟢 Торговый бот запущен",
                category='bot',
                trading_enabled=self.is_trading_enabled
            )
            
            # Запускаем основные циклы
            tasks = [
                asyncio.create_task(self._main_trading_loop()),
                asyncio.create_task(self._position_monitoring_loop()),
                asyncio.create_task(self._health_check_loop())
            ]
            
            # Запускаем Position Manager если торговля включена
            if self.is_trading_enabled:
                tasks.append(asyncio.create_task(self.position_manager.start_monitoring()))
            
            # Ждем завершения всех задач
            await asyncio.gather(*tasks, return_exceptions=True)
            
        except Exception as e:
            logger.error(f"❌ Ошибка запуска бота: {e}")
            self.is_running = False
            raise
    
    async def stop(self):
        """Остановка торгового бота"""
        logger.info("⏹️ Остановка торгового бота", category='bot')
        
        self.is_running = False
        
        # Останавливаем Position Manager
        if hasattr(self.position_manager, 'stop_monitoring'):
            self.position_manager.stop_monitoring()
        
        logger.info("✅ Торговый бот остановлен", category='bot')
    
    async def emergency_stop_all(self):
        """Экстренная остановка всех операций"""
        logger.critical("🚨 ЭКСТРЕННАЯ ОСТАНОВКА ВСЕХ ОПЕРАЦИЙ", category='bot')
        
        self.emergency_stop = True
        self.is_trading_enabled = False
        
        # Активируем экстренную остановку в движке исполнения
        self.execution_engine.activate_emergency_stop("Bot emergency stop")
        
        # Закрываем все позиции
        try:
            closed_count = await self.execution_engine.close_all_positions_emergency()
            
            logger.critical(
                f"🚨 Экстренно закрыто позиций: {closed_count}",
                category='bot'
            )
            
        except Exception as e:
            logger.critical(f"🚨 ОШИБКА ЭКСТРЕННОГО ЗАКРЫТИЯ: {e}")
    
    # =================================================================
    # ОСНОВНЫЕ ЦИКЛЫ
    # =================================================================
    
    async def _main_trading_loop(self):
        """Основной цикл торговли"""
        logger.info("🔄 Запуск основного цикла торговли", category='bot')
        
        while self.is_running:
            try:
                if not self.emergency_stop:
                    await self._trading_cycle()
                
                await asyncio.sleep(self.analysis_interval)
                
            except Exception as e:
                logger.error(f"❌ Ошибка в торговом цикле: {e}")
                await asyncio.sleep(10)  # Пауза при ошибке
    
    async def _trading_cycle(self):
        """Один цикл анализа и торговли"""
        start_time = datetime.utcnow()
        self.cycle_count += 1
        
        try:
            # 1. Анализ рынка для всех пар
            market_analysis_results = {}
            
            for symbol in self.trading_pairs:
                try:
                    analysis = await self._analyze_market_for_symbol(symbol)
                    market_analysis_results[symbol] = analysis
                    
                except Exception as e:
                    logger.error(f"❌ Ошибка анализа {symbol}: {e}")
                    continue
            
            # 2. Генерация сигналов
            trading_signals = []
            
            for symbol, analysis in market_analysis_results.items():
                try:
                    signals = await self._generate_signals_for_symbol(symbol, analysis)
                    trading_signals.extend(signals)
                    
                except Exception as e:
                    logger.error(f"❌ Ошибка генерации сигналов {symbol}: {e}")
                    continue
            
            # 3. Обработка и исполнение сигналов
            if trading_signals and self.is_trading_enabled:
                await self._process_trading_signals(trading_signals)
            
            # 4. Обновление статистики
            cycle_time = (datetime.utcnow() - start_time).total_seconds()
            self.last_activity = datetime.utcnow()
            
            logger.debug(
                f"✅ Торговый цикл завершен",
                category='bot',
                cycle_count=self.cycle_count,
                cycle_time=cycle_time,
                symbols_analyzed=len(market_analysis_results),
                signals_generated=len(trading_signals)
            )
            
        except Exception as e:
            logger.error(f"❌ Ошибка в торговом цикле: {e}")
    
    async def _position_monitoring_loop(self):
        """Цикл мониторинга позиций"""
        logger.info("👁️ Запуск цикла мониторинга позиций", category='bot')
        
        while self.is_running:
            try:
                if not self.emergency_stop:
                    await self._check_positions_health()
                
                await asyncio.sleep(self.position_check_interval)
                
            except Exception as e:
                logger.error(f"❌ Ошибка мониторинга позиций: {e}")
                await asyncio.sleep(5)
    
    async def _health_check_loop(self):
        """Цикл проверки здоровья системы"""
        while self.is_running:
            try:
                await self._system_health_check()
                await asyncio.sleep(300)  # Каждые 5 минут
                
            except Exception as e:
                logger.error(f"❌ Ошибка проверки здоровья: {e}")
                await asyncio.sleep(60)
    
    # =================================================================
    # МЕТОДЫ АНАЛИЗА И ТОРГОВЛИ
    # =================================================================
    
    async def _analyze_market_for_symbol(self, symbol: str) -> Dict[str, Any]:
        """Анализ рынка для конкретного символа"""
        try:
            # Получаем рыночные данные
            candles = await self.exchange.get_candles(symbol, '5m', limit=200)
            ticker = await self.exchange.fetch_ticker(symbol)
            order_book = await self.exchange.fetch_order_book(symbol)
            
            # Текущие условия рынка
            market_conditions = {
                'symbol': symbol,
                'current_price': ticker['last'],
                'volume_24h': ticker['quoteVolume'],
                'price_change_24h': ticker['percentage'],
                'bid_ask_spread': (ticker['ask'] - ticker['bid']) / ticker['last'] * 100,
                'candles': candles,
                'order_book': order_book,
                'timestamp': datetime.utcnow()
            }
            
            return market_conditions
            
        except Exception as e:
            logger.error(f"❌ Ошибка анализа рынка {symbol}: {e}")
            return {}
    
    async def _generate_signals_for_symbol(self, symbol: str, 
                                         market_analysis: Dict[str, Any]) -> List:
        """Генерация торговых сигналов для символа"""
        try:
            if not market_analysis:
                return []
            
            # Получаем оптимальную стратегию
            recommended_strategy = await self.strategy_selector.select_optimal_strategy(
                symbol=symbol,
                market_conditions=market_analysis
            )
            
            if not recommended_strategy:
                return []
            
            strategy_name = recommended_strategy['strategy']
            strategy = self.strategy_selector.get_strategy(strategy_name)
            
            if not strategy:
                return []
            
            # Генерируем сигнал
            signal = await strategy.analyze(market_analysis['candles'])
            
            if signal and signal.action != 'HOLD':
                self.signals_generated += 1
                
                logger.info(
                    f"📈 Сигнал сгенерирован",
                    category='bot',
                    symbol=symbol,
                    action=signal.action,
                    strategy=strategy_name,
                    confidence=recommended_strategy.get('confidence', 0),
                    price=signal.price
                )
                
                return [{
                    'signal': signal,
                    'strategy_name': strategy_name,
                    'confidence': recommended_strategy.get('confidence', 0),
                    'market_conditions': market_analysis
                }]
            
            return []
            
        except Exception as e:
            logger.error(f"❌ Ошибка генерации сигналов {symbol}: {e}")
            return []
    
    async def _process_trading_signals(self, signals: List[Dict]) -> None:
        """Обработка торговых сигналов"""
        try:
            # Проверяем лимит одновременных сделок
            current_positions = await self.position_manager.get_positions_summary()
            active_trades = current_positions['total_positions']
            
            if active_trades >= self.max_concurrent_trades:
                logger.info(
                    f"⚠️ Лимит одновременных сделок достигнут: {active_trades}/{self.max_concurrent_trades}",
                    category='bot'
                )
                return
            
            # Сортируем сигналы по уверенности
            signals.sort(key=lambda x: x['confidence'], reverse=True)
            
            # Исполняем сигналы
            executed_count = 0
            
            for signal_data in signals:
                if executed_count >= (self.max_concurrent_trades - active_trades):
                    break
                
                try:
                    # Исполняем через Execution Engine
                    result = await self.execution_engine.execute_signal(
                        signal=signal_data['signal'],
                        strategy_name=signal_data['strategy_name'],
                        confidence=signal_data['confidence'],
                        market_conditions=signal_data['market_conditions']
                    )
                    
                    if result.status.value == 'completed':
                        executed_count += 1
                        self.trades_executed += 1
                        
                        logger.info(
                            f"✅ Сделка исполнена",
                            category='bot',
                            symbol=signal_data['signal'].symbol,
                            trade_id=result.trade_id,
                            order_id=result.order_id
                        )
                    
                except Exception as e:
                    logger.error(f"❌ Ошибка исполнения сигнала: {e}")
            
            if executed_count > 0:
                logger.info(
                    f"📊 Исполнено сделок в цикле: {executed_count}",
                    category='bot'
                )
                
        except Exception as e:
            logger.error(f"❌ Ошибка обработки сигналов: {e}")
    
    async def _check_positions_health(self):
        """Проверка здоровья позиций"""
        try:
            positions_summary = await self.position_manager.get_positions_summary()
            
            if positions_summary['total_positions'] > 0:
                total_pnl = positions_summary['total_pnl']
                total_pnl_percent = positions_summary['total_pnl_percent']
                
                # Проверяем критические условия
                if total_pnl_percent < -10:  # -10% общий PnL
                    logger.warning(
                        f"⚠️ Критический PnL: {total_pnl_percent:.1f}%",
                        category='bot',
                        total_pnl=total_pnl
                    )
                
                # Логируем статус позиций
                logger.debug(
                    f"📊 Позиции: {positions_summary['total_positions']} | PnL: {total_pnl:.2f} USDT ({total_pnl_percent:.1f}%)",
                    category='bot'
                )
                
        except Exception as e:
            logger.error(f"❌ Ошибка проверки позиций: {e}")
    
    async def _system_health_check(self):
        """Проверка здоровья системы"""
        try:
            # Проверяем подключение к бирже
            if not self.exchange.is_connected:
                logger.error("❌ Потеряно подключение к бирже", category='bot')
                return
            
            # Проверяем статистику исполнений
            exec_stats = self.execution_engine.get_execution_stats()
            success_rate = exec_stats['success_rate_percent']
            
            if success_rate < 80 and exec_stats['total_executions'] > 10:
                logger.warning(
                    f"⚠️ Низкий успех исполнений: {success_rate:.1f}%",
                    category='bot'
                )
            
            # Проверяем активность
            time_since_activity = (datetime.utcnow() - self.last_activity).total_seconds()
            if time_since_activity > 600:  # 10 минут без активности
                logger.warning(
                    f"⚠️ Нет активности {time_since_activity:.0f} секунд",
                    category='bot'
                )
            
            logger.debug(
                "💓 Проверка здоровья системы пройдена",
                category='bot',
                cycles=self.cycle_count,
                signals=self.signals_generated,
                trades=self.trades_executed
            )
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки здоровья: {e}")
    
    # =================================================================
    # ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ
    # =================================================================
    
    async def _validate_connections(self):
        """Валидация всех подключений"""
        try:
            # Проверяем подключение к бирже
            if not self.exchange.is_connected:
                raise Exception("Нет подключения к бирже")
            
            # Проверяем баланс
            balance = await self.exchange.fetch_balance()
            usdt_balance = balance.get('USDT', {}).get('free', 0)
            
            if usdt_balance < 10:
                logger.warning(
                    f"⚠️ Низкий баланс: {usdt_balance:.2f} USDT",
                    category='bot'
                )
            
            logger.info(
                "✅ Все подключения проверены",
                category='bot',
                balance_usdt=usdt_balance
            )
            
        except Exception as e:
            logger.error(f"❌ Ошибка валидации подключений: {e}")
            raise
    
    def get_bot_status(self) -> Dict[str, Any]:
        """Получение статуса бота"""
        exec_stats = self.execution_engine.get_execution_stats()
        
        return {
            'is_running': self.is_running,
            'is_trading_enabled': self.is_trading_enabled,
            'emergency_stop': self.emergency_stop,
            'cycle_count': self.cycle_count,
            'signals_generated': self.signals_generated,
            'trades_executed': self.trades_executed,
            'last_activity': self.last_activity,
            'trading_pairs_count': len(self.trading_pairs),
            'execution_stats': exec_stats
        }
    
    def enable_trading(self):
        """Включение торговли"""
        self.is_trading_enabled = True
        self.execution_engine.deactivate_emergency_stop()
        
        logger.info("✅ Торговля включена", category='bot')
    
    def disable_trading(self):
        """Отключение торговли"""
        self.is_trading_enabled = False
        
        logger.info("⏸️ Торговля отключена", category='bot')

# =================================================================
# ГЛОБАЛЬНЫЕ ФУНКЦИИ
# =================================================================

# Глобальный экземпляр
trading_bot = None

def get_trading_bot(config: Optional[Dict] = None) -> TradingBotWithRealTrading:
    """Получить глобальный экземпляр торгового бота"""
    global trading_bot
    
    if trading_bot is None and config:
        trading_bot = TradingBotWithRealTrading(config)
    
    return trading_bot

def create_trading_bot(config: Dict[str, Any]) -> TradingBotWithRealTrading:
    """Создать новый экземпляр торгового бота"""
    return TradingBotWithRealTrading(config)

# Экспорты
__all__ = [
    'TradingBotWithRealTrading',
    'get_trading_bot',
    'create_trading_bot'
]