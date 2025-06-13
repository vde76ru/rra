"""Веб-интерфейс"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import router as api_router
from .websocket import websocket_endpoint

def create_app() -> FastAPI:
    """Создание FastAPI приложения"""
    app = FastAPI(
        title="Crypto Trading Bot",
        version="3.0",
        description="Professional Crypto Trading Bot"
    )
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Роуты
    app.include_router(api_router, prefix="/api")
    app.websocket("/ws")(websocket_endpoint)
    
    return app

app = create_app()
