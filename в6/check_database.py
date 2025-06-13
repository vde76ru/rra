#!/usr/bin/env python3
# check_database.py - Проверка подключения к БД и создание таблиц

import os
import sys
import pymysql
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Параметры подключения
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_NAME = os.getenv('DB_NAME', 'crypto_top_bd_mysql')
DB_USER = os.getenv('DB_USER', 'crypto_top_admin')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'LSM6_PqnuZ10nvEdzfe6')

print(f"🔍 Проверка подключения к БД {DB_NAME}...")

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
    
    # Проверяем существующие таблицы
    cursor.execute("SHOW TABLES")
    existing_tables = [table[0] for table in cursor.fetchall()]
    
    if existing_tables:
        print(f"\n📊 Найдено таблиц: {len(existing_tables)}")
        for table in existing_tables:
            print(f"   - {table}")
    
    # SQL для создания таблиц (если их нет)
    tables_sql = [
        """
        CREATE TABLE IF NOT EXISTS trades (
            id INT AUTO_INCREMENT PRIMARY KEY,
            symbol VARCHAR(20) NOT NULL,
            side VARCHAR(10) NOT NULL,
            entry_price FLOAT NOT NULL,
            exit_price FLOAT,
            quantity FLOAT NOT NULL,
            profit FLOAT,
            status VARCHAR(20) NOT NULL DEFAULT 'OPEN',
            strategy VARCHAR(50) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            closed_at TIMESTAMP NULL,
            INDEX idx_symbol (symbol),
            INDEX idx_status (status),
            INDEX idx_created_at (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """,
        
        """
        CREATE TABLE IF NOT EXISTS signals (
            id INT AUTO_INCREMENT PRIMARY KEY,
            symbol VARCHAR(20) NOT NULL,
            action VARCHAR(10) NOT NULL,
            confidence FLOAT NOT NULL,
            price FLOAT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            executed BOOLEAN DEFAULT FALSE,
            INDEX idx_symbol (symbol),
            INDEX idx_created_at (created_at),
            INDEX idx_executed (executed)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """,
        
        """
        CREATE TABLE IF NOT EXISTS balances (
            id INT AUTO_INCREMENT PRIMARY KEY,
            currency VARCHAR(10) NOT NULL,
            total FLOAT NOT NULL,
            free FLOAT NOT NULL,
            used FLOAT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_currency (currency),
            INDEX idx_timestamp (timestamp)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    ]
    
    # Создаем таблицы
    print("\n🔨 Создание таблиц...")
    for i, sql in enumerate(tables_sql):
        cursor.execute(sql)
        print(f"   ✅ Таблица {i+1} создана/проверена")
    
    connection.commit()
    
    # Финальная проверка
    cursor.execute("SHOW TABLES")
    final_tables = cursor.fetchall()
    
    print(f"\n✅ База данных готова! Всего таблиц: {len(final_tables)}")
    
    connection.close()
    
except pymysql.Error as e:
    print(f"❌ Ошибка MySQL: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Ошибка: {e}")
    sys.exit(1)