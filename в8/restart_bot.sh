#!/bin/bash
# restart_bot.sh - Перезапуск бота с правильными настройками

cd /var/www/www-root/data/www/systemetech.ru

echo "🔄 ПЕРЕЗАПУСК CRYPTO TRADING BOT"
echo "================================"

# 1. Останавливаем все процессы
echo -e "\n🛑 Останавливаем текущие процессы..."
./stop_all.sh

# Ждем пару секунд
sleep 2

# 2. Проверяем логи
echo -e "\n📋 Создаем резервную копию логов..."
if [ -f "logs/trading.log" ]; then
    cp logs/trading.log "logs/trading_$(date +%Y%m%d_%H%M%S).log"
    echo "" > logs/trading.log  # Очищаем основной лог
fi

# 3. Активируем виртуальное окружение
echo -e "\n🐍 Активация виртуального окружения..."
source venv/bin/activate

# 4. Проверяем API ключи
echo -e "\n🔑 Проверка API ключей..."
source /etc/crypto/config/.env

if [ -z "$BYBIT_API_KEY" ] || [ "$BYBIT_API_KEY" = "" ] || [ "$BYBIT_API_KEY" = "your_testnet_api_key_here" ]; then
    echo "❌ API ключи не настроены!"
    exit 1
fi
echo "✅ API ключи найдены"

# 5. Запускаем веб-интерфейс в фоне
echo -e "\n🌐 Запуск веб-интерфейса..."
nohup python app.py > logs/web.log 2>&1 &
WEB_PID=$!
echo "✅ Веб-интерфейс запущен (PID: $WEB_PID)"

# Ждем запуска веб-сервера
sleep 3

# Проверяем что веб-интерфейс работает
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
    echo "✅ Веб-интерфейс доступен на http://systemetech.ru:8000"
else
    echo "❌ Веб-интерфейс не запустился!"
    exit 1
fi

# 6. Показываем инструкции
echo -e "\n📊 СЛЕДУЮЩИЕ ШАГИ:"
echo "=================="
echo "1. Откройте веб-интерфейс: http://systemetech.ru:8000"
echo "2. Войдите в систему"
echo "3. Нажмите кнопку 'Start Bot' для запуска торговли"
echo ""
echo "🔍 Для мониторинга активности:"
echo "   python monitor_bot.py"
echo ""
echo "📋 Для просмотра логов:"
echo "   tail -f logs/trading.log"
echo ""
echo "🔍 Для проверки статуса:"
echo "   python check_bot_status.py"
echo ""
echo "✅ Перезапуск завершен!"