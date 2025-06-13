"""
FastAPI веб-приложение
Путь: /var/www/www-root/data/www/systemetech.ru/src/web/app.py
"""
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from .auth import router as auth_router
from .api import router as api_router
from .websocket import WebSocketManager
from .dashboard import get_dashboard_html

def create_app() -> FastAPI:
    """Создание и настройка FastAPI приложения"""
    
    app = FastAPI(
        title="Crypto Trading Bot",
        description="Professional Cryptocurrency Trading Bot",
        version="3.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc"
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # В продакшене указать конкретные домены
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Подключаем роутеры
    app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
    app.include_router(api_router, prefix="/api", tags=["API"])
    
    # Статические файлы
    app.mount("/static", StaticFiles(directory="static"), name="static")
    
    # WebSocket менеджер
    ws_manager = WebSocketManager()
    
    @app.get("/", response_class=HTMLResponse)
    async def root():
        """Главная страница - редирект на дашборд"""
        return get_dashboard_html()
    
    @app.websocket("/ws/{client_id}")
    async def websocket_endpoint(websocket: WebSocket, client_id: str):
        """WebSocket endpoint для real-time обновлений"""
        await ws_manager.connect(websocket, client_id)
        try:
            while True:
                data = await websocket.receive_text()
                # Обработка входящих сообщений если нужно
        except WebSocketDisconnect:
            ws_manager.disconnect(client_id)
    
    @app.on_event("startup")
    async def startup_event():
        """События при запуске приложения"""
        # Здесь можно инициализировать подключения, запустить фоновые задачи и т.д.
        pass
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """События при остановке приложения"""
        # Закрытие подключений, остановка фоновых задач
        pass
    
    return app

# Создаем экземпляр приложения
app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "src.web.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )