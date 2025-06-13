"""
Миксин для имитации человеческого поведения
Путь: /var/www/www-root/data/www/systemetech.ru/src/exchange/humanizer.py
"""
import random
import asyncio
import logging
from datetime import datetime, timedelta

from ..core.config import config

logger = logging.getLogger(__name__)

class HumanBehaviorMixin:
    """
    Поведение для имитации человека
    Делает торговлю более естественной
    """
    
    def _init_human_behavior(self):
        """Инициализация параметров поведения"""
        self.last_action_time = datetime.now()
        self.actions_count = 0
        self.session_start = datetime.now()
        
        # Персональные характеристики "трейдера"
        self.typing_speed = random.uniform(0.8, 1.2)  # Скорость "печати"
        self.reaction_time = random.uniform(0.5, 2.0)  # Время реакции
        self.fatigue_factor = 0  # Усталость
        self.mistake_probability = random.uniform(0.01, 0.03)  # Вероятность ошибок
        
        # Паттерны поведения
        self.favorite_numbers = [10, 50, 100, 500, 1000]  # Любимые круглые числа
        self.working_hours = self._generate_working_hours()
        
        logger.debug(f"🧑 Инициализированы параметры человека: скорость={self.typing_speed:.2f}, реакция={self.reaction_time:.2f}")
    
    def _generate_working_hours(self) -> tuple:
        """Генерация рабочих часов трейдера"""
        # Утренний трейдер, дневной или ночной
        trader_type = random.choice(['morning', 'day', 'night'])
        
        if trader_type == 'morning':
            return (6, 12)  # 6:00 - 12:00
        elif trader_type == 'day':
            return (9, 18)  # 9:00 - 18:00
        else:
            return (20, 2)  # 20:00 - 02:00
        
    async def human_delay(self):
        """Базовая человеческая задержка"""
        if not config.ENABLE_HUMAN_MODE:
            return
            
        base_delay = random.uniform(config.MIN_DELAY_SECONDS, config.MAX_DELAY_SECONDS)
        
        # Учитываем усталость
        fatigue_multiplier = 1 + (self.fatigue_factor * 0.5)
        delay = base_delay * fatigue_multiplier * self.reaction_time
        
        # Учитываем время суток
        current_hour = datetime.now().hour
        if not (self.working_hours[0] <= current_hour <= self.working_hours[1]):
            # Вне рабочих часов работаем медленнее
            delay *= random.uniform(1.5, 2.0)
        
        # Иногда "отвлекаемся"
        if random.random() < 0.05:  # 5% шанс
            delay += random.uniform(5, 15)
            logger.debug(f"💭 Отвлеклись на {delay:.1f} секунд")
        
        await asyncio.sleep(delay)
        
        # Обновляем параметры
        self._update_fatigue()
    
    async def think_before_action(self):
        """Имитация размышлений перед действием"""
        if not config.ENABLE_HUMAN_MODE:
            return
            
        # Базовое время на раздумья
        think_time = random.uniform(2, 8)
        
        # Иногда думаем дольше (сложное решение)
        if random.random() < 0.15:  # 15% шанс
            think_time = random.uniform(10, 30)
            logger.debug(f"🤔 Долгие раздумья: {think_time:.1f} сек")
        
        # С опытом думаем быстрее
        if self.actions_count > 50:
            think_time *= 0.7
        
        await asyncio.sleep(think_time)
    
    async def micro_delay(self):
        """Микро-задержки между действиями"""
        if not config.ENABLE_HUMAN_MODE:
            return
            
        # Имитация времени на клик мышкой, движение и т.д.
        delay = random.uniform(0.1, 0.5) * self.typing_speed
        
        # Иногда "промахиваемся" и повторяем действие
        if random.random() < 0.02:  # 2% шанс
            delay += random.uniform(0.5, 1.0)
            logger.debug("🖱️ Промахнулись мышкой")
        
        await asyncio.sleep(delay)
    
    def humanize_amount(self, amount: float) -> float:
        """Округление суммы как человек"""
        if not config.ENABLE_HUMAN_MODE:
            return amount
            
        # Люди любят круглые числа
        if random.random() < 0.3:  # 30% шанс использовать круглое число
            # Находим ближайшее любимое число
            for fav_num in self.favorite_numbers:
                if amount * 0.8 <= fav_num <= amount * 1.2:
                    return float(fav_num)
        
        # Обычное человеческое округление
        if amount > 1000:
            # Округляем до сотен
            return round(amount, -2)
        elif amount > 100:
            # Округляем до десятков
            return round(amount, -1)
        elif amount > 10:
            # Округляем до целых
            return round(amount, 0)
        elif amount > 1:
            # Округляем до одного знака
            return round(amount, 1)
        else:
            # Для мелких сумм - до 2-3 знаков
            return round(amount, random.choice([2, 3]))
    
    def should_hesitate(self) -> bool:
        """Должны ли мы засомневаться"""
        if not config.ENABLE_HUMAN_MODE:
            return False
            
        # Базовый шанс сомнений
        hesitation_chance = 0.02  # 2%
        
        # Увеличиваем при усталости
        hesitation_chance += self.fatigue_factor * 0.03
        
        # Уменьшаем с опытом (количество действий)
        if self.actions_count > 50:
            hesitation_chance *= 0.5
        
        # В стрессовых ситуациях (много действий подряд) сомневаемся чаще
        time_since_last = (datetime.now() - self.last_action_time).total_seconds()
        if time_since_last < 10:  # Меньше 10 секунд с прошлого действия
            hesitation_chance *= 2
        
        return random.random() < hesitation_chance
    
    def _update_fatigue(self):
        """Обновление усталости"""
        session_duration = (datetime.now() - self.session_start).total_seconds() / 3600
        
        # Усталость растет со временем
        self.fatigue_factor = min(1.0, session_duration / 8)  # Макс усталость через 8 часов
        
        # Сбрасываем усталость после "перерыва"
        if (datetime.now() - self.last_action_time).total_seconds() > 1800:  # 30 минут
            self.fatigue_factor *= 0.3
            logger.debug("😌 Усталость снижена после перерыва")
        
        self.last_action_time = datetime.now()
        self.actions_count += 1
        
        # Каждые 20 действий немного меняем характеристики (человек адаптируется)
        if self.actions_count % 20 == 0:
            self.reaction_time *= random.uniform(0.9, 1.1)
            self.typing_speed *= random.uniform(0.95, 1.05)