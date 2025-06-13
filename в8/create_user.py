#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# create_user.py - Создание пользователя для веб-интерфейса

import sys
import os
from getpass import getpass
from src.core.database import SessionLocal
from src.core.models import User
from src.web.auth import auth_service

# Принудительная установка кодировки для терминала
if sys.platform.startswith('win'):
    # Для Windows
    os.system('chcp 65001 >nul')
    
# Функция безопасного ввода с обработкой кодировок
def safe_input(prompt):
    """Безопасный ввод текста с обработкой различных кодировок"""
    try:
        return input(prompt).strip()
    except UnicodeDecodeError:
        # Попробуем различные кодировки
        import codecs
        encodings = ['utf-8', 'cp1251', 'windows-1251', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                # Перенаправляем stdin с указанной кодировкой
                sys.stdin.reconfigure(encoding=encoding)
                return input(prompt).strip()
            except (UnicodeDecodeError, AttributeError):
                continue
        
        # Если ничего не помогло, используем ASCII с игнорированием ошибок
        print("⚠️  Обнаружены проблемы с кодировкой. Используем безопасный режим.")
        return input(prompt).encode('ascii', 'ignore').decode('ascii').strip()

def validate_username(username):
    """Валидация имени пользователя"""
    if not username:
        return False, "❌ Username не может быть пустым!"
    
    if len(username) < 3:
        return False, "❌ Username должен быть минимум 3 символа!"
    
    if len(username) > 50:
        return False, "❌ Username не может превышать 50 символов!"
    
    # Проверка на допустимые символы
    import re
    if not re.match(r'^[a-zA-Z0-9_.-]+$', username):
        return False, "❌ Username может содержать только буквы, цифры, '_', '.' и '-'"
    
    return True, "✅ Username валиден"

def validate_password(password):
    """Расширенная валидация пароля"""
    if len(password) < 8:
        return False, "❌ Пароль должен быть минимум 8 символов!"
    
    if len(password) > 128:
        return False, "❌ Пароль не может превышать 128 символов!"
    
    # Дополнительные проверки безопасности
    import re
    checks = []
    
    if not re.search(r"[a-z]", password):
        checks.append("строчную букву")
    if not re.search(r"[A-Z]", password):
        checks.append("заглавную букву") 
    if not re.search(r"\d", password):
        checks.append("цифру")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        checks.append("специальный символ")
    
    if checks:
        return False, f"❌ Пароль должен содержать: {', '.join(checks)}"
    
    return True, "✅ Пароль достаточно надежен"

def create_user():
    """Создание нового пользователя с улучшенной обработкой ошибок"""
    print("🔐 Создание пользователя для Crypto Trading Bot")
    print("=" * 50)
    
    # Безопасный ввод username
    while True:
        try:
            username = safe_input("👤 Username: ")
            is_valid, message = validate_username(username)
            
            if is_valid:
                break
            else:
                print(message)
                print("💡 Попробуйте снова...")
        except KeyboardInterrupt:
            print("\n👋 Отменено пользователем")
            sys.exit(0)
        except Exception as e:
            print(f"❌ Неожиданная ошибка при вводе username: {e}")
            print("💡 Попробуйте снова...")
    
    # Ввод и валидация пароля
    while True:
        try:
            password = getpass("🔒 Password: ")
            is_valid, message = validate_password(password)
            
            if is_valid:
                break
            else:
                print(message)
                print("💡 Попробуйте создать более надежный пароль...")
        except KeyboardInterrupt:
            print("\n👋 Отменено пользователем")
            sys.exit(0)
    
    # Подтверждение пароля
    while True:
        try:
            password_confirm = getpass("🔒 Confirm password: ")
            if password == password_confirm:
                break
            else:
                print("❌ Пароли не совпадают!")
                print("💡 Попробуйте снова...")
        except KeyboardInterrupt:
            print("\n👋 Отменено пользователем")  
            sys.exit(0)
    
    # Работа с базой данных
    db = None
    try:
        print("\n🔄 Подключение к базе данных...")
        db = SessionLocal()
        
        # Проверяем существование пользователя
        print("🔍 Проверка уникальности username...")
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            print(f"❌ Пользователь '{username}' уже существует!")
            print("💡 Попробуйте другое имя пользователя")
            sys.exit(1)
        
        # Создаем нового пользователя
        print("🔐 Хеширование пароля...")
        hashed_password = auth_service.get_password_hash(password)
        
        print("👤 Создание пользователя...")
        new_user = User(
            username=username,
            hashed_password=hashed_password,
            is_active=True
        )
        
        db.add(new_user)
        db.commit()
        
        print(f"\n✅ Пользователь '{username}' успешно создан!")
        print("\n🌐 Теперь вы можете войти в веб-интерфейс:")
        print("   http://systemetech.ru:8000")
        print("\n📊 Данные для входа:")
        print(f"   Username: {username}")
        print("   Password: [введенный вами пароль]")
        
    except Exception as e:
        print(f"\n❌ Ошибка при создании пользователя: {e}")
        print("🔧 Возможные причины:")
        print("   • Проблемы с подключением к базе данных")
        print("   • Недостаточные права доступа")
        print("   • Некорректная конфигурация")
        sys.exit(1)
        
    finally:
        if db:
            db.close()
            print("🔌 Соединение с базой данных закрыто")

if __name__ == "__main__":
    try:
        create_user()
    except KeyboardInterrupt:
        print("\n\n👋 Программа прервана пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
        print("🆘 Обратитесь к администратору или проверьте логи")
        sys.exit(1)