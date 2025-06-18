#!/usr/bin/env python3
"""
Тестовый скрипт для диагностики проблем с веб-интерфейсом
Файл: test_web.py
"""
import sys
import os

# Подавляем предупреждения
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import warnings
warnings.filterwarnings('ignore')

print("🔍 Тестирование веб-модуля...")

# 1. Проверка импорта Flask
try:
    from flask import Flask
    print("✅ Flask импортирован успешно")
except ImportError as e:
    print(f"❌ Ошибка импорта Flask: {e}")
    sys.exit(1)

# 2. Проверка импорта SocketIO
try:
    from flask_socketio import SocketIO
    print("✅ Flask-SocketIO импортирован успешно")
except ImportError as e:
    print(f"❌ Ошибка импорта Flask-SocketIO: {e}")
    sys.exit(1)

# 3. Проверка импорта веб-модуля
try:
    from src.web.app import app, socketio
    print("✅ Веб-модуль импортирован успешно")
    print(f"   App: {app}")
    print(f"   SocketIO: {socketio}")
except Exception as e:
    print(f"❌ Ошибка импорта веб-модуля: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 4. Проверка создания приложения
try:
    if app is None:
        print("❌ Приложение не создано (app is None)")
    else:
        print("✅ Flask приложение создано")
        
    if socketio is None:
        print("❌ SocketIO не создан (socketio is None)")
    else:
        print("✅ SocketIO создан")
except Exception as e:
    print(f"❌ Ошибка проверки приложения: {e}")

# 5. Попытка тестового запуска
print("\n🚀 Попытка тестового запуска...")
try:
    # Создаем минимальное приложение
    test_app = Flask(__name__)
    test_socketio = SocketIO(test_app)
    
    @test_app.route('/')
    def test_route():
        return "Test OK"
    
    print("✅ Тестовое приложение создано успешно")
    print("   Для запуска используйте: python main.py web")
    
except Exception as e:
    print(f"❌ Ошибка создания тестового приложения: {e}")

print("\n📊 Итог: Проверьте вывод выше для диагностики проблемы")