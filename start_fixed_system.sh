#!/bin/bash

echo "🚀 === ЗАПУСК ИСПРАВЛЕННОЙ СИСТЕМЫ ==="

# Переходим в рабочую директорию
cd /var/www/www-root/data/www/systemetech.ru

# Активируем виртуальное окружение
source venv/bin/activate

# Устанавливаем исправленные зависимости
echo "📦 Обновляем зависимости..."
pip install --upgrade passlib[bcrypt]
pip install --upgrade bcrypt

# Создаем новые файлы
echo "📝 Создаем новые файлы..."
# (здесь файлы уже созданы выше)

# Останавливаем все старые процессы
echo "🛑 Останавливаем старые процессы..."
pkill -f "python.*main.py" || true
pkill -f "python.*app.py" || true

# Очищаем старые PID файлы
rm -f bot.pid app.pid

# Запускаем веб-интерфейс
echo "🌐 Запускаем веб-интерфейс..."
nohup python app_fixed.py > logs/web.log 2>&1 &
echo $! > app.pid

echo "✅ Система запущена!"
echo "🌐 Веб-интерфейс: http://0.0.0.0:8000"
echo "📊 Проверь статус в дашборде"