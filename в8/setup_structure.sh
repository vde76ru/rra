#!/bin/bash
# Скрипт создания правильной структуры проекта

cd /var/www/www-root/data/www/systemetech.ru

# Создаем необходимые директории
mkdir -p src/{core,exchange,strategies,utils,web}
mkdir -p logs
mkdir -p data/{cache,backups}
mkdir -p static/css
mkdir -p templates

# Создаем __init__.py файлы для всех модулей
touch src/__init__.py
touch src/core/__init__.py
touch src/exchange/__init__.py
touch src/strategies/__init__.py
touch src/utils/__init__.py
touch src/web/__init__.py

# Устанавливаем правильные права
chown -R www-root:www-root /var/www/www-root/data/www/systemetech.ru
chmod -R 755 /var/www/www-root/data/www/systemetech.ru
chmod -R 777 logs  # Для записи логов

echo "✅ Структура проекта создана"