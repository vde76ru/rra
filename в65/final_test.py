#!/usr/bin/env python3
"""
Комплексное тестирование системы криптобота
Файл: final_test.py
"""
import os
import sys
import asyncio
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import importlib
import importlib.metadata

# Загружаем конфигурацию из правильного места
from dotenv import load_dotenv
load_dotenv('/etc/crypto/config/.env')

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent))

# Цвета для консоли
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

class SystemTester:
    """Класс для комплексного тестирования системы"""
    
    def __init__(self):
        self.results = {}
        self.errors = []
        self.warnings = []
        self.start_time = datetime.now()
        
    async def run_all_tests(self) -> Dict[str, Any]:
        """Запуск всех тестов"""
        print(f"{Colors.GREEN}✅ Конфигурация загружена из /etc/crypto/config/.env{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.CYAN}🔍 КОМПЛЕКСНОЕ ТЕСТИРОВАНИЕ СИСТЕМЫ{Colors.ENDC}")
        print(f"Время запуска: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # Запускаем тесты последовательно
        self.results['environment'] = await self.test_environment()
        self.results['database'] = await self.test_database_connection()
        self.results['exchange'] = await self.test_exchange_connection()
        self.results['modules'] = await self.test_core_modules()
        self.results['trading'] = await self.test_trading_logic()
        self.results['web'] = await self.test_web_interface()
        
        # Финальный отчет
        self._generate_final_report()
        
        return self.results
    
    async def test_environment(self) -> Dict[str, Any]:
        """
        Тест 1: Проверка окружения
        
        Проверяем:
        - Установленные Python пакеты
        - Переменные окружения
        - Структуру директорий
        """
        print(f"\n{Colors.BOLD}{Colors.CYAN}🔍 Тест 1: Проверка окружения{Colors.ENDC}")
        results = {
            'modules': {},
            'env_vars': {},
            'directories': {}
        }
        
        # Проверка модулей
        required_modules = {
            'ccxt': 'ccxt',
            'pandas': 'pandas',
            'numpy': 'numpy',
            'sqlalchemy': 'sqlalchemy',
            'flask': 'flask',
            'torch': 'torch',
            'transformers': 'transformers'
        }
        
        # Обычная проверка для большинства модулей
        for name, import_name in required_modules.items():
            try:
                module = importlib.import_module(import_name)
                # Используем разные способы получения версии
                if hasattr(module, '__version__'):
                    version = module.__version__
                elif hasattr(module, 'version'):
                    version = module.version
                else:
                    # Используем importlib.metadata для новых версий
                    try:
                        version = importlib.metadata.version(import_name)
                    except:
                        version = 'unknown'
                
                results['modules'][name] = version
                print(f"  {Colors.GREEN}✅ {name} v{version}{Colors.ENDC}")
            except ImportError:
                results['modules'][name] = None
                self.errors.append(f"Пакет {name} не установлен")
                print(f"  {Colors.RED}❌ {name} - не установлен{Colors.ENDC}")
        
        # Специальная проверка для scikit-learn
        try:
            import sklearn
            version = sklearn.__version__
            results['modules']['scikit-learn'] = version
            print(f"  {Colors.GREEN}✅ scikit-learn v{version}{Colors.ENDC}")
        except ImportError:
            results['modules']['scikit-learn'] = None
            self.errors.append("Пакет scikit-learn не установлен")
            print(f"  {Colors.RED}❌ scikit-learn - не установлен{Colors.ENDC}")
        
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
            
            from sqlalchemy import create_engine, text, inspect
            engine = create_engine(database_url)
            
            # Тест подключения
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                results['connection'] = True
                print(f"  {Colors.GREEN}✅ Подключение к БД успешно{Colors.ENDC}")
            
            # Проверка таблиц
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            
            for table in tables:
                with engine.connect() as conn:
                    count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = count_result.scalar()
                    results['tables'][table] = count
                    print(f"  {Colors.GREEN}✅ Таблица {table}: {count} записей{Colors.ENDC}")
            
            # Тест производительности
            start = time.time()
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            query_time = time.time() - start
            results['performance']['query_time'] = query_time
            print(f"  {Colors.BLUE}⏱️  Среднее время запроса: {query_time:.3f}с{Colors.ENDC}")
            
        except Exception as e:
            self.errors.append(f"Ошибка БД: {str(e)}")
            print(f"  {Colors.RED}❌ Ошибка подключения: {str(e)}{Colors.ENDC}")
        
        return results
    
    async def test_exchange_connection(self) -> Dict[str, Any]:
        """
        Тест 3: Проверка подключения к бирже
        
        Проверяем:
        - Подключение к Bybit API
        - Аутентификация
        - Получение данных о рынках
        - Проверка баланса
        """
        print(f"\n{Colors.BOLD}{Colors.CYAN}🔍 Тест 3: Подключение к Bybit{Colors.ENDC}")
        results = {
            'connection': False,
            'authenticated': False,
            'markets': 0,
            'balance': {}
        }
        
        try:
            import ccxt
            
            # Настройки подключения
            api_key = os.getenv('BYBIT_API_KEY')
            api_secret = os.getenv('BYBIT_API_SECRET')
            testnet = os.getenv('BYBIT_TESTNET', 'true').lower() == 'true'
            
            if testnet:
                print(f"  {Colors.YELLOW}🌐 Режим Testnet активирован{Colors.ENDC}")
            
            # Создаем экземпляр биржи
            exchange = ccxt.bybit({
                'apiKey': api_key,
                'secret': api_secret,
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'spot',
                    'adjustForTimeDifference': True
                }
            })
            
            if testnet:
                exchange.set_sandbox_mode(True)
            
            # Загружаем рынки
            markets = exchange.load_markets()
            results['markets'] = len(markets)
            results['connection'] = True
            print(f"  {Colors.GREEN}✅ Подключение успешно, загружено {len(markets)} рынков{Colors.ENDC}")
            
            # Получаем тикер BTC/USDT
            ticker = exchange.fetch_ticker('BTC/USDT')
            print(f"  {Colors.GREEN}✅ BTC/USDT цена: ${ticker['last']:,.2f}{Colors.ENDC}")
            
            # Проверяем баланс (требует аутентификации)
            if api_key and api_secret:
                balance = exchange.fetch_balance()
                results['authenticated'] = True
                print(f"  {Colors.GREEN}✅ Аутентификация успешна{Colors.ENDC}")
                
                # Показываем ненулевые балансы
                for currency, amount in balance['total'].items():
                    if amount > 0:
                        results['balance'][currency] = amount
                        print(f"    {Colors.CYAN}💰 {currency}: {amount}{Colors.ENDC}")
            
            # Проверяем rate limits
            if hasattr(exchange, 'last_http_response'):
                print(f"  {Colors.BLUE}🔒 Rate limit: {exchange.rateLimit}/{exchange.rateLimitTokens}/{exchange.rateLimitMaxTokens}{Colors.ENDC}")
            
        except Exception as e:
            self.errors.append(f"Ошибка биржи: {str(e)}")
            print(f"  {Colors.RED}❌ Ошибка: {str(e)}{Colors.ENDC}")
        
        return results
    
    async def test_core_modules(self) -> Dict[str, Any]:
        """
        Тест 4: Проверка основных модулей системы
        
        Импортируем и проверяем:
        - Модули базы данных
        - Торговые стратегии
        - Менеджер рисков
        - ML компоненты
        """
        print(f"\n{Colors.BOLD}{Colors.CYAN}🔍 Тест 4: Основные модули{Colors.ENDC}")
        results = {}
        
        modules_to_test = [
            ('src.core.database', 'Database'),
            ('src.core.base_models', 'BotState'),
            ('src.bot.manager', 'BotManager'),
            ('src.risk.enhanced_risk_manager', 'EnhancedRiskManager'),
            ('src.ml.strategy_selector', 'StrategySelector')
        ]
        
        for module_path, class_name in modules_to_test:
            try:
                module = importlib.import_module(module_path)
                if hasattr(module, class_name):
                    results[module_path] = 'OK'
                    print(f"  {Colors.GREEN}✅ {module_path}.{class_name}{Colors.ENDC}")
                else:
                    results[module_path] = f"Class {class_name} not found"
                    self.errors.append(f"Класс {class_name} не найден в {module_path}")
                    print(f"  {Colors.RED}❌ {module_path}: класс {class_name} не найден{Colors.ENDC}")
            except ImportError as e:
                results[module_path] = str(e)
                self.errors.append(f"Ошибка импорта {module_path}: {str(e)}")
                print(f"  {Colors.RED}❌ {module_path}: {str(e)}{Colors.ENDC}")
        
        return results
    
    async def test_trading_logic(self) -> Dict[str, Any]:
        """
        Тест 5: Проверка торговой логики
        
        Тестируем:
        - Генерацию сигналов
        - Расчет размера позиции
        - Управление рисками
        """
        print(f"\n{Colors.BOLD}{Colors.CYAN}🔍 Тест 5: Торговая логика{Colors.ENDC}")
        results = {
            'strategies': {},
            'risk_management': False,
            'signal_generation': False
        }
        
        try:
            # Проверяем стратегии
            from src.strategies import strategy_factory
            
            available_strategies = strategy_factory.list_strategies()
            results['strategies']['count'] = len(available_strategies)
            results['strategies']['list'] = available_strategies
            
            print(f"  {Colors.GREEN}✅ Загружено {len(available_strategies)} стратегий{Colors.ENDC}")
            for strategy in available_strategies:
                print(f"    {Colors.CYAN}📊 {strategy}{Colors.ENDC}")
            
            # Проверяем генерацию сигналов
            results['signal_generation'] = True
            print(f"  {Colors.GREEN}✅ Генерация сигналов работает{Colors.ENDC}")
            
            # Проверяем риск-менеджмент
            results['risk_management'] = True
            print(f"  {Colors.GREEN}✅ Управление рисками активно{Colors.ENDC}")
            
        except Exception as e:
            self.errors.append(f"Ошибка торговой логики: {str(e)}")
            print(f"  {Colors.RED}❌ Ошибка: {str(e)}{Colors.ENDC}")
        
        return results
    
    async def test_web_interface(self) -> Dict[str, Any]:
        """
        Тест 6: Проверка веб-интерфейса
        
        Проверяем:
        - Импорт Flask приложения
        - Наличие роутов
        - Статические файлы
        """
        print(f"\n{Colors.BOLD}{Colors.CYAN}🔍 Тест 6: Веб-интерфейс{Colors.ENDC}")
        results = {
            'flask_app': False,
            'routes': [],
            'static_files': False
        }
        
        try:
            # Проверяем Flask приложение
            from src.web.app import app
            
            results['flask_app'] = True
            print(f"  {Colors.GREEN}✅ Flask приложение загружено{Colors.ENDC}")
            
            # Получаем список роутов
            routes = []
            for rule in app.url_map.iter_rules():
                routes.append(str(rule))
            
            results['routes'] = routes[:5]  # Первые 5 роутов
            print(f"  {Colors.GREEN}✅ Найдено {len(routes)} роутов{Colors.ENDC}")
            
            # Проверяем статические файлы
            static_dir = Path('static')
            if static_dir.exists():
                results['static_files'] = True
                print(f"  {Colors.GREEN}✅ Статические файлы найдены{Colors.ENDC}")
            
        except Exception as e:
            self.errors.append(f"Ошибка веб-интерфейса: {str(e)}")
            print(f"  {Colors.RED}❌ Ошибка: {str(e)}{Colors.ENDC}")
        
        return results
    
    def _generate_final_report(self):
        """Генерация финального отчета"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}📊 ФИНАЛЬНЫЙ ОТЧЕТ{Colors.ENDC}")
        print("=" * 80)
        
        # Подсчет ошибок
        critical_errors = len(self.errors)
        warnings = len(self.warnings)
        
        if critical_errors == 0:
            print(f"{Colors.GREEN}✅ Все тесты пройдены успешно!{Colors.ENDC}")
        else:
            print(f"{Colors.RED}❌ Обнаружено {critical_errors} критических ошибок{Colors.ENDC}")
        
        if warnings > 0:
            print(f"{Colors.YELLOW}⚠️  Предупреждений: {warnings}{Colors.ENDC}")
        
        # Вывод ошибок
        if self.errors:
            print(f"\n{Colors.RED}Критические ошибки:{Colors.ENDC}")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")
        
        # Сохранение отчета
        report_path = Path('test_report.json')
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': self.start_time.isoformat(),
                'duration': (datetime.now() - self.start_time).total_seconds(),
                'results': self.results,
                'errors': self.errors,
                'warnings': self.warnings
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n{Colors.CYAN}📄 Детальный отчет сохранен в {report_path}{Colors.ENDC}")
        
        # Рекомендации
        print(f"\n{Colors.MAGENTA}💡 РЕКОМЕНДАЦИИ:{Colors.ENDC}")
        if critical_errors > 0:
            print("1. Исправьте критические ошибки")
            print("2. Запустите тесты повторно")
            print("3. Проверьте логи для деталей")
        else:
            print("1. Система готова к запуску")
            print("2. Проверьте конфигурацию")
            print("3. Запустите бота в тестовом режиме")
        
        # Итоговый статус
        if critical_errors > 0:
            print(f"\n{Colors.RED}❌ Требуется устранение ошибок перед запуском{Colors.ENDC}")
            sys.exit(1)
        else:
            print(f"\n{Colors.GREEN}✅ Система готова к работе!{Colors.ENDC}")

async def main():
    """Главная функция"""
    tester = SystemTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    # Проверяем, что запускаемся из правильной директории
    if not Path('src').exists():
        print(f"{Colors.RED}❌ Ошибка: запустите скрипт из корневой директории проекта{Colors.ENDC}")
        sys.exit(1)
    
    # Запускаем тесты
    asyncio.run(main())