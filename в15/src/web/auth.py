"""
Модуль аутентификации для веб-интерфейса
Путь: /var/www/www-root/data/www/systemetech.ru/src/web/auth.py
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from ..core.config import config
from ..core.database import get_db
from ..core.models import User

# Настройки безопасности
SECRET_KEY = config.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Контекст для хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 схема
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class AuthService:
    """Сервис аутентификации"""
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Проверка пароля"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Хеширование пароля"""
        return pwd_context.hash(password)
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        """Создание JWT токена"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        
        return encoded_jwt
    
    async def authenticate_user(self, db: Session, username: str, password: str) -> Optional[User]:
        """Аутентификация пользователя"""
        user = db.query(User).filter(User.username == username).first()
        
        if not user:
            return None
        
        if not user.is_active:
            return None
        
        if user.is_blocked:
            return None
        
        if not self.verify_password(password, user.hashed_password):
            user.failed_login_attempts += 1
            
            if user.failed_login_attempts >= 5:
                user.is_blocked = True
                user.blocked_at = datetime.utcnow()
            
            db.commit()
            return None
        
        user.failed_login_attempts = 0
        user.last_login = datetime.utcnow()
        db.commit()
        
        return user
    
    async def get_current_user(self, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
        """Получение текущего пользователя из токена"""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                raise credentials_exception
        except JWTError:
            raise credentials_exception
        
        user = db.query(User).filter(User.username == username).first()
        
        if user is None:
            raise credentials_exception
        
        if not user.is_active:
            raise HTTPException(status_code=400, detail="Inactive user")
        
        if user.is_blocked:
            raise HTTPException(status_code=400, detail="User is blocked")
        
        return user
    
    def create_user(self, db: Session, username: str, password: str, email: str = None, is_admin: bool = False) -> User:
        """Создание нового пользователя"""
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            raise ValueError(f"User {username} already exists")
        
        hashed_password = self.get_password_hash(password)
        
        user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            is_active=True,
            is_admin=is_admin
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user
    
    def unblock_user(self, db: Session, username: str) -> bool:
        """Разблокировка пользователя"""
        user = db.query(User).filter(User.username == username).first()
        
        if not user:
            return False
        
        user.is_blocked = False
        user.failed_login_attempts = 0
        user.blocked_at = None
        
        db.commit()
        return True

# Глобальный экземпляр сервиса
auth_service = AuthService()

# 🔧 ИСПРАВЛЕНИЕ: Функции-обёртки для импорта
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Функция-обёртка для создания JWT токена"""
    return auth_service.create_access_token(data, expires_delta)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Функция-обёртка для проверки пароля"""
    return auth_service.verify_password(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Функция-обёртка для хеширования пароля"""
    return auth_service.get_password_hash(password)

# Shortcut функции для FastAPI dependencies
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """Dependency для получения текущего пользователя"""
    import asyncio
    return asyncio.run(auth_service.get_current_user(token, db))

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Dependency для получения активного пользователя"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Dependency для получения администратора"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user