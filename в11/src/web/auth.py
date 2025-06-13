from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
import jwt
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.core.models import User
import os

# Настройки безопасности
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class AuthService:
    """Сервис аутентификации"""
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        return pwd_context.hash(password)
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    async def get_current_user(self, token: str = Depends(oauth2_scheme), 
                              db: Session = Depends(get_db)):
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
        except jwt.PyJWTError:
            raise credentials_exception
        
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            raise credentials_exception
        
        if user.is_blocked:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is blocked"
            )
        
        return user
    
    async def authenticate_user(self, db: Session, username: str, password: str):
        user = db.query(User).filter(User.username == username).first()
        
        if not user:
            return False
        
        # Проверяем блокировку
        if user.is_blocked:
            return False
        
        # Проверяем пароль
        if not self.verify_password(password, user.hashed_password):
            # Увеличиваем счетчик неудачных попыток
            user.failed_login_attempts += 1
            
            # Блокируем после 3 попыток
            if user.failed_login_attempts >= 3:
                user.is_blocked = True
                user.blocked_at = datetime.utcnow()
            
            db.commit()
            return False
        
        # Сбрасываем счетчик при успешном входе
        user.failed_login_attempts = 0
        user.last_login = datetime.utcnow()
        db.commit()
        
        return user

auth_service = AuthService()