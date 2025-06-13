#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для проверки статуса и активности бота
Исправлены проблемы с кодировкой и синхронизацией состояния
"""
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
import asyncio
import locale

# ✅ ИСПРАВЛЕНИЕ: Настройка локали для корректной работы с UTF-8
try:
    # Пытаемся установить UTF-8 локаль
    locale.setlocale(locale.LC_ALL, 'C.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
    except:
        # Если не удается, используем системную
        pass

# Добавляем путь к проекту
sys.path.append('/var/www/www-root/data/www/systemetech.ru')

from src.core.database import SessionLocal
from src.core.models import Trade, Signal, BotState, TradingPair
from src.core.unified_bot_manager import unified_bot_manager  # ✅ Используем единый менеджер

load_dotenv()

def check_bot_status():
    """Проверка статуса бота с корректной диагностикой"""
    print("🔍 ПРОВЕРКА СТАТУСА БОТА")
    print("=" * 50)
    
    # 1. ✅ ИСПРАВЛЕНИЕ: Проверяем реальное состояние через единый менеджер
    try:
        status = unified_bot_manager.get_comprehensive_status()
        
        print(f"\n📊 Статус процесса:")
        print(f"   Процесс запущен: {'✅ Да' if status['process_running'] else '❌ Нет'}")
        print(f"   PID процесса: {status.get('process_pid', 'Не найден')}")
        
        print(f"\n📊 Статус менеджера:")
        print(f"   Внутреннее состояние: {'✅ Активен' if status['manager_running'] else '❌ Неактивен'}")
        print(f"   Активные пары: {', '.join(status['active_pairs'])}")
        print(f"   Открытые позиции: {status['open_positions']}")
        
    except Exception as e:
        print(f"❌ Ошибка получения статуса менеджера: {e}")
        status = {'manager_running': False, 'process_running': False, 'active_pairs': [], 'open_positions': 0}
    
    # 2. Проверка БД (остается без изменений, но с улучшенной обработкой ошибок)
    db = SessionLocal()
    try:
        # Состояние бота
        bot_state = db.query(BotState).first()
        if bot_state:
            print(f"\n📊 Состояние в БД:")
            print(f"   Запущен: {'✅ Да' if bot_state.is_running else '❌ Нет'}")
            print(f"   Время запуска: {bot_state.start_time}")
            print(f"   Всего сделок: {bot_state.total_trades}")
            print(f"   Прибыльных: {bot_state.profitable_trades}")
            print(f"   Общая прибыль: ${bot_state.total_profit:.2f}")
            print(f"   Текущий баланс: ${bot_state.current_balance:.2f}")
        else:
            print(f"\n📊 Состояние в БД: ❌ Данные не найдены")
        
        # ✅ ИСПРАВЛЕНИЕ: Диагностика рассинхронизации
        if bot_state and status:
            if bot_state.is_running != status['manager_running']:
                print(f"\n⚠️ ОБНАРУЖЕНА РАССИНХРОНИЗАЦИЯ:")
                print(f"   БД показывает: {'Запущен' if bot_state.is_running else 'Остановлен'}")
                print(f"   Менеджер показывает: {'Запущен' if status['manager_running'] else 'Остановлен'}")
                print(f"   Рекомендация: Выполните синхронизацию состояния")
        
        # Активные пары
        active_pairs = db.query(TradingPair).filter(TradingPair.is_active == True).all()
        print(f"\n💱 Активные торговые пары ({len(active_pairs)}):")
        for pair in active_pairs:
            print(f"   - {pair.symbol} (стратегия: {pair.strategy})")
        
        # Последние сигналы
        recent_signals = db.query(Signal).order_by(Signal.created_at.desc()).limit(5).all()
        print(f"\n📡 Последние сигналы ({len(recent_signals)}):")
        for signal in recent_signals:
            time_ago = datetime.utcnow() - signal.created_at
            print(f"   - {signal.created_at.strftime('%H:%M:%S')} ({int(time_ago.total_seconds()/60)}м назад): "
                  f"{signal.symbol} {signal.action} (уверенность: {signal.confidence:.2f})")
        
        # Открытые позиции
        open_trades = db.query(Trade).filter(Trade.status == 'OPEN').all()
        print(f"\n💼 Открытые позиции ({len(open_trades)}):")
        for trade in open_trades:
            print(f"   - {trade.symbol} {trade.side} @ ${trade.entry_price:.2f} "
                  f"(кол-во: {trade.quantity:.4f})")
        
        # Последние закрытые сделки
        closed_trades = db.query(Trade).filter(
            Trade.status == 'CLOSED'
        ).order_by(Trade.closed_at.desc()).limit(5).all()
        
        print(f"\n📈 Последние закрытые сделки ({len(closed_trades)}):")
        for trade in closed_trades:
            if trade.closed_at:
                time_ago = datetime.utcnow() - trade.closed_at
                print(f"   - {trade.closed_at.strftime('%H:%M:%S')} ({int(time_ago.total_seconds()/60)}м назад): "
                      f"{trade.symbol} P&L: ${trade.profit:.2f}")
        
    except Exception as e:
        print(f"❌ Ошибка работы с БД: {e}")
    finally:
        db.close()
    
    # 3. Проверка логов с улучшенной обработкой ошибок
    print(f"\n📋 Последние записи в логах:")
    try:
        log_path = '/var/www/www-root/data/www/systemetech.ru/logs/trading.log'
        if os.path.exists(log_path):
            with open(log_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines[-10:]:  # Последние 10 строк
                    print(f"   {line.strip()}")
        else:
            print(f"   ⚠️ Файл логов не найден: {log_path}")
    except Exception as e:
        print(f"   ❌ Ошибка чтения логов: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Проверка завершена")

async def test_bot_cycle():
    """Тест одного цикла анализа с улучшенной диагностикой"""
    print("\n🧪 ТЕСТ ЦИКЛА АНАЛИЗА")
    print("=" * 50)
    
    try:
        # ✅ ИСПРАВЛЕНИЕ: Используем единый менеджер
        status = unified_bot_manager.get_comprehensive_status()
        
        if not status['manager_running']:
            print("⚠️  Бот не запущен, запускаем тестовый цикл...")
            
            # Загружаем состояние
            unified_bot_manager.load_state()
            
            # Анализируем первую пару
            if status['active_pairs']:
                symbol = status['active_pairs'][0]
                print(f"\n🔍 Анализируем {symbol}...")
                
                try:
                    signal = await unified_bot_manager.analyze_pair_test(symbol)
                    if signal:
                        print(f"✅ Получен сигнал: {signal.action} (уверенность: {signal.confidence:.2f})")
                        print(f"   Причина: {signal.reason}")
                        print(f"   Цена: ${signal.price:.2f}")
                    else:
                        print("❌ Сигнал не получен (WAIT)")
                except Exception as e:
                    print(f"❌ Ошибка анализа: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print("❌ Нет активных пар для анализа")
        else:
            print("ℹ️  Бот уже запущен, проверьте логи для активности")
            
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")

def sync_bot_state():
    """✅ НОВАЯ ФУНКЦИЯ: Синхронизация состояния бота"""
    print("\n🔄 СИНХРОНИЗАЦИЯ СОСТОЯНИЯ БОТА")
    print("=" * 50)
    
    try:
        result = unified_bot_manager.sync_state()
        if result['success']:
            print("✅ Состояние синхронизировано")
            print(f"   Новое состояние: {'Запущен' if result['is_running'] else 'Остановлен'}")
        else:
            print(f"❌ Ошибка синхронизации: {result['error']}")
    except Exception as e:
        print(f"❌ Ошибка выполнения синхронизации: {e}")

def safe_input(prompt: str) -> str:
    """✅ ИСПРАВЛЕНИЕ: Безопасный ввод с обработкой кодировки"""
    try:
        # Пытаемся использовать стандартный input
        return input(prompt).strip().lower()
    except UnicodeDecodeError:
        # Если ошибка кодировки, используем альтернативный способ
        import sys
        sys.stdout.write(prompt)
        sys.stdout.flush()
        
        # Читаем байты и декодируем
        try:
            line = sys.stdin.buffer.readline()
            return line.decode('utf-8', errors='ignore').strip().lower()
        except:
            # В крайнем случае возвращаем 'n'
            return 'n'

if __name__ == "__main__":
    try:
        # Синхронная проверка
        check_bot_status()
        
        # ✅ ИСПРАВЛЕНИЕ: Безопасный ввод
        user_input = safe_input("\nЗапустить тест цикла анализа? (y/n): ")
        if user_input == 'y':
            asyncio.run(test_bot_cycle())
        
        # ✅ НОВАЯ ФУНКЦИЯ: Предложение синхронизации
        sync_input = safe_input("\nВыполнить синхронизацию состояния? (y/n): ")
        if sync_input == 'y':
            sync_bot_state()
            
    except KeyboardInterrupt:
        print("\n👋 Выход...")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()