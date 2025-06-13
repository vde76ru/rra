#!/bin/bash
# Скрипт установки всех зависимостей

echo "🔧 Установка зависимостей для Crypto Trading Bot..."

# Обновление системы
sudo apt update

# Установка Redis если не установлен
if ! command -v redis-server &> /dev/null; then
    echo "📦 Установка Redis..."
    sudo apt install redis-server -y
    sudo systemctl enable redis-server
    sudo systemctl start redis-server
else
    echo "✅ Redis уже установлен"
fi

# Установка необходимых системных пакетов
echo "📦 Установка системных пакетов..."
sudo apt install -y build-essential python3-dev libmysqlclient-dev

# Проверка статуса Redis
if systemctl is-active --quiet redis-server; then
    echo "✅ Redis работает"
else
    echo "❌ Redis не запущен. Запускаем..."
    sudo systemctl start redis-server
fi

# Проверка MySQL
if systemctl is-active --quiet mysql; then
    echo "✅ MySQL работает"
else
    echo "❌ MySQL не запущен!"
    exit 1
fi

echo "✅ Все системные зависимости установлены"