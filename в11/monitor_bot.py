#!/usr/bin/env python3
"""
Мониторинг активности бота в реальном времени
"""
import os
import sys
import time
import subprocess
from datetime import datetime
from colorama import init, Fore, Style

# Инициализация colorama для цветного вывода
init()

def clear_screen():
    """Очистка экрана"""
    os.system('clear' if os.name == 'posix' else 'cls')

def get_last_lines(filename, n=20):
    """Получить последние n строк из файла"""
    try:
        result = subprocess.run(['tail', '-n', str(n), filename], 
                              capture_output=True, text=True)
        return result.stdout.splitlines()
    except:
        try:
            with open(filename, 'r') as f:
                lines = f.readlines()
                return [line.strip() for line in lines[-n:]]
        except:
            return []

def colorize_log_line(line):
    """Раскрасить строку лога в зависимости от содержимого"""
    if 'ERROR' in line or '❌' in line:
        return f"{Fore.RED}{line}{Style.RESET_ALL}"
    elif 'WARNING' in line or '⚠️' in line:
        return f"{Fore.YELLOW}{line}{Style.RESET_ALL}"
    elif 'INFO' in line and ('✅' in line or '🎯' in line or 'сигнал' in line.lower()):
        return f"{Fore.GREEN}{line}{Style.RESET_ALL}"
    elif '🔄' in line or 'Цикл #' in line:
        return f"{Fore.CYAN}{line}{Style.RESET_ALL}"
    elif '📊' in line or '💼' in line or '📈' in line:
        return f"{Fore.BLUE}{line}{Style.RESET_ALL}"
    else:
        return line

def get_process_status():
    """Проверка статуса процессов"""
    processes = {
        'app.py': False,
        'main.py': False
    }
    
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        for line in result.stdout.splitlines():
            if 'python' in line:
                if 'app.py' in line:
                    processes['app.py'] = True
                elif 'main.py' in line and 'main_simple' not in line:
                    processes['main.py'] = True
    except:
        pass
    
    return processes

def monitor():
    """Основной цикл мониторинга"""
    log_file = '/var/www/www-root/data/www/systemetech.ru/logs/trading.log'
    web_log_file = '/var/www/www-root/data/www/systemetech.ru/logs/web.log'
    
    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}🔍 МОНИТОРИНГ CRYPTO TRADING BOT - Нажмите Ctrl+C для выхода{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
    print()
    
    while True:
        clear_screen()
        
        # Заголовок
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"{Fore.CYAN}🤖 CRYPTO BOT MONITOR | {current_time}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
        
        # Статус процессов
        processes = get_process_status()
        print(f"\n{Fore.YELLOW}📊 СТАТУС ПРОЦЕССОВ:{Style.RESET_ALL}")
        print(f"   Web интерфейс (app.py): {'✅ Запущен' if processes['app.py'] else '❌ Остановлен'}")
        print(f"   Торговый бот (main.py): {'✅ Запущен' if processes['main.py'] else '❌ Остановлен'}")
        
        # Последние логи бота
        print(f"\n{Fore.YELLOW}📋 ПОСЛЕДНИЕ ЛОГИ БОТА:{Style.RESET_ALL}")
        bot_logs = get_last_lines(log_file, 15)
        if bot_logs:
            for line in bot_logs:
                print(f"   {colorize_log_line(line)}")
        else:
            print(f"   {Fore.RED}Логи недоступны{Style.RESET_ALL}")
        
        # Последние логи веб-интерфейса
        print(f"\n{Fore.YELLOW}🌐 ПОСЛЕДНИЕ ЛОГИ ВЕБ-ИНТЕРФЕЙСА:{Style.RESET_ALL}")
        web_logs = get_last_lines(web_log_file, 5)
        if web_logs:
            for line in web_logs:
                print(f"   {colorize_log_line(line)}")
        else:
            print(f"   {Fore.BLUE}Нет активности{Style.RESET_ALL}")
        
        # Статистика из логов
        print(f"\n{Fore.YELLOW}📈 СТАТИСТИКА:{Style.RESET_ALL}")
        
        # Подсчет событий в логах
        if bot_logs:
            cycles = sum(1 for line in bot_logs if 'Цикл #' in line)
            signals = sum(1 for line in bot_logs if 'сигнал' in line.lower() and 'WAIT' not in line)
            errors = sum(1 for line in bot_logs if 'ERROR' in line or '❌' in line)
            
            print(f"   Циклов анализа: {cycles}")
            print(f"   Сигналов найдено: {signals}")
            print(f"   Ошибок: {errors}")
        
        print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}Обновление каждые 3 секунды... Нажмите Ctrl+C для выхода{Style.RESET_ALL}")
        
        time.sleep(3)

if __name__ == "__main__":
    try:
        monitor()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}👋 Мониторинг остановлен{Style.RESET_ALL}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Fore.RED}❌ Ошибка: {e}{Style.RESET_ALL}")
        sys.exit(1)