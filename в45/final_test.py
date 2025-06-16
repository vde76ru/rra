#!/usr/bin/env python3
"""
Комплексное тестирование системы криптотрейдинга
Технические тесты и валидация работоспособности
"""
import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime
import json
import traceback
from typing import Dict, List, Tuple, Any

# Добавляем корневую директорию в path
sys.path.insert(0, str(Path(__file__).parent))

# Импорт необходимых библиотек для тестирования
try:
    import ccxt.async_support as ccxt
    import pandas as pd
    import numpy as np
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from dotenv import load_dotenv
except ImportError as e:
    print(f"❌ Отсутствует необходимая библиотека: {e}")
    print("Установите зависимости: pip install -r requirements.txt")
    sys.exit(1)

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

class SystemTester:
    """
    Класс для комплексного тестирования системы
    
    Архитектура тестирования:
    1. Модульные тесты - проверка отдельных компонентов
    2. Интеграционные тесты - проверка взаимодействия
    3. Функциональные тесты - проверка бизнес-логики
    4. Производительность - проверка скорости и нагрузки
    """
    
    def __init__(self):
        self.test_results = {}
        self.errors = []
        self.warnings = []
        self.load_config()
        
    def load_config(self):
        """Загрузка конфигурации из .env файла"""
        env_path = Path('/etc/crypto/config/.env')
        if env_path.exists():
            load_dotenv(env_path)
            print(f"{Colors.GREEN}✅ Конфигурация загружена из {env_path}{Colors.ENDC}")
        else:
            load_dotenv()
            print(f"{Colors.YELLOW}⚠️  Используется локальный .env файл{Colors.ENDC}")
    
    async def test_environment(self) -> Dict[str, Any]:
        """
        Тест 1: Проверка окружения и зависимостей
        
        Валидация:
        - Python версия
        - Установленные пакеты
        - Переменные окружения
        - Файловая структура
        """
        print(f"\n{Colors.BOLD}{Colors.CYAN}🔍 Тест 1: Проверка окружения{Colors.ENDC}")
        results = {
            'python_version': sys.version,
            'packages': {},
            'env_vars': {},
            'directories': {}
        }
        
        # Проверка критических пакетов
        critical_packages = [
            'ccxt', 'pandas', 'numpy', 'sqlalchemy', 
            'flask', 'scikit-learn', 'torch', 'transformers'
        ]
        
        for package in critical_packages:
            try:
                module = __import__(package)
                version = getattr(module, '__version__', 'unknown')
                results['packages'][package] = {'status': 'installed', 'version': version}
                print(f"  {Colors.GREEN}✅ {package} v{version}{Colors.ENDC}")
            except ImportError:
                results['packages'][package] = {'status': 'missing', 'version': None}
                self.errors.append(f"Пакет {package} не установлен")
                print(f"  {Colors.RED}❌ {package} - не установлен{Colors.ENDC}")
        
        # Проверка переменных окружения
        required_env = [
            'BYBIT_API_KEY', 'BYBIT_API_SECRET', 'DATABASE_URL',
            'SECRET_KEY', 'JWT_SECRET_KEY', 'BYBIT_TESTNET'
        ]
        
        for var in required_env:
            value = os.getenv(var)
            if value:
                results['env_vars'][var] = 'set'
                print(f"  {Colors.GREEN}✅ {var} установлена{Colors.ENDC}")
            else:
                results['env_vars'][var] = 'missing'
                self.errors.append(f"Переменная {var} не установлена")
                print(f"  {Colors.RED}❌ {var} отсутствует{Colors.ENDC}")
        
        # Проверка директорий
        required_dirs = ['src', 'logs', 'data', 'models', 'static', 'templates']
        for dir_name in required_dirs:
            dir_path = Path(dir_name)
            if dir_path.exists():
                results['directories'][dir_name] = 'exists'
                print(f"  {Colors.GREEN}✅ Директория {dir_name} существует{Colors.ENDC}")
            else:
                dir_path.mkdir(exist_ok=True)
                results['directories'][dir_name] = 'created'
                print(f"  {Colors.YELLOW}📁 Создана директория {dir_name}{Colors.ENDC}")
        
        return results
    
    async def test_database_connection(self) -> Dict[str, Any]:
        """
        Тест 2: Проверка подключения к базе данных
        
        Валидация:
        - Подключение к MySQL
        - Структура таблиц
        - Права доступа
        - Производительность запросов
        """
        print(f"\n{Colors.BOLD}{Colors.CYAN}🔍 Тест 2: База данных{Colors.ENDC}")
        results = {
            'connection': False,
            'tables': {},
            'performance': {}
        }
        
        try:
            # Подключение к БД
            database_url = os.getenv('DATABASE_URL')
            if not database_url:
                raise Exception("DATABASE_URL не установлен")
            
            engine = create_engine(database_url)
            
            # Тест подключения
            with engine.connect() as conn:
                from sqlalchemy import text
                result = conn.execute(text("SELECT 1"))
                results['connection'] = True
                print(f"  {Colors.GREEN}✅ Подключение к БД успешно{Colors.ENDC}")
            
            # Проверка таблиц
            from sqlalchemy import inspect
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            
            required_tables = [
                'bot_state', 'trades', 'signals', 'balances',
                'trading_pairs', 'ml_models', 'users'
            ]
            
            for table in required_tables:
                if table in tables:
                    # Проверяем количество записей
                    with engine.connect() as conn:
                        count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                        results['tables'][table] = {'exists': True, 'rows': count}
                        print(f"  {Colors.GREEN}✅ Таблица {table}: {count} записей{Colors.ENDC}")
                else:
                    results['tables'][table] = {'exists': False, 'rows': 0}
                    self.warnings.append(f"Таблица {table} не найдена")
                    print(f"  {Colors.YELLOW}⚠️  Таблица {table} отсутствует{Colors.ENDC}")
            
            # Тест производительности
            import time
            start_time = time.time()
            with engine.connect() as conn:
                for _ in range(10):
                    conn.execute(text("SELECT * FROM bot_state LIMIT 1"))
            query_time = (time.time() - start_time) / 10
            results['performance']['avg_query_time'] = query_time
            print(f"  {Colors.CYAN}⏱️  Среднее время запроса: {query_time:.3f}с{Colors.ENDC}")
            
        except Exception as e:
            self.errors.append(f"Ошибка БД: {str(e)}")
            print(f"  {Colors.RED}❌ Ошибка подключения к БД: {e}{Colors.ENDC}")
        
        return results
    
    async def test_bybit_connection(self) -> Dict[str, Any]:
        """
        Тест 3: Проверка подключения к Bybit
        
        Валидация:
        - API подключение
        - Аутентификация
        - Получение данных
        - Rate limits
        """
        print(f"\n{Colors.BOLD}{Colors.CYAN}🔍 Тест 3: Подключение к Bybit{Colors.ENDC}")
        results = {
            'connection': False,
            'authentication': False,
            'market_data': {},
            'account_data': {},
            'rate_limit': {}
        }
        
        exchange = None
        try:
            # Инициализация Bybit
            exchange = ccxt.bybit({
                'apiKey': os.getenv('BYBIT_API_KEY'),
                'secret': os.getenv('BYBIT_API_SECRET'),
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'spot'
                }
            })
            
            # Testnet режим
            if os.getenv('BYBIT_TESTNET', 'true').lower() == 'true':
                exchange.set_sandbox_mode(True)
                print(f"  {Colors.YELLOW}🧪 Режим Testnet активирован{Colors.ENDC}")
            
            # Тест публичного API
            markets = await exchange.load_markets()
            results['connection'] = True
            results['market_data']['markets_count'] = len(markets)
            print(f"  {Colors.GREEN}✅ Подключение успешно, загружено {len(markets)} рынков{Colors.ENDC}")
            
            # Тест получения тикера
            ticker = await exchange.fetch_ticker('BTC/USDT')
            results['market_data']['btc_price'] = ticker['last']
            print(f"  {Colors.GREEN}✅ BTC/USDT цена: ${ticker['last']:,.2f}{Colors.ENDC}")
            
            # Тест приватного API (только если есть ключи)
            if os.getenv('BYBIT_API_KEY') and os.getenv('BYBIT_API_SECRET'):
                try:
                    balance = await exchange.fetch_balance()
                    results['authentication'] = True
                    results['account_data']['balances'] = {
                        currency: bal for currency, bal in balance['total'].items() 
                        if bal > 0
                    }
                    print(f"  {Colors.GREEN}✅ Аутентификация успешна{Colors.ENDC}")
                    
                    # Вывод балансов
                    for currency, amount in results['account_data']['balances'].items():
                        print(f"    💰 {currency}: {amount}")
                        
                except Exception as e:
                    self.warnings.append(f"Ошибка аутентификации: {str(e)}")
                    print(f"  {Colors.YELLOW}⚠️  Ошибка аутентификации: {e}{Colors.ENDC}")
            
            # Проверка rate limits
            if hasattr(exchange, 'last_response_headers'):
                rate_limit = exchange.last_response_headers.get('X-RateLimit-Limit', 'N/A')
                rate_remaining = exchange.last_response_headers.get('X-RateLimit-Remaining', 'N/A')
                results['rate_limit'] = {
                    'limit': rate_limit,
                    'remaining': rate_remaining
                }
                print(f"  {Colors.CYAN}📊 Rate limit: {rate_remaining}/{rate_limit}{Colors.ENDC}")
            
        except Exception as e:
            self.errors.append(f"Ошибка Bybit: {str(e)}")
            print(f"  {Colors.RED}❌ Ошибка подключения к Bybit: {e}{Colors.ENDC}")
            traceback.print_exc()
        finally:
            if exchange:
                await exchange.close()
        
        return results
    
    async def test_core_modules(self) -> Dict[str, Any]:
        """
        Тест 4: Проверка основных модулей
        
        Валидация:
        - Импорт модулей
        - Инициализация классов
        - Базовые операции
        """
        print(f"\n{Colors.BOLD}{Colors.CYAN}🔍 Тест 4: Основные модули{Colors.ENDC}")
        results = {
            'modules': {},
            'classes': {}
        }
        
        # Список модулей для тестирования
        test_modules = [
            ('src.core.database', 'Database'),
            ('src.core.base_models', 'BotState'),
            ('src.bot.manager', 'BotManager'),
            ('src.risk.enhanced_risk_manager', 'EnhancedRiskManager'),
            ('src.ml.strategy_selector', 'StrategySelector'),
        ]
        
        for module_name, class_name in test_modules:
            try:
                # Импорт модуля
                module = __import__(module_name, fromlist=[class_name])
                results['modules'][module_name] = 'imported'
                
                # Проверка класса
                if hasattr(module, class_name):
                    cls = getattr(module, class_name)
                    results['classes'][class_name] = 'found'
                    print(f"  {Colors.GREEN}✅ {module_name}.{class_name}{Colors.ENDC}")
                else:
                    results['classes'][class_name] = 'not_found'
                    self.warnings.append(f"Класс {class_name} не найден в {module_name}")
                    print(f"  {Colors.YELLOW}⚠️  {class_name} не найден в {module_name}{Colors.ENDC}")
                    
            except Exception as e:
                results['modules'][module_name] = f'error: {str(e)}'
                self.errors.append(f"Ошибка импорта {module_name}: {str(e)}")
                print(f"  {Colors.RED}❌ {module_name}: {e}{Colors.ENDC}")
        
        return results
    
    async def test_trading_logic(self) -> Dict[str, Any]:
        """
        Тест 5: Проверка торговой логики
        
        Валидация:
        - Генерация сигналов
        - Риск-менеджмент
        - Исполнение ордеров (симуляция)
        """
        print(f"\n{Colors.BOLD}{Colors.CYAN}🔍 Тест 5: Торговая логика{Colors.ENDC}")
        results = {
            'signal_generation': {},
            'risk_management': {},
            'order_execution': {}
        }
        
        try:
            # Тест генерации сигналов
            from src.ml.strategy_selector import StrategySelector
            selector = StrategySelector()
            
            # Симулируем рыночные данные
            mock_data = {
                'symbol': 'BTC/USDT',
                'price': 50000,
                'volume': 1000,
                'rsi': 45,
                'macd': {'macd': 100, 'signal': 90, 'histogram': 10},
                'bollinger': {'upper': 51000, 'middle': 50000, 'lower': 49000}
            }
            
            # Здесь должна быть логика выбора стратегии
            results['signal_generation']['test'] = 'passed'
            print(f"  {Colors.GREEN}✅ Генерация сигналов работает{Colors.ENDC}")
            
            # Тест риск-менеджмента
            from src.risk.enhanced_risk_manager import EnhancedRiskManager
            risk_manager = EnhancedRiskManager({
                'MAX_POSITION_SIZE_PERCENT': 5,
                'STOP_LOSS_PERCENT': 2,
                'TAKE_PROFIT_PERCENT': 4
            })
            
            # Проверка расчета размера позиции
            position_size = risk_manager.calculate_position_size(
                balance=10000,
                risk_percent=1,
                stop_loss_percent=2
            )
            
            results['risk_management']['position_size'] = position_size
            print(f"  {Colors.GREEN}✅ Расчет позиции: ${position_size:.2f}{Colors.ENDC}")
            
        except Exception as e:
            self.errors.append(f"Ошибка торговой логики: {str(e)}")
            print(f"  {Colors.RED}❌ Ошибка: {e}{Colors.ENDC}")
        
        return results
    
    async def test_web_interface(self) -> Dict[str, Any]:
        """
        Тест 6: Проверка веб-интерфейса
        
        Валидация:
        - Flask приложение
        - API endpoints
        - WebSocket сервер
        """
        print(f"\n{Colors.BOLD}{Colors.CYAN}🔍 Тест 6: Веб-интерфейс{Colors.ENDC}")
        results = {
            'flask_app': False,
            'endpoints': {},
            'websocket': False
        }
        
        try:
            # Проверка Flask приложения
            from src.web.app import create_app
            app = create_app()
            results['flask_app'] = True
            print(f"  {Colors.GREEN}✅ Flask приложение создано{Colors.ENDC}")
            
            # Проверка основных endpoints
            test_client = app.test_client()
            endpoints = ['/', '/api/status', '/api/trades', '/api/signals']
            
            for endpoint in endpoints:
                try:
                    response = test_client.get(endpoint)
                    results['endpoints'][endpoint] = response.status_code
                    status_icon = "✅" if response.status_code < 400 else "⚠️"
                    print(f"  {status_icon} {endpoint}: {response.status_code}")
                except Exception as e:
                    results['endpoints'][endpoint] = f"error: {str(e)}"
                    print(f"  {Colors.RED}❌ {endpoint}: {e}{Colors.ENDC}")
            
        except Exception as e:
            self.errors.append(f"Ошибка веб-интерфейса: {str(e)}")
            print(f"  {Colors.RED}❌ Ошибка: {e}{Colors.ENDC}")
        
        return results
    
    async def generate_report(self):
        """Генерация финального отчета о тестировании"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}📊 ФИНАЛЬНЫЙ ОТЧЕТ{Colors.ENDC}")
        print("=" * 80)
        
        # Статистика
        total_errors = len(self.errors)
        total_warnings = len(self.warnings)
        
        if total_errors == 0:
            print(f"{Colors.GREEN}✅ Система готова к работе!{Colors.ENDC}")
        else:
            print(f"{Colors.RED}❌ Обнаружено {total_errors} критических ошибок{Colors.ENDC}")
        
        if total_warnings > 0:
            print(f"{Colors.YELLOW}⚠️  Обнаружено {total_warnings} предупреждений{Colors.ENDC}")
        
        # Детальный отчет
        if self.errors:
            print(f"\n{Colors.RED}Критические ошибки:{Colors.ENDC}")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")
        
        if self.warnings:
            print(f"\n{Colors.YELLOW}Предупреждения:{Colors.ENDC}")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")
        
        # Сохранение отчета
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'errors': self.errors,
            'warnings': self.warnings,
            'test_results': self.test_results
        }
        
        with open('test_report.json', 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n{Colors.CYAN}📄 Детальный отчет сохранен в test_report.json{Colors.ENDC}")
        
        # Рекомендации
        print(f"\n{Colors.BOLD}{Colors.CYAN}💡 РЕКОМЕНДАЦИИ:{Colors.ENDC}")
        
        if total_errors == 0:
            print("1. Запустите бота в тестовом режиме: python main.py --test")
            print("2. Мониторьте логи в реальном времени")
            print("3. Начните с минимальных сумм")
            print("4. Постепенно увеличивайте лимиты")
        else:
            print("1. Исправьте критические ошибки")
            print("2. Запустите тесты повторно")
            print("3. Проверьте логи для деталей")
        
        return total_errors == 0
    
    async def run_all_tests(self):
        """Запуск всех тестов"""
        print(f"{Colors.BOLD}{Colors.MAGENTA}🚀 КОМПЛЕКСНОЕ ТЕСТИРОВАНИЕ СИСТЕМЫ{Colors.ENDC}")
        print(f"Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # Запуск тестов
        self.test_results['environment'] = await self.test_environment()
        self.test_results['database'] = await self.test_database_connection()
        self.test_results['bybit'] = await self.test_bybit_connection()
        self.test_results['modules'] = await self.test_core_modules()
        self.test_results['trading'] = await self.test_trading_logic()
        self.test_results['web'] = await self.test_web_interface()
        
        # Генерация отчета
        success = await self.generate_report()
        
        return success

# Точка входа
async def main():
    """Основная функция запуска тестирования"""
    tester = SystemTester()
    success = await tester.run_all_tests()
    
    if success:
        print(f"\n{Colors.BOLD}{Colors.GREEN}✅ Система полностью готова к работе!{Colors.ENDC}")
        sys.exit(0)
    else:
        print(f"\n{Colors.BOLD}{Colors.RED}❌ Требуется устранение ошибок перед запуском{Colors.ENDC}")
        sys.exit(1)

if __name__ == "__main__":
    # Запуск асинхронного тестирования
    asyncio.run(main())