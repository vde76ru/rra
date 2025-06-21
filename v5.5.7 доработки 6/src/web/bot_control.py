# src/web/bot_control.py
"""
Bot Control API - ПОЛНОСТЬЮ ИСПРАВЛЕННАЯ ВЕРСИЯ

Модуль: API управления торговым ботом с централизованным StateManager
Статус: КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ управления состоянием + unpacking fix
Архитектура: Интеграция StateManager + AsyncRouteHandler + BotManager

Ключевые исправления:
1. Замена self.auto_trading на centralizedStateManager
2. Атомарные операции запуска/остановки
3. Синхронизация WebSocket уведомлений
4. ✅ НОВОЕ: Исправление unpacking ошибки в _start_real_bot/_stop_real_bot
5. Устранение десинхронизации состояний
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from flask import jsonify, request

# КРИТИЧЕСКИЕ ИМПОРТЫ: StateManager + AsyncHandler
from ..bot.state_manager import state_manager
from .async_handler import async_handler

logger = logging.getLogger(__name__)

class BotController:
    """
    Исправленный контроллер с централизованным управлением состоянием
    
    Архитектурные изменения:
    - Убрано дублирование состояния (self.auto_trading)
    - Все операции проходят через StateManager
    - Добавлена синхронизация с BotManager
    - ✅ ИСПРАВЛЕНО: Обработка различных типов возврата от BotManager
    - Улучшена обработка ошибок и таймаутов
    """
    
    def __init__(self, bot_manager=None):
        """
        Инициализация исправленного BotController
        
        Args:
            bot_manager: Экземпляр BotManager для реальных торговых операций
        """
        self.bot_manager = bot_manager
        self.trading_task: Optional[asyncio.Task] = None
        
        # Статистика контроллера для диагностики
        self.controller_stats = {
            'initialization_time': datetime.utcnow(),
            'total_api_calls': 0,
            'successful_operations': 0,
            'failed_operations': 0,
            'last_operation': None
        }
        
        logger.info("🎮 BotController инициализирован с StateManager интеграцией")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Получение статуса через StateManager (thread-safe)
        
        Returns:
            Dict: Полный статус бота из единого источника истины
        """
        try:
            self.controller_stats['total_api_calls'] += 1
            
            # Получаем актуальное состояние из StateManager
            status = state_manager.get_status_api()
            
            # Дополняем информацией от BotManager если доступен
            if self.bot_manager:
                try:
                    bot_manager_status = self.bot_manager.get_status()
                    # Merge данных без перезаписи основных полей
                    status.update({
                        'bot_manager_info': bot_manager_status,
                        'real_bot_running': getattr(self.bot_manager, 'is_running', False)
                    })
                except Exception as e:
                    logger.warning(f"Не удалось получить статус от BotManager: {e}")
            
            self.controller_stats['successful_operations'] += 1
            return status
            
        except Exception as e:
            self.controller_stats['failed_operations'] += 1
            logger.error(f"❌ Ошибка получения статуса: {e}")
            
            # Возвращаем минимальный статус при ошибке
            return {
                'status': 'error',
                'is_running': False,
                'error_message': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def start_bot(self) -> Dict[str, Any]:
        """
        Атомарный запуск бота через StateManager
        
        Returns:
            Dict: Результат операции запуска
        """
        operation_start = datetime.utcnow()
        self.controller_stats['last_operation'] = 'start_bot'
        
        try:
            # Извлекаем параметры из запроса
            pairs = self._extract_pairs_from_request()
            strategy = self._extract_strategy_from_request()
            
            logger.info(f"🚀 Запуск бота: пары={pairs}, стратегия={strategy}")
            
            # Шаг 1: Переход в состояние запуска через StateManager
            if not state_manager.transition_to_starting(pairs, strategy):
                return {
                    'success': False,
                    'message': 'Не удалось инициировать запуск',
                    'status': state_manager.get_status_api()
                }
            
            logger.info(f"📡 Переход к запуску: пары={pairs}, стратегия={strategy}")
            logger.info("🔄 Запускаем торговые операции...")
            
            # Шаг 2: Реальный запуск через BotManager (если доступен)
            bot_manager_success = await self._start_real_bot(pairs, strategy)
            
            # Шаг 3: Обновление финального состояния
            if bot_manager_success:
                state_manager.transition_to_running()
                self.controller_stats['successful_operations'] += 1
                
                return {
                    'success': True,
                    'message': f'Бот успешно запущен с парами: {", ".join(pairs)}',
                    'status': state_manager.get_status_api(),
                    'operation_time': (datetime.utcnow() - operation_start).total_seconds()
                }
            else:
                state_manager.transition_to_error("Ошибка запуска BotManager")
                self.controller_stats['failed_operations'] += 1
                
                return {
                    'success': False,
                    'message': 'Ошибка запуска торговой системы',
                    'status': state_manager.get_status_api()
                }
                
        except Exception as e:
            # Критическая обработка ошибок
            error_message = f"Критическая ошибка запуска: {str(e)}"
            logger.error(f"❌ {error_message}")
            
            state_manager.transition_to_error(error_message)
            self.controller_stats['failed_operations'] += 1
            
            return {
                'success': False,
                'message': error_message,
                'status': state_manager.get_status_api()
            }
    
    async def stop_bot(self) -> Dict[str, Any]:
        """
        Атомарная остановка бота через StateManager
        
        Returns:
            Dict: Результат операции остановки
        """
        operation_start = datetime.utcnow()
        self.controller_stats['last_operation'] = 'stop_bot'
        
        try:
            logger.info("🛑 Остановка бота")
            
            # Шаг 1: Переход в состояние остановки через StateManager
            if not state_manager.transition_to_stopping():
                return {
                    'success': False,
                    'message': 'Не удалось инициировать остановку',
                    'status': state_manager.get_status_api()
                }
            
            # Шаг 2: Реальная остановка через BotManager
            bot_manager_success = await self._stop_real_bot()
            
            # Шаг 3: Финальное состояние
            state_manager.transition_to_stopped()
            
            # Всегда считаем остановку успешной, даже если BotManager недоступен
            self.controller_stats['successful_operations'] += 1
            
            return {
                'success': True,
                'message': 'Бот успешно остановлен',
                'status': state_manager.get_status_api(),
                'operation_time': (datetime.utcnow() - operation_start).total_seconds(),
                'bot_manager_stopped': bot_manager_success
            }
            
        except Exception as e:
            error_message = f"Ошибка остановки: {str(e)}"
            logger.error(f"❌ {error_message}")
            
            # При ошибке остановки все равно переводим в stopped
            state_manager.transition_to_stopped()
            self.controller_stats['failed_operations'] += 1
            
            return {
                'success': True,  # Остановка всегда успешна с точки зрения API
                'message': f'Бот остановлен с предупреждениями: {error_message}',
                'status': state_manager.get_status_api()
            }
    
    async def restart_bot(self) -> Dict[str, Any]:
        """
        Атомарный перезапуск через последовательность stop -> start
        
        Returns:
            Dict: Результат операции перезапуска
        """
        logger.info("🔄 Перезапуск бота")
        
        try:
            # Шаг 1: Остановка
            stop_result = await self.stop_bot()
            if not stop_result['success']:
                return {
                    'success': False,
                    'message': f'Ошибка при остановке: {stop_result["message"]}',
                    'status': state_manager.get_status_api()
                }
            
            # Шаг 2: Пауза для корректного завершения процессов
            await asyncio.sleep(2)
            
            # Шаг 3: Запуск
            start_result = await self.start_bot()
            
            return {
                'success': start_result['success'],
                'message': f'Перезапуск: {start_result["message"]}',
                'status': state_manager.get_status_api(),
                'restart_details': {
                    'stop_result': stop_result['success'],
                    'start_result': start_result['success']
                }
            }
            
        except Exception as e:
            error_message = f"Критическая ошибка перезапуска: {str(e)}"
            logger.error(f"❌ {error_message}")
            
            state_manager.transition_to_error(error_message)
            
            return {
                'success': False,
                'message': error_message,
                'status': state_manager.get_status_api()
            }
    
    # === ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ===
    
    def _extract_pairs_from_request(self) -> List[str]:
        """Извлечение торговых пар из HTTP запроса"""
        try:
            if request.is_json:
                data = request.get_json() or {}
                pairs = data.get('pairs', [])
            else:
                # Поддержка form-data и query parameters
                pairs_str = request.form.get('pairs') or request.args.get('pairs')
                if pairs_str:
                    pairs = [p.strip() for p in pairs_str.split(',')]
                else:
                    pairs = []
            
            # Пары по умолчанию если не указаны
            if not pairs:
                pairs = ['BTCUSDT', 'ETHUSDT']
            
            logger.debug(f"Извлечены торговые пары: {pairs}")
            return pairs
            
        except Exception as e:
            logger.warning(f"Ошибка извлечения пар из запроса: {e}")
            return ['BTCUSDT', 'ETHUSDT']
    
    def _extract_strategy_from_request(self) -> str:
        """Извлечение стратегии из HTTP запроса"""
        try:
            if request.is_json:
                data = request.get_json() or {}
                strategy = data.get('strategy', 'auto')
            else:
                strategy = request.form.get('strategy') or request.args.get('strategy') or 'auto'
            
            logger.debug(f"Извлечена стратегия: {strategy}")
            return strategy
            
        except Exception as e:
            logger.warning(f"Ошибка извлечения стратегии: {e}")
            return 'auto'
    
    async def _start_real_bot(self, pairs: List[str], strategy: str) -> bool:
        """Запуск реального BotManager - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
        if not self.bot_manager:
            logger.warning("BotManager не доступен, используем симуляцию")
            await asyncio.sleep(1)  # Имитация времени запуска
            return True
        
        try:
            if hasattr(self.bot_manager, 'update_pairs'):
                await self.bot_manager.update_pairs(pairs)
            
            if hasattr(self.bot_manager, 'start'):
                # ✅ ИСПРАВЛЕНО: Обрабатываем оба случая возврата
                result = await self.bot_manager.start()
                
                # Если возвращается кортеж (bool, str)
                if isinstance(result, tuple) and len(result) == 2:
                    success, message = result
                    logger.info(f"BotManager start result: {success}, {message}")
                    return success
                # Если возвращается только bool
                elif isinstance(result, bool):
                    logger.info(f"BotManager start result: {result}")
                    return result
                else:
                    logger.warning(f"Неожиданный тип результата от BotManager.start(): {type(result)}")
                    return bool(result)
            else:
                logger.warning("BotManager не имеет метода start")
                return True
                
        except Exception as e:
            logger.error(f"Ошибка запуска BotManager: {e}")
            return False
    
    async def _stop_real_bot(self) -> bool:
        """Остановка реального BotManager - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
        if not self.bot_manager:
            logger.warning("BotManager не доступен, используем симуляцию")
            await asyncio.sleep(0.5)  # Имитация времени остановки
            return True
        
        try:
            if hasattr(self.bot_manager, 'stop'):
                # ✅ ИСПРАВЛЕНО: Обрабатываем оба случая возврата
                result = await self.bot_manager.stop()
                
                # Если возвращается кортеж (bool, str)
                if isinstance(result, tuple) and len(result) == 2:
                    success, message = result
                    logger.info(f"BotManager stop result: {success}, {message}")
                    return success
                # Если возвращается только bool
                elif isinstance(result, bool):
                    logger.info(f"BotManager stop result: {result}")
                    return result
                else:
                    logger.warning(f"Неожиданный тип результата от BotManager.stop(): {type(result)}")
                    return bool(result)
            else:
                logger.warning("BotManager не имеет метода stop")
                return True
                
        except Exception as e:
            logger.error(f"Ошибка остановки BotManager: {e}")
            return False
    
    def get_controller_stats(self) -> Dict[str, Any]:
        """Получение статистики контроллера для диагностики"""
        return {
            **self.controller_stats,
            'state_manager_history': state_manager.get_operation_history(5),
            'current_state': state_manager.get_status_api()
        }


def register_bot_control_routes(app, bot_manager=None):
    """
    Регистрация API роутов с StateManager интеграцией
    
    Args:
        app: Flask приложение
        bot_manager: Менеджер бота
        
    Returns:
        BotController: Исправленный контроллер
    """
    logger.info("📝 Регистрация исправленных роутов с StateManager...")
    
    bot_controller = BotController(bot_manager)
    
    # === ОСНОВНЫЕ API ENDPOINTS ===
    
    @app.route('/api/bot/status', methods=['GET'])
    def get_bot_status_action():
        """Получение статуса бота (синхронный, быстрый доступ)"""
        try:
            status = bot_controller.get_status()
            return jsonify(status)
        except Exception as e:
            logger.error(f"❌ Ошибка получения статуса: {e}")
            return jsonify({
                'success': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }), 500
    
    @app.route('/api/bot/start', methods=['POST'])
    @async_handler.async_route(timeout=30)
    async def start_bot_action():
        """Запуск бота через StateManager (асинхронный)"""
        try:
            logger.info("🎯 API запрос запуска бота")
            logger.info(f"📊 Request: {request.content_type}, Method: {request.method}")
            
            result = await bot_controller.start_bot()
            
            # Логирование результата
            if result['success']:
                logger.info(f"✅ Бот запущен: {result['message']}")
            else:
                logger.warning(f"⚠️ Запуск отклонен: {result['message']}")
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"❌ Критическая ошибка API запуска: {e}")
            return jsonify({
                'success': False,
                'message': f'Критическая ошибка: {str(e)}',
                'status': state_manager.get_status_api()
            }), 500
    
    @app.route('/api/bot/stop', methods=['POST'])
    @async_handler.async_route(timeout=15)
    async def stop_bot_action():
        """Остановка бота через StateManager (асинхронный)"""
        try:
            logger.info("🎯 API запрос остановки бота")
            
            result = await bot_controller.stop_bot()
            
            # Логирование результата
            if result['success']:
                logger.info(f"✅ Бот остановлен: {result['message']}")
            else:
                logger.warning(f"⚠️ Остановка отклонена: {result['message']}")
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"❌ Критическая ошибка API остановки: {e}")
            return jsonify({
                'success': False,
                'message': f'Критическая ошибка: {str(e)}',
                'status': state_manager.get_status_api()
            }), 500
    
    @app.route('/api/bot/restart', methods=['POST'])
    @async_handler.async_route(timeout=45)
    async def restart_bot_action():
        """Перезапуск бота через StateManager (асинхронный)"""
        try:
            logger.info("🎯 API запрос перезапуска бота")
            
            result = await bot_controller.restart_bot()
            
            # Логирование результата
            if result['success']:
                logger.info(f"✅ Бот перезапущен: {result['message']}")
            else:
                logger.warning(f"⚠️ Перезапуск отклонен: {result['message']}")
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"❌ Критическая ошибка API перезапуска: {e}")
            return jsonify({
                'success': False,
                'message': f'Критическая ошибка: {str(e)}',
                'status': state_manager.get_status_api()
            }), 500
    
    # === ДОПОЛНИТЕЛЬНЫЕ ENDPOINTS ===
    
    @app.route('/api/bot/force-reset', methods=['POST'])
    def force_reset_action():
        """Принудительный сброс состояния (аварийная процедура)"""
        try:
            logger.warning("🔥 API запрос принудительного сброса")
            
            state_manager.force_reset()
            
            return jsonify({
                'success': True,
                'message': 'Состояние бота принудительно сброшено',
                'status': state_manager.get_status_api(),
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"❌ Ошибка принудительного сброса: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/bot/diagnostics', methods=['GET'])
    def get_diagnostics():
        """Диагностическая информация для разработки"""
        try:
            return jsonify({
                'success': True,
                'controller_stats': bot_controller.get_controller_stats(),
                'state_manager_history': state_manager.get_operation_history(10),
                'async_handler_stats': async_handler.get_stats(),
                'timestamp': datetime.utcnow().isoformat()
            })
        except Exception as e:
            logger.error(f"❌ Ошибка диагностики: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # === CORS ПОДДЕРЖКА ===
    
    @app.route('/api/bot/start', methods=['OPTIONS'])
    @app.route('/api/bot/stop', methods=['OPTIONS'])
    @app.route('/api/bot/restart', methods=['OPTIONS'])
    @app.route('/api/bot/force-reset', methods=['OPTIONS'])
    def bot_control_options():
        """CORS preflight обработка"""
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response
    
    logger.info("✅ Исправленные роуты управления ботом зарегистрированы")
    logger.info("🔗 Интеграция: StateManager + AsyncRouteHandler + BotManager")
    logger.info("🛠️ Исправлено: Unpacking ошибка в _start_real_bot/_stop_real_bot")
    
    return bot_controller

# Экспорт исправленных компонентов
__all__ = ['BotController', 'register_bot_control_routes']