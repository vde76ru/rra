"""Миксин для имитации человеческого поведения"""
import random
import asyncio
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class HumanBehaviorMixin:
    """Поведение для имитации человека"""
    
    def _init_human_behavior(self):
        """Инициализация параметров поведения"""
        self.last_action_time = datetime.now()
        self.actions_count = 0
        self.session_start = datetime.now()
        
        # Персональные характеристики "трейдера"
        self.typing_speed = random.uniform(0.8, 1.2)  # Скорость "печати"
        self.reaction_time = random.uniform(0.5, 2.0)  # Время реакции
        self.fatigue_factor = 0  # Усталость
    
    async def human_delay(self):
        """Базовая человеческая задержка"""
        base_delay = random.uniform(0.5, 3.0)
        
        # Учитываем усталость
        fatigue_multiplier = 1 + (self.fatigue_factor * 0.5)
        delay = base_delay * fatigue_multiplier * self.reaction_time
        
        await asyncio.sleep(delay)
        
        # Увеличиваем усталость
        self._update_fatigue()
    
    async def think_before_action(self):
        """Имитация размышлений перед действием"""
        # Базовое время на раздумья
        think_time = random.uniform(2, 8)
        
        # Иногда думаем дольше (сложное решение)
        if random.random() < 0.15:  # 15% шанс
            think_time = random.uniform(10, 30)
            logger.debug(f"Долгие раздумья: {think_time:.1f} сек")
        
        await asyncio.sleep(think_time)
    
    async def micro_delay(self):
        """Микро-задержки между действиями"""
        # Имитация времени на клик мышкой, движение и т.д.
        delay = random.uniform(0.1, 0.5) * self.typing_speed
        await asyncio.sleep(delay)
    
    def humanize_amount(self, amount: float) -> float:
        """Округление суммы как человек"""
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
        # Базовый шанс сомнений
        hesitation_chance = 0.02  # 2%
        
        # Увеличиваем при усталости
        hesitation_chance += self.fatigue_factor * 0.03
        
        # Уменьшаем с опытом (количество действий)
        if self.actions_count > 50:
            hesitation_chance *= 0.5
        
        return random.random() < hesitation_chance
    
    def _update_fatigue(self):
        """Обновление усталости"""
        session_duration = (datetime.now() - self.session_start).total_seconds() / 3600
        
        # Усталость растет со временем
        self.fatigue_factor = min(1.0, session_duration / 8)  # Макс усталость через 8 часов
        
        # Сбрасываем усталость после "перерыва"
        if (datetime.now() - self.last_action_time).total_seconds() > 1800:  # 30 минут
            self.fatigue_factor *= 0.3
            logger.debug("Усталость снижена после перерыва")
        
        self.last_action_time = datetime.now()
        self.actions_count += 1