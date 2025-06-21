"""
API роуты для управления реальной торговлей - ИСПРАВЛЕННАЯ ВЕРСИЯ
Файл: src/web/trading_api.py

🎯 УПРАВЛЕНИЕ РЕАЛЬНОЙ ТОРГОВЛЕЙ:
✅ Запуск/остановка бота
✅ Экстренная остановка  
✅ Управление позициями
✅ Мониторинг торговых операций

ИСПРАВЛЕНИЯ:
✅ УДАЛЕНА дублированная функция get_trading_pairs
✅ Переименованы функции для уникальности
✅ Исправлены все конфликты имен
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from flask import jsonify, request
from functools import wraps

from ..core.config import config
from ..logging.smart_logger import get_logger

logger = get_logger(__name__)

def login_required(f):
    """Декоратор для проверки авторизации"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Упрощенная проверка авторизации для разработки
        auth_header = request.headers.get('Authorization', '')
        if not auth_header and not request.cookies.get('session'):
            return jsonify({
                'success': False,
                'error': 'Authorization required'
            }), 401
        return f(*args, **kwargs)
    return decorated_function

def register_trading_api_routes(app, bot_manager=None):
    """
    Регистрирует API роуты для управления торговлей
    
    Args:
        app: Flask приложение
        bot_manager: Менеджер торгового бота
    """
    
    logger.info("🔄 Регистрация API роутов торговли...")
    
    # =================================================================
    # УПРАВЛЕНИЕ БОТОМ
    # =================================================================
    
    @app.route('/api/bot/start', methods=['POST'])
    @login_required
    def start_bot():
        """Запуск торгового бота"""
        try:
            if not bot_manager:
                return jsonify({
                    'success': False,
                    'error': 'Bot manager not available'
                }), 503
            
            success = bot_manager.start()
            
            if success:
                return jsonify({
                    'success': True,
                    'message': 'Bot started successfully',
                    'timestamp': datetime.utcnow().isoformat()
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to start bot'
                }), 500
                
        except Exception as e:
            logger.error(f"❌ Ошибка запуска бота: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/bot/stop', methods=['POST'])
    @login_required
    def stop_bot():
        """Остановка торгового бота"""
        try:
            if not bot_manager:
                return jsonify({
                    'success': False,
                    'error': 'Bot manager not available'
                }), 503
            
            success = bot_manager.stop()
            
            if success:
                return jsonify({
                    'success': True,
                    'message': 'Bot stopped successfully',
                    'timestamp': datetime.utcnow().isoformat()
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to stop bot'
                }), 500
                
        except Exception as e:
            logger.error(f"❌ Ошибка остановки бота: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/bot/restart', methods=['POST'])
    @login_required 
    def restart_bot():
        """Перезапуск торгового бота"""
        try:
            if not bot_manager:
                return jsonify({
                    'success': False,
                    'error': 'Bot manager not available'
                }), 503
            
            # Останавливаем
            stop_success = bot_manager.stop()
            if not stop_success:
                return jsonify({
                    'success': False,
                    'error': 'Failed to stop bot for restart'
                }), 500
            
            # Запускаем
            start_success = bot_manager.start()
            if not start_success:
                return jsonify({
                    'success': False,
                    'error': 'Failed to start bot after stop'
                }), 500
            
            return jsonify({
                'success': True,
                'message': 'Bot restarted successfully',
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"❌ Ошибка перезапуска бота: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/bot/emergency-stop', methods=['POST'])
    @login_required
    def emergency_stop_bot():
        """Экстренная остановка бота"""
        try:
            if not bot_manager:
                return jsonify({
                    'success': False,
                    'error': 'Bot manager not available'
                }), 503
            
            success = bot_manager.emergency_stop()
            
            return jsonify({
                'success': success,
                'message': 'Emergency stop executed' if success else 'Emergency stop failed',
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"❌ Ошибка экстренной остановки: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # =================================================================
    # УПРАВЛЕНИЕ ПОЗИЦИЯМИ
    # =================================================================
    
    @app.route('/api/bot/positions')
    @login_required
    def get_bot_positions():
        """Получение открытых позиций бота"""
        try:
            if not bot_manager:
                return jsonify({
                    'success': False,
                    'error': 'Bot manager not available'
                }), 503
            
            if hasattr(bot_manager, 'get_open_positions'):
                positions = bot_manager.get_open_positions()
            elif hasattr(bot_manager, 'positions'):
                positions = list(bot_manager.positions.values())
            else:
                positions = []
            
            return jsonify({
                'success': True,
                'positions': positions,
                'count': len(positions),
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения позиций: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/bot/close-position/<symbol>', methods=['POST'])
    @login_required
    def close_bot_position(symbol):
        """Закрытие конкретной позиции"""
        try:
            if not bot_manager:
                return jsonify({
                    'success': False,
                    'error': 'Bot manager not available'
                }), 503
            
            success = bot_manager.close_position(symbol)
            
            return jsonify({
                'success': success,
                'message': f'Position {symbol} closed' if success else f'Failed to close {symbol}',
                'symbol': symbol,
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"❌ Ошибка закрытия позиции {symbol}: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/bot/close-all-positions', methods=['POST'])
    @login_required
    def close_all_bot_positions():
        """Закрытие всех открытых позиций"""
        try:
            if not bot_manager:
                return jsonify({
                    'success': False,
                    'error': 'Bot manager not available'
                }), 503
            
            result = bot_manager.close_all_positions()
            
            return jsonify({
                'success': result.get('success', False),
                'closed_count': result.get('closed_count', 0),
                'failed_count': result.get('failed_count', 0),
                'message': result.get('message', 'Completed'),
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"❌ Ошибка закрытия всех позиций: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # =================================================================
    # УПРАВЛЕНИЕ ТОРГОВЫМИ ПАРАМИ (ПЕРЕИМЕНОВАНО)
    # =================================================================
    
    @app.route('/api/bot/active-pairs', methods=['GET'])
    @login_required
    def get_bot_active_pairs():
        """
        ПЕРЕИМЕНОВАННАЯ ФУНКЦИЯ: Получение активных торговых пар бота
        (была get_trading_pairs - конфликтовала с charts_routes.py)
        """
        try:
            if not bot_manager:
                return jsonify({
                    'success': False,
                    'error': 'Bot manager not available'
                }), 503
            
            status = bot_manager.get_status()
            active_pairs = status.get('active_pairs', [])
            all_pairs = status.get('available_pairs', [])
            
            # Если нет доступных пар, используем активные
            if not all_pairs:
                all_pairs = active_pairs
            
            return jsonify({
                'success': True,
                'active_pairs': active_pairs,
                'available_pairs': all_pairs,
                'count': len(active_pairs),
                'total_available': len(all_pairs),
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения торговых пар бота: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/bot/active-pairs', methods=['POST'])
    @login_required
    def update_bot_active_pairs():
        """
        ПЕРЕИМЕНОВАННАЯ ФУНКЦИЯ: Обновление активных торговых пар бота
        (была update_trading_pairs - конфликтовала)
        """
        try:
            if not bot_manager:
                return jsonify({
                    'success': False,
                    'error': 'Bot manager not available'
                }), 503
            
            data = request.get_json() or {}
            pairs = data.get('pairs', [])
            
            if not pairs:
                return jsonify({
                    'success': False,
                    'error': 'No pairs specified'
                }), 400
            
            # Валидация пар
            invalid_pairs = [pair for pair in pairs if not isinstance(pair, str) or len(pair) < 6]
            if invalid_pairs:
                return jsonify({
                    'success': False,
                    'error': f'Invalid pairs format: {invalid_pairs}'
                }), 400
            
            success = bot_manager.update_trading_pairs(pairs)
            
            return jsonify({
                'success': success,
                'active_pairs': pairs,
                'count': len(pairs),
                'message': 'Trading pairs updated' if success else 'Failed to update pairs',
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"❌ Ошибка обновления торговых пар бота: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # =================================================================
    # СТРАТЕГИИ И НАСТРОЙКИ
    # =================================================================
    
    @app.route('/api/bot/strategies')
    @login_required
    def get_bot_strategies():
        """Получение доступных стратегий"""
        try:
            if not bot_manager:
                return jsonify({
                    'success': False,
                    'error': 'Bot manager not available'
                }), 503
            
            strategies = bot_manager.get_available_strategies()
            current_strategy = bot_manager.get_current_strategy()
            
            return jsonify({
                'success': True,
                'strategies': strategies,
                'current_strategy': current_strategy,
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения стратегий: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/bot/strategy', methods=['POST'])
    @login_required
    def set_bot_strategy():
        """Установка стратегии бота"""
        try:
            if not bot_manager:
                return jsonify({
                    'success': False,
                    'error': 'Bot manager not available'
                }), 503
            
            data = request.get_json() or {}
            strategy = data.get('strategy')
            
            if not strategy:
                return jsonify({
                    'success': False,
                    'error': 'Strategy not specified'
                }), 400
            
            success = bot_manager.set_strategy(strategy)
            
            return jsonify({
                'success': success,
                'strategy': strategy,
                'message': 'Strategy updated' if success else 'Failed to update strategy',
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"❌ Ошибка установки стратегии: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # =================================================================
    # МОНИТОРИНГ И ДИАГНОСТИКА
    # =================================================================
    
    @app.route('/api/bot/health')
    @login_required
    def get_bot_health():
        """Проверка здоровья бота"""
        try:
            if not bot_manager:
                return jsonify({
                    'success': False,
                    'error': 'Bot manager not available',
                    'status': 'unavailable'
                }), 503
            
            health = bot_manager.get_health_status()
            
            return jsonify({
                'success': True,
                'health': health,
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки здоровья: {e}")
            return jsonify({
                'success': False,
                'error': str(e),
                'status': 'error'
            }), 500
    
    @app.route('/api/bot/metrics')
    @login_required
    def get_bot_metrics():
        """Получение метрик производительности бота"""
        try:
            if not bot_manager:
                return jsonify({
                    'success': False,
                    'error': 'Bot manager not available'
                }), 503
            
            metrics = bot_manager.get_performance_metrics()
            
            return jsonify({
                'success': True,
                'metrics': metrics,
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения метрик: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # =================================================================
    # CORS ПОДДЕРЖКА
    # =================================================================
    
    @app.route('/api/bot/start', methods=['OPTIONS'])
    @app.route('/api/bot/stop', methods=['OPTIONS'])
    @app.route('/api/bot/restart', methods=['OPTIONS'])
    @app.route('/api/bot/emergency-stop', methods=['OPTIONS'])
    @app.route('/api/bot/close-all-positions', methods=['OPTIONS'])
    def trading_api_options():
        """CORS preflight обработка"""
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response
    
    # =================================================================
    # ЛОГИРОВАНИЕ РЕЗУЛЬТАТОВ
    # =================================================================
    
    logger.info("✅ API роуты торговли зарегистрированы:")
    logger.info("   🟢 POST /api/bot/start - запуск бота")
    logger.info("   🟢 POST /api/bot/stop - остановка бота")
    logger.info("   🟢 POST /api/bot/restart - перезапуск бота")
    logger.info("   🟢 POST /api/bot/emergency-stop - экстренная остановка")
    logger.info("   🟢 GET /api/bot/positions - открытые позиции")
    logger.info("   🟢 POST /api/bot/close-position/<symbol> - закрытие позиции")
    logger.info("   🟢 POST /api/bot/close-all-positions - закрытие всех позиций")
    logger.info("   🟢 GET/POST /api/bot/active-pairs - управление торговыми парами")
    logger.info("   🟢 GET /api/bot/strategies - доступные стратегии")
    logger.info("   🟢 POST /api/bot/strategy - установка стратегии")
    logger.info("   🟢 GET /api/bot/health - здоровье бота")
    logger.info("   🟢 GET /api/bot/metrics - метрики производительности")
    
    return True

# Экспорт
__all__ = ['register_trading_api_routes']