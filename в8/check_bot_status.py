#!/usr/bin/env python3
"""
Скрипт для проверки статуса и активности бота
"""
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
import asyncio

# Добавляем путь к проекту
sys.path.append('/var/www/www-root/data/www/systemetech.ru')

from src.core.database import SessionLocal
from src.core.models import Trade, Signal, BotState, TradingPair
from src.core.bot_manager import bot_manager

load_dotenv()

def check_bot_status():
    """Проверка статуса бота"""
    print("🔍 ПРОВЕРКА СТАТУСА БОТА")
    print("=" * 50)
    
    # 1. Статус менеджера
    status = bot_manager.get_status()
    print(f"\n📊 Статус менеджера:")
    print(f"   Запущен: {'✅ Да' if status['is_running'] else '❌ Нет'}")
    print(f"   Активные пары: {', '.join(status['active_pairs'])}")
    print(f"   Открытые позиции: {status['open_positions']}")
    
    # 2. Проверка БД
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
        
    finally:
        db.close()
    
    # 3. Проверка логов
    print(f"\n📋 Последние записи в логах:")
    try:
        with open('/var/www/www-root/data/www/systemetech.ru/logs/trading.log', 'r') as f:
            lines = f.readlines()
            for line in lines[-10:]:  # Последние 10 строк
                print(f"   {line.strip()}")
    except Exception as e:
        print(f"   ❌ Ошибка чтения логов: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Проверка завершена")

async def test_bot_cycle():
    """Тест одного цикла анализа"""
    print("\n🧪 ТЕСТ ЦИКЛА АНАЛИЗА")
    print("=" * 50)
    
    # Принудительно запускаем один цикл анализа
    if not bot_manager.is_running:
        print("⚠️  Бот не запущен, запускаем тестовый цикл...")
        
        # Загружаем активные пары
        bot_manager._load_state()
        
        # Анализируем первую пару
        if bot_manager.active_pairs:
            symbol = bot_manager.active_pairs[0]
            print(f"\n🔍 Анализируем {symbol}...")
            
            try:
                signal = await bot_manager._analyze_pair(symbol)
                if signal:
                    print(f"✅ Получен сигнал: {signal.action} (уверенность: {signal.confidence:.2f})")
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

if __name__ == "__main__":
    # Синхронная проверка
    check_bot_status()
    
    # Асинхронный тест
    print("\nЗапустить тест цикла анализа? (y/n): ", end='')
    if input().lower() == 'y':
        asyncio.run(test_bot_cycle())