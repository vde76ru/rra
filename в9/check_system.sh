#!/bin/bash
# check_system.sh - Полная проверка системы

echo "🔍 ПОЛНАЯ ПРОВЕРКА CRYPTO TRADING BOT"
echo "====================================="

cd /var/www/www-root/data/www/systemetech.ru

# 1. Проверка символической ссылки
echo -e "\n1️⃣ Проверка конфигурации..."
if [ -L ".env" ]; then
    echo "✅ Символическая ссылка .env существует"
    echo "   → $(readlink -f .env)"
else
    echo "❌ Символическая ссылка .env не найдена"
    echo "   Создаем: ln -sf /etc/crypto/config/.env .env"
    ln -sf /etc/crypto/config/.env .env
fi

# 2. Проверка сервисов
echo -e "\n2️⃣ Проверка сервисов..."

# MySQL
if systemctl is-active --quiet mysql; then
    echo "✅ MySQL работает"
else
    echo "❌ MySQL не запущен"
fi

# Redis
if systemctl is-active --quiet redis-server; then
    echo "✅ Redis работает"
    # Проверяем доступность
    if redis-cli ping > /dev/null 2>&1; then
        echo "   ✅ Redis отвечает на запросы"
    else
        echo "   ⚠️  Redis требует аутентификации"
    fi
else
    echo "❌ Redis не запущен"
fi

# 3. Проверка Python окружения
echo -e "\n3️⃣ Проверка Python окружения..."
if [ -d "venv" ]; then
    echo "✅ Виртуальное окружение существует"
    source venv/bin/activate
    echo "✅ Активировано: $(which python)"
    
    # Проверка основных пакетов
    if python -c "import ccxt" 2>/dev/null; then
        echo "✅ CCXT установлен"
    else
        echo "❌ CCXT не установлен"
    fi
    
    if python -c "import fastapi" 2>/dev/null; then
        echo "✅ FastAPI установлен"
    else
        echo "❌ FastAPI не установлен"
    fi
else
    echo "❌ Виртуальное окружение не найдено"
fi

# 4. Проверка API ключей
echo -e "\n4️⃣ Проверка API ключей..."
source /etc/crypto/config/.env

if [ -n "$BYBIT_API_KEY" ] && [ "$BYBIT_API_KEY" != "" ] && [ "$BYBIT_API_KEY" != "your_testnet_api_key_here" ]; then
    echo "✅ BYBIT_API_KEY установлен"
else
    echo "❌ BYBIT_API_KEY не настроен"
fi

if [ -n "$BYBIT_API_SECRET" ] && [ "$BYBIT_API_SECRET" != "" ]; then
    echo "✅ BYBIT_API_SECRET установлен"
else
    echo "❌ BYBIT_API_SECRET не настроен"
fi

if [ "$BYBIT_TESTNET" = "true" ]; then
    echo "✅ Режим: TESTNET (безопасный)"
else
    echo "⚠️  Режим: MAINNET (реальные деньги!)"
fi

# 5. Проверка файловой структуры
echo -e "\n5️⃣ Проверка файлов проекта..."
required_files=(
    "app.py"
    "main_simple.py"
    "src/core/database.py"
    "src/core/models.py"
    "src/exchange/bybit_client.py"
    "src/strategies/simple_momentum.py"
)

all_files_exist=true
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file не найден"
        all_files_exist=false
    fi
done

# 6. Финальный статус
echo -e "\n📊 ИТОГОВЫЙ СТАТУС:"
echo "=================="

if [ "$all_files_exist" = true ] && [ -n "$BYBIT_API_KEY" ] && [ "$BYBIT_API_KEY" != "" ] && [ "$BYBIT_API_KEY" != "your_testnet_api_key_here" ]; then
    echo "✅ Система готова к запуску!"
    echo ""
    echo "🚀 Команды для запуска:"
    echo "1. Тест подключения к API:"
    echo "   python test_bybit_connection.py"
    echo ""
    echo "2. Запуск простого мониторинга:"
    echo "   python main_simple.py"
    echo ""
    echo "3. Запуск веб-интерфейса:"
    echo "   ./start_web.sh"
else
    echo "❌ Система не готова к запуску"
    echo ""
    echo "📝 Необходимо выполнить:"
    if [ -z "$BYBIT_API_KEY" ] || [ "$BYBIT_API_KEY" = "" ] || [ "$BYBIT_API_KEY" = "your_testnet_api_key_here" ]; then
        echo "• Добавить API ключи: sudo python add_api_keys.py"
    fi
    if [ "$all_files_exist" = false ]; then
        echo "• Создать недостающие файлы: bash create_main_files.sh"
    fi
fi