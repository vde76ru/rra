"""
Единый менеджер торгового бота - ядро системы
Путь: /var/www/www-root/data/www/systemetech.ru/src/bot/manager.py

Этот файл является "мозгом" всего торгового бота. Он управляет:
- Запуском и остановкой торговли
- Координацией всех компонентов (биржа, стратегии, уведомления)
- Управлением позициями и рисками
- Сохранением статистики и состояния

Важные принципы архитектуры:
1. Singleton pattern - только один экземпляр менеджера
2. Graceful degradation - продолжаем работу даже при частичных сбоях
3. Подробное логирование для отладки и мониторинга
4. Безопасная работа с базой данных
"""

import asyncio
import sys
import logging
import psutil
import os
from typing import Any, List, Optional, Tuple, Dict
from datetime import datetime, timedelta
from enum import Enum
import random

# ✅ ВАЖНО: Импорты для безопасной работы с SQL
from sqlalchemy import text, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError


# Импорты компонентов нашей системы
from ..core.config import config
from ..core.database import SessionLocal
from ..core.models import Trade, Signal, BotState, TradingPair, TradeStatus, OrderSide, Balance, User
from ..exchange.client import ExchangeClient
from ..strategies import strategy_factory
from ..analysis.market_analyzer import MarketAnalyzer
from ..notifications.telegram import telegram_notifier
from .trader import Trader
from .risk_manager import RiskManager
from ..strategies.auto_strategy_selector import auto_strategy_selector
from ..logging.smart_logger import SmartLogger
from ..logging.log_manager import cleanup_scheduler

# Настраиваем логгер для этого модуля
smart_logger = SmartLogger(__name__)
logger = smart_logger  # Для совместимости со старым кодом


class BotStatus(Enum):
    """
    Возможные статусы бота
    
    Каждый статус имеет свое назначение:
    - STOPPED: Бот полностью остановлен
    - STARTING: Процесс запуска (проверки, инициализация)
    - RUNNING: Бот активно торгует
    - STOPPING: Процесс остановки (закрытие позиций, сохранение данных)
    - ERROR: Критическая ошибка, требующая вмешательства
    """
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"

class BotManager:
    """
    Единый менеджер для всего бота
    
    Этот класс реализует паттерн Singleton, что означает:
    - Может существовать только один экземпляр
    - Все компоненты системы используют один и тот же менеджер
    - Состояние сохраняется между вызовами
    
    Управляет всеми компонентами торговой системы:
    - Подключением к бирже
    - Анализом рынка
    - Исполнением сделок
    - Управлением рисками
    - Уведомлениями
    """
    
    # Переменные класса для реализации Singleton
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """
        Реализация паттерна Singleton
        
        Этот метод гарантирует, что создается только один экземпляр класса.
        При повторных вызовах BotManager() возвращается тот же объект.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """
        Инициализация компонентов (только при первом создании)
        
        Используем флаг _initialized, чтобы избежать повторной инициализации
        при многократных вызовах конструктора (особенность Singleton).
        """
        if not BotManager._initialized:
            logger.info("🔧 Инициализируем BotManager...")
            
            # Инициализация системы логирования
            asyncio.create_task(self._initialize_logging())
            
            # === ОСНОВНЫЕ КОМПОНЕНТЫ ===
            # Каждый компонент отвечает за свою область
            self.exchange = ExchangeClient()           # Взаимодействие с биржей
            self.analyzer = MarketAnalyzer()           # Анализ рыночных данных
            self.notifier = telegram_notifier          # Уведомления в Telegram
            self.strategy_factory = strategy_factory  # Создание торговых стратегий
            self.trader = Trader(self.exchange)        # Исполнение сделок
            self.risk_manager = RiskManager()          # Управление рисками
            
            # === СОСТОЯНИЕ БОТА ===
            self.status = BotStatus.STOPPED
            self.positions: Dict[str, Trade] = {}      # Открытые позиции {symbol: Trade}
            self.active_pairs: List[str] = []          # Активные торговые пары
            
            # === УПРАВЛЕНИЕ ПРОЦЕССОМ ===
            self._main_task: Optional[asyncio.Task] = None  # Основная задача торговли
            self._stop_event = asyncio.Event()              # Событие для остановки
            self._process_info: Dict = {}                   # Информация о процессе
            
            # === СТАТИСТИКА ===
            self.start_time: Optional[datetime] = None
            self.cycles_count = 0                      # Количество циклов анализа
            self.trades_today = 0                      # Сделок за сегодня
            
            # Загружаем сохраненное состояние из базы данных
            self._load_state_from_db()
            
            # Помечаем как инициализированный
            BotManager._initialized = True
            logger.info("✅ BotManager инициализирован успешно")
    
    async def _initialize_logging(self):
    """Инициализирует систему логирования"""
    try:
        # Запускаем DB writer для логов
        await smart_logger.start_db_writer()
        
        # Запускаем планировщик очистки
        await cleanup_scheduler.start()
        
        smart_logger.info(
            "Система умного логирования инициализирована",
            category='system',
            log_stats=smart_logger.get_statistics()
        )
    except Exception as e:
        logger.error(f"Ошибка инициализации системы логирования: {e}")
        # Можно добавить fallback на обычное логирование
    
    
    # =========================================================================
    # === УПРАВЛЕНИЕ ЖИЗНЕННЫМ ЦИКЛОМ БОТА ===
    # =========================================================================
    
    async def start(self) -> Tuple[bool, str]:
        """
        Запуск торгового бота
        
        Последовательность запуска:
        1. Проверка текущего статуса
        2. Предварительные проверки (API, БД, баланс)
        3. Загрузка конфигурации
        4. Запуск основного торгового цикла
        5. Уведомление о запуске
        
        Returns:
            Tuple[bool, str]: (успешность, сообщение)
        """
        # Проверяем, не запущен ли уже бот
        if self.status in [BotStatus.RUNNING, BotStatus.STARTING]:
            message = f"Бот уже {self.status.value}"
            logger.warning(f"⚠️ {message}")
            return False, message
        
        try:
            # Устанавливаем статус "запускается"
            self.status = BotStatus.STARTING
            smart_logger.info(
                "🚀 Начинаем запуск торгового бота...",
                category='system',
                action='bot_start'
            )
                        
            # === ШАГ 1: ПРЕДВАРИТЕЛЬНЫЕ ПРОВЕРКИ ===
            logger.info("🔍 Выполняем предварительные проверки...")
            if not await self._pre_start_checks():
                raise ValueError("Предварительные проверки не пройдены")
            
            # === ШАГ 2: ЗАГРУЗКА КОНФИГУРАЦИИ ===
            logger.info("📋 Загружаем конфигурацию...")
            await self._load_configuration()
            
            # === ШАГ 3: ОБНОВЛЕНИЕ СОСТОЯНИЯ В БД ===
            logger.info("💾 Обновляем состояние в базе данных...")
            self._update_bot_state_db(is_running=True)
            
            # === ШАГ 4: ЗАПУСК ОСНОВНОГО ЦИКЛА ===
            logger.info("🔄 Запускаем основной торговый цикл...")
            self._stop_event.clear()  # Сбрасываем флаг остановки
            self._main_task = asyncio.create_task(self._trading_loop())
            
            # === ШАГ 5: ОБНОВЛЕНИЕ ИНФОРМАЦИИ О ПРОЦЕССЕ ===
            self._update_process_info()
            
            # === ШАГ 6: УВЕДОМЛЕНИЕ О ЗАПУСКЕ ===
            try:
                await self.notifier.send_startup_message(
                    pairs=self.active_pairs,
                    mode='TESTNET' if config.BYBIT_TESTNET else 'MAINNET'
                )
            except Exception as notify_error:
                # Не падаем из-за ошибки уведомления
                logger.warning(f"⚠️ Не удалось отправить уведомление о запуске: {notify_error}")
            
            # === ФИНАЛ: УСПЕШНЫЙ ЗАПУСК ===
            self.status = BotStatus.RUNNING
            self.start_time = datetime.utcnow()
            
            success_message = f"Бот успешно запущен. Активные пары: {len(self.active_pairs)}"
            logger.info(f"✅ {success_message}")
            return True, success_message
            
        except Exception as e:
            # При любой ошибке переводим в статус ERROR
            self.status = BotStatus.ERROR
            error_msg = f"Ошибка запуска: {str(e)}"
            logger.error(f"❌ {error_msg}", exc_info=True)
            
            # Обновляем состояние в БД
            self._update_bot_state_db(is_running=False)
            
            return False, error_msg
    
    async def stop(self) -> Tuple[bool, str]:
        """
        Остановка торгового бота
        
        Последовательность остановки:
        1. Проверка текущего статуса
        2. Сигнал остановки основному циклу
        3. Ожидание завершения торгового цикла
        4. Закрытие всех открытых позиций
        5. Сохранение статистики
        6. Уведомление об остановке
        
        Returns:
            Tuple[bool, str]: (успешность, сообщение)
        """
        # Проверяем, что есть что останавливать
        if self.status not in [BotStatus.RUNNING, BotStatus.ERROR]:
            message = f"Бот не запущен (текущий статус: {self.status.value})"
            logger.warning(f"⚠️ {message}")
            return False, message
        
        try:
            # Устанавливаем статус "останавливается"
            self.status = BotStatus.STOPPING
            logger.info("🛑 Начинаем остановку торгового бота...")
            
            # === ШАГ 1: СИГНАЛ ОСТАНОВКИ ===
            logger.info("📡 Подаем сигнал остановки основному циклу...")
            self._stop_event.set()
            
            # === ШАГ 2: ОЖИДАНИЕ ЗАВЕРШЕНИЯ ОСНОВНОЙ ЗАДАЧИ ===
            if self._main_task and not self._main_task.done():
                logger.info("⏳ Ожидаем завершения торгового цикла (максимум 30 секунд)...")
                try:
                    await asyncio.wait_for(self._main_task, timeout=30.0)
                    logger.info("✅ Торговый цикл завершен корректно")
                except asyncio.TimeoutError:
                    logger.warning("⚠️ Таймаут ожидания, принудительно останавливаем цикл")
                    self._main_task.cancel()
                    try:
                        await self._main_task
                    except asyncio.CancelledError:
                        logger.info("✅ Торговый цикл принудительно остановлен")
            
            # === ШАГ 3: ЗАКРЫТИЕ ПОЗИЦИЙ ===
            logger.info("🔄 Закрываем все открытые позиции...")
            await self._close_all_positions("Bot shutdown")
            
            # === ШАГ 4: ОБНОВЛЕНИЕ СОСТОЯНИЯ В БД ===
            logger.info("💾 Обновляем состояние в базе данных...")
            self._update_bot_state_db(is_running=False)
            
            # === ШАГ 5: СОХРАНЕНИЕ СТАТИСТИКИ ===
            logger.info("📊 Сохраняем статистику работы...")
            self._save_statistics()
            
            # === ШАГ 6: УВЕДОМЛЕНИЕ ОБ ОСТАНОВКЕ ===
            try:
                runtime = datetime.utcnow() - self.start_time if self.start_time else None
                await self.notifier.send_shutdown_message(
                    runtime=runtime,
                    trades_count=self.trades_today
                )
            except Exception as notify_error:
                # Не падаем из-за ошибки уведомления
                logger.warning(f"⚠️ Не удалось отправить уведомление об остановке: {notify_error}")
            
            # === ФИНАЛ: УСПЕШНАЯ ОСТАНОВКА ===
            self.status = BotStatus.STOPPED
            self.start_time = None
            
            success_message = "Бот успешно остановлен"
            logger.info(f"✅ {success_message}")
            return True, success_message
            
        except Exception as e:
            # При ошибке остановки все равно помечаем как остановленный
            self.status = BotStatus.ERROR
            error_msg = f"Ошибка при остановке: {str(e)}"
            logger.error(f"❌ {error_msg}", exc_info=True)
            return False, error_msg
    
    # =========================================================================
    # === ОСНОВНОЙ ТОРГОВЫЙ ЦИКЛ ===
    # =========================================================================
    
    async def _trading_loop(self):
        """
        Основной торговый цикл бота
        
        Этот метод является "сердцем" бота. Он работает в бесконечном цикле и:
        1. Проверяет торговые лимиты
        2. Обновляет баланс
        3. Анализирует каждую активную пару
        4. Генерирует и исполняет торговые сигналы
        5. Управляет открытыми позициями
        6. Делает паузы для имитации человеческого поведения
        
        Цикл продолжается до получения сигнала остановки.
        """
        logger.info("🔄 Основной торговый цикл запущен")
        
        # Основной бесконечный цикл
        while not self._stop_event.is_set():
            try:
                # Увеличиваем счетчик циклов
                self.cycles_count += 1
                cycle_start = datetime.utcnow()
                
                logger.debug(f"📊 Начинаем цикл анализа #{self.cycles_count}")
                
                # === ШАГ 1: ПРОВЕРКА ТОРГОВЫХ ЛИМИТОВ ===
                if not self._check_trading_limits():
                    logger.info("📊 Достигнуты дневные лимиты торговли, делаем длинную паузу")
                    await self._human_delay(300, 600)  # Пауза 5-10 минут
                    continue
                
                # === ШАГ 2: ОБНОВЛЕНИЕ БАЛАНСА ===
                try:
                    await self._update_balance()
                except Exception as balance_error:
                    logger.warning(f"⚠️ Не удалось обновить баланс: {balance_error}")
                
                # === ШАГ 3: АНАЛИЗ ВСЕХ АКТИВНЫХ ПАР ===
                for symbol in self.active_pairs:
                    # Проверяем сигнал остановки перед каждой парой
                    if self._stop_event.is_set():
                        logger.info("🛑 Получен сигнал остановки, прерываем анализ пар")
                        break
                    
                    try:
                        logger.debug(f"🔍 Анализируем пару: {symbol}")
                        
                        # Анализируем рыночные данные
                        market_data = await self.analyzer.analyze_symbol(symbol)
                        if not market_data:
                            logger.debug(f"📊 Нет данных для анализа {symbol}")
                            continue
                        
                        # Генерируем торговый сигнал
                        signal = await self._generate_signal(symbol, market_data)
                        if not signal:
                            logger.debug(f"📊 Сигнал для {symbol} не сгенерирован")
                            continue
                        
                        # Сохраняем сигнал в базу данных
                        self._save_signal(signal)
                        
                        # Исполняем сигнал если он достаточно сильный
                        if signal.action in ['BUY', 'SELL'] and signal.confidence >= 0.6:
                            logger.info(f"🎯 Сильный сигнал {signal.action} для {symbol} (уверенность: {signal.confidence:.1%})")
                            await self._execute_signal_human_like(signal)
                        else:
                            logger.debug(f"📊 Слабый сигнал для {symbol}: {signal.action} (уверенность: {signal.confidence:.1%})")
                        
                    except Exception as symbol_error:
                        logger.error(f"❌ Ошибка анализа {symbol}: {symbol_error}")
                        # Отправляем уведомление об ошибке, но продолжаем работу
                        try:
                            await self.notifier.send_error(f"Ошибка анализа {symbol}: {str(symbol_error)}")
                        except:
                            pass  # Не падаем из-за ошибки уведомления
                
                # === ШАГ 4: УПРАВЛЕНИЕ ОТКРЫТЫМИ ПОЗИЦИЯМИ ===
                try:
                    await self._manage_positions()
                except Exception as positions_error:
                    logger.error(f"❌ Ошибка управления позициями: {positions_error}")
                
                # === ШАГ 5: ОБНОВЛЕНИЕ СТАТИСТИКИ ===
                try:
                    self._update_statistics()
                except Exception as stats_error:
                    logger.warning(f"⚠️ Ошибка обновления статистики: {stats_error}")
                
                # === ШАГ 6: ПАУЗА МЕЖДУ ЦИКЛАМИ ===
                cycle_duration = (datetime.utcnow() - cycle_start).total_seconds()
                logger.debug(f"⏱️ Цикл #{self.cycles_count} выполнен за {cycle_duration:.1f} секунд")
                
                # Делаем паузу с имитацией человеческого поведения
                await self._human_delay()
                
            except asyncio.CancelledError:
                logger.info("🛑 Торговый цикл был отменен")
                break
            except Exception as cycle_error:
                logger.error(f"❌ Критическая ошибка в торговом цикле: {cycle_error}", exc_info=True)
                # Отправляем уведомление и делаем паузу перед следующей попыткой
                try:
                    await self.notifier.send_error(f"Критическая ошибка цикла: {str(cycle_error)}")
                except:
                    pass
                await self._human_delay(60, 180)  # Пауза 1-3 минуты при ошибке
        
        logger.info("🏁 Основной торговый цикл завершен")
    
    # =========================================================================
    # === ГЕНЕРАЦИЯ И ИСПОЛНЕНИЕ ТОРГОВЫХ СИГНАЛОВ ===
    # =========================================================================
    
    async def _generate_signal(self, symbol: str, market_data: Dict) -> Optional[Signal]:
        """
        Генерация торгового сигнала с автоматическим выбором стратегии
        
        Новая версия:
        1. Автоматически выбирает лучшую стратегию для текущих условий
        2. Использует машинное обучение для улучшения выбора
        3. Адаптируется к изменениям рынка
        
        Args:
            symbol: Торговая пара (например, 'BTCUSDT')
            market_data: Данные о рынке (цены, объемы, индикаторы)
            
        Returns:
            Signal или None если сигнал не сгенерирован
        """
        try:
            logger.info(f"🎯 Генерируем сигнал для {symbol}")
            
            # === ШАГ 1: АВТОМАТИЧЕСКИЙ ВЫБОР СТРАТЕГИИ ===
            # Используем интеллектуальный селектор
            best_strategy_name, strategy_confidence = await auto_strategy_selector.select_best_strategy(symbol)
            
            logger.info(f"🧠 Выбрана стратегия '{best_strategy_name}' для {symbol} "
                       f"с уверенностью {strategy_confidence:.1%}")
            
            # === ШАГ 2: ПОЛУЧАЕМ КОНФИГУРАЦИЮ ПАРЫ ===
            pair_config = self._get_pair_config(symbol)
            
            # Обновляем стратегию в конфигурации на выбранную
            # (это временное изменение, не сохраняется в БД)
            original_strategy = pair_config.strategy
            pair_config.strategy = best_strategy_name
            
            # === ШАГ 3: СОЗДАЕМ ЭКЗЕМПЛЯР ВЫБРАННОЙ СТРАТЕГИИ ===
            try:
                strategy = self.strategy_factory.create(best_strategy_name)
            except ValueError as e:
                logger.error(f"❌ Не удалось создать стратегию {best_strategy_name}: {e}")
                # Fallback к безопасной стратегии
                strategy = self.strategy_factory.create('safe_multi_indicator')
                best_strategy_name = 'safe_multi_indicator'
            
            # === ШАГ 4: АНАЛИЗИРУЕМ РЫНОЧНЫЕ ДАННЫЕ ===
            analysis = await strategy.analyze(market_data['df'], symbol)
            
            # Если стратегия рекомендует ждать, сигнал не генерируем
            if analysis.action == 'WAIT':
                logger.debug(f"📊 Стратегия {best_strategy_name} рекомендует ждать: {analysis.reason}")
                return None
            
            # === ШАГ 5: КОРРЕКТИРУЕМ УВЕРЕННОСТЬ ===
            # Учитываем уверенность в выборе стратегии
            combined_confidence = analysis.confidence * strategy_confidence
            
            # Если общая уверенность слишком низкая, не торгуем
            if combined_confidence < 0.5:
                logger.info(f"📊 Низкая общая уверенность ({combined_confidence:.1%}), "
                           f"пропускаем сигнал")
                return None
            
            # === ШАГ 6: СОЗДАЕМ СИГНАЛ ===
            signal = Signal(
                symbol=symbol,
                action=analysis.action,
                confidence=combined_confidence,
                price=market_data['current_price'],
                stop_loss=analysis.stop_loss,
                take_profit=analysis.take_profit,
                strategy=best_strategy_name,  # Используем выбранную стратегию
                reason=f"[AUTO] {analysis.reason} (стратегия: {best_strategy_name}, "
                       f"уверенность выбора: {strategy_confidence:.1%})",
                created_at=datetime.utcnow()
            )
            
            logger.info(f"✅ Сгенерирован сигнал {signal.action} для {symbol}: {signal.reason}")
            
            # === ШАГ 7: ОБУЧЕНИЕ СЕЛЕКТОРА ===
            # Асинхронно запускаем обучение если накопилось достаточно данных
            if len(auto_strategy_selector.selection_history) > 100 and \
               len(auto_strategy_selector.selection_history) % 100 == 0:
                asyncio.create_task(self._train_strategy_selector())
            
            return signal
            
        except Exception as e:
            logger.error(f"❌ Ошибка генерации сигнала для {symbol}: {e}")
            return None
            
    async def _train_strategy_selector(self):
        """Асинхронное обучение селектора стратегий"""
        try:
            logger.info("🎓 Запускаем обучение селектора стратегий...")
            await asyncio.get_event_loop().run_in_executor(
                None, auto_strategy_selector.train_ml_model
            )
        except Exception as e:
            logger.error(f"❌ Ошибка обучения селектора: {e}")
    
    # =========================================================================
    # === УПРАВЛЕНИЕ ОТКРЫТЫМИ ПОЗИЦИЯМИ ===
    # =========================================================================
    
    async def _manage_positions(self):
        """
        Управление всеми открытыми позициями
        
        Для каждой позиции проверяем:
        1. Достижение стоп-лосса
        2. Достижение тейк-профита
        3. Таймаут позиции (если настроен)
        4. Изменение рыночных условий
        
        При необходимости закрываем позицию.
        """
        if not self.positions:
            return  # Нет открытых позиций
        
        logger.debug(f"🔄 Проверяем {len(self.positions)} открытых позиций")
        
        # Создаем копию словаря для безопасной итерации
        positions_copy = list(self.positions.items())
        
        for symbol, trade in positions_copy:
            try:
                # Получаем текущую цену с биржи
                ticker = await self.exchange.fetch_ticker(symbol)
                current_price = ticker['last']
                
                # Проверяем условия закрытия позиции
                should_close, reason = self._should_close_position(trade, current_price)
                
                if should_close:
                    logger.info(f"🔄 Закрываем позицию {symbol}: {reason}")
                    await self._close_position(trade, current_price, reason)
                    # Удаляем из активных позиций
                    if symbol in self.positions:
                        del self.positions[symbol]
                else:
                    # Обновляем текущую прибыль/убыток
                    self._update_position_pnl(trade, current_price)
                
            except Exception as position_error:
                logger.error(f"❌ Ошибка управления позицией {symbol}: {position_error}")
                # Продолжаем с другими позициями
    
    def _should_close_position(self, trade: Trade, current_price: float) -> Tuple[bool, str]:
        """
        Определяет, нужно ли закрывать позицию
        
        Args:
            trade: Открытая сделка
            current_price: Текущая цена
            
        Returns:
            Tuple[bool, str]: (нужно_закрывать, причина)
        """
        # Для длинных позиций (BUY)
        if trade.side == OrderSide.BUY:
            if current_price <= trade.stop_loss:
                return True, "Stop Loss triggered"
            elif current_price >= trade.take_profit:
                return True, "Take Profit triggered"
        
        # Для коротких позиций (SELL)
        else:
            if current_price >= trade.stop_loss:
                return True, "Stop Loss triggered"
            elif current_price <= trade.take_profit:
                return True, "Take Profit triggered"
        
        # Проверяем таймаут позиции (например, максимум 24 часа)
        if hasattr(config, 'MAX_POSITION_HOURS'):
            position_age = datetime.utcnow() - trade.created_at
            if position_age.total_seconds() > config.MAX_POSITION_HOURS * 3600:
                return True, "Position timeout"
        
        return False, ""
    
    def _update_position_pnl(self, trade: Trade, current_price: float):
        """
        Обновляет текущую прибыль/убыток позиции
        
        Args:
            trade: Сделка для обновления
            current_price: Текущая цена
        """
        try:
            if trade.side == OrderSide.BUY:
                # Для длинной позиции: прибыль = (текущая цена - цена входа) * количество
                unrealized_pnl = (current_price - trade.entry_price) * trade.quantity
            else:
                # Для короткой позиции: прибыль = (цена входа - текущая цена) * количество
                unrealized_pnl = (trade.entry_price - current_price) * trade.quantity
            
            # Учитываем комиссию
            commission = trade.commission or 0
            trade.unrealized_pnl = unrealized_pnl - commission
            
        except Exception as e:
            logger.warning(f"⚠️ Ошибка обновления PnL для {trade.symbol}: {e}")
    
    async def _close_position(self, trade: Trade, current_price: float, reason: str):
        """
        Закрытие конкретной позиции
        
        Args:
            trade: Сделка для закрытия
            current_price: Цена закрытия
            reason: Причина закрытия
        """
        try:
            # Отправляем ордер на закрытие через trader
            close_result = await self.trader.close_position(trade, current_price)
            
            if close_result:
                # Обновляем информацию о сделке
                trade.exit_price = current_price
                trade.status = TradeStatus.CLOSED
                trade.closed_at = datetime.utcnow()
                trade.notes = reason
                
                # Рассчитываем итоговую прибыль
                trade.calculate_profit()
                
                # Сохраняем в базу данных
                self._update_trade_db(trade)
                
                # Отправляем уведомление
                try:
                    await self.notifier.send_trade_closed(
                        symbol=trade.symbol,
                        side=trade.side.value if hasattr(trade.side, 'value') else str(trade.side),
                        profit=trade.profit,
                        reason=reason
                    )
                except Exception as notify_error:
                    logger.warning(f"⚠️ Не удалось отправить уведомление о закрытии: {notify_error}")
                
                # Обновляем статистику риск-менеджера
                if trade.profit > 0:
                    self.risk_manager.update_statistics('win', trade.profit)
                else:
                    self.risk_manager.update_statistics('loss', abs(trade.profit))
                
                logger.info(f"✅ Позиция {trade.symbol} закрыта с прибылью ${trade.profit:.2f}")
            else:
                logger.error(f"❌ Не удалось закрыть позицию {trade.symbol}")
                
        except Exception as e:
            logger.error(f"❌ Ошибка закрытия позиции {trade.symbol}: {e}")
    
    # =========================================================================
    # === ПРЕДВАРИТЕЛЬНЫЕ ПРОВЕРКИ ===
    # =========================================================================
    
    async def _pre_start_checks(self) -> bool:
        """
        Комплексная проверка готовности системы к запуску
        
        Проверяем:
        1. Наличие и корректность API ключей
        2. Подключение к бирже
        3. Подключение к базе данных
        4. Наличие торговых пар
        5. Достаточность баланса
        
        Returns:
            bool: True если все проверки пройдены
        """
        logger.info("🔍 Начинаем предварительные проверки...")
        
        # === ПРОВЕРКА 1: API КЛЮЧИ ===
        logger.debug("🔑 Проверяем API ключи...")
        if not config.BYBIT_API_KEY or config.BYBIT_API_KEY == 'your_testnet_api_key_here':
            logger.error("❌ API ключи не настроены в конфигурации")
            return False
        
        if not config.BYBIT_API_SECRET or config.BYBIT_API_SECRET == 'your_testnet_secret_here':
            logger.error("❌ Secret ключ не настроен в конфигурации")
            return False
        
        logger.info("✅ API ключи настроены")
        
        # === ПРОВЕРКА 2: ПОДКЛЮЧЕНИЕ К БИРЖЕ ===
        logger.debug("🌐 Проверяем подключение к бирже...")
        try:
            await self.exchange.test_connection()
            logger.info("✅ Подключение к бирже успешно")
        except Exception as exchange_error:
            logger.error(f"❌ Не удалось подключиться к бирже: {exchange_error}")
            return False
        
        # === ПРОВЕРКА 3: ПОДКЛЮЧЕНИЕ К БАЗЕ ДАННЫХ ===
        logger.debug("💾 Проверяем подключение к базе данных...")
        try:
            db = SessionLocal()
            try:
                # Используем text() для безопасного SQL запроса
                result = db.execute(text("SELECT 1 as test_connection"))
                test_value = result.fetchone()
                
                if test_value and test_value[0] == 1:
                    logger.info("✅ Подключение к базе данных успешно")
                else:
                    logger.error("❌ База данных вернула неожиданный результат")
                    return False
            finally:
                db.close()
        except Exception as db_error:
            logger.error(f"❌ Не удалось подключиться к базе данных: {db_error}")
            return False
        
        # === ПРОВЕРКА 4: НАЛИЧИЕ ТОРГОВЫХ ПАР ===
        logger.debug("📋 Проверяем наличие торговых пар...")
        if not self.active_pairs:
            # Попробуем загрузить из конфигурации
            if hasattr(config, 'TRADING_PAIRS') and config.TRADING_PAIRS:
                self.active_pairs = config.TRADING_PAIRS
                logger.info(f"✅ Загружены пары из конфигурации: {self.active_pairs}")
            else:
                logger.error("❌ Не настроены торговые пары")
                return False
        
        # === ПРОВЕРКА 5: БАЛАНС (необязательно, но полезно) ===
        logger.debug("💰 Проверяем баланс...")
        try:
            balance = await self.exchange.fetch_balance()
            usdt_balance = balance.get('USDT', {}).get('free', 0)
            
            if usdt_balance < 10:  # Минимальный баланс
                logger.warning(f"⚠️ Низкий баланс USDT: ${usdt_balance:.2f}")
            else:
                logger.info(f"✅ Баланс USDT: ${usdt_balance:.2f}")
        except Exception as balance_error:
            logger.warning(f"⚠️ Не удалось проверить баланс: {balance_error}")
            # Не критичная ошибка, продолжаем
        
        logger.info("✅ Все предварительные проверки пройдены")
        return True
    
    # =========================================================================
    # === ЗАГРУЗКА КОНФИГУРАЦИИ ===
    # =========================================================================
    
    async def _load_configuration(self):
        """
        Загрузка конфигурации из базы данных
        
        Загружаем:
        1. Активные торговые пары
        2. Открытые позиции
        3. Настройки стратегий
        """
        logger.info("📋 Загружаем конфигурацию из базы данных...")
        
        db = SessionLocal()
        try:
            # === ЗАГРУЗКА АКТИВНЫХ ТОРГОВЫХ ПАР ===
            pairs = db.query(TradingPair).filter(
                TradingPair.is_active == True
            ).all()
            
            if pairs:
                self.active_pairs = [pair.symbol for pair in pairs]
                logger.info(f"📋 Загружены активные пары из БД: {self.active_pairs}")
            else:
                # Используем пары из конфигурации как fallback
                if hasattr(config, 'TRADING_PAIRS'):
                    self.active_pairs = config.TRADING_PAIRS
                    logger.info(f"📋 Используем пары из конфигурации: {self.active_pairs}")
                else:
                    # Дефолтные пары
                    self.active_pairs = ['BTCUSDT', 'ETHUSDT']
                    logger.warning(f"⚠️ Используем дефолтные пары: {self.active_pairs}")
            
            # === ЗАГРУЗКА ОТКРЫТЫХ ПОЗИЦИЙ ===
            open_trades = db.query(Trade).filter(
                Trade.status == TradeStatus.OPEN
            ).all()
            
            if open_trades:
                self.positions = {trade.symbol: trade for trade in open_trades}
                logger.info(f"📊 Загружены открытые позиции: {list(self.positions.keys())}")
            else:
                self.positions = {}
                logger.info("📊 Открытых позиций не найдено")
            
            logger.info(f"✅ Конфигурация загружена: {len(self.active_pairs)} пар, {len(self.positions)} позиций")
            
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки конфигурации: {e}")
            # Используем дефолтные значения
            self.active_pairs = getattr(config, 'TRADING_PAIRS', ['BTCUSDT', 'ETHUSDT'])
            self.positions = {}
            logger.warning("⚠️ Используем дефолтную конфигурацию")
        finally:
            db.close()
    
    # =========================================================================
    # === ИМИТАЦИЯ ЧЕЛОВЕЧЕСКОГО ПОВЕДЕНИЯ ===
    # =========================================================================
    
    async def _human_delay(self, min_seconds: float = None, max_seconds: float = None):
        """
        Умная задержка с имитацией человеческого поведения
        
        Учитывает различные факторы:
        1. Время суток (ночью медленнее)
        2. Усталость (больше циклов = больше задержка)
        3. Случайные перерывы
        4. Настройки режима имитации
        
        Args:
            min_seconds: Минимальная задержка (по умолчанию из конфига)
            max_seconds: Максимальная задержка (по умолчанию из конфига)
        """
        # Если режим имитации человека отключен, используем стандартную задержку
        if not getattr(config, 'ENABLE_HUMAN_MODE', True):
            await asyncio.sleep(60)  # Стандартная минута
            return
        
        # Определяем базовые параметры задержки
        min_delay = min_seconds or getattr(config, 'MIN_DELAY_SECONDS', 30)
        max_delay = max_seconds or getattr(config, 'MAX_DELAY_SECONDS', 120)
        
        # Базовая случайная задержка
        delay = random.uniform(min_delay, max_delay)
        
        # === ФАКТОР ВРЕМЕНИ СУТОК ===
        hour = datetime.utcnow().hour
        if 0 <= hour < 6:  # Ночь - человек спит или менее активен
            delay *= random.uniform(1.5, 2.5)
            logger.debug("🌙 Ночное время - увеличиваем задержку")
        elif 6 <= hour < 9:  # Утро - просыпается, может быть медленным
            delay *= random.uniform(1.2, 1.5)
            logger.debug("🌅 Утреннее время - слегка увеличиваем задержку")
        elif 22 <= hour <= 23:  # Поздний вечер - усталость
            delay *= random.uniform(1.3, 1.7)
            logger.debug("🌆 Вечернее время - увеличиваем задержку из-за усталости")
        
        # === ФАКТОР УСТАЛОСТИ ===
        # Чем больше циклов выполнено, тем больше "усталость"
        if self.cycles_count > 100:
            fatigue_factor = min(2.0, 1 + (self.cycles_count - 100) / 200)
            delay *= fatigue_factor
            logger.debug(f"😴 Фактор усталости: x{fatigue_factor:.1f} (циклов: {self.cycles_count})")
        
        # === СЛУЧАЙНЫЕ ПЕРЕРЫВЫ ===
        random_value = random.random()
        
        # Короткие перерывы (как будто отвлекся на телефон)
        if random_value < 0.02:  # 2% шанс
            delay = random.uniform(300, 900)  # 5-15 минут
            logger.info(f"☕ Имитируем короткий перерыв: {delay/60:.1f} минут")
        
        # Длинные перерывы (обед, отдых)
        elif random_value < 0.005:  # 0.5% шанс
            delay = random.uniform(1800, 3600)  # 30-60 минут
            logger.info(f"🍽️ Имитируем длинный перерыв: {delay/60:.1f} минут")
        
        # === ВЫПОЛНЕНИЕ ЗАДЕРЖКИ ===
        # Разбиваем на маленькие кусочки для возможности быстрой остановки
        remaining = delay
        while remaining > 0 and not self._stop_event.is_set():
            sleep_time = min(1.0, remaining)  # Максимум 1 секунда за раз
            await asyncio.sleep(sleep_time)
            remaining -= sleep_time
        
        if delay > 60:  # Логируем только длинные задержки
            logger.debug(f"⏳ Задержка завершена: {delay:.1f} секунд")
    
    # =========================================================================
    # === РАБОТА С БАЗОЙ ДАННЫХ ===
    # =========================================================================
    
    def _safe_db_operation(self, operation_name: str, operation_func, *args, **kwargs):
        """
        Безопасное выполнение операций с базой данных
        
        Этот метод предоставляет единообразный способ работы с БД:
        1. Логирует начало и конец операции
        2. Обрабатывает ошибки
        3. Возвращает результат или None при ошибке
        
        Args:
            operation_name: Название операции для логов
            operation_func: Функция для выполнения
            *args, **kwargs: Аргументы для функции
            
        Returns:
            Результат операции или None при ошибке
        """
        try:
            logger.debug(f"💾 Выполняем операцию БД: {operation_name}")
            result = operation_func(*args, **kwargs)
            logger.debug(f"✅ Операция БД завершена: {operation_name}")
            return result
        except Exception as e:
            logger.error(f"❌ Ошибка в операции БД '{operation_name}': {e}")
            return None
    
    def _load_state_from_db(self):
        """
        Загрузка состояния бота из базы данных при инициализации
        
        Проверяем, не был ли бот некорректно завершен в прошлый раз.
        Если да, то сбрасываем флаг запуска.
        """
        logger.debug("💾 Загружаем состояние бота из БД...")
        
        def _load_operation():
            db = SessionLocal()
            try:
                bot_state = db.query(BotState).first()
                if bot_state and bot_state.is_running:
                    logger.warning("⚠️ Бот был запущен при последнем выключении, сбрасываем флаг")
                    bot_state.is_running = False
                    bot_state.stop_time = datetime.utcnow()
                    db.commit()
                    return True
                return False
            finally:
                db.close()
        
        try:
            self._safe_db_operation("загрузка состояния", _load_operation)
        except Exception as e:
            logger.warning(f"⚠️ Не удалось загрузить состояние из БД: {e}")
    
    def _update_bot_state_db(self, is_running: bool):
        """
        Обновление состояния бота в базе данных
        
        Args:
            is_running: Флаг запуска бота
        """
        def _update_operation():
            db = SessionLocal()
            try:
                # Ищем существующую запись состояния
                state = db.query(BotState).first()
                if not state:
                    # Создаем новую запись
                    state = BotState()
                    db.add(state)
                
                # Обновляем поля
                state.is_running = is_running
                if is_running:
                    state.start_time = datetime.utcnow()
                    state.stop_time = None
                else:
                    state.stop_time = datetime.utcnow()
                
                # Обновляем статистику
                state.total_trades = self.trades_today
                state.current_balance = self._get_current_balance()
                
                db.commit()
                return True
            except Exception as e:
                db.rollback()
                raise e
            finally:
                db.close()
        
        self._safe_db_operation("обновление состояния бота", _update_operation)
    
    def _save_signal(self, signal: Signal):
        """
        Сохранение торгового сигнала в базу данных
        
        Args:
            signal: Объект сигнала для сохранения
        """
        def _save_operation():
            db = SessionLocal()
            try:
                # Создаем новый объект Signal в контексте текущей сессии
                new_signal = Signal(
                    symbol=signal.symbol,
                    action=signal.action,
                    confidence=signal.confidence,
                    price=signal.price,
                    stop_loss=signal.stop_loss,
                    take_profit=signal.take_profit,
                    strategy=signal.strategy,
                    reason=signal.reason,
                    created_at=signal.created_at
                )
                db.add(new_signal)
                db.commit()
                # Обновляем ID в исходном объекте
                signal.id = new_signal.id
                return True
            except Exception as e:
                db.rollback()
                raise e
            finally:
                db.close()
        
        self._safe_db_operation(f"сохранение сигнала {signal.symbol}", _save_operation)
    
    def _update_signal_db(self, signal: Signal):
        """
        Обновление сигнала в базе данных
        
        Args:
            signal: Объект сигнала для обновления
        """
        def _update_operation():
            db = SessionLocal()
            try:
                # Получаем объект из БД и обновляем его
                db_signal = db.query(Signal).filter(Signal.id == signal.id).first()
                if db_signal:
                    db_signal.executed = signal.executed
                    db_signal.executed_at = signal.executed_at
                    db_signal.trade_id = signal.trade_id
                    db.commit()
                    return True
                else:
                    logger.warning(f"Сигнал с ID {signal.id} не найден в БД")
                    return False
            except Exception as e:
                db.rollback()
                raise e
            finally:
                db.close()
        
        self._safe_db_operation(f"обновление сигнала {signal.symbol}", _update_operation)
    
    def _update_trade_db(self, trade: Trade):
        """
        Обновление сделки в базе данных
        
        Args:
            trade: Объект сделки для обновления
        """
        def _update_operation():
            db = SessionLocal()
            try:
                db.merge(trade)
                db.commit()
                return True
            except Exception as e:
                db.rollback()
                raise e
            finally:
                db.close()
        
        self._safe_db_operation(f"обновление сделки {trade.symbol}", _update_operation)
    
    def _save_statistics(self):
        """
        Сохранение статистики работы бота при остановке
        
        Рассчитывает и сохраняет:
        1. Общее количество сделок
        2. Количество прибыльных сделок
        3. Общую прибыль
        4. Win rate
        """
        logger.info("📊 Сохраняем статистику работы бота...")
        
        def _stats_operation():
            db = SessionLocal()
            try:
                # Получаем или создаем запись состояния
                state = db.query(BotState).first()
                if not state:
                    state = BotState()
                    db.add(state)
                
                # === БЕЗОПАСНЫЙ ПОДСЧЕТ СТАТИСТИКИ ===
                try:
                    # Общее количество сделок
                    total_trades = db.query(Trade).count()
                    logger.info(f"📈 Всего сделок в системе: {total_trades}")
                except Exception as trade_error:
                    logger.warning(f"⚠️ Не удалось подсчитать общее количество сделок: {trade_error}")
                    total_trades = 0
                
                try:
                    # Прибыльные сделки
                    profitable_trades = db.query(Trade).filter(
                        Trade.profit > 0,
                        Trade.status == TradeStatus.CLOSED
                    ).count()
                    logger.info(f"💰 Прибыльных сделок: {profitable_trades}")
                except Exception as profit_error:
                    logger.warning(f"⚠️ Не удалось подсчитать прибыльные сделки: {profit_error}")
                    profitable_trades = 0
                
                try:
                    # Общая прибыль
                    total_profit_result = db.query(func.sum(Trade.profit)).filter(
                        Trade.status == TradeStatus.CLOSED
                    ).scalar()
                    total_profit = float(total_profit_result) if total_profit_result else 0.0
                    logger.info(f"🎯 Общая прибыль: ${total_profit:.2f}")
                except Exception as sum_error:
                    logger.warning(f"⚠️ Не удалось подсчитать общую прибыль: {sum_error}")
                    total_profit = 0.0
                
                # Обновляем статистику в состоянии
                state.total_trades = total_trades
                state.profitable_trades = profitable_trades
                state.total_profit = total_profit
                state.stop_time = datetime.utcnow()
                
                db.commit()
                
                # Вычисляем и логируем итоговую статистику
                win_rate = (profitable_trades / total_trades * 100) if total_trades > 0 else 0
                uptime = datetime.utcnow() - self.start_time if self.start_time else timedelta(0)
                
                logger.info("=" * 50)
                logger.info("📊 ИТОГОВАЯ СТАТИСТИКА СЕССИИ")
                logger.info("=" * 50)
                logger.info(f"⏰ Время работы: {uptime}")
                logger.info(f"🔄 Циклов анализа: {self.cycles_count}")
                logger.info(f"📊 Всего сделок: {total_trades}")
                logger.info(f"💰 Прибыльных сделок: {profitable_trades}")
                logger.info(f"🎯 Общая прибыль: ${total_profit:.2f}")
                logger.info(f"📈 Win Rate: {win_rate:.1f}%")
                logger.info("=" * 50)
                
                return True
                
            except Exception as e:
                logger.error(f"❌ Критическая ошибка при сохранении статистики: {e}")
                db.rollback()
                return False
            finally:
                db.close()
        
        # Выполняем сохранение статистики
        result = self._safe_db_operation("сохранение статистики", _stats_operation)
        if result:
            logger.info("✅ Статистика успешно сохранена")
        else:
            logger.warning("⚠️ Не удалось сохранить статистику, но продолжаем работу")
    
    # =========================================================================
    # === ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ===
    # =========================================================================
    
    def _check_trading_limits(self) -> bool:
        """
        Проверка дневных лимитов торговли
        
        Returns:
            bool: True если можно продолжать торговлю
        """
        max_daily_trades = getattr(config, 'MAX_DAILY_TRADES', 50)
        return self.trades_today < max_daily_trades
    
    async def _update_balance(self):
        """
        Обновление информации о балансе в базе данных
        
        Получает текущий баланс с биржи и сохраняет в БД
        для последующего анализа и ведения статистики.
        """
        try:
            # Получаем баланс с биржи
            balance = await self.exchange.fetch_balance()
            logger.debug("💰 Обновляем информацию о балансе...")
            
            def _save_balance():
                db = SessionLocal()
                try:
                    # Сохраняем только валюты с ненулевым балансом
                    for currency, amount_info in balance.items():
                        if amount_info['total'] > 0:
                            balance_record = Balance(
                                currency=currency,
                                total=float(amount_info['total']),
                                free=float(amount_info['free']),
                                used=float(amount_info['used']),
                                timestamp=datetime.utcnow()
                            )
                            db.add(balance_record)
                    
                    db.commit()
                    return True
                except Exception as e:
                    db.rollback()
                    raise e
                finally:
                    db.close()
            
            # Сохраняем через безопасный метод
            result = self._safe_db_operation("обновление баланса", _save_balance)
            if result:
                logger.debug("✅ Баланс обновлен в БД")
            
        except Exception as e:
            logger.warning(f"⚠️ Ошибка обновления баланса: {e}")
            # Не критично, продолжаем работу
    
    def _get_current_balance(self) -> float:
        """
        Получение текущего баланса в USDT из базы данных
        
        Returns:
            float: Баланс в USDT
        """
        def _get_balance():
            db = SessionLocal()
            try:
                # Ищем последнюю запись баланса USDT
                latest_balance = db.query(Balance).filter(
                    Balance.currency == 'USDT'
                ).order_by(Balance.timestamp.desc()).first()
                
                if latest_balance:
                    return float(latest_balance.total)
                else:
                    # Если записей нет, возвращаем начальный капитал
                    return float(getattr(config, 'INITIAL_CAPITAL', 1000))
            finally:
                db.close()
        
        result = self._safe_db_operation("получение текущего баланса", _get_balance)
        return result if result is not None else 1000.0
    
    def _get_pair_config(self, symbol: str) -> TradingPair:
        """
        Получение конфигурации торговой пары
        
        Args:
            symbol: Символ торговой пары (например, 'BTCUSDT')
            
        Returns:
            TradingPair: Конфигурация пары
        """
        def _get_config():
            db = SessionLocal()
            try:
                pair = db.query(TradingPair).filter(
                    TradingPair.symbol == symbol
                ).first()
                
                if pair:
                    return pair
                else:
                    # Возвращаем дефолтную конфигурацию (не сохраняем в БД здесь)
                    logger.debug(f"🔧 Создаем дефолтную конфигурацию для {symbol}")
                    return TradingPair(
                        symbol=symbol,
                        strategy='multi_indicator',
                        stop_loss_percent=float(getattr(config, 'STOP_LOSS_PERCENT', 2.0)),
                        take_profit_percent=float(getattr(config, 'TAKE_PROFIT_PERCENT', 4.0)),
                        is_active=True
                    )
            finally:
                db.close()
        
        result = self._safe_db_operation(f"получение конфигурации {symbol}", _get_config)
        
        # Если произошла ошибка, возвращаем минимальную конфигурацию
                # Если произошла ошибка, возвращаем минимальную конфигурацию
        if result is None:
            logger.warning(f"⚠️ Не удалось получить конфигурацию для {symbol}, используем дефолтную")
            return TradingPair(
                symbol=symbol,
                strategy='multi_indicator',
                stop_loss_percent=2.0,
                take_profit_percent=4.0,
                is_active=True
            )
        
        return result
    
    def _update_process_info(self):
        """
        Обновление информации о процессе для мониторинга
        
        Собирает полезную информацию о текущем состоянии процесса:
        - PID процесса
        - Использование памяти
        - Загрузка CPU
        - Количество потоков
        - Время создания процесса
        
        Эта информация помогает при отладке и мониторинге производительности.
        """
        try:
            # Получаем информацию о текущем процессе
            process = psutil.Process()
            
            # Собираем метрики производительности
            memory_info = process.memory_info()
            
            self._process_info = {
                'pid': process.pid,
                'memory_mb': round(memory_info.rss / 1024 / 1024, 2),  # RSS в мегабайтах
                'memory_vms_mb': round(memory_info.vms / 1024 / 1024, 2),  # VMS в мегабайтах
                'cpu_percent': process.cpu_percent(),
                'threads': process.num_threads(),
                'create_time': datetime.fromtimestamp(process.create_time()),
                'status': process.status(),
                'connections': len(process.connections()) if hasattr(process, 'connections') else 0
            }
            
            logger.debug(f"📊 Процесс: PID={self._process_info['pid']}, "
                        f"RAM={self._process_info['memory_mb']}MB, "
                        f"CPU={self._process_info['cpu_percent']}%")
            
        except Exception as e:
            logger.warning(f"⚠️ Не удалось обновить информацию о процессе: {e}")
            # Устанавливаем минимальную информацию
            self._process_info = {
                'pid': os.getpid(),
                'memory_mb': 0,
                'cpu_percent': 0,
                'threads': 1,
                'create_time': datetime.utcnow(),
                'status': 'unknown'
            }
    
    def _update_statistics(self):
        """
        Обновление внутренней статистики бота
        
        Обновляет счетчики и метрики, которые используются
        для принятия торговых решений и мониторинга:
        - Количество сделок за сегодня
        - Текущую производительность
        - Статистику активности
        """
        def _stats_operation():
            db = SessionLocal()
            try:
                # Определяем начало текущего дня в UTC
                today_start = datetime.utcnow().replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                
                # Считаем сделки за сегодня
                today_trades_count = db.query(Trade).filter(
                    Trade.created_at >= today_start
                ).count()
                
                # Обновляем внутренний счетчик
                self.trades_today = today_trades_count
                
                logger.debug(f"📊 Обновлена статистика: {self.trades_today} сделок сегодня")
                return True
                
            except Exception as e:
                logger.warning(f"⚠️ Ошибка обновления статистики: {e}")
                # Сохраняем текущее значение при ошибке
                return False
            finally:
                db.close()
        
        # Выполняем обновление через безопасный метод
        self._safe_db_operation("обновление внутренней статистики", _stats_operation)
    
    async def _close_all_positions(self, reason: str):
        """
        Экстренное закрытие всех открытых позиций
        
        Используется при остановке бота или в критических ситуациях.
        Пытается закрыть каждую позицию по рыночной цене.
        
        Args:
            reason: Причина закрытия (для логов и уведомлений)
        """
        if not self.positions:
            logger.info("✅ Открытых позиций для закрытия нет")
            return
        
        logger.info(f"🔄 Закрываем {len(self.positions)} открытых позиций. Причина: {reason}")
        
        # Создаем копию словаря для безопасной итерации
        positions_to_close = list(self.positions.items())
        
        for symbol, trade in positions_to_close:
            try:
                logger.info(f"🔄 Закрываем позицию {symbol}...")
                
                # Получаем текущую цену
                ticker = await self.exchange.fetch_ticker(symbol)
                current_price = ticker['last']
                
                # Закрываем позицию
                await self._close_position(trade, current_price, reason)
                
                # Удаляем из активных позиций
                if symbol in self.positions:
                    del self.positions[symbol]
                
                logger.info(f"✅ Позиция {symbol} закрыта")
                
            except Exception as position_error:
                logger.error(f"❌ Не удалось закрыть позицию {symbol}: {position_error}")
                # Продолжаем с другими позициями
                # Принудительно удаляем из списка активных
                if symbol in self.positions:
                    del self.positions[symbol]
                    logger.warning(f"⚠️ Позиция {symbol} удалена из активных принудительно")
        
        logger.info(f"✅ Процедура закрытия позиций завершена. Причина: {reason}")
    
    # =========================================================================
    # === ПУБЛИЧНЫЕ МЕТОДЫ ДЛЯ ВНЕШНЕГО API ===
    # =========================================================================
    
    def get_status(self) -> Dict[str, Any]:
        """
        Получение полного статуса бота для веб-интерфейса и API
        
        Возвращает детальную информацию о состоянии бота,
        которая используется в веб-интерфейсе и для мониторинга.
        
        Returns:
            Dict: Полная информация о статусе бота
        """
        try:
            # Базовая информация о статусе
            status_info = {
                'status': self.status.value,
                'is_running': self.status == BotStatus.RUNNING,
                'active_pairs': self.active_pairs.copy(),
                'open_positions': len(self.positions),
            }
            
            # Детальная информация о позициях
            positions_details = {}
            for symbol, trade in self.positions.items():
                try:
                    positions_details[symbol] = {
                        'side': trade.side.value if hasattr(trade.side, 'value') else str(trade.side),
                        'entry_price': float(trade.entry_price) if trade.entry_price else 0,
                        'quantity': float(trade.quantity) if trade.quantity else 0,
                        'profit': float(trade.profit) if trade.profit else 0,
                        'unrealized_pnl': float(getattr(trade, 'unrealized_pnl', 0)),
                        'created_at': trade.created_at.isoformat() if trade.created_at else None
                    }
                except Exception as pos_error:
                    logger.warning(f"⚠️ Ошибка получения данных позиции {symbol}: {pos_error}")
                    positions_details[symbol] = {'error': 'Ошибка получения данных'}
            
            status_info['positions_details'] = positions_details
            
            # Статистика работы
            uptime_str = None
            if self.start_time:
                uptime_delta = datetime.utcnow() - self.start_time
                hours = uptime_delta.seconds // 3600
                minutes = (uptime_delta.seconds % 3600) // 60
                uptime_str = f"{uptime_delta.days}д {hours}ч {minutes}м"
            
            status_info['statistics'] = {
                'start_time': self.start_time.isoformat() if self.start_time else None,
                'uptime': uptime_str,
                'cycles_count': self.cycles_count,
                'trades_today': self.trades_today
            }
            
            # Информация о процессе
            status_info['process_info'] = self._process_info.copy()
            
            # Конфигурация
            status_info['config'] = {
                'mode': 'TESTNET' if getattr(config, 'BYBIT_TESTNET', True) else 'MAINNET',
                'max_positions': getattr(config, 'MAX_POSITIONS', 5),
                'human_mode': getattr(config, 'ENABLE_HUMAN_MODE', True),
                'max_daily_trades': getattr(config, 'MAX_DAILY_TRADES', 50)
            }
            
            return status_info
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения статуса: {e}")
            # Возвращаем минимальную информацию при ошибке
            return {
                'status': 'error',
                'is_running': False,
                'error': str(e),
                'active_pairs': [],
                'open_positions': 0,
                'positions_details': {},
                'statistics': {},
                'process_info': {},
                'config': {}
            }
    
    async def update_pairs(self, pairs: List[str]) -> Tuple[bool, str]:
        """
        Обновление списка активных торговых пар
        
        Этот метод позволяет динамически изменять список торгуемых пар
        без перезапуска бота. Изменения сохраняются в базе данных.
        
        Args:
            pairs: Список символов торговых пар (например, ['BTCUSDT', 'ETHUSDT'])
            
        Returns:
            Tuple[bool, str]: (успешность, сообщение)
        """
        if not pairs:
            return False, "Список пар не может быть пустым"
        
        # Проверяем корректность символов пар
        valid_pairs = []
        for pair in pairs:
            if isinstance(pair, str) and len(pair) >= 6:  # Минимальная длина символа
                valid_pairs.append(pair.upper())
            else:
                logger.warning(f"⚠️ Некорректный символ пары: {pair}")
        
        if not valid_pairs:
            return False, "Не найдено корректных торговых пар"
        
        def _update_operation():
            db = SessionLocal()
            try:
                # Деактивируем все существующие пары
                db.query(TradingPair).update({TradingPair.is_active: False})
                
                # Активируем или создаем выбранные пары
                updated_count = 0
                created_count = 0
                
                for symbol in valid_pairs:
                    pair = db.query(TradingPair).filter(
                        TradingPair.symbol == symbol
                    ).first()
                    
                    if pair:
                        # Обновляем существующую пару
                        pair.is_active = True
                        pair.updated_at = datetime.utcnow()
                        updated_count += 1
                    else:
                        # Создаем новую пару с дефолтными настройками
                        pair = TradingPair(
                            symbol=symbol,
                            is_active=True,
                            strategy='multi_indicator',
                            stop_loss_percent=float(getattr(config, 'STOP_LOSS_PERCENT', 2.0)),
                            take_profit_percent=float(getattr(config, 'TAKE_PROFIT_PERCENT', 4.0)),
                            created_at=datetime.utcnow()
                        )
                        db.add(pair)
                        created_count += 1
                
                db.commit()
                
                return {
                    'updated': updated_count,
                    'created': created_count,
                    'total': len(valid_pairs)
                }
                
            except Exception as e:
                db.rollback()
                raise e
            finally:
                db.close()
        
        try:
            # Выполняем обновление в БД
            result = self._safe_db_operation("обновление торговых пар", _update_operation)
            
            if result:
                # Обновляем внутренний список активных пар
                self.active_pairs = valid_pairs
                
                success_message = (
                    f"Торговые пары обновлены: {result['total']} активных, "
                    f"{result['updated']} обновлено, {result['created']} создано"
                )
                
                logger.info(f"✅ {success_message}")
                logger.info(f"📋 Новый список пар: {self.active_pairs}")
                
                return True, success_message
            else:
                return False, "Ошибка при обновлении пар в базе данных"
                
        except Exception as e:
            error_msg = f"Ошибка обновления торговых пар: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg
    
    async def close_position(self, symbol: str) -> Tuple[bool, str]:
        """
        Ручное закрытие конкретной позиции
        
        Используется для принудительного закрытия позиции
        через веб-интерфейс или API.
        
        Args:
            symbol: Символ торговой пары для закрытия
            
        Returns:
            Tuple[bool, str]: (успешность, сообщение)
        """
        # Проверяем существование позиции
        if symbol not in self.positions:
            message = f"Открытая позиция {symbol} не найдена"
            logger.warning(f"⚠️ {message}")
            return False, message
        
        try:
            trade = self.positions[symbol]
            
            logger.info(f"🔄 Ручное закрытие позиции {symbol}...")
            
            # Получаем текущую цену
            ticker = await self.exchange.fetch_ticker(symbol)
            current_price = ticker['last']
            
            # Закрываем позицию
            await self._close_position(trade, current_price, "Manual close via API")
            
            # Удаляем из активных позиций
            del self.positions[symbol]
            
            success_message = f"Позиция {symbol} успешно закрыта по цене {current_price}"
            logger.info(f"✅ {success_message}")
            
            return True, success_message
            
        except Exception as e:
            error_msg = f"Ошибка закрытия позиции {symbol}: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg
    
    def get_detailed_statistics(self) -> Dict[str, Any]:
        """
        Получение детальной статистики для аналитики
        
        Возвращает расширенную статистику, включающую:
        - Статистику по парам
        - Временные показатели
        - Анализ производительности
        
        Returns:
            Dict: Детальная статистика
        """
        def _stats_operation():
            db = SessionLocal()
            try:
                # Временные границы для анализа
                now = datetime.utcnow()
                today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                week_start = today_start - timedelta(days=7)
                month_start = today_start - timedelta(days=30)
                
                # Статистика за разные периоды
                periods_stats = {}
                
                for period_name, start_date in [
                    ('today', today_start),
                    ('week', week_start),
                    ('month', month_start),
                    ('all_time', datetime.min)
                ]:
                    trades = db.query(Trade).filter(
                        Trade.created_at >= start_date
                    ).all()
                    
                    total_trades = len(trades)
                    profitable_trades = len([t for t in trades if t.profit and t.profit > 0])
                    total_profit = sum(t.profit or 0 for t in trades)
                    
                    periods_stats[period_name] = {
                        'total_trades': total_trades,
                        'profitable_trades': profitable_trades,
                        'total_profit': round(total_profit, 2),
                        'win_rate': round((profitable_trades / total_trades * 100) if total_trades > 0 else 0, 2),
                        'average_profit': round(total_profit / total_trades if total_trades > 0 else 0, 2)
                    }
                
                # Статистика по торговым парам
                pairs_stats = {}
                for symbol in self.active_pairs:
                    pair_trades = db.query(Trade).filter(
                        Trade.symbol == symbol
                    ).all()
                    
                    if pair_trades:
                        pair_total = len(pair_trades)
                        pair_profitable = len([t for t in pair_trades if t.profit and t.profit > 0])
                        pair_profit = sum(t.profit or 0 for t in pair_trades)
                        
                        pairs_stats[symbol] = {
                            'total_trades': pair_total,
                            'profitable_trades': pair_profitable,
                            'total_profit': round(pair_profit, 2),
                            'win_rate': round((pair_profitable / pair_total * 100) if pair_total > 0 else 0, 2)
                        }
                
                return {
                    'periods': periods_stats,
                    'pairs': pairs_stats,
                    'generated_at': now.isoformat()
                }
                
            except Exception as e:
                logger.error(f"❌ Ошибка получения детальной статистики: {e}")
                return {'error': str(e)}
            finally:
                db.close()
        
        result = self._safe_db_operation("получение детальной статистики", _stats_operation)
        return result or {'error': 'Не удалось получить статистику'}
    
    # =========================================================================
    # === МЕТОДЫ ДЛЯ ОТЛАДКИ И МОНИТОРИНГА ===
    # =========================================================================
    
    def get_health_check(self) -> Dict[str, Any]:
        """
        Проверка здоровья системы для мониторинга
        
        Возвращает информацию о состоянии всех компонентов
        для систем мониторинга и алертинга.
        
        Returns:
            Dict: Информация о здоровье системы
        """
        health_info = {
            'timestamp': datetime.utcnow().isoformat(),
            'overall_status': 'healthy',
            'components': {}
        }
        
        # Проверка основных компонентов
        components_to_check = [
            ('bot_manager', self.status != BotStatus.ERROR),
            ('exchange', hasattr(self, 'exchange') and self.exchange is not None),
            ('database', True),  # Проверим отдельно
            ('telegram', hasattr(self, 'notifier') and self.notifier is not None),
            ('positions', len(self.positions) >= 0),  # Всегда True, но для полноты
        ]
        
        all_healthy = True
        
        for component_name, is_healthy in components_to_check:
            health_info['components'][component_name] = {
                'status': 'healthy' if is_healthy else 'unhealthy',
                'last_check': datetime.utcnow().isoformat()
            }
            
            if not is_healthy:
                all_healthy = False
        
        # Отдельная проверка базы данных
        try:
            db = SessionLocal()
            db.execute(text("SELECT 1"))
            db.close()
            health_info['components']['database']['status'] = 'healthy'
        except Exception as db_error:
            health_info['components']['database']['status'] = 'unhealthy'
            health_info['components']['database']['error'] = str(db_error)
            all_healthy = False
        
        # Общий статус
        if not all_healthy:
            health_info['overall_status'] = 'degraded'
        
        if self.status == BotStatus.ERROR:
            health_info['overall_status'] = 'unhealthy'
        
        return health_info
    
    def __repr__(self) -> str:
        """
        Строковое представление объекта для отладки
        
        Returns:
            str: Информативное описание состояния менеджера
        """
        return (
            f"BotManager(status={self.status.value}, "
            f"pairs={len(self.active_pairs)}, "
            f"positions={len(self.positions)}, "
            f"cycles={self.cycles_count})"
        )


# =========================================================================
# === СОЗДАНИЕ ГЛОБАЛЬНОГО ЭКЗЕМПЛЯРА ===
# =========================================================================

# Создаем единственный экземпляр менеджера бота (Singleton)
# Этот объект будет использоваться во всем приложении
bot_manager = BotManager()

# Дополнительная проверка для отладки
if __name__ == "__main__":
    # Этот блок выполняется только при прямом запуске файла
    # Полезно для тестирования отдельных компонентов
    print("🤖 BotManager module loaded successfully")
    print(f"📊 Manager instance: {bot_manager}")
    print(f"🔧 Configuration loaded: {hasattr(config, 'BYBIT_API_KEY')}")