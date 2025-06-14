#!/usr/bin/env python3
"""
Скрипт для создания администратора
"""
import sys
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.append(str(Path(__file__).parent.parent))

from src.core.database import SessionLocal
from src.core.models import User
from src.web.auth import auth_service
import getpass

def create_admin():
    """Создание администратора"""
    print("🔐 СОЗДАНИЕ АДМИНИСТРАТОРА")
    print("=" * 50)
    
    username = input("👤 Введите логин: ")
    
    if not username:
        print("❌ Логин не может быть пустым")
        return
    
    # Проверяем что пользователь не существует
    db = SessionLocal()
    try:
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            print(f"❌ Пользователь {username} уже существует")
            return
        
        # Запрашиваем пароль
        password = getpass.getpass("🔑 Введите пароль: ")
        password_confirm = getpass.getpass("🔑 Подтвердите пароль: ")
        
        if password != password_confirm:
            print("❌ Пароли не совпадают")
            return
        
        if len(password) < 6:
            print("❌ Пароль должен быть не менее 6 символов")
            return
        
        # Создаем пользователя
        user = auth_service.create_user(
            db=db,
            username=username,
            password=password,
            email=f"{username}@crypto-bot.local",
            is_admin=True
        )
        
        print(f"✅ Администратор {username} создан успешно!")
        print(f"📧 Email: {user.email}")
        print(f"🛡️ Права: Администратор")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()