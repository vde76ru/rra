#!/usr/bin/env python3
# add_api_keys.py - Безопасное добавление API ключей

import os
import sys
import getpass
import re

CONFIG_FILE = "/etc/crypto/config/.env"

print("🔐 Добавление API ключей Bybit")
print("=" * 50)
print("")
print("⚠️  ВАЖНО: Используйте только TESTNET ключи для начала!")
print("📌 Получите их на: https://testnet.bybit.com")
print("")
print("Инструкция:")
print("1. Зайдите на https://testnet.bybit.com")
print("2. Зарегистрируйтесь или войдите")
print("3. Перейдите в API Management")
print("4. Создайте новый API ключ")
print("5. Дайте права: Read + Trade (НЕ давайте права на вывод!)")
print("")

# Проверка прав доступа
if os.geteuid() != 0:
    print("❌ Запустите скрипт с sudo:")
    print("   sudo python add_api_keys.py")
    sys.exit(1)

# Проверка существования файла
if not os.path.exists(CONFIG_FILE):
    print(f"❌ Файл {CONFIG_FILE} не найден!")
    sys.exit(1)

# Ввод API ключа
print("-" * 50)
api_key = input("Введите BYBIT_API_KEY: ").strip()
if not api_key:
    print("❌ API ключ не может быть пустым!")
    sys.exit(1)

# Проверка формата ключа (базовая)
if len(api_key) < 10:
    print("❌ API ключ слишком короткий!")
    sys.exit(1)

# Ввод API секрета
api_secret = getpass.getpass("Введите BYBIT_API_SECRET (ввод скрыт): ").strip()
if not api_secret:
    print("❌ API секрет не может быть пустым!")
    sys.exit(1)

print("")
print("📝 Обновление конфигурации...")

try:
    # Читаем текущий файл
    with open(CONFIG_FILE, 'r') as f:
        lines = f.readlines()
    
    # Обновляем значения
    updated = False
    new_lines = []
    
    for line in lines:
        # Обновляем API ключ
        if line.startswith('BYBIT_API_KEY='):
            new_lines.append(f'BYBIT_API_KEY={api_key}\n')
            updated = True
        # Обновляем API секрет
        elif line.startswith('BYBIT_API_SECRET='):
            new_lines.append(f'BYBIT_API_SECRET={api_secret}\n')
            updated = True
        else:
            new_lines.append(line)
    
    # Записываем обратно
    with open(CONFIG_FILE, 'w') as f:
        f.writelines(new_lines)
    
    # Устанавливаем безопасные права
    os.chmod(CONFIG_FILE, 0o600)
    
    print("✅ API ключи успешно обновлены!")
    print("")
    print("📊 Проверка конфигурации:")
    
    # Проверяем что ключи установлены
    from dotenv import load_dotenv
    load_dotenv(CONFIG_FILE)
    
    if os.getenv('BYBIT_TESTNET') == 'true':
        print("✅ Режим: TESTNET (безопасный режим)")
    else:
        print("⚠️  Режим: MAINNET (реальные деньги!)")
    
    print("")
    print("🚀 Следующие шаги:")
    print("1. Вернитесь в директорию проекта:")
    print("   cd /var/www/www-root/data/www/systemetech.ru")
    print("")
    print("2. Активируйте виртуальное окружение:")
    print("   source venv/bin/activate")
    print("")
    print("3. Проверьте установку:")
    print("   python test_installation_fixed.py")
    print("")
    print("4. Запустите простой тест подключения:")
    print("   python main_simple.py")
    
except Exception as e:
    print(f"❌ Ошибка при обновлении конфигурации: {e}")
    sys.exit(1)