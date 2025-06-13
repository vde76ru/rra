#!/bin/bash
# stop_all.sh - Остановка всех процессов бота

echo "🛑 Остановка всех процессов Crypto Trading Bot"
echo "============================================="

# Поиск и остановка Python процессов
echo -e "\n🔍 Поиск запущенных процессов..."

# Ищем процессы app.py
APP_PIDS=$(pgrep -f "python.*app.py")
if [ ! -z "$APP_PIDS" ]; then
    echo "📌 Найден веб-интерфейс (PID: $APP_PIDS)"
    kill $APP_PIDS
    echo "✅ Веб-интерфейс остановлен"
else
    echo "⚠️  Веб-интерфейс не запущен"
fi

# Ищем процессы main_simple.py
MAIN_PIDS=$(pgrep -f "python.*main_simple.py")
if [ ! -z "$MAIN_PIDS" ]; then
    echo "📌 Найден мониторинг цен (PID: $MAIN_PIDS)"
    kill $MAIN_PIDS
    echo "✅ Мониторинг цен остановлен"
else
    echo "⚠️  Мониторинг цен не запущен"
fi

# Ищем процессы main.py
BOT_PIDS=$(pgrep -f "python.*main.py" | grep -v main_simple)
if [ ! -z "$BOT_PIDS" ]; then
    echo "📌 Найден основной бот (PID: $BOT_PIDS)"
    kill $BOT_PIDS
    echo "✅ Основной бот остановлен"
else
    echo "⚠️  Основной бот не запущен"
fi

# Проверка портов
echo -e "\n🔍 Проверка портов..."
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Порт 8000 все еще занят"
    PORT_PID=$(lsof -Pi :8000 -sTCP:LISTEN -t)
    echo "📌 Процесс на порту 8000 (PID: $PORT_PID)"
    kill -9 $PORT_PID 2>/dev/null
    echo "✅ Порт 8000 освобожден"
else
    echo "✅ Порт 8000 свободен"
fi

echo -e "\n✅ Все процессы остановлены!"