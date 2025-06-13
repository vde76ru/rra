"""
✅ ПОЛНОСТЬЮ ИСПРАВЛЕННЫЙ unified_bot_manager.py
🎯 Решает проблемы: рассинхронизация, ошибки API, некорректное управление процессами
"""
import asyncio
import os
import subprocess
import psutil
import signal
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging
from pathlib import Path

from .database import SessionLocal
from .models import Trade, Signal, BotState, TradingPair, TradeStatus
from .bot_manager import BotManager

logger = logging.getLogger(__name__)

class UnifiedBotManager:
    """
    🎯 Единый менеджер для управления торговым ботом
    
    ИСПРАВЛЕНИЯ в этой версии:
    ✅ Надежная проверка процессов без ошибок NoneType
    ✅ Корректная синхронизация состояний
    ✅ Обработка всех исключений с детальным логированием
    ✅ Восстановление после сбоев
    """
    
    def __init__(self):
        # Пути к файлам бота
        self.bot_script_path = "/var/www/www-root/data/www/systemetech.ru/main.py"
        self.venv_python = "/var/www/www-root/data/www/systemetech.ru/venv/bin/python"
        self.working_dir = "/var/www/www-root/data/www/systemetech.ru"
        
        # Внутренний менеджер для прямого доступа
        self._internal_manager = BotManager()
        
        logger.info("🔧 Единый менеджер бота инициализирован")
    
    def get_comprehensive_status(self) -> Dict[str, Any]:
        """
        📊 ИСПРАВЛЕННАЯ функция получения полного статуса
        
        Теперь включает:
        ✅ Безопасную проверку процессов
        ✅ Обработку всех исключений
        ✅ Детальное логирование проблем
        """
        try:
            logger.debug("🔍 Начинаем проверку статуса бота...")
            
            # 1. Безопасная проверка процесса
            process_info = self._safe_check_bot_process()
            logger.debug(f"📊 Статус процесса: {process_info}")
            
            # 2. Проверка внутреннего менеджера
            manager_status = self._safe_get_manager_status()
            logger.debug(f"📊 Статус менеджера: {manager_status}")
            
            # 3. Проверка состояния в БД
            db_status = self._safe_get_db_status()
            logger.debug(f"📊 Статус БД: {db_status}")
            
            # 4. Анализ синхронизации
            is_synchronized = self._analyze_synchronization(process_info, manager_status, db_status)
            
            result = {
                # Информация о процессе
                'process_running': process_info.get('running', False),
                'process_pid': process_info.get('pid'),
                'process_memory': process_info.get('memory', 0),
                'process_cpu': process_info.get('cpu', 0),
                'process_error': process_info.get('error'),
                
                # Информация о менеджере
                'manager_running': manager_status.get('is_running', False),
                'active_pairs': manager_status.get('active_pairs', []),
                'open_positions': manager_status.get('open_positions', 0),
                'manager_error': manager_status.get('error'),
                
                # Информация из БД
                'db_state': db_status.get('is_running') if db_status else None,
                'db_start_time': db_status.get('start_time') if db_status else None,
                'total_trades': db_status.get('total_trades', 0) if db_status else 0,
                'total_profit': db_status.get('total_profit', 0) if db_status else 0,
                'db_error': db_status.get('error') if db_status else None,
                
                # Общие показатели
                'synchronized': is_synchronized,
                'last_check': datetime.utcnow().isoformat(),
                'status_summary': self._get_status_summary(process_info, manager_status, db_status)
            }
            
            logger.debug(f"✅ Статус собран успешно: синхронизация={is_synchronized}")
            return result
            
        except Exception as e:
            error_msg = f"Критическая ошибка получения статуса: {str(e)}"
            logger.error(f"💥 {error_msg}", exc_info=True)
            
            # Возвращаем безопасную структуру при критической ошибке
            return {
                'process_running': False,
                'manager_running': False,
                'active_pairs': [],
                'open_positions': 0,
                'synchronized': False,
                'error': error_msg,
                'last_check': datetime.utcnow().isoformat(),
                'status_summary': 'КРИТИЧЕСКАЯ ОШИБКА'
            }
    
    def _safe_check_bot_process(self) -> Dict[str, Any]:
        """
        🔍 ИСПРАВЛЕННАЯ безопасная проверка процесса бота
        
        Изменения:
        ✅ Полная обработка исключений
        ✅ Защита от NoneType ошибок
        ✅ Детальное логирование для отладки
        ✅ Fallback на альтернативные методы проверки
        """
        try:
            logger.debug("🔍 Ищем процесс бота...")
            
            # Пробуем несколько способов найти процесс
            found_processes = []
            
            # Способ 1: Поиск по командной строке
            try:
                for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info', 'cpu_percent']):
                    try:
                        proc_info = proc.info
                        cmdline = proc_info.get('cmdline')
                        
                        # ✅ КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ: Проверяем что cmdline существует и это список
                        if not cmdline or not isinstance(cmdline, (list, tuple)):
                            continue
                        
                        # Безопасно проверяем элементы командной строки
                        cmdline_str = ' '.join(str(cmd) for cmd in cmdline if cmd)
                        
                        # Ищем наш процесс по ключевым словам
                        has_python = any('python' in str(cmd).lower() for cmd in cmdline if cmd)
                        has_main = any('main.py' in str(cmd) for cmd in cmdline if cmd)
                        
                        if has_python and has_main:
                            # Найден подходящий процесс!
                            memory_info = proc_info.get('memory_info', {})
                            memory_mb = (memory_info.get('rss', 0) / 1024 / 1024) if memory_info else 0
                            
                            process_data = {
                                'running': True,
                                'pid': proc_info.get('pid'),
                                'memory': round(memory_mb, 1),
                                'cpu': proc_info.get('cpu_percent', 0),
                                'cmdline': cmdline_str,
                                'name': proc_info.get('name', 'unknown')
                            }
                            
                            found_processes.append(process_data)
                            logger.debug(f"🎯 Найден процесс: PID={process_data['pid']}, команда={cmdline_str}")
                            
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        # Эти исключения нормальны - процесс мог завершиться
                        continue
                    except Exception as proc_error:
                        # Логируем неожиданные ошибки, но продолжаем поиск
                        logger.debug(f"⚠️ Ошибка обработки процесса: {proc_error}")
                        continue
                        
            except Exception as search_error:
                logger.warning(f"⚠️ Ошибка поиска процессов через psutil: {search_error}")
            
            # Способ 2: Поиск через PID файл (если есть)
            pid_file_path = os.path.join(self.working_dir, 'bot.pid')
            if not found_processes and os.path.exists(pid_file_path):
                try:
                    with open(pid_file_path, 'r') as f:
                        saved_pid = int(f.read().strip())
                    
                    if psutil.pid_exists(saved_pid):
                        proc = psutil.Process(saved_pid)
                        logger.debug(f"🎯 Найден процесс через PID файл: {saved_pid}")
                        found_processes.append({
                            'running': True,
                            'pid': saved_pid,
                            'memory': proc.memory_info().rss / 1024 / 1024,
                            'cpu': proc.cpu_percent(),
                            'source': 'pid_file'
                        })
                except Exception as pid_error:
                    logger.debug(f"⚠️ Ошибка проверки PID файла: {pid_error}")
            
            # Анализируем результаты
            if found_processes:
                # Если найдено несколько процессов, берем первый (самый свежий)
                main_process = found_processes[0]
                logger.info(f"✅ Процесс бота найден: PID={main_process['pid']}")
                return main_process
            else:
                logger.info("ℹ️ Процесс бота не найден")
                return {'running': False, 'reason': 'Процесс не найден'}
                
        except Exception as e:
            error_msg = f"Критическая ошибка проверки процесса: {str(e)}"
            logger.error(f"💥 {error_msg}", exc_info=True)
            return {
                'running': False, 
                'error': error_msg,
                'reason': 'Ошибка проверки'
            }
    
    def _safe_get_manager_status(self) -> Dict[str, Any]:
        """
        📊 Безопасное получение статуса внутреннего менеджера
        """
        try:
            if self._internal_manager:
                status = self._internal_manager.get_status()
                logger.debug(f"📊 Статус внутреннего менеджера получен: {status}")
                return status
            else:
                return {
                    'is_running': False,
                    'active_pairs': [],
                    'open_positions': 0,
                    'error': 'Внутренний менеджер не инициализирован'
                }
        except Exception as e:
            error_msg = f"Ошибка получения статуса менеджера: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return {
                'is_running': False,
                'active_pairs': [],
                'open_positions': 0,
                'error': error_msg
            }
    
    def _safe_get_db_status(self) -> Optional[Dict[str, Any]]:
        """
        💾 Безопасное получение статуса из базы данных
        """
        db = None
        try:
            db = SessionLocal()
            state = db.query(BotState).first()
            
            if state:
                result = {
                    'is_running': state.is_running,
                    'start_time': state.start_time,
                    'stop_time': getattr(state, 'stop_time', None),
                    'total_trades': getattr(state, 'total_trades', 0) or 0,
                    'total_profit': getattr(state, 'total_profit', 0) or 0,
                    'current_balance': getattr(state, 'current_balance', 0) or 0
                }
                logger.debug(f"💾 Статус из БД получен: запущен={result['is_running']}")
                return result
            else:
                logger.warning("⚠️ Состояние бота в БД не найдено")
                return None
                
        except Exception as e:
            error_msg = f"Ошибка получения статуса из БД: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return {'error': error_msg}
        finally:
            if db:
                try:
                    db.close()
                except:
                    pass
    
    def _analyze_synchronization(self, process_info: Dict, manager_status: Dict, db_status: Optional[Dict]) -> bool:
        """
        🔄 УЛУЧШЕННЫЙ анализ синхронизации состояний
        
        Теперь включает:
        ✅ Детальное логирование причин рассинхронизации
        ✅ Анализ каждого компонента отдельно
        ✅ Рекомендации по исправлению
        """
        try:
            # Получаем состояния из всех источников
            process_running = process_info.get('running', False)
            manager_running = manager_status.get('is_running', False)
            db_running = db_status.get('is_running', False) if db_status and 'error' not in db_status else False
            
            # Проверяем синхронизацию
            all_states = [process_running, manager_running, db_running]
            unique_states = set(all_states)
            is_synchronized = len(unique_states) == 1
            
            if not is_synchronized:
                # Детальное логирование проблемы
                logger.warning(
                    f"⚠️ РАССИНХРОНИЗАЦИЯ ОБНАРУЖЕНА:\n"
                    f"   🔹 Процесс: {process_running} ({'запущен' if process_running else 'остановлен'})\n"
                    f"   🔹 Менеджер: {manager_running} ({'активен' if manager_running else 'неактивен'})\n"
                    f"   🔹 База данных: {db_running} ({'запущен' if db_running else 'остановлен'})\n"
                    f"   💡 Рекомендация: выполните синхронизацию состояния"
                )
                
                # Определяем тип рассинхронизации для более точной диагностики
                if db_running and not process_running and not manager_running:
                    logger.info("🔍 Тип проблемы: процесс завершился, но БД не обновилась")
                elif process_running and not manager_running:
                    logger.info("🔍 Тип проблемы: процесс работает, но менеджер неактивен")
                elif manager_running and not process_running:
                    logger.info("🔍 Тип проблемы: менеджер активен, но процесса нет")
            else:
                logger.debug(f"✅ Все компоненты синхронизированы: {'запущен' if process_running else 'остановлен'}")
            
            return is_synchronized
            
        except Exception as e:
            logger.error(f"❌ Ошибка анализа синхронизации: {e}")
            return False
    
    def _get_status_summary(self, process_info: Dict, manager_status: Dict, db_status: Optional[Dict]) -> str:
        """
        📝 Получение краткого описания состояния системы
        """
        try:
            process_running = process_info.get('running', False)
            manager_running = manager_status.get('is_running', False)
            db_running = db_status.get('is_running', False) if db_status and 'error' not in db_status else False
            
            if process_running and manager_running and db_running:
                return "🟢 ВСЕ СИСТЕМЫ РАБОТАЮТ"
            elif not process_running and not manager_running and not db_running:
                return "🔴 ВСЕ СИСТЕМЫ ОСТАНОВЛЕНЫ"
            elif db_running and not process_running:
                return "🟡 ТРЕБУЕТСЯ СИНХРОНИЗАЦИЯ (БД думает что запущен)"
            elif process_running and not manager_running:
                return "🟡 ПРОБЛЕМА С МЕНЕДЖЕРОМ"
            else:
                return "🟡 ЧАСТИЧНАЯ РАССИНХРОНИЗАЦИЯ"
                
        except Exception:
            return "❓ НЕИЗВЕСТНОЕ СОСТОЯНИЕ"
    
    async def start_bot(self) -> Dict[str, Any]:
        """
        🚀 ИСПРАВЛЕННАЯ функция запуска бота
        
        Новые возможности:
        ✅ Проверка всех состояний перед запуском
        ✅ Очистка старых состояний при необходимости
        ✅ Детальное логирование процесса запуска
        ✅ Восстановление после сбоев
        """
        try:
            logger.info("🚀 === НАЧИНАЕМ ЗАПУСК ТОРГОВОГО БОТА ===")
            
            # 1. Проверяем текущее состояние
            current_status = self.get_comprehensive_status()
            logger.info(f"📊 Текущее состояние: {current_status['status_summary']}")
            
            # 2. Если процесс уже запущен - возвращаем информацию
            if current_status['process_running']:
                logger.info(f"ℹ️ Процесс уже запущен с PID: {current_status['process_pid']}")
                return {
                    'success': False,
                    'message': f'Бот уже запущен (PID: {current_status["process_pid"]})',
                    'pid': current_status['process_pid'],
                    'already_running': True
                }
            
            # 3. Если есть рассинхронизация - сначала синхронизируем
            if not current_status['synchronized']:
                logger.info("🔄 Обнаружена рассинхронизация, выполняем синхронизацию...")
                sync_result = self.sync_state()
                if not sync_result['success']:
                    logger.error(f"❌ Не удалось синхронизировать состояние: {sync_result.get('error')}")
                else:
                    logger.info("✅ Состояние синхронизировано")
            
            # 4. Проверяем файлы системы
            validation_result = self._validate_system()
            if not validation_result['valid']:
                return {
                    'success': False,
                    'message': f'Системная ошибка: {validation_result["error"]}'
                }
            
            # 5. Запускаем новый процесс
            logger.info("🔧 Запускаем новый процесс бота...")
            process_result = await self._launch_bot_process()
            
            if process_result['success']:
                # 6. Обновляем состояние в БД
                logger.info("💾 Обновляем состояние в базе данных...")
                await self._update_db_state(True)
                
                # 7. Финальная проверка
                await asyncio.sleep(2)
                final_status = self.get_comprehensive_status()
                
                logger.info(f"🎉 БОТ УСПЕШНО ЗАПУЩЕН! PID: {process_result['pid']}")
                return {
                    'success': True,
                    'message': 'Бот успешно запущен и работает',
                    'pid': process_result['pid'],
                    'status': final_status['status_summary']
                }
            else:
                logger.error(f"❌ Ошибка запуска процесса: {process_result['error']}")
                return {
                    'success': False,
                    'message': f'Ошибка запуска: {process_result["error"]}',
                    'details': process_result.get('details', {})
                }
                
        except Exception as e:
            error_msg = f"Критическая ошибка запуска: {str(e)}"
            logger.error(f"💥 {error_msg}", exc_info=True)
            return {
                'success': False,
                'message': error_msg
            }
    
    def _validate_system(self) -> Dict[str, Any]:
        """
        ✅ Проверка системных требований для запуска
        """
        try:
            # Проверяем Python
            if not os.path.exists(self.venv_python):
                return {
                    'valid': False,
                    'error': f'Python виртуального окружения не найден: {self.venv_python}'
                }
            
            # Проверяем скрипт бота
            if not os.path.exists(self.bot_script_path):
                return {
                    'valid': False,
                    'error': f'Скрипт бота не найден: {self.bot_script_path}'
                }
            
            # Проверяем рабочую директорию
            if not os.path.exists(self.working_dir):
                return {
                    'valid': False,
                    'error': f'Рабочая директория не найдена: {self.working_dir}'
                }
            
            # Проверяем права доступа
            if not os.access(self.venv_python, os.X_OK):
                return {
                    'valid': False,
                    'error': f'Нет прав на выполнение: {self.venv_python}'
                }
            
            return {'valid': True}
            
        except Exception as e:
            return {
                'valid': False,
                'error': f'Ошибка проверки системы: {str(e)}'
            }
    
    async def _launch_bot_process(self) -> Dict[str, Any]:
        """
        🔧 Запуск процесса бота
        """
        try:
            # Формируем команду запуска
            cmd = [self.venv_python, "main.py"]
            logger.info(f"🔧 Команда запуска: {' '.join(cmd)}")
            
            # Запускаем процесс
            process = subprocess.Popen(
                cmd,
                cwd=self.working_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                start_new_session=True,  # Независимая сессия
                env=os.environ.copy()  # Наследуем переменные окружения
            )
            
            logger.info(f"⏳ Процесс запущен с PID: {process.pid}")
            
            # Ждем инициализации
            initialization_time = 5  # секунд
            for i in range(initialization_time):
                await asyncio.sleep(1)
                
                # Проверяем что процесс еще работает
                if process.poll() is not None:
                    # Процесс завершился - получаем вывод
                    try:
                        stdout, stderr = process.communicate(timeout=5)
                        stdout_text = stdout.decode('utf-8', errors='ignore') if stdout else ''
                        stderr_text = stderr.decode('utf-8', errors='ignore') if stderr else ''
                    except subprocess.TimeoutExpired:
                        stdout_text = "Таймаут получения вывода"
                        stderr_text = "Таймаут получения ошибок"
                    
                    error_message = stderr_text or stdout_text or "Неизвестная ошибка"
                    
                    return {
                        'success': False,
                        'error': f'Процесс завершился при инициализации: {error_message}',
                        'details': {
                            'return_code': process.returncode,
                            'stdout': stdout_text,
                            'stderr': stderr_text
                        }
                    }
                
                logger.debug(f"⏳ Инициализация... {i+1}/{initialization_time}")
            
            # Процесс успешно запущен и работает
            return {
                'success': True,
                'pid': process.pid,
                'message': 'Процесс успешно запущен'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Исключение при запуске процесса: {str(e)}'
            }
    
    async def stop_bot(self) -> Dict[str, Any]:
        """
        ⏹️ ИСПРАВЛЕННАЯ функция остановки бота
        
        Улучшения:
        ✅ Многоуровневая остановка (мягкая -> жесткая)
        ✅ Проверка результатов на каждом этапе
        ✅ Принудительная очистка состояний
        ✅ Детальное логирование процесса
        """
        try:
            logger.info("🛑 === НАЧИНАЕМ ОСТАНОВКУ ТОРГОВОГО БОТА ===")
            
            # 1. Проверяем текущее состояние
            current_status = self.get_comprehensive_status()
            logger.info(f"📊 Текущее состояние: {current_status['status_summary']}")
            
            if not current_status['process_running'] and not current_status['manager_running']:
                # Бот уже остановлен, но возможно есть рассинхронизация в БД
                if current_status.get('db_state'):
                    logger.info("🔄 Синхронизируем состояние БД...")
                    await self._update_db_state(False)
                
                return {
                    'success': True,
                    'message': 'Бот уже остановлен',
                    'was_running': False
                }
            
            # 2. Пытаемся мягкую остановку через внутренний менеджер
            if current_status['manager_running']:
                logger.info("🔄 Попытка мягкой остановки через внутренний менеджер...")
                try:
                    stop_result = await asyncio.wait_for(
                        self._internal_manager.stop(), 
                        timeout=15.0
                    )
                    if stop_result:
                        logger.info("✅ Мягкая остановка успешна")
                    else:
                        logger.warning("⚠️ Мягкая остановка вернула False")
                except asyncio.TimeoutError:
                    logger.warning("⏰ Таймаут мягкой остановки")
                except Exception as e:
                    logger.warning(f"⚠️ Ошибка мягкой остановки: {e}")
            
            # 3. Проверяем и принудительно завершаем процесс если нужно
            await asyncio.sleep(3)  # Даем время на завершение
            
            process_info = self._safe_check_bot_process()
            if process_info.get('running'):
                logger.info("🔨 Требуется принудительное завершение процесса")
                termination_result = await self._force_terminate_process(process_info.get('pid'))
                
                if not termination_result['success']:
                    logger.error(f"❌ Не удалось завершить процесс: {termination_result['error']}")
                    return {
                        'success': False,
                        'message': f'Не удалось остановить бот: {termination_result["error"]}'
                    }
            
            # 4. Обновляем состояние в БД
            logger.info("💾 Обновляем состояние в базе данных...")
            await self._update_db_state(False)
            
            # 5. Финальная проверка
            await asyncio.sleep(2)
            final_status = self.get_comprehensive_status()
            
            if final_status['synchronized'] and not final_status['process_running']:
                logger.info("🎉 БОТ УСПЕШНО ОСТАНОВЛЕН!")
                return {
                    'success': True,
                    'message': 'Бот успешно остановлен',
                    'status': final_status['status_summary']
                }
            else:
                logger.warning("⚠️ Остановка завершена, но есть проблемы с синхронизацией")
                return {
                    'success': True,
                    'message': 'Бот остановлен, но требуется синхронизация',
                    'sync_needed': True
                }
                
        except Exception as e:
            error_msg = f"Критическая ошибка остановки: {str(e)}"
            logger.error(f"💥 {error_msg}", exc_info=True)
            return {
                'success': False,
                'message': error_msg
            }
    
    async def _force_terminate_process(self, pid: int) -> Dict[str, Any]:
        """
        💀 Принудительное завершение процесса
        """
        try:
            if not pid:
                return {'success': False, 'error': 'PID не указан'}
            
            logger.info(f"🔨 Принудительное завершение процесса {pid}")
            
            # Шаг 1: Мягкий сигнал SIGTERM
            try:
                os.kill(pid, signal.SIGTERM)
                logger.info(f"📤 Отправлен SIGTERM процессу {pid}")
                
                # Ждем до 10 секунд
                for _ in range(10):
                    await asyncio.sleep(1)
                    if not psutil.pid_exists(pid):
                        logger.info(f"✅ Процесс {pid} корректно завершился")
                        return {'success': True, 'method': 'SIGTERM'}
                
            except ProcessLookupError:
                logger.info(f"✅ Процесс {pid} уже завершен")
                return {'success': True, 'method': 'already_dead'}
            
            # Шаг 2: Жесткий сигнал SIGKILL
            try:
                if psutil.pid_exists(pid):
                    logger.warning(f"💀 Отправляем SIGKILL процессу {pid}")
                    os.kill(pid, signal.SIGKILL)
                    
                    # Ждем еще 5 секунд
                    for _ in range(5):
                        await asyncio.sleep(1)
                        if not psutil.pid_exists(pid):
                            logger.info(f"✅ Процесс {pid} принудительно завершен")
                            return {'success': True, 'method': 'SIGKILL'}
                    
                    return {'success': False, 'error': f'Процесс {pid} не отвечает на SIGKILL'}
                else:
                    return {'success': True, 'method': 'disappeared'}
                    
            except ProcessLookupError:
                return {'success': True, 'method': 'killed'}
            except Exception as e:
                return {'success': False, 'error': f'Ошибка SIGKILL: {str(e)}'}
                
        except Exception as e:
            return {'success': False, 'error': f'Критическая ошибка завершения: {str(e)}'}
    
    async def _update_db_state(self, is_running: bool):
        """
        💾 ИСПРАВЛЕННОЕ обновление состояния в БД
        
        Улучшения:
        ✅ Более надежная обработка транзакций
        ✅ Создание записи если её нет
        ✅ Детальное логирование операций
        """
        db = None
        try:
            logger.debug(f"💾 Обновляем состояние БД: {'запущен' if is_running else 'остановлен'}")
            
            db = SessionLocal()
            
            # Ищем существующую запись
            state = db.query(BotState).first()
            
            if not state:
                # Создаем новую запись
                logger.info("📝 Создаем новую запись состояния в БД")
                state = BotState()
                db.add(state)
            
            # Обновляем поля
            old_state = state.is_running
            state.is_running = is_running
            
            current_time = datetime.utcnow()
            if is_running:
                state.start_time = current_time
                logger.debug(f"📝 Установлено время запуска: {current_time}")
            else:
                state.stop_time = current_time
                logger.debug(f"📝 Установлено время остановки: {current_time}")
            
            # Сохраняем изменения
            db.commit()
            
            change_info = "создано" if old_state is None else ("изменено" if old_state != is_running else "обновлено")
            logger.info(f"💾 Состояние БД {change_info}: {'запущен' if is_running else 'остановлен'}")
            
        except Exception as e:
            error_msg = f"Ошибка обновления БД: {str(e)}"
            logger.error(f"❌ {error_msg}")
            if db:
                try:
                    db.rollback()
                    logger.debug("🔄 Откат транзакции БД выполнен")
                except:
                    pass
            raise Exception(error_msg)
        finally:
            if db:
                try:
                    db.close()
                except:
                    pass
    
    def sync_state(self) -> Dict[str, Any]:
        """
        🔄 ПОЛНОСТЬЮ ПЕРЕПИСАННАЯ функция синхронизации
        
        Новая логика:
        ✅ Определяем "источник истины"
        ✅ Приводим все компоненты к единому состоянию
        ✅ Детальная отчетность о проделанных изменениях
        ✅ Безопасная обработка всех ошибок
        """
        try:
            logger.info("🔄 === НАЧИНАЕМ СИНХРОНИЗАЦИЮ СОСТОЯНИЙ ===")
            
            # 1. Собираем текущее состояние всех компонентов
            process_info = self._safe_check_bot_process()
            manager_status = self._safe_get_manager_status()
            db_status = self._safe_get_db_status()
            
            process_running = process_info.get('running', False)
            manager_running = manager_status.get('is_running', False)
            db_running = db_status.get('is_running', False) if db_status and 'error' not in db_status else False
            
            logger.info(
                f"📊 Текущие состояния:\n"
                f"   🔹 Процесс: {process_running}\n"
                f"   🔹 Менеджер: {manager_running}\n"
                f"   🔹 База данных: {db_running}"
            )
            
            # 2. Определяем "источник истины"
            # Приоритет: Процесс > Менеджер > БД
            if process_running:
                # Если процесс запущен - это главный источник истины
                target_state = True
                truth_source = "процесс"
                logger.info("🎯 Источник истины: ПРОЦЕСС (бот реально работает)")
            elif manager_running and not process_running:
                # Менеджер думает что работает, но процесса нет - ошибка
                target_state = False
                truth_source = "реальность"
                logger.info("🎯 Источник истины: РЕАЛЬНОСТЬ (процесса нет)")
            else:
                # Нет активных процессов - должно быть остановлено
                target_state = False
                truth_source = "реальность"
                logger.info("🎯 Источник истины: РЕАЛЬНОСТЬ (ничего не работает)")
            
            # 3. Синхронизируем все компоненты к целевому состоянию
            changes_made = []
            
            # Синхронизируем БД
            if db_running != target_state:
                try:
                    db = SessionLocal()
                    try:
                        state = db.query(BotState).first()
                        if not state:
                            state = BotState()
                            db.add(state)
                        
                        state.is_running = target_state
                        if target_state:
                            state.start_time = datetime.utcnow()
                        else:
                            state.stop_time = datetime.utcnow()
                        
                        db.commit()
                        changes_made.append(f"БД: {db_running} → {target_state}")
                        logger.info(f"💾 БД синхронизирована: {target_state}")
                        
                    finally:
                        db.close()
                except Exception as e:
                    logger.error(f"❌ Ошибка синхронизации БД: {e}")
                    changes_made.append(f"БД: ОШИБКА - {str(e)}")
            
            # Синхронизируем внутренний менеджер
            if manager_running != target_state:
                try:
                    self._internal_manager.is_running = target_state
                    changes_made.append(f"Менеджер: {manager_running} → {target_state}")
                    logger.info(f"🔧 Менеджер синхронизирован: {target_state}")
                except Exception as e:
                    logger.error(f"❌ Ошибка синхронизации менеджера: {e}")
                    changes_made.append(f"Менеджер: ОШИБКА - {str(e)}")
            
            # 4. Проверяем результат
            if changes_made:
                changes_text = "; ".join(changes_made)
                message = f'Синхронизация выполнена ({truth_source}): {changes_text}'
            else:
                message = 'Все компоненты уже синхронизированы'
            
            logger.info(f"✅ {message}")
            
            return {
                'success': True,
                'is_running': target_state,
                'changed': len(changes_made) > 0,
                'changes': changes_made,
                'truth_source': truth_source,
                'message': message
            }
            
        except Exception as e:
            error_msg = f"Критическая ошибка синхронизации: {str(e)}"
            logger.error(f"💥 {error_msg}", exc_info=True)
            return {
                'success': False,
                'error': error_msg
            }
    
    # 🔧 Вспомогательные методы для тестирования и отладки
    
    def load_state(self):
        """📥 Загрузка состояния в внутренний менеджер"""
        try:
            if self._internal_manager:
                self._internal_manager._load_state()
                logger.info("📥 Состояние внутреннего менеджера загружено")
            else:
                logger.warning("⚠️ Внутренний менеджер не инициализирован")
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки состояния: {e}")
    
    async def analyze_pair_test(self, symbol: str):
        """🧪 Тестовый анализ торговой пары"""
        try:
            logger.info(f"🧪 Начинаем тестовый анализ пары {symbol}")
            
            if not self._internal_manager:
                logger.error("❌ Внутренний менеджер не доступен")
                return None
            
            result = await self._internal_manager._analyze_pair(symbol)
            
            if result:
                logger.info(f"📊 Результат анализа {symbol}: {result.action} (уверенность: {result.confidence:.2f})")
            else:
                logger.info(f"📊 Результат анализа {symbol}: WAIT (нет сигнала)")
            
            return result
        except Exception as e:
            logger.error(f"❌ Ошибка тестового анализа {symbol}: {e}")
            return None
    
    async def update_pairs(self, pairs: List[str]) -> Dict[str, Any]:
        """💱 Обновление списка торговых пар"""
        try:
            logger.info(f"💱 Обновляем торговые пары: {pairs}")
            
            if not self._internal_manager:
                raise Exception("Внутренний менеджер не доступен")
            
            await self._internal_manager.update_pairs(pairs)
            
            message = f'Обновлено {len(pairs)} торговых пар: {", ".join(pairs)}'
            logger.info(f"✅ {message}")
            
            return {
                'success': True,
                'pairs': pairs,
                'message': message
            }
        except Exception as e:
            error_msg = f"Ошибка обновления торговых пар: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }
    
    async def close_position(self, symbol: str) -> Dict[str, Any]:
        """📤 Ручное закрытие позиции"""
        try:
            logger.info(f"📤 Попытка закрыть позицию {symbol}")
            
            if not self._internal_manager:
                raise Exception("Внутренний менеджер не доступен")
            
            result = await self._internal_manager.manual_close_position(symbol)
            
            message = f'Позиция {symbol} {"закрыта" if result else "не найдена"}'
            logger.info(f"📤 {message}")
            
            return {
                'success': result,
                'message': message
            }
        except Exception as e:
            error_msg = f"Ошибка закрытия позиции {symbol}: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }

# 🌍 Глобальный экземпляр единого менеджера
unified_bot_manager = UnifiedBotManager()