#!/usr/bin/env python3
# test_bybit_connection.py - Проверка подключения к Bybit API

import os
import sys
from dotenv import load_dotenv
import ccxt

print("🔍 Тест подключения к Bybit API")
print("=" * 50)

# Загружаем конфигурацию
load_dotenv()

# Проверяем наличие ключей
api_key = os.getenv('BYBIT_API_KEY')
api_secret = os.getenv('BYBIT_API_SECRET')
testnet = os.getenv('BYBIT_TESTNET', 'true').lower() == 'true'

if not api_key or not api_secret:
    print("❌ API ключи не найдены в конфигурации!")
    print("   Запустите: sudo python add_api_keys.py")
    sys.exit(1)

if api_key == '' or api_key == 'your_testnet_api_key_here':
    print("❌ API ключи не настроены!")
    print("   Запустите: sudo python add_api_keys.py")
    sys.exit(1)

print(f"\n📊 Конфигурация:")
print(f"   Режим: {'TESTNET' if testnet else 'MAINNET'}")
print(f"   API Key: {api_key[:10]}...{api_key[-4:]}")  # Показываем только часть ключа

try:
    # Создаем подключение
    print("\n🔌 Подключение к Bybit...")
    
    exchange = ccxt.bybit({
        'apiKey': api_key,
        'secret': api_secret,
        'enableRateLimit': True,
        'options': {
            'defaultType': 'swap',  # Для бессрочных контрактов
            'testnet': testnet
        }
    })
    
    if testnet:
        exchange.set_sandbox_mode(True)
    
    # Тест 1: Получаем баланс
    print("\n💰 Проверка баланса...")
    balance = exchange.fetch_balance()
    
    # Показываем балансы
    print("\n📊 Ваши балансы:")
    for currency, balance_info in balance['total'].items():
        if balance_info > 0:
            print(f"   {currency}: {balance_info:.8f}")
    
    # Показываем USDT баланс отдельно
    usdt_balance = balance.get('USDT', {})
    if usdt_balance:
        total_usdt = usdt_balance.get('total', 0)
        free_usdt = usdt_balance.get('free', 0)
        print(f"\n💵 USDT баланс:")
        print(f"   Всего: {total_usdt:.2f} USDT")
        print(f"   Доступно: {free_usdt:.2f} USDT")
    
    # Тест 2: Получаем текущую цену BTC
    print("\n📈 Проверка рыночных данных...")
    ticker = exchange.fetch_ticker('BTCUSDT')
    current_price = ticker['last']
    volume_24h = ticker['quoteVolume']
    
    print(f"   BTC/USDT: ${current_price:,.2f}")
    print(f"   Объем 24ч: ${volume_24h:,.0f}")
    
    # Тест 3: Проверяем доступные торговые пары
    print("\n🔍 Загрузка доступных рынков...")
    markets = exchange.load_markets()
    print(f"   Найдено рынков: {len(markets)}")
    
    # Показываем популярные пары
    popular_pairs = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT']
    print("\n📊 Популярные пары:")
    for pair in popular_pairs:
        if pair in markets:
            print(f"   ✅ {pair}")
    
    print("\n✅ Подключение успешно!")
    print("\n🎉 Поздравляем! API ключи работают правильно.")
    
    if testnet and total_usdt == 0:
        print("\n💡 Совет: Пополните тестовый баланс на https://testnet.bybit.com/faucet")
    
    print("\n🚀 Теперь можно запускать бота:")
    print("   python main_simple.py")
    
except ccxt.BaseError as e:
    print(f"\n❌ Ошибка API: {e}")
    print("\nВозможные причины:")
    print("1. Неверные API ключи")
    print("2. API ключи не активированы")
    print("3. Нет прав на чтение баланса")
    print("4. IP адрес не в белом списке (если включена защита)")
    
except Exception as e:
    print(f"\n❌ Неожиданная ошибка: {e}")
    print("\nПроверьте подключение к интернету и попробуйте снова.")