#!/usr/bin/env python3
"""
Скрипт обновления базы данных
Добавляет недостающие таблицы и поля
"""

import os
import sys
import pymysql
from dotenv import load_dotenv
from sqlalchemy import text

# Загружаем переменные окружения
load_dotenv()

# Параметры подключения
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_NAME = os.getenv('DB_NAME', 'crypto_top_bd_mysql')
DB_USER = os.getenv('DB_USER', 'crypto_top_admin')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'LSM6_PqnuZ10nvEdzfe6')

print("🔨 Обновление структуры базы данных...")
print("=" * 50)

try:
    # Подключение к MySQL
    connection = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset='utf8mb4'
    )
    
    cursor = connection.cursor()
    print("✅ Подключение к БД успешно!")
    
    # Список изменений
    updates = []
    
    # 1. Проверяем и добавляем недостающие колонки в таблицу trades
    print("\n📋 Проверка таблицы trades...")
    cursor.execute("""
        SELECT COLUMN_NAME 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'trades'
    """, (DB_NAME,))
    
    existing_columns = [row[0] for row in cursor.fetchall()]
    
    # Добавляем недостающие колонки
    if 'stop_loss' not in existing_columns:
        cursor.execute("ALTER TABLE trades ADD COLUMN stop_loss FLOAT")
        updates.append("✅ Добавлена колонка stop_loss в trades")
    
    if 'take_profit' not in existing_columns:
        cursor.execute("ALTER TABLE trades ADD COLUMN take_profit FLOAT")
        updates.append("✅ Добавлена колонка take_profit в trades")
    
    if 'profit_percent' not in existing_columns:
        cursor.execute("ALTER TABLE trades ADD COLUMN profit_percent FLOAT")
        updates.append("✅ Добавлена колонка profit_percent в trades")
    
    if 'trailing_stop' not in existing_columns:
        cursor.execute("ALTER TABLE trades ADD COLUMN trailing_stop BOOLEAN DEFAULT FALSE")
        updates.append("✅ Добавлена колонка trailing_stop в trades")
    
    if 'commission' not in existing_columns:
        cursor.execute("ALTER TABLE trades ADD COLUMN commission FLOAT DEFAULT 0")
        updates.append("✅ Добавлена колонка commission в trades")
    
    if 'notes' not in existing_columns:
        cursor.execute("ALTER TABLE trades ADD COLUMN notes TEXT")
        updates.append("✅ Добавлена колонка notes в trades")
    
    # 2. Проверяем таблицу signals
    print("\n📋 Проверка таблицы signals...")
    cursor.execute("""
        SELECT COLUMN_NAME 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'signals'
    """, (DB_NAME,))
    
    signal_columns = [row[0] for row in cursor.fetchall()]
    
    if signal_columns:  # Таблица существует
        if 'stop_loss' not in signal_columns:
            cursor.execute("ALTER TABLE signals ADD COLUMN stop_loss FLOAT")
            updates.append("✅ Добавлена колонка stop_loss в signals")
        
        if 'take_profit' not in signal_columns:
            cursor.execute("ALTER TABLE signals ADD COLUMN take_profit FLOAT")
            updates.append("✅ Добавлена колонка take_profit в signals")
        
        if 'strategy' not in signal_columns:
            cursor.execute("ALTER TABLE signals ADD COLUMN strategy VARCHAR(50)")
            updates.append("✅ Добавлена колонка strategy в signals")
        
        if 'reason' not in signal_columns:
            cursor.execute("ALTER TABLE signals ADD COLUMN reason TEXT")
            updates.append("✅ Добавлена колонка reason в signals")
        
        if 'executed_at' not in signal_columns:
            cursor.execute("ALTER TABLE signals ADD COLUMN executed_at TIMESTAMP NULL")
            updates.append("✅ Добавлена колонка executed_at в signals")
        
        if 'trade_id' not in signal_columns:
            cursor.execute("ALTER TABLE signals ADD COLUMN trade_id INT")
            updates.append("✅ Добавлена колонка trade_id в signals")
    
    # 3. Создаем новую таблицу bot_state если не существует
    print("\n📋 Проверка таблицы bot_state...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bot_state (
            id INT AUTO_INCREMENT PRIMARY KEY,
            is_running BOOLEAN DEFAULT FALSE,
            start_time TIMESTAMP NULL,
            stop_time TIMESTAMP NULL,
            total_trades INT DEFAULT 0,
            profitable_trades INT DEFAULT 0,
            total_profit FLOAT DEFAULT 0,
            current_balance FLOAT DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_updated_at (updated_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    updates.append("✅ Создана/проверена таблица bot_state")
    
    # 4. Обновляем таблицу users
    print("\n📋 Проверка таблицы users...")
    cursor.execute("""
        SELECT COLUMN_NAME 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'users'
    """, (DB_NAME,))
    
    user_columns = [row[0] for row in cursor.fetchall()]
    
    if user_columns:
        if 'email' not in user_columns:
            cursor.execute("ALTER TABLE users ADD COLUMN email VARCHAR(100)")
            updates.append("✅ Добавлена колонка email в users")
        
        if 'is_admin' not in user_columns:
            cursor.execute("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE")
            updates.append("✅ Добавлена колонка is_admin в users")
    
    # 5. Обновляем таблицу trading_pairs
    print("\n📋 Проверка таблицы trading_pairs...")
    cursor.execute("""
        SELECT COLUMN_NAME 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'trading_pairs'
    """, (DB_NAME,))
    
    pair_columns = [row[0] for row in cursor.fetchall()]
    
    if pair_columns:
        if 'stop_loss_percent' not in pair_columns:
            cursor.execute("ALTER TABLE trading_pairs ADD COLUMN stop_loss_percent FLOAT DEFAULT 2.0")
            updates.append("✅ Добавлена колонка stop_loss_percent в trading_pairs")
        
        if 'take_profit_percent' not in pair_columns:
            cursor.execute("ALTER TABLE trading_pairs ADD COLUMN take_profit_percent FLOAT DEFAULT 4.0")
            updates.append("✅ Добавлена колонка take_profit_percent в trading_pairs")
        
        if 'updated_at' not in pair_columns:
            cursor.execute("""
                ALTER TABLE trading_pairs 
                ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            """)
            updates.append("✅ Добавлена колонка updated_at в trading_pairs")
    
    # 6. Обновляем таблицу bot_settings
    print("\n📋 Проверка таблицы bot_settings...")
    cursor.execute("""
        SELECT COLUMN_NAME 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'bot_settings'
    """, (DB_NAME,))
    
    settings_columns = [row[0] for row in cursor.fetchall()]
    
    if settings_columns and 'description' not in settings_columns:
        cursor.execute("ALTER TABLE bot_settings ADD COLUMN description TEXT")
        updates.append("✅ Добавлена колонка description в bot_settings")
    
    # 7. Создаем индексы если не существуют
    print("\n📋 Проверка индексов...")
    
    # Функция для безопасного создания индекса
    def create_index_if_not_exists(table, index_name, columns):
        cursor.execute(f"""
            SELECT COUNT(1) 
            FROM INFORMATION_SCHEMA.STATISTICS 
            WHERE table_schema = '{DB_NAME}' 
            AND table_name = '{table}' 
            AND index_name = '{index_name}'
        """)
        if cursor.fetchone()[0] == 0:
            cursor.execute(f"CREATE INDEX {index_name} ON {table} ({columns})")
            updates.append(f"✅ Создан индекс {index_name} на {table}")
    
    # Создаем индексы
    create_index_if_not_exists('trades', 'idx_closed_at', 'closed_at')
    create_index_if_not_exists('signals', 'idx_executed', 'executed')
    create_index_if_not_exists('signals', 'idx_strategy', 'strategy')
    create_index_if_not_exists('balances', 'idx_currency_timestamp', 'currency, timestamp')
    
    # Применяем изменения
    connection.commit()
    
    # Выводим результаты
    print("\n" + "=" * 50)
    print("📊 РЕЗУЛЬТАТЫ ОБНОВЛЕНИЯ:")
    print("=" * 50)
    
    if updates:
        print(f"\n✅ Выполнено обновлений: {len(updates)}")
        for update in updates:
            print(f"   {update}")
    else:
        print("\n✅ База данных уже актуальна, обновления не требуются")
    
    # Показываем финальную структуру
    print("\n📊 Финальная структура БД:")
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    print(f"Всего таблиц: {len(tables)}")
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
        count = cursor.fetchone()[0]
        print(f"   - {table[0]}: {count} записей")
    
    connection.close()
    print("\n✅ Обновление завершено успешно!")
    
except pymysql.Error as e:
    print(f"\n❌ Ошибка MySQL: {e}")
    sys.exit(1)
except Exception as e:
    print(f"\n❌ Неожиданная ошибка: {e}")
    sys.exit(1)