"""
Система аутентификации для веб-интерфейса
"""
import jwt
import logging
from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from ..core.config import config
from ..core.models import User
from ..core.database import get_db

logger = logging.getLogger(__name__)

# ✅ ИСПРАВЛЕНИЕ: Добавляем недостающие схемы OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")
security = HTTPBearer()

# Настройка хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    """Сервис аутентификации"""
    
    def __init__(self):
        self.secret_key = config.SECRET_KEY
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Проверка пароля"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Хеширование пароля"""
        return pwd_context.hash(password)
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Создание JWT токена"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    async def authenticate_user(self, db: Session, username: str, password: str) -> Optional[User]:
        """Аутентификация пользователя"""
        try:
            user = db.query(User).filter(User.username == username).first()
            if not user:
                return None
            
            if not self.verify_password(password, user.hashed_password):
                return None
            
            # Обновляем время последнего входа
            user.last_login = datetime.utcnow()
            db.commit()
            
            return user
        except Exception as e:
            logger.error(f"Ошибка аутентификации: {e}")
            return None
    
    def get_current_user_from_token(self, token: str, db: Session) -> User:
        """Получение пользователя из JWT токена"""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            username: str = payload.get("sub")
            if username is None:
                raise credentials_exception
        except jwt.PyJWTError:
            raise credentials_exception
        
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            raise credentials_exception
        
        return user

# Глобальный экземпляр сервиса
auth_service = AuthService()

# ✅ ИСПРАВЛЕНИЕ: Правильные функции-обёртки без дублирования
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Функция-обёртка для создания JWT токена"""
    return auth_service.create_access_token(data, expires_delta)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Функция-обёртка для проверки пароля"""
    return auth_service.verify_password(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Функция-обёртка для хеширования пароля"""
    return auth_service.get_password_hash(password)

# ✅ ИСПРАВЛЕНИЕ: Dependency для OAuth2PasswordBearer
def get_current_user_oauth2(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """Dependency для получения текущего пользователя через OAuth2PasswordBearer"""
    return auth_service.get_current_user_from_token(token, db)

# ✅ ИСПРАВЛЕНИЕ: Dependency для HTTPBearer (используется в app.py)
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Dependency для получения текущего пользователя через HTTPBearer"""
    return auth_service.get_current_user_from_token(credentials.credentials, db)

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