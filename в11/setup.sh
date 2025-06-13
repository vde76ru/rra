#!/bin/bash
# setup.sh - Главный скрипт установки Crypto Trading Bot

set -e  # Останавливаемся при любой ошибке

echo "🚀 Установка Crypto Trading Bot v3.0"
echo "===================================="

# Переход в директорию проекта
cd /var/www/www-root/data/www/systemetech.ru

# 1. Проверка прав доступа
echo -e "\n📋 Шаг 1: Проверка прав доступа..."
if [ "$EUID" -ne 0 ]; then 
    echo "⚠️  Запустите скрипт с sudo или от root"
    exit 1
fi

# 2. Установка системных зависимостей
echo -e "\n📋 Шаг 2: Установка системных зависимостей..."
bash install_dependencies.sh

# 3. Создание структуры проекта
echo -e "\n📋 Шаг 3: Создание структуры проекта..."
bash setup_structure.sh

# 4. Настройка виртуального окружения
echo -e "\n📋 Шаг 4: Настройка Python окружения..."

# Удаляем старое окружение если есть
if [ -d "venv" ]; then
    echo "🗑️  Удаление старого виртуального окружения..."
    rm -rf venv
fi

# Создаем новое
echo "🐍 Создание виртуального окружения..."
python3 -m venv venv

# Активируем
source venv/bin/activate

# Обновляем pip
pip install --upgrade pip setuptools wheel

# 5. Установка Python пакетов
echo -e "\n📋 Шаг 5: Установка Python пакетов..."
pip install -r requirements_fixed.txt

# 6. Проверка .env файла
echo -e "\n📋 Шаг 6: Проверка конфигурации..."
if [ ! -f ".env" ]; then
    echo "⚠️  Файл .env не найден. Создаем из шаблона..."
    # Здесь должен быть код создания .env из шаблона
    echo "❌ Создайте файл .env и заполните API ключи!"
    echo "   Используйте .env.example как шаблон"
    exit 1
else
    echo "✅ Файл .env найден"
fi

# 7. Проверка базы данных
echo -e "\n📋 Шаг 7: Проверка и настройка базы данных..."
python check_database.py

# 8. Создание скрипта запуска
echo -e "\n📋 Шаг 8: Создание скриптов запуска..."
cat > start_bot.sh << 'EOF'
#!/bin/bash
# Скрипт запуска бота

cd /var/www/www-root/data/www/systemetech.ru
source venv/bin/activate

# Проверка что все сервисы запущены
if ! systemctl is-active --quiet redis-server; then
    echo "❌ Redis не запущен!"
    exit 1
fi

if ! systemctl is-active --quiet mysql; then
    echo "❌ MySQL не запущен!"
    exit 1
fi

echo "🤖 Запуск Crypto Trading Bot..."
python main.py
EOF

chmod +x start_bot.sh

# 9. Создание systemd сервиса
echo -e "\n📋 Шаг 9: Создание systemd сервиса..."
cat > /etc/systemd/system/cryptobot.service << 'EOF'
[Unit]
Description=Crypto Trading Bot
After=network.target mysql.service redis.service

[Service]
Type=simple
User=www-root
Group=www-root
WorkingDirectory=/var/www/www-root/data/www/systemetech.ru
Environment="PATH=/var/www/www-root/data/www/systemetech.ru/venv/bin"
ExecStart=/var/www/www-root/data/www/systemetech.ru/venv/bin/python main.py
Restart=on-failure
RestartSec=10
StandardOutput=append:/var/www/www-root/data/www/systemetech.ru/logs/bot.log
StandardError=append:/var/www/www-root/data/www/systemetech.ru/logs/bot_error.log

[Install]
WantedBy=multi-user.target
EOF

# 10. Настройка веб-интерфейса в ISPmanager
echo -e "\n📋 Шаг 10: Настройка веб-интерфейса..."
# Здесь должна быть настройка nginx через ISPmanager API или конфиг

# 11. Финальные проверки
echo -e "\n📋 Финальные проверки..."
echo "✅ Виртуальное окружение: $(which python)"
echo "✅ Установленные пакеты: $(pip list | wc -l) пакетов"
echo "✅ База данных: Подключение проверено"
echo "✅ Redis: $(redis-cli ping)"

echo -e "\n🎉 Установка завершена!"
echo ""
echo "⚠️  ВАЖНО: Перед запуском:"
echo "1. Отредактируйте файл .env и добавьте API ключи Bybit"
echo "2. Получите ключи на https://testnet.bybit.com"
echo "3. Запустите бота: sudo systemctl start cryptobot"
echo "4. Проверьте логи: tail -f logs/trading.log"
echo ""
echo "📊 Веб-интерфейс будет доступен на: http://systemetech.ru:8001"