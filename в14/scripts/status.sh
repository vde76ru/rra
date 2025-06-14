#!/bin/bash
if pgrep -f "python.*main.py" > /dev/null; then
    echo "✅ Бот запущен"
    ps aux | grep "python.*main.py" | grep -v grep
else
    echo "❌ Бот не запущен"
fi
