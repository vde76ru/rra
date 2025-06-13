import asyncio
import os
from datetime import datetime
import logging
from dotenv import load_dotenv
import pandas as pd

from src.exchange.bybit_client import HumanizedBybitClient
from src.strategies.simple_momentum import SimpleMomentumStrategy
from src.core.database import SessionLocal
from src.core.models import Trade, Signal

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/trading.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()

class CryptoTradingBot:
    def __init__(self):
        self.client = HumanizedBybitClient()
        self.strategy = SimpleMomentumStrategy()
        self.symbol = os.getenv('TRADING_SYMBOL', 'BTCUSDT')
        self.position_size_percent = float(os.getenv('MAX_POSITION_SIZE_PERCENT', 5))
        self.is_running = True
        self.current_position = None
        
    async def fetch_klines(self, limit=100):
        """Получить исторические данные"""
        try:
            ohlcv = self.client.exchange.fetch_ohlcv(
                self.symbol, 
                timeframe='5m', 
                limit=limit
            )
            df = pd.DataFrame(
                ohlcv, 
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            logger.error(f"Ошибка получения данных: {e}")
            return None
    
    async def check_signals(self):
        """Проверка торговых сигналов"""
        df = await self.fetch_klines()
        if df is None or df.empty:
            return
        
        # Анализ стратегии
        analysis = self.strategy.analyze(df)
        
        # Логирование анализа
        logger.info(f"Анализ: {analysis}")
        
        # Если есть сигнал с достаточной уверенностью
        if analysis['confidence'] > 0.65:
            await self.execute_signal(analysis)
    
    async def execute_signal(self, analysis):
        """Исполнение торгового сигнала"""
        # Получаем баланс
        balance = await self.client.fetch_balance()
        free_balance = balance.get('USDT', {}).get('free', 0)
        
        if free_balance <= 0:
            logger.warning("Недостаточно средств")
            return
        
        # Получаем текущую цену
        ticker = await self.client.fetch_ticker(self.symbol)
        current_price = ticker['last']
        
        # Расчет размера позиции
        position_value = free_balance * (self.position_size_percent / 100)
        amount = position_value / current_price
        
        # Исполнение ордера
        if analysis['signal'] == 'BUY' and self.current_position is None:
            order = await self.client.create_order(
                self.symbol,
                'buy',
                amount
            )
            
            if order:
                # Сохраняем в БД
                db = SessionLocal()
                trade = Trade(
                    symbol=self.symbol,
                    side='BUY',
                    entry_price=current_price,
                    quantity=amount,
                    status='OPEN',
                    strategy='momentum'
                )
                db.add(trade)
                db.commit()
                db.close()
                
                self.current_position = trade
                logger.info(f"Позиция открыта: BUY {amount} @ {current_price}")
        
        elif analysis['signal'] == 'SELL' and self.current_position:
            order = await self.client.create_order(
                self.symbol,
                'sell',
                self.current_position.quantity
            )
            
            if order:
                # Обновляем в БД
                db = SessionLocal()
                trade = db.query(Trade).filter(Trade.id == self.current_position.id).first()
                trade.exit_price = current_price
                trade.profit = (current_price - trade.entry_price) * trade.quantity
                trade.status = 'CLOSED'
                trade.closed_at = datetime.utcnow()
                db.commit()
                db.close()
                
                logger.info(f"Позиция закрыта: SELL @ {current_price}, Profit: {trade.profit}")
                self.current_position = None
    
    async def run(self):
        """Основной цикл бота"""
        logger.info(f"Бот запущен. Торговая пара: {self.symbol}")
        
        while self.is_running:
            try:
                await self.check_signals()
                
                # Пауза между проверками (имитация человека)
                await asyncio.sleep(60)  # Проверка раз в минуту
                
            except Exception as e:
                logger.error(f"Ошибка в основном цикле: {e}")
                await asyncio.sleep(30)

async def main():
    bot = CryptoTradingBot()
    await bot.run()

if __name__ == "__main__":
    asyncio.run(main())