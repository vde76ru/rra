#!/bin/bash
# start_web.sh - Запуск веб-интерфейса

cd /var/www/www-root/data/www/systemetech.ru

# Активируем виртуальное окружение
source venv/bin/activate

# Проверяем порт
PORT=${WEB_PORT:-8000}

# Проверяем не занят ли порт
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null ; then
    echo "❌ Порт $PORT уже занят!"
    echo "Попробуйте остановить процесс:"
    echo "  sudo lsof -i :$PORT"
    echo "  sudo kill -9 <PID>"
    exit 1
fi

echo "🌐 Запуск веб-интерфейса на порту $PORT..."
echo "📊 Доступ: http://systemetech.ru:$PORT"
echo ""
echo "Для остановки нажмите Ctrl+C"
echo ""

# Запускаем веб-интерфейс
python app.py