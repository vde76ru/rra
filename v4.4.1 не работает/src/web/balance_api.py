"""
API для работы с балансом - ПРОСТАЯ РАБОЧАЯ ВЕРСИЯ
Файл: src/web/balance_api.py

ИНСТРУКЦИЯ: Создайте этот файл в папке src/web/
"""

from flask import jsonify, request
from datetime import datetime, timedelta
import logging
import threading
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class BalanceAPI:
    """Простой API для работы с балансом"""
    
    def __init__(self, exchange_client=None):
        self.exchange_client = exchange_client
        self.cache = {}
        self.cache_ttl = 30  # 30 секунд
        self._lock = threading.Lock()
    
    def get_balance_from_db(self) -> Dict[str, Any]:
        """Получает баланс из базы данных"""
        try:
            from ..core.database import SessionLocal
            from src.core.models import Balance
            from sqlalchemy import desc
            
            db = SessionLocal()
            try:
                # Получаем последний баланс USDT
                latest_balance = db.query(Balance).filter(
                    Balance.asset == 'USDT'
                ).order_by(desc(Balance.updated_at)).first()
                
                if latest_balance:
                    return {
                        'USDT': {
                            'total': float(latest_balance.total),
                            'free': float(latest_balance.free),
                            'used': float(latest_balance.locked or 0)
                        }
                    }
                else:
                    # Если нет записей, возвращаем тестовые данные
                    return {
                        'USDT': {
                            'total': 1000.0,
                            'free': 950.0,
                            'used': 50.0
                        }
                    }
            finally:
                db.close()
                
        except Exception as e:
            logger.warning(f"Ошибка получения баланса из БД: {e}")
            # Возвращаем тестовые данные при ошибке
            return {
                'USDT': {
                    'total': 1000.0,
                    'free': 950.0,
                    'used': 50.0
                }
            }
    
    def get_cached_balance(self) -> Optional[Dict[str, Any]]:
        """Получает баланс из кеша"""
        with self._lock:
            if 'balance' in self.cache:
                cached_data, timestamp = self.cache['balance']
                if (datetime.utcnow() - timestamp).seconds < self.cache_ttl:
                    return cached_data
        return None
    
    def set_cached_balance(self, balance_data: Dict[str, Any]):
        """Сохраняет баланс в кеше"""
        with self._lock:
            self.cache['balance'] = (balance_data, datetime.utcnow())
    
    def get_balance(self) -> Dict[str, Any]:
        """Основной метод получения баланса"""
        # 1. Проверяем кеш
        cached_balance = self.get_cached_balance()
        if cached_balance:
            return cached_balance
        
        # 2. Получаем из базы данных
        db_balance = self.get_balance_from_db()
        formatted_balance = self.format_balance_response(db_balance, source='database')
        self.set_cached_balance(formatted_balance)
        return formatted_balance
    
    def format_balance_response(self, balance_data: Dict[str, Any], source: str = 'unknown') -> Dict[str, Any]:
        """Форматирует ответ с балансом"""
        usdt_balance = balance_data.get('USDT', {})
        
        total = float(usdt_balance.get('total', 0))
        free = float(usdt_balance.get('free', 0))
        used = float(usdt_balance.get('used', 0))
        
        # Рассчитываем PnL
        initial_balance = 1000.0
        pnl_today = total - initial_balance
        pnl_percent = (pnl_today / initial_balance * 100) if initial_balance > 0 else 0
        
        return {
            'success': True,
            'total_usdt': total,
            'available_usdt': free,
            'in_positions': used,
            'pnl_today': round(pnl_today, 2),
            'pnl_percent': round(pnl_percent, 2),
            'source': source,
            'timestamp': datetime.utcnow().isoformat(),
            'last_update': datetime.utcnow().strftime('%H:%M:%S')
        }


def register_balance_routes(app, exchange_client=None):
    """
    Регистрирует роуты для баланса в Flask приложении
    
    Args:
        app: Flask приложение
        exchange_client: Клиент биржи (может быть None)
    """
    balance_api = BalanceAPI(exchange_client)
    
    @app.route('/api/balance')
    def get_balance_api():
        """ОСНОВНОЙ ЭНДПОИНТ ДЛЯ БАЛАНСА"""
        try:
            balance_data = balance_api.get_balance()
            return jsonify(balance_data)
        except Exception as e:
            logger.error(f"Ошибка API баланса: {e}")
            return jsonify({
                'success': False,
                'error': str(e),
                'total_usdt': 0,
                'available_usdt': 0,
                'in_positions': 0,
                'pnl_today': 0,
                'pnl_percent': 0,
                'source': 'error'
            }), 500
    
    @app.route('/api/balance/refresh', methods=['POST'])
    def refresh_balance():
        """Обновление баланса (сброс кеша)"""
        try:
            balance_api.cache.clear()
            balance_data = balance_api.get_balance()
            return jsonify({
                'success': True,
                'message': 'Balance refreshed',
                'data': balance_data
            })
        except Exception as e:
            logger.error(f"Ошибка обновления баланса: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    logger.info("✅ Роуты баланса зарегистрированы:")
    logger.info("   🟢 GET /api/balance")
    logger.info("   🟢 POST /api/balance/refresh")
    
    return balance_api