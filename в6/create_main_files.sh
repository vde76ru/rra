#!/bin/bash
# Скрипт создания основных файлов проекта

cd /var/www/www-root/data/www/systemetech.ru

echo "📝 Создание основных файлов проекта..."

# 1. Создаем файл database.py
cat > src/core/database.py << 'EOF'
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Подключение к MySQL
DATABASE_URL = f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
EOF

# 2. Создаем файл models.py
cat > src/core/models.py << 'EOF'
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from datetime import datetime
from .database import Base

class Trade(Base):
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), index=True)
    side = Column(String(10))  # BUY/SELL
    entry_price = Column(Float)
    exit_price = Column(Float, nullable=True)
    quantity = Column(Float)
    profit = Column(Float, nullable=True)
    status = Column(String(20))  # OPEN/CLOSED
    strategy = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)

class Signal(Base):
    __tablename__ = "signals"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20))
    action = Column(String(10))  # BUY/SELL
    confidence = Column(Float)
    price = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    executed = Column(Boolean, default=False)

class Balance(Base):
    __tablename__ = "balances"
    
    id = Column(Integer, primary_key=True, index=True)
    currency = Column(String(10))
    total = Column(Float)
    free = Column(Float)
    used = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
EOF

# 3. Создаем файл bybit_client.py
cat > src/exchange/bybit_client.py << 'EOF'
import ccxt
import asyncio
import time
import random
from typing import Dict, Optional
import os
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)

class HumanizedBybitClient:
    """Клиент Bybit с имитацией человеческого поведения"""
    
    def __init__(self):
        self.testnet = os.getenv('BYBIT_TESTNET', 'true').lower() == 'true'
        
        # Настройка подключения
        if self.testnet:
            self.exchange = ccxt.bybit({
                'apiKey': os.getenv('BYBIT_API_KEY'),
                'secret': os.getenv('BYBIT_API_SECRET'),
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'swap',  # Для бессрочных контрактов
                    'testnet': True
                }
            })
            self.exchange.set_sandbox_mode(True)
        else:
            self.exchange = ccxt.bybit({
                'apiKey': os.getenv('BYBIT_API_KEY'),
                'secret': os.getenv('BYBIT_API_SECRET'),
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'swap'
                }
            })
    
    async def human_delay(self):
        """Человеческая задержка между действиями"""
        delay = random.uniform(
            float(os.getenv('MIN_DELAY_SECONDS', 0.5)),
            float(os.getenv('MAX_DELAY_SECONDS', 3.0))
        )
        await asyncio.sleep(delay)
    
    async def fetch_balance(self) -> Dict:
        """Получить баланс с человеческой задержкой"""
        await self.human_delay()
        try:
            balance = self.exchange.fetch_balance()
            return balance
        except Exception as e:
            logger.error(f"Ошибка получения баланса: {e}")
            return {}
    
    async def fetch_ticker(self, symbol: str) -> Dict:
        """Получить текущую цену"""
        await self.human_delay()
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return ticker
        except Exception as e:
            logger.error(f"Ошибка получения цены: {e}")
            return {}
    
    async def create_order(self, symbol: str, side: str, amount: float, price: Optional[float] = None):
        """Создать ордер с человеческим поведением"""
        # Думаем перед ордером
        thinking_time = random.uniform(1.0, 3.0)
        await asyncio.sleep(thinking_time)
        
        # Округляем размер позиции по-человечески
        if amount > 100:
            amount = round(amount, -1)  # До десятков
        elif amount > 10:
            amount = round(amount, 0)   # До целых
        else:
            amount = round(amount, 2)   # До сотых
        
        try:
            # Иногда делаем "ошибку" и отменяем
            if random.random() < 0.02:  # 2% шанс
                logger.info("Имитация ошибки - отмена действия")
                await asyncio.sleep(random.uniform(0.5, 1.5))
                return None
            
            # Создаем ордер
            order_type = 'market'
            order = self.exchange.create_order(
                symbol=symbol,
                type=order_type,
                side=side,
                amount=amount,
                price=price
            )
            
            logger.info(f"Ордер создан: {side} {amount} {symbol}")
            return order
            
        except Exception as e:
            logger.error(f"Ошибка создания ордера: {e}")
            return None
EOF

# 4. Создаем файл simple_momentum.py
cat > src/strategies/simple_momentum.py << 'EOF'
import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator
import logging

logger = logging.getLogger(__name__)

class SimpleMomentumStrategy:
    """Простая momentum стратегия с защитой от шума"""
    
    def __init__(self):
        self.rsi_period = 14
        self.ema_fast = 9
        self.ema_slow = 21
        self.rsi_oversold = 30
        self.rsi_overbought = 70
        
    def analyze(self, df: pd.DataFrame) -> dict:
        """Анализ данных и генерация сигнала"""
        if len(df) < 50:
            return {'signal': 'WAIT', 'confidence': 0}
        
        # Расчет индикаторов
        df['rsi'] = RSIIndicator(df['close'], window=self.rsi_period).rsi()
        df['ema_fast'] = EMAIndicator(df['close'], window=self.ema_fast).ema_indicator()
        df['ema_slow'] = EMAIndicator(df['close'], window=self.ema_slow).ema_indicator()
        
        # Последние значения
        current_rsi = df['rsi'].iloc[-1]
        current_ema_fast = df['ema_fast'].iloc[-1]
        current_ema_slow = df['ema_slow'].iloc[-1]
        current_volume = df['volume'].iloc[-1]
        avg_volume = df['volume'].rolling(20).mean().iloc[-1]
        
        signal = 'WAIT'
        confidence = 0.0
        
        # Условия для покупки
        if (current_ema_fast > current_ema_slow and
            self.rsi_oversold < current_rsi < 50 and
            current_volume > avg_volume * 1.2):
            
            signal = 'BUY'
            confidence = min(0.8, (current_volume / avg_volume) * 0.4 + 0.4)
            
        # Условия для продажи
        elif (current_ema_fast < current_ema_slow and
              50 < current_rsi < self.rsi_overbought and
              current_volume > avg_volume):
            
            signal = 'SELL'
            confidence = min(0.8, (current_volume / avg_volume) * 0.4 + 0.4)
        
        return {
            'signal': signal,
            'confidence': confidence,
            'rsi': current_rsi,
            'ema_diff': current_ema_fast - current_ema_slow,
            'volume_ratio': current_volume / avg_volume if avg_volume > 0 else 1
        }
EOF

echo "✅ Основные файлы созданы"