#!/bin/bash
# start_bot.sh - Скрипт запуска бота

# Переход в директорию проекта
cd /var/www/www-root/data/www/systemetech.ru

# Активация виртуального окружения
source venv/bin/activate

# Экспорт пути для модулей
export PYTHONPATH=/var/www/www-root/data/www/systemetech.ru:$PYTHONPATH

# Создание директории для логов если не существует
mkdir -p logs

# Проверка что все сервисы запущены
echo "🔍 Проверка сервисов..."

if ! systemctl is-active --quiet redis-server; then
    echo "❌ Redis не запущен!"
    exit 1
fi

if ! systemctl is-active --quiet mysql; then
    echo "❌ MySQL не запущен!"
    exit 1
fi

echo "✅ Все сервисы работают"

# Проверка конфигурации
if [ ! -f ".env" ] && [ ! -L ".env" ]; then
    echo "❌ Файл .env не найден!"
    exit 1
fi

# Проверка API ключей
source .env
if [ -z "$BYBIT_API_KEY" ] || [ "$BYBIT_API_KEY" == "your_testnet_api_key_here" ]; then
    echo "❌ API ключи не настроены!"
    echo "Используйте: sudo bash update_api_keys.sh"
    exit 1
fi

echo "🤖 Запуск Crypto Trading Bot..."

# Запуск основного бота
python main.py