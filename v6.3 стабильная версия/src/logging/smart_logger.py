#!/usr/bin/env python3
"""
ПОЛНАЯ ИНТЕЛЛЕКТУАЛЬНАЯ СИСТЕМА ЛОГИРОВАНИЯ - ИСПРАВЛЕННАЯ ВЕРСИЯ
==============================================================

⚠️ ВАЖНО: Этот файл ПОЛНОСТЬЮ ЗАМЕНЯЕТ существующий src/logging/smart_logger.py

Интеллектуальная система логирования с аналитикой, агрегацией и автоматической записью в БД
Специальные методы для торговых операций, ошибок, производительности

ИСПРАВЛЕНИЕ: Заменен timestamp на created_at для совместимости с моделью TradingLog

Путь: src/logging/smart_logger.py
"""

import logging
import logging.handlers
import json
import asyncio
import hashlib
import threading
import traceback
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Set, Union, Callable
from collections import defaultdict, deque
from contextlib import contextmanager
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import sys
import os

# Исправленные импорты
try:
    from sqlalchemy.orm import Session
    from ..core.database import SessionLocal
    from ..core.models import TradingLog
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    Session = None
    SessionLocal = None
    TradingLog = None
    SQLALCHEMY_AVAILABLE = False
    print("⚠️ SQLAlchemy не найден, используем только файловое логирование")

# =================================================================
# ENUMS И DATACLASSES
# =================================================================

class LogLevel(Enum):
    """Уровни логирования"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class LogCategory(Enum):
    """Категории логов"""
    TRADE = "trade"
    SIGNAL = "signal"
    PROFIT_LOSS = "profit_loss"
    STRATEGY = "strategy"
    RISK = "risk"
    MARKET = "market"
    ERROR = "error"
    SYSTEM = "system"
    DEBUG = "debug"
    PERFORMANCE = "performance"
    EXCHANGE = "exchange"
    ML = "ml"
    NEWS = "news"

@dataclass
class LogEntry:
    """Структура записи лога"""
    timestamp: datetime
    level: str
    category: str
    message: str
    context: Dict[str, Any] = None
    symbol: Optional[str] = None
    strategy: Optional[str] = None
    trade_id: Optional[int] = None
    signal_id: Optional[int] = None
    thread_id: Optional[str] = None
    correlation_id: Optional[str] = None

@dataclass
class AggregatedLogGroup:
    """Группа агрегированных логов"""
    hash_key: str
    count: int
    first_occurrence: datetime
    last_occurrence: datetime
    level: str
    category: str
    message_template: str
    context_summary: Dict[str, Any]

# =================================================================
# LOG AGGREGATOR
# =================================================================

class LogAggregator:
    """
    Агрегатор похожих логов для уменьшения спама
    """
    
    def __init__(self, window_minutes: int = 5, max_groups: int = 1000):
        self.window_minutes = window_minutes
        self.max_groups = max_groups
        self.groups: Dict[str, AggregatedLogGroup] = {}
        self.last_cleanup = datetime.utcnow()
    
    def add_log(self, log_hash: str, log_entry: LogEntry) -> bool:
        """
        Добавляет лог в агрегацию
        
        Returns:
            bool: True если лог должен быть записан немедленно
        """
        now = datetime.utcnow()
        
        # Очистка старых групп
        if (now - self.last_cleanup).total_seconds() > 60:  # Каждую минуту
            self._cleanup_old_groups(now)
            self.last_cleanup = now
        
        # Проверяем существующую группу
        if log_hash in self.groups:
            group = self.groups[log_hash]
            group.count += 1
            group.last_occurrence = now
            
            # Не записываем если группа недавно создана
            time_diff = (now - group.first_occurrence).total_seconds()
            return time_diff > self.window_minutes * 60
        
        # Создаем новую группу
        self.groups[log_hash] = AggregatedLogGroup(
            hash_key=log_hash,
            count=1,
            first_occurrence=now,
            last_occurrence=now,
            level=log_entry.level,
            category=log_entry.category,
            message_template=log_entry.message,
            context_summary=log_entry.context or {}
        )
        
        return True  # Первое вхождение всегда записываем
    
    def get_aggregated_logs(self) -> List[AggregatedLogGroup]:
        """Получает все агрегированные группы"""
        return list(self.groups.values())
    
    def _cleanup_old_groups(self, now: datetime):
        """Очищает старые группы"""
        cutoff = now - timedelta(minutes=self.window_minutes * 2)
        old_keys = [
            key for key, group in self.groups.items()
            if group.last_occurrence < cutoff
        ]
        
        for key in old_keys:
            del self.groups[key]
        
        # Ограничиваем размер
        if len(self.groups) > self.max_groups:
            sorted_groups = sorted(
                self.groups.items(),
                key=lambda x: x[1].last_occurrence
            )
            for key, _ in sorted_groups[:len(self.groups) - self.max_groups]:
                del self.groups[key]
    
    def get_log_hash(self, log_entry: LogEntry) -> str:
        """Создает хэш для агрегации логов"""
        # Создаем хэш на основе уровня, категории и упрощенного сообщения
        simplified_message = log_entry.message[:100]  # Первые 100 символов
        hash_data = f"{log_entry.level}:{log_entry.category}:{simplified_message}"
        return hashlib.md5(hash_data.encode()).hexdigest()[:8]

# =================================================================
# DATABASE WRITER - ИСПРАВЛЕННАЯ ВЕРСИЯ
# =================================================================

class DatabaseLogWriter:
    """
    Асинхронная запись логов в базу данных
    
    ИСПРАВЛЕНИЕ: Использует created_at вместо timestamp
    """
    
    def __init__(self, batch_size: int = 50, flush_interval: int = 30):
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.log_queue = asyncio.Queue() if asyncio else None
        self.is_running = False
        self.writer_task = None
        
    async def start(self):
        """Запускает writer"""
        if not SQLALCHEMY_AVAILABLE:
            return
            
        self.is_running = True
        if self.log_queue:
            self.writer_task = asyncio.create_task(self._write_loop())
    
    async def stop(self):
        """Останавливает writer"""
        self.is_running = False
        if self.writer_task:
            await self.writer_task
    
    async def add_log(self, log_entry: LogEntry):
        """Добавляет лог в очередь"""
        if not self.is_running or not self.log_queue:
            return
        await self.log_queue.put(log_entry)
    
    async def _write_loop(self):
        """Основной цикл записи"""
        batch = []
        last_write = datetime.utcnow()
        
        while self.is_running:
            try:
                # Получаем логи из очереди
                try:
                    log_entry = await asyncio.wait_for(self.log_queue.get(), timeout=1.0)
                    batch.append(log_entry)
                except asyncio.TimeoutError:
                    pass
                
                # Проверяем условия записи
                should_write = (
                    # 1. Прошло достаточно времени
                    (datetime.utcnow() - last_write).total_seconds() > self.flush_interval or
                    # 2. Батч достаточно большой
                    len(batch) >= self.batch_size or
                    # 3. Есть критичный лог
                    any(log.level in ['ERROR', 'CRITICAL'] for log in batch)
                )
                
                if should_write and batch:
                    await self._write_logs_to_db(batch)
                    batch.clear()
                    last_write = datetime.utcnow()
                    
            except Exception as e:
                print(f"❌ Ошибка в DB writer: {e}")
                await asyncio.sleep(5)
    
    async def _write_logs_to_db(self, logs: List[LogEntry]):
        """
        Записывает логи в базу данных
        
        ИСПРАВЛЕНИЕ: Использует created_at вместо timestamp
        """
        if not SQLALCHEMY_AVAILABLE or not logs:
            return
            
        db = SessionLocal()
        try:
            for log_entry in logs:
                # ✅ ИСПРАВЛЕНИЕ: Используем created_at вместо timestamp
                db_log = TradingLog(
                    created_at=log_entry.timestamp,  # ← ИСПРАВЛЕНО!
                    log_level=log_entry.level,
                    category=log_entry.category,
                    message=log_entry.message,
                    context=log_entry.context,
                    symbol=log_entry.symbol,
                    strategy=log_entry.strategy,
                    trade_id=log_entry.trade_id,
                    signal_id=log_entry.signal_id
                )
                db.add(db_log)
            db.commit()
        except Exception as e:
            print(f"❌ Ошибка записи логов в БД: {e}")
            db.rollback()
        finally:
            db.close()

# =================================================================
# SMART LOGGER - ГЛАВНЫЙ КЛАСС
# =================================================================

class SmartLogger:
    """
    Интеллектуальный логгер с приоритетами и аналитикой
    
    ВОЗМОЖНОСТИ:
    ✅ Агрегация похожих сообщений
    ✅ Асинхронная запись в БД (ИСПРАВЛЕНА)
    ✅ Специальные методы для торговли
    ✅ Контекстуальное логирование
    ✅ Автоматические метрики
    ✅ Ротация файлов
    """
    
    # Приоритеты категорий логов
    CATEGORY_PRIORITIES = {
        LogCategory.TRADE.value: 10,      # Самый высокий приоритет
        LogCategory.SIGNAL.value: 9,
        LogCategory.PROFIT_LOSS.value: 9,
        LogCategory.STRATEGY.value: 8,
        LogCategory.RISK.value: 8,
        LogCategory.MARKET.value: 7,
        LogCategory.ERROR.value: 10,
        LogCategory.PERFORMANCE.value: 6,
        LogCategory.EXCHANGE.value: 7,
        LogCategory.ML.value: 6,
        LogCategory.NEWS.value: 5,
        LogCategory.SYSTEM.value: 5,
        LogCategory.DEBUG.value: 1
    }
    
    # Важные паттерны для обязательного логирования
    IMPORTANT_PATTERNS = {
        'trade_opened', 'trade_closed', 'profit_realized', 'loss_realized',
        'stop_loss_triggered', 'take_profit_reached', 'strategy_changed',
        'risk_limit_reached', 'error_occurred', 'market_crash', 'unusual_volume',
        'emergency_stop', 'circuit_breaker', 'position_liquidated'
    }
    
    def __init__(self, name: str, log_dir: Path = Path("logs")):
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Основной логгер
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Агрегатор логов
        self.aggregator = LogAggregator()
        
        # Database writer (исправленный)
        self.db_writer = DatabaseLogWriter()
        
        # Контекстная информация
        self.default_context = {}
        self.correlation_id_stack = []
        
        # Метрики
        self.log_counts = defaultdict(int)
        self.error_patterns = defaultdict(int)
        self.performance_metrics = defaultdict(list)
        
        # Настройка обработчиков
        self._setup_handlers()
        
        # Запускаем DB writer
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            loop.create_task(self.db_writer.start())
        except:
            pass  # Возможно, не в async контексте
    
    def _setup_handlers(self):
        """Настройка обработчиков логирования"""
        # Очищаем существующие обработчики
        self.logger.handlers.clear()
        
        # Файловый обработчик с ротацией
        file_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / f"{self.name}.log",
            maxBytes=50*1024*1024,  # 50MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        
        # Консольный обработчик
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Форматтер
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Добавляем обработчики
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # Специальный обработчик для ошибок
        error_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / f"{self.name}_errors.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=3
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        self.logger.addHandler(error_handler)
    
    def _create_log_hash(self, level: str, category: str, message: str) -> str:
        """Создает хэш для агрегации логов"""
        simplified_message = message[:100]  # Первые 100 символов
        hash_data = f"{level}:{category}:{simplified_message}"
        return hashlib.md5(hash_data.encode()).hexdigest()[:8]
    
    def _create_log_entry(self, level: str, message: str, category: str, **context) -> LogEntry:
        """Создает запись лога"""
        # Обогащаем контекст
        enriched_context = {**self.default_context, **context}
        
        # Добавляем информацию о потоке
        thread_id = threading.current_thread().name
        
        # Correlation ID
        correlation_id = self.correlation_id_stack[-1] if self.correlation_id_stack else None
        
        return LogEntry(
            timestamp=datetime.utcnow(),
            level=level,
            category=category,
            message=message,
            context=enriched_context,
            symbol=context.get('symbol'),
            strategy=context.get('strategy'),
            trade_id=context.get('trade_id'),
            signal_id=context.get('signal_id'),
            thread_id=thread_id,
            correlation_id=correlation_id
        )
    
    def log(self, level: str, message: str, category: str = 'system', **context):
        """
        Основной метод логирования
        
        Args:
            level: Уровень лога (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            message: Сообщение
            category: Категория лога
            **context: Дополнительный контекст
        """
        # Создаем запись лога
        log_entry = self._create_log_entry(level, message, category, **context)
        
        # Проверяем агрегацию
        log_hash = self._create_log_hash(level, category, message)
        should_write_immediately = self.aggregator.add_log(log_hash, log_entry)
        
        # Обновляем метрики
        self.log_counts[f"{level}:{category}"] += 1
        
        # Записываем в стандартный логгер
        log_level = getattr(logging, level)
        extra_context = {k: v for k, v in context.items() if isinstance(v, (str, int, float, bool))}
        
        # Обработка исключений
        exc_info = context.get('exc_info')
        if exc_info is True:
            exc_info = sys.exc_info()
        
        self.logger.log(
            log_level, 
            message, 
            extra=extra_context,
            exc_info=exc_info
        )
        
        # Асинхронная запись в БД
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            loop.create_task(self.db_writer.add_log(log_entry))
        except:
            pass  # Не в async контексте
        
        # Немедленная обработка для критичных логов
        if should_write_immediately or level in ['ERROR', 'CRITICAL']:
            self._process_aggregated_logs()
    
    def _process_aggregated_logs(self):
        """Обрабатывает агрегированные логи"""
        aggregated_groups = self.aggregator.get_aggregated_logs()
        
        for group in aggregated_groups:
            # Дополнительная обработка для агрегированных логов
            if group.count > 1:
                self.error_patterns[group.hash_key] += group.count
    
    # =================================================================
    # УДОБНЫЕ МЕТОДЫ ЛОГИРОВАНИЯ
    # =================================================================
    
    def debug(self, message: str, category: str = 'system', **context):
        self.log('DEBUG', message, category, **context)
    
    def info(self, message: str, category: str = 'system', **context):
        self.log('INFO', message, category, **context)
    
    def warning(self, message: str, category: str = 'system', **context):
        self.log('WARNING', message, category, **context)
    
    def error(self, message: str, category: str = 'error', **context):
        """Логирование ошибки с автоматическим трейсбэком"""
        # Автоматически добавляем трейсбэк если есть исключение
        if 'exc_info' not in context:
            context['exc_info'] = True
        
        self.log('ERROR', message, category, **context)
    
    def critical(self, message: str, category: str = 'system', **context):
        self.log('CRITICAL', message, category, **context)
    
    # =================================================================
    # СПЕЦИАЛИЗИРОВАННЫЕ МЕТОДЫ ДЛЯ ТРЕЙДИНГА
    # =================================================================
    
    def trade_opened(self, symbol: str, side: str, quantity: float, price: float, 
                     strategy: str, trade_id: Optional[int] = None, **kwargs):
        """Логирование открытия сделки"""
        self.info(
            f"🟢 Открыта позиция: {side} {quantity} {symbol} @ ${price:,.2f}",
            category=LogCategory.TRADE.value,
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=price,
            strategy=strategy,
            trade_id=trade_id,
            position_value=quantity * price,
            **kwargs
        )
    
    def trade_closed(self, symbol: str, profit: float, profit_percent: float,
                     reason: str, trade_id: Optional[int] = None, **kwargs):
        """Логирование закрытия сделки"""
        emoji = "🟢" if profit >= 0 else "🔴"
        status = "прибыль" if profit >= 0 else "убыток"
        level = 'INFO' if profit >= 0 else 'WARNING'
        
        self.log(
            level,
            f"{emoji} Закрыта позиция {symbol}: {status} ${profit:.2f} ({profit_percent:+.2f}%). Причина: {reason}",
            category=LogCategory.PROFIT_LOSS.value,
            symbol=symbol,
            profit=profit,
            profit_percent=profit_percent,
            reason=reason,
            trade_id=trade_id,
            **kwargs
        )
    
    def signal_generated(self, symbol: str, action: str, confidence: float,
                        strategy: str, signal_id: Optional[int] = None, **kwargs):
        """Логирование торгового сигнала"""
        self.info(
            f"📡 Сигнал {action} для {symbol} (уверенность: {confidence:.1%})",
            category=LogCategory.SIGNAL.value,
            symbol=symbol,
            action=action,
            confidence=confidence,
            strategy=strategy,
            signal_id=signal_id,
            **kwargs
        )
    
    def strategy_performance(self, strategy: str, metric: str, value: float, **kwargs):
        """Логирование производительности стратегии"""
        self.info(
            f"📊 {strategy}: {metric} = {value}",
            category=LogCategory.PERFORMANCE.value,
            strategy=strategy,
            metric=metric,
            value=value,
            **kwargs
        )
        
        # Добавляем в метрики производительности
        self.performance_metrics[f"{strategy}:{metric}"].append({
            'value': value,
            'timestamp': datetime.utcnow()
        })
    
    def risk_alert(self, risk_type: str, level: str, message: str, **kwargs):
        """Логирование риск-алертов"""
        level_emoji = {
            'INFO': '💡',
            'WARNING': '⚠️', 
            'ERROR': '🚨',
            'CRITICAL': '🔴'
        }
        
        self.log(
            level,
            f"{level_emoji.get(level, '⚠️')} РИСК {risk_type}: {message}",
            category=LogCategory.RISK.value,
            risk_type=risk_type,
            **kwargs
        )
    
    def market_event(self, event_type: str, description: str, **kwargs):
        """Логирование рыночных событий"""
        self.info(
            f"🌐 Рыночное событие {event_type}: {description}",
            category=LogCategory.MARKET.value,
            event_type=event_type,
            **kwargs
        )
    
    # =================================================================
    # КОНТЕКСТУАЛЬНОЕ ЛОГИРОВАНИЕ
    # =================================================================
    
    @contextmanager
    def trading_context(self, symbol: str, strategy: str):
        """Контекстный менеджер для торговых операций"""
        old_context = self.default_context.copy()
        self.default_context.update({
            'symbol': symbol,
            'strategy': strategy
        })
        try:
            yield
        finally:
            self.default_context = old_context
    
    @contextmanager
    def correlation_context(self, correlation_id: str):
        """Контекстный менеджер для отслеживания связанных операций"""
        self.correlation_id_stack.append(correlation_id)
        try:
            yield
        finally:
            if self.correlation_id_stack:
                self.correlation_id_stack.pop()
    
    # =================================================================
    # АНАЛИЗ И МЕТРИКИ
    # =================================================================
    
    def get_log_statistics(self) -> Dict[str, Any]:
        """Получает статистику логирования"""
        return {
            'total_logs': sum(self.log_counts.values()),
            'by_level_category': dict(self.log_counts),
            'error_patterns': dict(self.error_patterns),
            'aggregated_groups': len(self.aggregator.groups),
            'logger_name': self.name
        }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Получает сводку метрик производительности"""
        summary = {}
        
        for metric_name, values in self.performance_metrics.items():
            if not values:
                continue
                
            metric_values = [v['value'] for v in values]
            summary[metric_name] = {
                'count': len(metric_values),
                'avg': sum(metric_values) / len(metric_values),
                'min': min(metric_values),
                'max': max(metric_values),
                'latest': metric_values[-1],
                'latest_timestamp': values[-1]['timestamp'].isoformat()
            }
        
        return summary
    
    def export_logs(self, start_time: Optional[datetime] = None,
                   end_time: Optional[datetime] = None,
                   categories: Optional[List[str]] = None) -> List[Dict]:
        """Экспортирует логи в JSON формате"""
        # Реализация зависит от хранилища логов
        # Здесь базовая заглушка
        return []
    
    # =================================================================
    # УТИЛИТЫ ОЧИСТКИ
    # =================================================================
    
    def cleanup_old_logs(self, days: int = 30):
        """Очищает старые логи"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Очистка файлов логов
        for log_file in self.log_dir.glob("*.log*"):
            try:
                file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                if file_mtime < cutoff_date:
                    log_file.unlink()
                    self.info(f"Удален старый лог-файл: {log_file.name}")
            except Exception as e:
                self.error(f"Ошибка удаления лог-файла {log_file}: {e}")
        
        # Очистка метрик в памяти
        for metric_name in list(self.performance_metrics.keys()):
            self.performance_metrics[metric_name] = [
                v for v in self.performance_metrics[metric_name]
                if v['timestamp'] > cutoff_date
            ]
    
    async def shutdown(self):
        """Корректное завершение работы логгера"""
        # Обрабатываем оставшиеся агрегированные логи
        self._process_aggregated_logs()
        
        # Останавливаем DB writer
        await self.db_writer.stop()
        
        # Закрываем все обработчики
        for handler in self.logger.handlers:
            handler.close()

# =================================================================
# СПЕЦИАЛИЗИРОВАННЫЙ ЛОГГЕР ДЛЯ ТОРГОВЛИ
# =================================================================

class TradingLogger(SmartLogger):
    """Специализированный логгер для торговых операций"""
    
    def __init__(self, name: str = "trading", log_dir: Path = Path("logs/trading")):
        super().__init__(name, log_dir)
        
        # Дополнительные обработчики для торговли
        self._setup_trading_handlers()
    
    def _setup_trading_handlers(self):
        """Настройка специальных обработчиков для торговли"""
        # Отдельный файл для сделок
        trades_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "trades.log",
            maxBytes=20*1024*1024,  # 20MB
            backupCount=10
        )
        trades_handler.setLevel(logging.INFO)
        
        # Фильтр только для торговых логов
        trades_filter = logging.Filter()
        trades_filter.filter = lambda record: hasattr(record, 'category') and record.category in ['trade', 'profit_loss']
        trades_handler.addFilter(trades_filter)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        trades_handler.setFormatter(formatter)
        
        self.logger.addHandler(trades_handler)

# =================================================================
# ГЛОБАЛЬНЫЕ ФУНКЦИИ
# =================================================================

def get_logger(name: str) -> SmartLogger:
    """Получить логгер по имени"""
    return SmartLogger(name)

def get_trading_logger() -> TradingLogger:
    """Получить торговый логгер"""
    return TradingLogger()

# Создаем глобальный логгер по умолчанию
logger = SmartLogger("crypto_bot")

# Экспорты
__all__ = [
    'SmartLogger',
    'TradingLogger', 
    'LogLevel',
    'LogCategory',
    'LogEntry',
    'get_logger',
    'get_trading_logger',
    'logger'
]