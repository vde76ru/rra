#!/usr/bin/env python3
# create_missing_tables.py - Создание недостающих таблиц

import os
import sys
import pymysql
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_NAME = os.getenv('DB_NAME', 'crypto_top_bd_mysql')
DB_USER = os.getenv('DB_USER', 'crypto_top_admin')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'LSM6_PqnuZ10nvEdzfe6')

print("🔨 Создание недостающих таблиц...")

try:
    connection = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset='utf8mb4'
    )
    
    cursor = connection.cursor()
    
    # Таблица пользователей
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        hashed_password VARCHAR(128) NOT NULL,
        is_active BOOLEAN DEFAULT TRUE,
        is_blocked BOOLEAN DEFAULT FALSE,
        failed_login_attempts INT DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP NULL,
        blocked_at TIMESTAMP NULL,
        INDEX idx_username (username)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    print("✅ Таблица users создана")
    
    # Таблица настроек бота
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bot_settings (
        id INT AUTO_INCREMENT PRIMARY KEY,
        `key` VARCHAR(50) UNIQUE NOT NULL,
        value TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        INDEX idx_key (`key`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    print("✅ Таблица bot_settings создана")
    
    # Таблица торговых пар
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS trading_pairs (
        id INT AUTO_INCREMENT PRIMARY KEY,
        symbol VARCHAR(20) UNIQUE NOT NULL,
        is_active BOOLEAN DEFAULT TRUE,
        min_position_size FLOAT,
        max_position_size FLOAT,
        strategy VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_symbol (symbol)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    print("✅ Таблица trading_pairs создана")
    
    # Проверяем существование колонок перед добавлением
    cursor.execute("""
        SELECT COLUMN_NAME 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = %s 
        AND TABLE_NAME = 'trades'
    """, (DB_NAME,))
    
    existing_columns = [row[0] for row in cursor.fetchall()]
    
    # Добавляем stop_loss если не существует
    if 'stop_loss' not in existing_columns:
        cursor.execute("ALTER TABLE trades ADD COLUMN stop_loss FLOAT")
        print("✅ Добавлена колонка stop_loss")
    
    # Добавляем take_profit если не существует
    if 'take_profit' not in existing_columns:
        cursor.execute("ALTER TABLE trades ADD COLUMN take_profit FLOAT")
        print("✅ Добавлена колонка take_profit")
    
    connection.commit()
    
    # Проверяем все таблицы
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    print(f"\n📊 Всего таблиц в БД: {len(tables)}")
    for table in tables:
        print(f"   - {table[0]}")
    
    # Добавляем начальные торговые пары
    print("\n📝 Добавление начальных торговых пар...")
    pairs = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT']
    for pair in pairs:
        cursor.execute("""
            INSERT IGNORE INTO trading_pairs (symbol, is_active, strategy) 
            VALUES (%s, TRUE, 'multi_indicator')
        """, (pair,))
    connection.commit()
    print("✅ Торговые пары добавлены")
    
    connection.close()
    print("\n✅ Все таблицы созданы успешно!")
    
except Exception as e:
    print(f"❌ Ошибка: {e}")
    sys.exit(1)