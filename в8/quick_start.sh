#!/bin/bash
# quick_start.sh - Быстрый запуск после добавления API ключей

cd /var/www/www-root/data/www/systemetech.ru

echo "🚀 БЫСТРЫЙ ЗАПУСК CRYPTO TRADING BOT"
echo "===================================="

# Активируем виртуальное окружение
echo -e "\n📦 Активация виртуального окружения..."
source venv/bin/activate

# Проверяем API ключи
echo -e "\n🔑 Проверка API ключей..."
source /etc/crypto/config/.env

if [ -z "$BYBIT_API_KEY" ] || [ "$BYBIT_API_KEY" = "" ] || [ "$BYBIT_API_KEY" = "your_testnet_api_key_here" ]; then
    echo "❌ API ключи не настроены!"
    echo ""
    echo "📝 Сначала добавьте API ключи:"
    echo "   sudo python add_api_keys.py"
    echo ""
    echo "Инструкция:"
    echo "1. Зайдите на https://testnet.bybit.com"
    echo "2. Создайте API ключ с правами Read + Trade"
    echo "3. Запустите: sudo python add_api_keys.py"
    exit 1
fi

echo "✅ API ключи найдены"

# Проверяем подключение к API
echo -e "\n🔌 Проверка подключения к Bybit..."
if python test_bybit_connection.py > /tmp/bybit_test.log 2>&1; then
    echo "✅ Подключение успешно!"
    grep "USDT баланс:" /tmp/bybit_test.log || true
else
    echo "❌ Ошибка подключения!"
    cat /tmp/bybit_test.log
    exit 1
fi

# Меню выбора
echo -e "\n📋 ВЫБЕРИТЕ ДЕЙСТВИЕ:"
echo "====================
echo "1) Запустить простой мониторинг цен"
echo "2) Запустить веб-интерфейс"
echo "3) Запустить оба"
echo "4) Выход"
echo ""
read -p "Ваш выбор (1-4): " choice

case $choice in
    1)
        echo -e "\n🤖 Запуск мониторинга цен..."
        echo "Для остановки нажмите Ctrl+C"
        echo ""
        python main_simple.py
        ;;
    2)
        echo -e "\n🌐 Запуск веб-интерфейса..."
        ./start_web.sh
        ;;
    3)
        echo -e "\n🚀 Запуск полной системы..."
        echo "Веб-интерфейс запускается в фоне..."
        nohup python app.py > logs/web.log 2>&1 &
        WEB_PID=$!
        echo "✅ Веб-интерфейс запущен (PID: $WEB_PID)"
        echo "📊 Доступ: http://systemetech.ru:8000"
        echo ""
        echo "Запуск мониторинга цен..."
        echo "Для остановки нажмите Ctrl+C"
        echo ""
        python main_simple.py
        echo ""
        echo "Остановка веб-интерфейса..."
        kill $WEB_PID 2>/dev/null || true
        ;;
    4)
        echo "👋 До свидания!"
        exit 0
        ;;
    *)
        echo "❌ Неверный выбор!"
        exit 1
        ;;
esac