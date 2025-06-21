"""
API роуты для управления реальной торговлей
Файл: src/web/trading_api.py

🎯 УПРАВЛЕНИЕ РЕАЛЬНОЙ ТОРГОВЛЕЙ:
✅ Запуск/остановка бота
✅ Экстренная остановка
✅ Управление позициями
✅ Мониторинг торговых операций
✅ Интеграция с TradingController
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from flask import jsonify, request
from functools import wraps

from ..core.config import config
from ..logging.smart_logger import get_logger
from ..web.async_handler import async_handler

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
    @async_handler()
    async def start_trading_bot():
        """Запуск торгового бота"""
        try:
            if not bot_manager:
                return jsonify({
                    'success': False,
                    'error': 'Bot manager not available'
                }), 503
            
            # Получаем параметры запуска
            data = request.get_json() or {}
            pairs = data.get('pairs', [])
            auto_strategy = data.get('auto_strategy', True)
            
            logger.info(
                "🚀 Запуск торгового бота",
                category='bot',
                pairs_count=len(pairs),
                auto_strategy=auto_strategy
            )
            
            # Проверяем текущий статус
            current_status = bot_manager.get_status()
            if current_status.get('is_running', False):
                return jsonify({
                    'success': False,
                    'error': 'Bot is already running'
                })
            
            # Устанавливаем торговые пары если указаны
            if pairs:
                await bot_manager.update_trading_pairs(pairs)
            
            # Запускаем бота
            success, message = await bot_manager.start()
            
            if success:
                logger.info(
                    "✅ Торговый бот запущен успешно",
                    category='bot',
                    message=message
                )
                
                return jsonify({
                    'success': True,
                    'message': message,
                    'status': 'starting',
                    'timestamp': datetime.utcnow().isoformat()
                })
            else:
                logger.error(
                    "❌ Ошибка запуска торгового бота",
                    category='bot',
                    error=message
                )
                
                return jsonify({
                    'success': False,
                    'error': message
                }), 500
                
        except Exception as e:
            logger.error(f"❌ Критическая ошибка запуска бота: {e}")
            return jsonify({
                'success': False,
                'error': f'Internal error: {str(e)}'
            }), 500
    
    @app.route('/api/bot/stop', methods=['POST'])
    @login_required
    def stop_trading_bot():
        """Остановка торгового бота"""
        try:
            if not bot_manager:
                return jsonify({
                    'success': False,
                    'error': 'Bot manager not available'
                }), 503
            
            logger.info("🛑 Остановка торгового бота", category='bot')
            
            # Проверяем текущий статус
            current_status = bot_manager.get_status()
            if not current_status.get('is_running', False):
                return jsonify({
                    'success': False,
                    'error': 'Bot is not running'
                })
            
            # Останавливаем бота
            success, message = await bot_manager.stop()
            
            if success:
                logger.info(
                    "✅ Торговый бот остановлен",
                    category='bot',
                    message=message
                )
                
                return jsonify({
                    'success': True,
                    'message': message,
                    'status': 'stopped',
                    'timestamp': datetime.utcnow().isoformat()
                })
            else:
                logger.error(
                    "❌ Ошибка остановки бота",
                    category='bot',
                    error=message
                )
                
                return jsonify({
                    'success': False,
                    'error': message
                }), 500
                
        except Exception as e:
            logger.error(f"❌ Критическая ошибка остановки бота: {e}")
            return jsonify({
                'success': False,
                'error': f'Internal error: {str(e)}'
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
            
            logger.critical("🚨 ЭКСТРЕННАЯ ОСТАНОВКА БОТА!", category='bot')
            
            # Экстренная остановка
            success, message = await bot_manager.emergency_stop()
            
            if success:
                logger.critical(
                    "🚨 Экстренная остановка выполнена",
                    category='bot',
                    message=message
                )
                
                return jsonify({
                    'success': True,
                    'message': message,
                    'status': 'emergency_stop',
                    'timestamp': datetime.utcnow().isoformat()
                })
            else:
                logger.error(
                    "❌ Ошибка экстренной остановки",
                    category='bot',
                    error=message
                )
                
                return jsonify({
                    'success': False,
                    'error': message
                }), 500
                
        except Exception as e:
            logger.critical(f"❌ Критическая ошибка экстренной остановки: {e}")
            return jsonify({
                'success': False,
                'error': f'Internal error: {str(e)}'
            }), 500
    
    # =================================================================
    # УПРАВЛЕНИЕ ПОЗИЦИЯМИ
    # =================================================================
    
    @app.route('/api/bot/positions')
    @login_required
    def get_open_positions():
        """Получение открытых позиций"""
        try:
            if not bot_manager:
                return jsonify({
                    'success': False,
                    'error': 'Bot manager not available'
                }), 503
            
            # Получаем статус бота с позициями
            status = bot_manager.get_status()
            positions = status.get('positions', [])
            
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
    def close_position(symbol):
        """Закрытие конкретной позиции"""
        try:
            if not bot_manager:
                return jsonify({
                    'success': False,
                    'error': 'Bot manager not available'
                }), 503
            
            logger.info(f"📊 Закрытие позиции {symbol}", category='trading')
            
            # Закрываем позицию
            result = await bot_manager.close_position(symbol)
            
            if result['success']:
                logger.info(
                    f"✅ Позиция {symbol} закрыта",
                    category='trading',
                    profit=result.get('profit', 0)
                )
                
                return jsonify({
                    'success': True,
                    'message': f'Position {symbol} closed successfully',
                    'result': result,
                    'timestamp': datetime.utcnow().isoformat()
                })
            else:
                return jsonify({
                    'success': False,
                    'error': result.get('error', 'Unknown error')
                }), 500
                
        except Exception as e:
            logger.error(f"❌ Ошибка закрытия позиции {symbol}: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/bot/close-all-positions', methods=['POST'])
    @login_required
    def close_all_positions():
        """Закрытие всех открытых позиций"""
        try:
            if not bot_manager:
                return jsonify({
                    'success': False,
                    'error': 'Bot manager not available'
                }), 503
            
            logger.warning("📊 Закрытие ВСЕХ позиций", category='trading')
            
            # Закрываем все позиции
            results = await bot_manager.close_all_positions()
            
            closed_count = sum(1 for r in results if r.get('success', False))
            failed_count = len(results) - closed_count
            
            logger.info(
                f"📊 Результат закрытия позиций: {closed_count} успешно, {failed_count} ошибок",
                category='trading'
            )
            
            return jsonify({
                'success': True,
                'message': f'Closed {closed_count} positions, {failed_count} failed',
                'results': results,
                'closed_count': closed_count,
                'failed_count': failed_count,
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"❌ Ошибка закрытия всех позиций: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # =================================================================
    # НАСТРОЙКИ ТОРГОВЛИ
    # =================================================================
    
    @app.route('/api/bot/pairs', methods=['GET'])
    @login_required
    @async_handler()
    async def get_trading_pairs():
        """Получение активных торговых пар"""
        try:
            if not bot_manager:
                return jsonify({
                    'success': False,
                    'error': 'Bot manager not available'
                }), 503
            
            status = bot_manager.get_status()
            active_pairs = status.get('active_pairs', [])
            all_pairs = status.get('available_pairs', [])
            
            return jsonify({
                'success': True,
                'active_pairs': active_pairs,
                'available_pairs': all_pairs,
                'count': len(active_pairs),
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения торговых пар: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/bot/pairs', methods=['POST'])
    @login_required
    @async_handler()
    async def update_trading_pairs():
        """Обновление активных торговых пар"""
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
            
            logger.info(
                f"🔄 Обновление торговых пар: {pairs}",
                category='config',
                pairs_count=len(pairs)
            )
            
            # Обновляем пары
            success = await bot_manager.update_trading_pairs(pairs)
            
            if success:
                logger.info("✅ Торговые пары обновлены", category='config')
                
                return jsonify({
                    'success': True,
                    'message': f'Updated {len(pairs)} trading pairs',
                    'pairs': pairs,
                    'timestamp': datetime.utcnow().isoformat()
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to update trading pairs'
                }), 500
                
        except Exception as e:
            logger.error(f"❌ Ошибка обновления торговых пар: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # =================================================================
    # СТРАТЕГИИ
    # =================================================================
    
    @app.route('/api/bot/strategies')
    @login_required
    def get_available_strategies():
        """Получение доступных стратегий"""
        try:
            if not bot_manager:
                strategies = ['momentum', 'multi_indicator', 'scalping']  # Fallback
            else:
                status = bot_manager.get_status()
                strategies = status.get('available_strategies', [])
            
            return jsonify({
                'success': True,
                'strategies': strategies,
                'count': len(strategies),
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
    def set_strategy():
        """Установка активной стратегии"""
        try:
            if not bot_manager:
                return jsonify({
                    'success': False,
                    'error': 'Bot manager not available'
                }), 503
            
            data = request.get_json() or {}
            strategy = data.get('strategy')
            symbol = data.get('symbol', 'default')
            
            if not strategy:
                return jsonify({
                    'success': False,
                    'error': 'No strategy specified'
                }), 400
            
            logger.info(
                f"🎯 Установка стратегии {strategy} для {symbol}",
                category='strategy'
            )
            
            # Устанавливаем стратегию
            success = await bot_manager.set_strategy(symbol, strategy)
            
            if success:
                logger.info(f"✅ Стратегия {strategy} установлена", category='strategy')
                
                return jsonify({
                    'success': True,
                    'message': f'Strategy {strategy} set for {symbol}',
                    'strategy': strategy,
                    'symbol': symbol,
                    'timestamp': datetime.utcnow().isoformat()
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to set strategy'
                }), 500
                
        except Exception as e:
            logger.error(f"❌ Ошибка установки стратегии: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # =================================================================
    # МОНИТОРИНГ
    # =================================================================
    
    @app.route('/api/bot/health')
    @login_required
    def get_bot_health():
        """Проверка здоровья торгового бота"""
        try:
            if not bot_manager:
                return jsonify({
                    'success': False,
                    'healthy': False,
                    'error': 'Bot manager not available'
                })
            
            # Получаем детальный статус здоровья
            health = await bot_manager.health_check()
            
            return jsonify({
                'success': True,
                'healthy': health.get('overall_healthy', False),
                'components': health.get('components', {}),
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки здоровья бота: {e}")
            return jsonify({
                'success': False,
                'healthy': False,
                'error': str(e)
            })
    
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
            
            # Получаем метрики
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
    # ЛОГИРОВАНИЕ
    # =================================================================
    
    logger.info("✅ API роуты торговли зарегистрированы:")
    logger.info("   🟢 POST /api/bot/start - запуск бота")
    logger.info("   🟢 POST /api/bot/stop - остановка бота")
    logger.info("   🟢 POST /api/bot/emergency-stop - экстренная остановка")
    logger.info("   🟢 GET /api/bot/positions - открытые позиции")
    logger.info("   🟢 POST /api/bot/close-position/<symbol> - закрытие позиции")
    logger.info("   🟢 POST /api/bot/close-all-positions - закрытие всех позиций")
    logger.info("   🟢 GET/POST /api/bot/pairs - управление торговыми парами")
    logger.info("   🟢 GET /api/bot/strategies - доступные стратегии")
    logger.info("   🟢 POST /api/bot/strategy - установка стратегии")
    logger.info("   🟢 GET /api/bot/health - здоровье бота")
    logger.info("   🟢 GET /api/bot/metrics - метрики производительности")
    
    return True

# Экспорт
__all__ = ['register_trading_api_routes']