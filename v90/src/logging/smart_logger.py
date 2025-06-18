from ..core.models import TradingLog
"""
Интеллектуальная система логирования с аналитикой
Файл: src/logging/smart_logger.py
"""
import logging
import logging.handlers
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Set
from collections import defaultdict, deque
from contextlib import contextmanager
import threading
from pathlib import Path

from sqlalchemy.orm import Session
from ..core.database import SessionLocal
from ..core.models import Base

# Создаем новую модель для логов
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, Index


class LogAggregator:
    """Агрегатор для группировки похожих логов"""
    
    def __init__(self, window_seconds: int = 60):
        self.window_seconds = window_seconds
        self.log_groups: Dict[str, List[Dict]] = defaultdict(list)
        self.last_flush = datetime.utcnow()
        self._lock = threading.Lock()
    
    def add_log(self, log_hash: str, log_data: Dict) -> bool:
        """
        Добавляет лог в группу, возвращает True если нужно записать
        """
        with self._lock:
            self.log_groups[log_hash].append({
                'data': log_data,
                'timestamp': datetime.utcnow()
            })
            
            # Проверяем, нужно ли флашить
            if (datetime.utcnow() - self.last_flush).total_seconds() > self.window_seconds:
                return True
            
            # Или если группа слишком большая
            if len(self.log_groups[log_hash]) > 100:
                return True
                
            return False
    
    def get_aggregated_logs(self) -> List[Dict]:
        """Получает агрегированные логи"""
        with self._lock:
            aggregated = []
            
            for log_hash, logs in self.log_groups.items():
                if not logs:
                    continue
                
                # Берем первый лог как образец
                sample_log = logs[0]['data']
                count = len(logs)
                
                if count > 1:
                    # Модифицируем сообщение
                    sample_log['message'] = f"[x{count}] {sample_log['message']}"
                    sample_log['context']['aggregated_count'] = count
                    sample_log['context']['first_occurrence'] = logs[0]['timestamp'].isoformat()
                    sample_log['context']['last_occurrence'] = logs[-1]['timestamp'].isoformat()
                
                aggregated.append(sample_log)
            
            # Очищаем группы
            self.log_groups.clear()
            self.last_flush = datetime.utcnow()
            
            return aggregated


class SmartLogger:
    """
    Интеллектуальный логгер с приоритетами и аналитикой
    """
    
    # Приоритеты категорий логов
    CATEGORY_PRIORITIES = {
        'trade': 10,      # Самый высокий приоритет
        'signal': 9,
        'profit_loss': 9,
        'strategy': 8,
        'risk': 8,
        'market': 7,
        'error': 10,
        'system': 5,
        'debug': 1
    }
    
    # Важные паттерны для обязательного логирования
    IMPORTANT_PATTERNS = {
        'trade_opened', 'trade_closed', 'profit_realized', 'loss_realized',
        'stop_loss_triggered', 'take_profit_reached', 'strategy_changed',
        'risk_limit_reached', 'error_occurred', 'market_crash', 'unusual_volume'
    }
    
    def __init__(self, name: str, log_dir: Path = Path("logs")):
        self.name = name
        self.log_dir = log_dir
        self.log_dir.mkdir(exist_ok=True)
        
        # Основной логгер
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Агрегатор логов
        self.aggregator = LogAggregator()
        
        # Статистика логов
        self.log_stats = defaultdict(int)
        
        # Кольцевой буфер для последних важных логов
        self.important_logs = deque(maxlen=1000)
        
        # Настройка обработчиков
        self._setup_handlers()
        
        # Фоновая задача для записи в БД
        self._db_queue = asyncio.Queue(maxsize=1000)
        self._db_writer_task = None
    
    def _setup_handlers(self):
        """Настройка обработчиков логов"""
        # Консольный обработчик с фильтрацией
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.addFilter(self._importance_filter)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        
        # Файловый обработчик для важных логов
        important_file = self.log_dir / f"{self.name}_important.log"
        important_handler = logging.handlers.RotatingFileHandler(
            important_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        important_handler.setLevel(logging.INFO)
        important_handler.addFilter(self._importance_filter)
        
        # Файловый обработчик для всех логов (ротация каждый день)
        all_logs_file = self.log_dir / f"{self.name}_all.log"
        all_handler = logging.handlers.TimedRotatingFileHandler(
            all_logs_file,
            when='midnight',
            interval=1,
            backupCount=7,  # Храним 7 дней
            encoding='utf-8'
        )
        all_handler.setLevel(logging.DEBUG)
        
        # Форматтер с полной информацией
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        important_handler.setFormatter(detailed_formatter)
        all_handler.setFormatter(detailed_formatter)
        
        # Добавляем обработчики
        self.logger.addHandler(console_handler)
        self.logger.addHandler(important_handler)
        self.logger.addHandler(all_handler)
    
    def _importance_filter(self, record):
        """Фильтр для определения важности лога"""
        # ERROR и CRITICAL всегда важны
        if record.levelno >= logging.ERROR:
            return True
        
        # Проверяем категорию
        category = getattr(record, 'category', 'system')
        priority = self.CATEGORY_PRIORITIES.get(category, 5)
        
        # Проверяем паттерны
        message_lower = record.getMessage().lower()
        for pattern in self.IMPORTANT_PATTERNS:
            if pattern.replace('_', ' ') in message_lower:
                return True
        
        # Фильтруем по приоритету
        return priority >= 7
    
    def _create_log_hash(self, level: str, category: str, message: str) -> str:
        """Создает хеш для группировки похожих логов"""
        # Убираем числа и специфичные данные
        clean_message = ''.join(c if not c.isdigit() else '#' for c in message)
        return f"{level}:{category}:{clean_message[:50]}"
    
    async def _db_writer_worker(self):
        """Фоновый воркер для записи логов в БД"""
        batch = []
        last_write = datetime.utcnow()
        
        while True:
            try:
                # Ждем лог или таймаут
                try:
                    log_data = await asyncio.wait_for(
                        self._db_queue.get(),
                        timeout=5.0
                    )
                    batch.append(log_data)
                except asyncio.TimeoutError:
                    pass
                
                # Записываем батч если:
                # 1. Прошло достаточно времени
                # 2. Батч достаточно большой
                # 3. Есть критичный лог
                should_write = (
                    (datetime.utcnow() - last_write).total_seconds() > 30 or
                    len(batch) >= 50 or
                    any(log['log_level'] in ['ERROR', 'CRITICAL'] for log in batch)
                )
                
                if should_write and batch:
                    await self._write_logs_to_db(batch)
                    batch.clear()
                    last_write = datetime.utcnow()
                    
            except Exception as e:
                print(f"Error in DB writer: {e}")
                await asyncio.sleep(5)
    
    async def _write_logs_to_db(self, logs: List[Dict]):
        """Записывает логи в базу данных"""
        db = SessionLocal()
        try:
            for log_data in logs:
                db_log = TradingLog(**log_data)
                db.add(db_log)
            db.commit()
        except Exception as e:
            print(f"Error writing logs to DB: {e}")
            db.rollback()
        finally:
            db.close()
    
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
        log_data = {
            'log_level': level,
            'category': category,
            'message': message,
            'context': context,
            'symbol': context.get('symbol'),
            'strategy': context.get('strategy'),
            'trade_id': context.get('trade_id'),
            'signal_id': context.get('signal_id')
        }
        
        # Проверяем агрегацию
        log_hash = self._create_log_hash(level, category, message)
        should_flush = self.aggregator.add_log(log_hash, log_data)
        
        if should_flush:
            # Флашим агрегированные логи
            aggregated_logs = self.aggregator.get_aggregated_logs()
            for agg_log in aggregated_logs:
                self._write_log(agg_log)
        
        # Обновляем статистику
        self.log_stats[f"{level}:{category}"] += 1
        
        # Для важных логов - пишем сразу
        if level in ['ERROR', 'CRITICAL'] or category in ['trade', 'profit_loss']:
            self._write_log(log_data)
            self.important_logs.append({
                'timestamp': datetime.utcnow(),
                'data': log_data
            })
    
    def _write_log(self, log_data: Dict):
        """Записывает лог через стандартный логгер и в очередь БД"""
        # Получаем уровень логирования
        level = getattr(logging, log_data['log_level'])
        
        # Создаем LogRecord с дополнительными атрибутами
        record = self.logger.makeRecord(
            self.logger.name,
            level,
            "(dynamic)",
            0,
            log_data['message'],
            (),
            None
        )
        
        # Добавляем атрибуты
        record.category = log_data['category']
        for key, value in log_data['context'].items():
            setattr(record, key, value)
        
        # Логируем
        self.logger.handle(record)
        
        # Добавляем в очередь БД
        if self._db_writer_task:
            try:
                self._db_queue.put_nowait(log_data)
            except asyncio.QueueFull:
                # Очередь полная - пропускаем менее важные логи
                if log_data['log_level'] in ['ERROR', 'CRITICAL']:
                    # Для критичных - ждем
                    asyncio.create_task(self._db_queue.put(log_data))
    
    # Удобные методы
    def debug(self, message: str, category: str = 'system', **context):
        self.log('DEBUG', message, category, **context)
    
    def info(self, message: str, category: str = 'system', **context):
        self.log('INFO', message, category, **context)
    
    def warning(self, message: str, category: str = 'system', **context):
        self.log('WARNING', message, category, **context)
    
    def error(self, message: str, category: str = 'system', **context):
        self.log('ERROR', message, category, **context)
    
    def critical(self, message: str, category: str = 'system', **context):
        self.log('CRITICAL', message, category, **context)
    
    # Специализированные методы для трейдинга
    def trade_opened(self, symbol: str, side: str, quantity: float, price: float, 
                     strategy: str, **kwargs):
        """Логирование открытия сделки"""
        self.info(
            f"Открыта позиция: {side} {quantity} {symbol} @ {price}",
            category='trade',
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=price,
            strategy=strategy,
            **kwargs
        )
    
    def trade_closed(self, symbol: str, profit: float, profit_percent: float,
                     reason: str, **kwargs):
        """Логирование закрытия сделки"""
        category = 'profit_loss'
        level = 'INFO' if profit >= 0 else 'WARNING'
        
        self.log(
            level,
            f"Закрыта позиция {symbol}: {'прибыль' if profit >= 0 else 'убыток'} "
            f"${profit:.2f} ({profit_percent:.2f}%). Причина: {reason}",
            category=category,
            symbol=symbol,
            profit=profit,
            profit_percent=profit_percent,
            reason=reason,
            **kwargs
        )
    
    def signal_generated(self, symbol: str, action: str, confidence: float,
                        strategy: str, **kwargs):
        """Логирование генерации сигнала"""
        self.info(
            f"Сигнал {action} для {symbol} (уверенность: {confidence:.2%}) от {strategy}",
            category='signal',
            symbol=symbol,
            action=action,
            confidence=confidence,
            strategy=strategy,
            **kwargs
        )
    
    def strategy_performance(self, strategy: str, symbol: str, win_rate: float,
                           avg_profit: float, **kwargs):
        """Логирование производительности стратегии"""
        self.info(
            f"Производительность {strategy} на {symbol}: "
            f"Win Rate: {win_rate:.2%}, Средняя прибыль: ${avg_profit:.2f}",
            category='strategy',
            strategy=strategy,
            symbol=symbol,
            win_rate=win_rate,
            avg_profit=avg_profit,
            **kwargs
        )
    
    def market_condition(self, symbol: str, condition: str, indicators: Dict, **kwargs):
        """Логирование рыночных условий"""
        self.info(
            f"Рыночные условия {symbol}: {condition}",
            category='market',
            symbol=symbol,
            condition=condition,
            indicators=indicators,
            **kwargs
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получает статистику логирования"""
        total_logs = sum(self.log_stats.values())
        
        return {
            'total_logs': total_logs,
            'by_category': dict(self.log_stats),
            'important_logs_count': len(self.important_logs),
            'log_rate_per_minute': total_logs / max(1, (datetime.utcnow() - 
                                  datetime.utcnow().replace(hour=0, minute=0, second=0)).total_seconds() / 60)
        }
    
    async def start_db_writer(self):
        """Запускает фоновую запись в БД"""
        if not self._db_writer_task:
            self._db_writer_task = asyncio.create_task(self._db_writer_worker())
    
    async def stop_db_writer(self):
        """Останавливает фоновую запись в БД"""
        if self._db_writer_task:
            self._db_writer_task.cancel()
            try:
                await self._db_writer_task
            except asyncio.CancelledError:
                pass
    
    @contextmanager
    def timer(self, operation: str, category: str = 'performance'):
        """Контекстный менеджер для измерения времени операций"""
        start_time = datetime.utcnow()
        try:
            yield
        finally:
            duration = (datetime.utcnow() - start_time).total_seconds()
            if duration > 1.0:  # Логируем только медленные операции
                self.warning(
                    f"Медленная операция '{operation}': {duration:.2f}s",
                    category=category,
                    operation=operation,
                    duration=duration
                )