
"""
Скрипт управления торговой системой
Простое управление всеми компонентами
"""

import subprocess
import psutil
import sys
import time
import os

class BotSystemManager:
    """Управление всей торговой системой"""
    
    def find_processes(self):
        """Поиск процессов торговой системы"""
        processes = {
            'main_bot': [],
            'web_app': []
        }
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info.get('cmdline', []))
                
                if 'main.py' in cmdline and 'python' in cmdline:
                    processes['main_bot'].append({
                        'pid': proc.info['pid'],
                        'cmdline': cmdline
                    })
                
                if ('app.py' in cmdline or 'uvicorn' in cmdline) and 'python' in cmdline:
                    processes['web_app'].append({
                        'pid': proc.info['pid'],
                        'cmdline': cmdline
                    })
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return processes
    
    def show_status(self):
        """Показать статус всех компонентов"""
        print("=" * 60)
        print("🤖 СТАТУС ТОРГОВОЙ СИСТЕМЫ")
        print("=" * 60)
        
        processes = self.find_processes()
        
        # Торговый бот
        print("\n📈 Торговый бот (main.py):")
        if processes['main_bot']:
            for proc in processes['main_bot']:
                print(f"   ✅ Запущен (PID: {proc['pid']})")
                print(f"      Команда: {proc['cmdline'][:80]}...")
        else:
            print("   ❌ Не запущен")
        
        # Веб-интерфейс
        print("\n🌐 Веб-интерфейс (app.py):")
        if processes['web_app']:
            for proc in processes['web_app']:
                print(f"   ✅ Запущен (PID: {proc['pid']})")
                print(f"      Команда: {proc['cmdline'][:80]}...")
            print("   🌍 Доступен на: http://localhost:8000")
        else:
            print("   ❌ Не запущен")
        
        # Проверка порта
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', 8000))
            sock.close()
            if result == 0:
                print("   🌍 Порт 8000: Занят (веб-интерфейс доступен)")
            else:
                print("   🌍 Порт 8000: Свободен")
        except:
            print("   🌍 Порт 8000: Не удалось проверить")
        
        print("\n" + "=" * 60)
    
    def stop_component(self, component):
        """Остановка компонента"""
        processes = self.find_processes()
        
        if component == 'bot':
            target_processes = processes['main_bot']
            name = "торгового бота"
        elif component == 'web':
            target_processes = processes['web_app']
            name = "веб-интерфейса"
        else:
            print(f"❌ Неизвестный компонент: {component}")
            return False
        
        if not target_processes:
            print(f"ℹ️ {name.capitalize()} уже остановлен")
            return True
        
        print(f"🛑 Остановка {name}...")
        
        for proc_info in target_processes:
            try:
                proc = psutil.Process(proc_info['pid'])
                print(f"   Останавливаем PID {proc_info['pid']}...")
                
                # Graceful shutdown
                proc.terminate()
                
                # Ждем до 10 секунд
                try:
                    proc.wait(timeout=10)
                    print(f"   ✅ PID {proc_info['pid']} остановлен")
                except psutil.TimeoutExpired:
                    print(f"   ⚠️ PID {proc_info['pid']} не отвечает, принудительная остановка...")
                    proc.kill()
                    proc.wait()
                    print(f"   ✅ PID {proc_info['pid']} принудительно остановлен")
                    
            except psutil.NoSuchProcess:
                print(f"   ℹ️ PID {proc_info['pid']} уже завершен")
            except Exception as e:
                print(f"   ❌ Ошибка остановки PID {proc_info['pid']}: {e}")
        
        print(f"✅ {name.capitalize()} остановлен")
        return True
    
    def stop_all(self):
        """Остановка всех компонентов"""
        print("🛑 Остановка всей системы...")
        self.stop_component('bot')
        self.stop_component('web')
        print("✅ Вся система остановлена")
    
    def start_web(self):
        """Запуск веб-интерфейса"""
        processes = self.find_processes()
        if processes['web_app']:
            print("ℹ️ Веб-интерфейс уже запущен")
            return
        
        print("🌐 Запуск веб-интерфейса...")
        try:
            subprocess.Popen(
                ["python", "app.py"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print("✅ Веб-интерфейс запущен")
            print("🌍 Доступен на: http://localhost:8000")
        except Exception as e:
            print(f"❌ Ошибка запуска веб-интерфейса: {e}")
    
    def restart_web(self):
        """Перезапуск веб-интерфейса"""
        print("🔄 Перезапуск веб-интерфейса...")
        self.stop_component('web')
        time.sleep(2)
        self.start_web()

def main():
    manager = BotSystemManager()
    
    if len(sys.argv) < 2:
        print("🤖 Управление торговой системой")
        print("\nДоступные команды:")
        print("  python manage_bot.py status     - Показать статус")
        print("  python manage_bot.py stop-web   - Остановить веб-интерфейс")
        print("  python manage_bot.py stop-bot   - Остановить торгового бота")
        print("  python manage_bot.py stop-all   - Остановить всё")
        print("  python manage_bot.py start-web  - Запустить веб-интерфейс")
        print("  python manage_bot.py restart-web - Перезапустить веб-интерфейс")
        return
    
    command = sys.argv[1]
    
    if command == 'status':
        manager.show_status()
    elif command == 'stop-web':
        manager.stop_component('web')
    elif command == 'stop-bot':
        manager.stop_component('bot')
    elif command == 'stop-all':
        manager.stop_all()
    elif command == 'start-web':
        manager.start_web()
    elif command == 'restart-web':
        manager.restart_web()
    else:
        print(f"❌ Неизвестная команда: {command}")

if __name__ == "__main__":
    main()
EOF

