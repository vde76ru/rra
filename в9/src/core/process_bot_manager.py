"""
Менеджер бота для управления процессами
Решает проблему межпроцессного взаимодействия
"""
import subprocess
import psutil
import signal
import os
import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, List, Tuple
from .database import SessionLocal
from .models import BotState, TradingPair

logger = logging.getLogger(__name__)

class ProcessBotManager:
    """
    Менеджер для управления ботом как отдельным процессом
    Используется в веб-интерфейсе для контроля main.py
    """
    
    def __init__(self):
        self.bot_process: Optional[subprocess.Popen] = None
        self.bot_pid: Optional[int] = None
        
        # При инициализации проверяем, не запущен ли уже бот
        self._check_existing_process()
    
    def _check_existing_process(self) -> bool:
        """
        Проверка запущенного процесса бота при старте веб-интерфейса
        Это решает проблему, когда main.py запущен отдельно
        """
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info.get('cmdline', [])
                    if not cmdline:
                        continue
                    
                    # Ищем процесс main.py в нашей директории
                    if (len(cmdline) >= 2 and 
                        'python' in cmdline[0].lower() and 
                        'main.py' in cmdline[1] and
                        str(os.getcwd()) in ' '.join(cmdline)):
                        
                        self.bot_pid = proc.info['pid']
                        logger.info(f"🔍 Найден запущенный бот (PID: {self.bot_pid})")
                        
                        # Обновляем статус в БД
                        asyncio.create_task(self._update_db_status(True))
                        return True
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
        except Exception as e:
            logger.error(f"Ошибка поиска процесса: {e}")
        
        return False
    
    async def start_bot(self) -> Tuple[bool, str]:
        """
        Запуск торгового бота как отдельного процесса
        Возвращает (успех, сообщение)
        """
        if await self.is_bot_running():
            return False, "Бот уже запущен"
        
        try:
            # Подготавливаем команду запуска
            cmd = ["python", "main.py"]
            
            # Запускаем процесс
            self.bot_process = subprocess.Popen(
                cmd,
                cwd=os.getcwd(),  # Текущая директория
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                # На Unix создаем новую группу процессов для корректной остановки
                preexec_fn=os.setsid if os.name != 'nt' else None
            )
            
            self.bot_pid = self.bot_process.pid
            
            # Даем процессу время на инициализацию
            await asyncio.sleep(3)
            
            # Проверяем, что процесс успешно запустился
            if self.bot_process.poll() is None:
                await self._update_db_status(True)
                
                logger.info(f"✅ Бот запущен (PID: {self.bot_pid})")
                return True, f"Бот запущен (PID: {self.bot_pid})"
            else:
                # Процесс завершился с ошибкой
                stdout, stderr = self.bot_process.communicate()
                error_msg = stderr.decode() if stderr else "Неизвестная ошибка"
                
                logger.error(f"❌ Бот не смог запуститься: {error_msg}")
                return False, f"Ошибка запуска: {error_msg[:200]}"
                
        except Exception as e:
            logger.error(f"Ошибка запуска бота: {e}")
            return False, f"Критическая ошибка: {str(e)}"
    
    async def stop_bot(self) -> Tuple[bool, str]:
        """
        Остановка торгового бота
        Использует graceful shutdown через сигналы
        """
        if not await self.is_bot_running():
            return False, "Бот не запущен"
        
        try:
            if self.bot_process and self.bot_process.poll() is None:
                # Graceful shutdown через SIGTERM
                if os.name != 'nt':  # Unix/Linux
                    os.killpg(os.getpgid(self.bot_process.pid), signal.SIGTERM)
                else:  # Windows
                    self.bot_process.terminate()
                
                # Ждем завершения (максимум 30 секунд)
                try:
                    self.bot_process.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    # Принудительная остановка
                    if os.name != 'nt':
                        os.killpg(os.getpgid(self.bot_process.pid), signal.SIGKILL)
                    else:
                        self.bot_process.kill()
                    
                    self.bot_process.wait()
                
            elif self.bot_pid:
                # Остановка через PID (если процесс был найден при старте)
                try:
                    proc = psutil.Process(self.bot_pid)
                    proc.terminate()
                    proc.wait(timeout=30)
                except psutil.TimeoutExpired:
                    proc.kill()
                except psutil.NoSuchProcess:
                    pass  # Процесс уже завершен
            
            # Очищаем ссылки
            self.bot_process = None
            self.bot_pid = None
            
            await self._update_db_status(False)
            
            logger.info("🛑 Бот остановлен")
            return True, "Бот успешно остановлен"
            
        except Exception as e:
            logger.error(f"Ошибка остановки бота: {e}")
            return False, f"Ошибка остановки: {str(e)}"
    
    async def is_bot_running(self) -> bool:
        """
        Проверка статуса бота
        Комбинирует проверку процесса и БД
        """
        # Проверка через subprocess
        if self.bot_process and self.bot_process.poll() is None:
            return True
        
        # Проверка через PID
        if self.bot_pid:
            try:
                if psutil.pid_exists(self.bot_pid):
                    proc = psutil.Process(self.bot_pid)
                    if proc.is_running():
                        return True
            except psutil.NoSuchProcess:
                pass
        
        # Поиск процесса в системе
        if self._check_existing_process():
            return True
        
        # Если процесс не найден, обновляем БД
        await self._update_db_status(False)
        return False
    
    async def get_bot_status(self) -> Dict:
        """
        Получение детального статуса бота
        """
        is_running = await self.is_bot_running()
        
        # Получаем данные из БД
        db = SessionLocal()
        try:
            bot_state = db.query(BotState).first()
            active_pairs = db.query(TradingPair).filter(
                TradingPair.is_active == True
            ).all()
            
            status = {
                'is_running': is_running,
                'pid': self.bot_pid,
                'active_pairs': [pair.symbol for pair in active_pairs],
                'total_pairs': len(active_pairs)
            }
            
            if bot_state:
                status.update({
                    'start_time': bot_state.start_time.isoformat() if bot_state.start_time else None,
                    'total_trades': bot_state.total_trades or 0,
                    'profitable_trades': bot_state.profitable_trades or 0,
                    'total_profit': bot_state.total_profit or 0.0,
                    'current_balance': bot_state.current_balance or 0.0
                })
            
            return status
            
        finally:
            db.close()
    
    async def _update_db_status(self, is_running: bool):
        """
        Обновление статуса в базе данных
        Синхронизация между процессами
        """
        db = SessionLocal()
        try:
            bot_state = db.query(BotState).first()
            if not bot_state:
                bot_state = BotState()
                db.add(bot_state)
            
            bot_state.is_running = is_running
            if is_running:
                bot_state.start_time = datetime.utcnow()
            else:
                bot_state.stop_time = datetime.utcnow()
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Ошибка обновления статуса в БД: {e}")
        finally:
            db.close()
    
    async def restart_bot(self) -> Tuple[bool, str]:
        """
        Перезапуск бота
        """
        logger.info("🔄 Перезапуск бота...")
        
        # Останавливаем
        stop_success, stop_msg = await self.stop_bot()
        if not stop_success:
            return False, f"Ошибка остановки: {stop_msg}"
        
        # Ждем полной остановки
        await asyncio.sleep(2)
        
        # Запускаем
        start_success, start_msg = await self.start_bot()
        return start_success, start_msg

# Глобальный экземпляр для веб-интерфейса
process_bot_manager = ProcessBotManager()