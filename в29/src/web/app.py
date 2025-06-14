"""
Веб-интерфейс для Crypto Trading Bot - ИСПРАВЛЕННАЯ ВЕРСИЯ
"""
from fastapi import FastAPI, Depends, HTTPException, WebSocket, status
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List, Dict, Any
import logging

# Импорты компонентов системы
from ..core.database import get_db, SessionLocal
from ..core.models import User, Trade, Signal, TradingPair

# Условные импорты
try:
    from ..bot.manager import bot_manager
    BOT_MANAGER_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Не удалось импортировать bot_manager: {e}")
    BOT_MANAGER_AVAILABLE = False
    bot_manager = None

try:
    from .auth import get_current_user, create_access_token, auth_service
    AUTH_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Не удалось импортировать модуль аутентификации: {e}")
    AUTH_AVAILABLE = False

try:
    from .websocket import websocket_endpoint
    WEBSOCKET_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Не удалось импортировать WebSocket: {e}")
    WEBSOCKET_AVAILABLE = False

try:
    from .dashboard import get_dashboard_html
    DASHBOARD_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Не удалось импортировать дашборд: {e}")
    DASHBOARD_AVAILABLE = False

logger = logging.getLogger(__name__)
from typing import List, Dict, Any
import logging

# Импорты компонентов системы
from ..core.database import get_db, SessionLocal
from ..core.models import User, Trade, Signal, TradingPair

# Условный импорт bot_manager
try:
    from ..bot.manager import bot_manager
    BOT_MANAGER_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Не удалось импортировать bot_manager: {e}")
    BOT_MANAGER_AVAILABLE = False
    bot_manager = None

# Импорты для аутентификации
try:
    from .auth import get_current_user, create_access_token, auth_service
    AUTH_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Не удалось импортировать модуль аутентификации: {e}")
    AUTH_AVAILABLE = False

# Импорты для WebSocket
try:
    from .websocket import websocket_endpoint
    WEBSOCKET_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Не удалось импортировать WebSocket: {e}")
    WEBSOCKET_AVAILABLE = False

# Импорт дашборда
try:
    from .dashboard import get_dashboard_html
    DASHBOARD_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Не удалось импортировать дашборд: {e}")
    DASHBOARD_AVAILABLE = False

logger = logging.getLogger(__name__)

# Создаем приложение
app = FastAPI(
    title="Crypto Trading Bot",
    version="3.0",
    description="Professional Crypto Trading Bot with Web Interface"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==============================================================================
# МОДЕЛИ ДЛЯ API
# ==============================================================================

class LoginRequest(BaseModel):
    username: str
    password: str

class BotActionRequest(BaseModel):
    action: str  # start, stop

class PairsUpdateRequest(BaseModel):
    pairs: List[str]

# ==============================================================================
# ОСНОВНЫЕ ENDPOINTS
# ==============================================================================

@app.get("/", response_class=HTMLResponse)
async def root():
    """Главная страница с дашбордом"""
    if DASHBOARD_AVAILABLE:
        return get_dashboard_html()
    else:
        return """
        <html>
            <head><title>Crypto Trading Bot</title></head>
            <body>
                <h1>🤖 Crypto Trading Bot</h1>
                <p>❌ Дашборд временно недоступен</p>
                <p>Используйте API endpoints:</p>
                <ul>
                    <li><a href="/docs">API Documentation</a></li>
                    <li><a href="/api/status">Bot Status</a></li>
                </ul>
            </body>
        </html>
        """

@app.get("/health")
async def health_check():
    """Проверка здоровья системы"""
    return {
        "status": "healthy",
        "components": {
            "bot_manager": BOT_MANAGER_AVAILABLE,
            "auth": AUTH_AVAILABLE,
            "websocket": WEBSOCKET_AVAILABLE,
            "dashboard": DASHBOARD_AVAILABLE
        }
    }

# ==============================================================================
# AUTHENTICATION ENDPOINTS
# ==============================================================================

if AUTH_AVAILABLE:
    @app.post("/auth/token")
    async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
        """OAuth2 совместимый endpoint для получения токена"""
        db = SessionLocal()
        try:
            user = await auth_service.authenticate_user(db, form_data.username, form_data.password)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect username or password",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            access_token = create_access_token(data={"sub": user.username})
            return {"access_token": access_token, "token_type": "bearer"}
        finally:
            db.close()

    @app.post("/api/login")
    async def login_json(request: LoginRequest):
        """JSON endpoint для веб-интерфейса"""
        db = SessionLocal()
        try:
            user = await auth_service.authenticate_user(db, request.username, request.password)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Неверные учетные данные"
                )
            
            access_token = create_access_token(data={"sub": user.username})
            return {
                "access_token": access_token, 
                "token_type": "bearer",
                "user": {
                    "username": user.username,
                    "is_admin": user.is_admin
                }
            }
        finally:
            db.close()

    @app.get("/api/user/me")
    async def get_current_user_info(current_user: User = Depends(get_current_user)):
        """Получить информацию о текущем пользователе"""
        return {
            "username": current_user.username,
            "email": current_user.email,
            "is_admin": current_user.is_admin,
            "is_active": current_user.is_active,
            "created_at": current_user.created_at,
            "last_login": current_user.last_login
        }
else:
    @app.post("/auth/token")
    async def login_disabled():
        return {"error": "Authentication is disabled"}

# ==============================================================================
# BOT MANAGEMENT ENDPOINTS
# ==============================================================================

if BOT_MANAGER_AVAILABLE:
    @app.get("/api/bot/status")
    async def get_bot_status():
        """Получить статус бота"""
        return bot_manager.get_status()

    @app.post("/api/bot/action")
    async def bot_action(request: BotActionRequest):
        """Управление ботом (если auth недоступен, разрешаем всем)"""
        if request.action == "start":
            success, message = await bot_manager.start()
            if not success:
                raise HTTPException(status_code=400, detail=message)
            return {"status": "started", "message": message}
        
        elif request.action == "stop":
            success, message = await bot_manager.stop()
            return {"status": "stopped", "message": message}
        
        else:
            raise HTTPException(status_code=400, detail="Invalid action")
else:
    @app.get("/api/bot/status")
    async def get_bot_status_disabled():
        return {"error": "Bot manager is not available", "status": "unavailable"}

# ==============================================================================
# DATA ENDPOINTS
# ==============================================================================

@app.get("/api/balance")
async def get_balance():
    """Получить баланс"""
    if BOT_MANAGER_AVAILABLE:
        try:
            balance = await bot_manager.exchange.fetch_balance()
            return {
                "USDT": balance.get("USDT", {}).get("free", 0),
                "total": balance.get("USDT", {}).get("total", 0)
            }
        except Exception as e:
            logger.error(f"Ошибка получения баланса: {e}")
            return {"USDT": 0, "total": 0}
    else:
        return {"error": "Bot manager not available"}

@app.get("/api/trades")
async def get_trades(limit: int = 50, db = Depends(get_db)):
    """Получить историю сделок"""
    trades = db.query(Trade).order_by(Trade.created_at.desc()).limit(limit).all()
    return trades

@app.get("/api/pairs")
async def get_pairs(db = Depends(get_db)):
    """Получить список торговых пар"""
    pairs = db.query(TradingPair).all()
    return pairs

@app.get("/api/dashboard")
async def get_dashboard_data(db = Depends(get_db)):
    """Получить все данные для дашборда"""
    try:
        # Статус бота
        if BOT_MANAGER_AVAILABLE:
            bot_status = bot_manager.get_status()
            # Баланс
            try:
                balance = await bot_manager.exchange.fetch_balance()
                balance_data = {
                    "USDT": balance.get("USDT", {}).get("free", 0),
                    "total": balance.get("USDT", {}).get("total", 0)
                }
            except:
                balance_data = {"USDT": 0, "total": 0}
        else:
            bot_status = {"status": "unavailable", "is_running": False}
            balance_data = {"USDT": 0, "total": 0}
        
        # Статистика из БД
        from datetime import datetime, timedelta
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        recent_trades = db.query(Trade).order_by(Trade.created_at.desc()).limit(10).all()
        recent_signals = db.query(Signal).order_by(Signal.created_at.desc()).limit(10).all()
        
        # Считаем статистику за день
        today_trades = db.query(Trade).filter(Trade.created_at >= today_start).all()
        total_profit = sum(t.profit or 0 for t in today_trades)
        profitable_trades = len([t for t in today_trades if t.profit and t.profit > 0])
        win_rate = (profitable_trades / len(today_trades) * 100) if today_trades else 0
        
        return {
            "bot_status": bot_status,
            "balance": balance_data,
            "statistics": {
                "total_trades": len(today_trades),
                "profitable_trades": profitable_trades,
                "total_profit": total_profit,
                "win_rate": win_rate
            },
            "recent_trades": [
                {
                    "id": t.id,
                    "symbol": t.symbol,
                    "side": t.side.value if hasattr(t.side, 'value') else str(t.side),
                    "entry_price": float(t.entry_price) if t.entry_price else 0,
                    "exit_price": float(t.exit_price) if t.exit_price else None,
                    "profit": float(t.profit) if t.profit else None,
                    "status": t.status.value if hasattr(t.status, 'value') else str(t.status),
                    "created_at": t.created_at.isoformat()
                } for t in recent_trades
            ],
            "recent_signals": [
                {
                    "id": s.id,
                    "symbol": s.symbol,
                    "action": s.action,
                    "confidence": float(s.confidence) if s.confidence else 0,
                    "reason": s.reason,
                    "created_at": s.created_at.isoformat()
                } for s in recent_signals
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Ошибка получения данных дашборда: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения данных")

# ==============================================================================
# WEBSOCKET
# ==============================================================================

if WEBSOCKET_AVAILABLE:
    @app.websocket("/ws")
    async def websocket_endpoint_route(websocket: WebSocket):
        """WebSocket endpoint"""
        await websocket_endpoint(websocket)
        
    @app.websocket("/ws/{client_id}")
    async def websocket_endpoint_with_id(websocket: WebSocket, client_id: str):
        """WebSocket endpoint с client_id"""
        await websocket_endpoint(websocket)

# ==============================================================================
# ERROR HANDLERS
# ==============================================================================

@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {"error": "Endpoint not found", "detail": str(exc)}

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error(f"Internal server error: {exc}")
    return {"error": "Internal server error", "detail": "Check logs for details"}

# ==============================================================================
# STARTUP EVENT
# ==============================================================================

@app.on_event("startup")
async def startup_event():
    """Событие запуска приложения"""
    logger.info("🚀 Веб-приложение запущено")
    logger.info(f"📊 Компоненты: Manager={BOT_MANAGER_AVAILABLE}, Auth={AUTH_AVAILABLE}, WS={WEBSOCKET_AVAILABLE}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)