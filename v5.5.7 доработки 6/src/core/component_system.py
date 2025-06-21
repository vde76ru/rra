#!/usr/bin/env python3
"""
Система управления компонентами бота
Файл: src/core/component_system.py

Этот модуль отвечает за правильную инициализацию всех компонентов системы
с учетом зависимостей и обработкой ошибок.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Callable, Set, Tuple
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

class ComponentStatus(Enum):
    """Статусы компонентов"""
    NOT_INITIALIZED = "not_initialized"
    INITIALIZING = "initializing"
    READY = "ready"
    FAILED = "failed"
    DISABLED = "disabled"

@dataclass
class ComponentInfo:
    """Информация о компоненте"""
    name: str
    status: ComponentStatus
    instance: Any = None
    error: Optional[str] = None
    dependencies: List[str] = None
    is_critical: bool = False
    retry_count: int = 0
    max_retries: int = 3
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []

class ComponentManager:
    """
    Менеджер компонентов для системы бота
    
    Обеспечивает:
    - Правильный порядок инициализации
    - Обработку зависимостей
    - Graceful degradation при ошибках
    - Возможность перезапуска компонентов
    """
    
    def __init__(self):
        self.components: Dict[str, ComponentInfo] = {}
        self.initialization_order: List[str] = []
        self._lock = asyncio.Lock()
        
    def register_component(
        self,
        name: str,
        initializer: Callable,
        dependencies: List[str] = None,
        is_critical: bool = False,
        max_retries: int = 3
    ):
        """
        Регистрация компонента
        
        Args:
            name: Имя компонента
            initializer: Функция инициализации
            dependencies: Список зависимостей
            is_critical: Критичность компонента
            max_retries: Максимальное количество попыток
        """
        if dependencies is None:
            dependencies = []
            
        self.components[name] = ComponentInfo(
            name=name,
            status=ComponentStatus.NOT_INITIALIZED,
            dependencies=dependencies,
            is_critical=is_critical,
            max_retries=max_retries
        )
        
        # Сохраняем функцию инициализации
        setattr(self, f"_init_{name}", initializer)
        
        logger.debug(f"📝 Зарегистрирован компонент: {name}")
    
    def _resolve_dependencies(self) -> List[str]:
        """
        Определение правильного порядка инициализации
        
        Returns:
            List[str]: Порядок инициализации компонентов
        """
        # Топологическая сортировка для разрешения зависимостей
        visited = set()
        temp_visited = set()
        order = []
        
        def visit(component_name: str):
            if component_name in temp_visited:
                raise ValueError(f"Циклическая зависимость обнаружена: {component_name}")
            
            if component_name not in visited:
                temp_visited.add(component_name)
                
                component = self.components.get(component_name)
                if component:
                    for dep in component.dependencies:
                        if dep in self.components:
                            visit(dep)
                
                temp_visited.remove(component_name)
                visited.add(component_name)
                order.append(component_name)
        
        # Посещаем все компоненты
        for component_name in self.components:
            if component_name not in visited:
                visit(component_name)
        
        return order
    
    async def initialize_all(self) -> Dict[str, bool]:
        """
        Инициализация всех компонентов в правильном порядке
        
        Returns:
            Dict[str, bool]: Результат инициализации каждого компонента
        """
        async with self._lock:
            logger.info("🚀 Начинаем инициализацию всех компонентов...")
            
            # Определяем порядок инициализации
            try:
                self.initialization_order = self._resolve_dependencies()
                logger.info(f"📋 Порядок инициализации: {self.initialization_order}")
            except ValueError as e:
                logger.error(f"❌ Ошибка разрешения зависимостей: {e}")
                return {}
            
            results = {}
            
            # Инициализируем компоненты по порядку
            for component_name in self.initialization_order:
                result = await self._initialize_component(component_name)
                results[component_name] = result
                
                # Если критичный компонент не инициализировался, останавливаемся
                component = self.components[component_name]
                if component.is_critical and not result:
                    logger.error(f"❌ Критичный компонент {component_name} не инициализирован")
                    break
            
            # Выводим итоговую статистику
            self._log_initialization_summary(results)
            return results
    
    async def _initialize_component(self, name: str) -> bool:
        """
        Инициализация конкретного компонента
        
        Args:
            name: Имя компонента
            
        Returns:
            bool: Успешность инициализации
        """
        component = self.components.get(name)
        if not component:
            logger.error(f"❌ Компонент {name} не найден")
            return False
        
        # Проверяем зависимости
        for dep in component.dependencies:
            dep_component = self.components.get(dep)
            if not dep_component or dep_component.status != ComponentStatus.READY:
                logger.error(f"❌ Зависимость {dep} для {name} не готова")
                component.status = ComponentStatus.FAILED
                component.error = f"Dependency {dep} not ready"
                return False
        
        # Пытаемся инициализировать
        for attempt in range(component.max_retries):
            try:
                logger.info(f"🔧 Инициализируем {name} (попытка {attempt + 1}/{component.max_retries})")
                component.status = ComponentStatus.INITIALIZING
                
                # Получаем функцию инициализации
                initializer = getattr(self, f"_init_{name}", None)
                if not initializer:
                    raise AttributeError(f"Initializer for {name} not found")
                
                # Выполняем инициализацию
                if asyncio.iscoroutinefunction(initializer):
                    instance = await initializer()
                else:
                    instance = initializer()
                
                # Успешная инициализация
                component.instance = instance
                component.status = ComponentStatus.READY
                component.error = None
                component.retry_count = attempt + 1
                
                logger.info(f"✅ Компонент {name} инициализирован успешно")
                return True
                
            except Exception as e:
                error_msg = f"Ошибка инициализации {name}: {str(e)}"
                logger.warning(f"⚠️ {error_msg}")
                component.error = error_msg
                component.retry_count = attempt + 1
                
                # Если это последняя попытка
                if attempt == component.max_retries - 1:
                    component.status = ComponentStatus.FAILED
                    logger.error(f"❌ Компонент {name} не удалось инициализировать после {component.max_retries} попыток")
                    return False
                
                # Ждем перед следующей попыткой
                await asyncio.sleep(1)
        
        return False
    
    def get_component(self, name: str) -> Any:
        """
        Получение экземпляра компонента
        
        Args:
            name: Имя компонента
            
        Returns:
            Any: Экземпляр компонента или None
        """
        component = self.components.get(name)
        if component and component.status == ComponentStatus.READY:
            return component.instance
        return None
    
    def get_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Получение статуса всех компонентов
        
        Returns:
            Dict: Статус каждого компонента
        """
        status = {}
        for name, component in self.components.items():
            status[name] = {
                'status': component.status.value,
                'is_critical': component.is_critical,
                'dependencies': component.dependencies,
                'retry_count': component.retry_count,
                'error': component.error,
                'has_instance': component.instance is not None
            }
        return status
    
    async def restart_component(self, name: str) -> bool:
        """
        Перезапуск компонента
        
        Args:
            name: Имя компонента
            
        Returns:
            bool: Успешность перезапуска
        """
        component = self.components.get(name)
        if not component:
            return False
        
        logger.info(f"🔄 Перезапускаем компонент: {name}")
        
        # Сбрасываем состояние
        component.status = ComponentStatus.NOT_INITIALIZED
        component.instance = None
        component.error = None
        component.retry_count = 0
        
        # Инициализируем заново
        return await self._initialize_component(name)
    
    def _log_initialization_summary(self, results: Dict[str, bool]):
        """
        Вывод итоговой статистики инициализации
        
        Args:
            results: Результаты инициализации
        """
        total = len(results)
        success = sum(1 for r in results.values() if r)
        failed = total - success
        
        logger.info("=" * 50)
        logger.info("📊 ИТОГИ ИНИЦИАЛИЗАЦИИ КОМПОНЕНТОВ")
        logger.info("=" * 50)
        logger.info(f"📈 Всего компонентов: {total}")
        logger.info(f"✅ Успешно: {success}")
        logger.info(f"❌ Не удалось: {failed}")
        logger.info("=" * 50)
        
        # Детальная информация
        for name, success in results.items():
            component = self.components[name]
            status_icon = "✅" if success else "❌"
            critical_icon = "🔥" if component.is_critical else "📦"
            
            logger.info(f"{status_icon} {critical_icon} {name}")
            if not success and component.error:
                logger.info(f"    └─ Ошибка: {component.error}")
        
        logger.info("=" * 50)
        
    def is_ready(self, component_name: str) -> bool:
        """
        Проверка готовности компонента к работе
        
        Метод проверяет, что компонент:
        1. Зарегистрирован в системе
        2. Имеет статус READY
        3. Успешно инициализирован
        
        Args:
            component_name (str): Имя компонента для проверки
            
        Returns:
            bool: True если компонент готов к работе, False в противном случае
            
        Raises:
            None: Метод никогда не вызывает исключения для обеспечения стабильности
            
        Example:
            >>> component_manager.is_ready('exchange')
            True
            >>> component_manager.is_ready('non_existent')
            False
        """
        try:
            # Проверка существования компонента
            if component_name not in self.components:
                logger.warning(f"⚠️ Компонент '{component_name}' не зарегистрирован в системе")
                return False
            
            # Получение информации о компоненте
            component_info = self.components[component_name]
            
            # Проверка статуса
            is_component_ready = component_info.status == ComponentStatus.READY
            
            # Дополнительная проверка критичности
            if not is_component_ready and component_info.is_critical:
                logger.error(f"❌ Критичный компонент '{component_name}' не готов. "
                            f"Статус: {component_info.status.value}")
            elif not is_component_ready:
                logger.warning(f"⚠️ Компонент '{component_name}' не готов. "
                             f"Статус: {component_info.status.value}")
            else:
                logger.debug(f"✅ Компонент '{component_name}' готов к работе")
            
            return is_component_ready
            
        except Exception as e:
            logger.error(f"❌ Ошибка при проверке компонента '{component_name}': {str(e)}")
            return False
    
    def get_component_status(self, component_name: str) -> Optional[ComponentStatus]:
        """
        Получение текущего статуса конкретного компонента
        
        Args:
            component_name (str): Имя компонента
            
        Returns:
            Optional[ComponentStatus]: Статус компонента или None если не найден
        """
        if component_name not in self.components:
            logger.debug(f"🔍 Компонент '{component_name}' не найден")
            return None
        
        return self.components[component_name].status
    
    def get_ready_components(self) -> List[str]:
        """
        Получение списка всех готовых компонентов
        
        Returns:
            List[str]: Список имен компонентов со статусом READY
        """
        ready_components = []
        for name, component in self.components.items():
            if component.status == ComponentStatus.READY:
                ready_components.append(name)
        
        return ready_components
    
    def get_failed_components(self) -> List[str]:
        """
        Получение списка всех проблемных компонентов
        
        Returns:
            List[str]: Список имен компонентов со статусом FAILED
        """
        failed_components = []
        for name, component in self.components.items():
            if component.status == ComponentStatus.FAILED:
                failed_components.append(name)
        
        return failed_components
    
    def validate_critical_components(self) -> Tuple[bool, List[str]]:
        """
        Проверка готовности всех критичных компонентов
        
        Returns:
            Tuple[bool, List[str]]: (Все ли критичные готовы, Список неготовых критичных)
        """
        critical_not_ready = []
        
        for name, component in self.components.items():
            if component.is_critical and component.status != ComponentStatus.READY:
                critical_not_ready.append(name)
        
        all_critical_ready = len(critical_not_ready) == 0
        
        if not all_critical_ready:
            logger.error(f"❌ Критичные компоненты не готовы: {critical_not_ready}")
        else:
            logger.info("✅ Все критичные компоненты готовы")
        
        return all_critical_ready, critical_not_ready

# Глобальный менеджер компонентов
component_manager = ComponentManager()