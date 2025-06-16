"""
Reinforcement Learning Agent для адаптивной торговли
Файл: src/ml/models/reinforcement.py
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any, Union
from collections import deque
from datetime import datetime
import random
import json

import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torch.distributions import Categorical

from ...logging.smart_logger import SmartLogger
from ...core.database import SessionLocal


class TradingEnvironment:
    """
    Среда для обучения RL агента
    """
    
    def __init__(self, market_data: pd.DataFrame, initial_balance: float = 10000):
        self.market_data = market_data
        self.initial_balance = initial_balance
        self.reset()
        
    def reset(self) -> np.ndarray:
        """Сброс среды в начальное состояние"""
        self.current_step = 0
        self.balance = self.initial_balance
        self.position = 0  # 0 - нет позиции, 1 - long, -1 - short
        self.entry_price = 0
        self.trades_history = []
        self.done = False
        
        return self._get_state()
    
    def _get_state(self) -> np.ndarray:
        """Получает текущее состояние среды"""
        if self.current_step >= len(self.market_data) - 1:
            return np.zeros(50)  # Пустое состояние
        
        # Берем последние 20 свечей
        window = 20
        start_idx = max(0, self.current_step - window + 1)
        end_idx = self.current_step + 1
        
        price_data = self.market_data.iloc[start_idx:end_idx]
        
        # Признаки состояния
        features = []
        
        # Нормализованные цены
        current_price = price_data.iloc[-1]['close']
        features.extend([
            (price_data['close'].iloc[-1] - price_data['close'].mean()) / price_data['close'].std(),
            (price_data['high'].iloc[-1] - price_data['high'].mean()) / price_data['high'].std(),
            (price_data['low'].iloc[-1] - price_data['low'].mean()) / price_data['low'].std(),
            (price_data['volume'].iloc[-1] - price_data['volume'].mean()) / (price_data['volume'].std() + 1e-8)
        ])
        
        # Технические индикаторы (если есть)
        if 'rsi' in price_data.columns:
            features.append((price_data['rsi'].iloc[-1] - 50) / 50)
        else:
            features.append(0)
            
        if 'macd' in price_data.columns:
            features.append(price_data['macd'].iloc[-1] / current_price)
        else:
            features.append(0)
        
        # Информация о позиции
        features.extend([
            self.position,  # Текущая позиция
            (self.balance - self.initial_balance) / self.initial_balance,  # Нормализованная прибыль
            (current_price - self.entry_price) / current_price if self.position != 0 else 0  # Текущий P&L
        ])
        
        # Паттерны цены
        returns = price_data['close'].pct_change().fillna(0)
        features.extend([
            returns.mean() * 100,
            returns.std() * 100,
            returns.iloc[-1] * 100
        ])
        
        # Дополняем до нужного размера
        while len(features) < 50:
            features.append(0)
        
        return np.array(features[:50], dtype=np.float32)
    
    def step(self, action: int) -> Tuple[np.ndarray, float, bool, Dict]:
        """
        Выполняет действие в среде
        
        Args:
            action: 0 - hold, 1 - buy, 2 - sell
            
        Returns:
            state: Новое состояние
            reward: Награда
            done: Завершен ли эпизод
            info: Дополнительная информация
        """
        if self.done:
            return self._get_state(), 0, True, {}
        
        current_price = self.market_data.iloc[self.current_step]['close']
        reward = 0
        info = {}
        
        # Выполняем действие
        if action == 1 and self.position <= 0:  # Buy
            if self.position == -1:  # Закрываем short
                profit = (self.entry_price - current_price) * abs(self.position)
                self.balance += profit
                reward += profit / self.initial_balance * 100
                
            self.position = 1
            self.entry_price = current_price
            info['action'] = 'buy'
            
        elif action == 2 and self.position >= 0:  # Sell
            if self.position == 1:  # Закрываем long
                profit = (current_price - self.entry_price) * self.position
                self.balance += profit
                reward += profit / self.initial_balance * 100
                
            self.position = -1
            self.entry_price = current_price
            info['action'] = 'sell'
            
        else:  # Hold
            if self.position != 0:
                # Награда за удержание прибыльной позиции
                unrealized_pnl = (current_price - self.entry_price) * self.position
                reward += unrealized_pnl / self.initial_balance * 10  # Меньше, чем за закрытие
            info['action'] = 'hold'
        
        # Штраф за большую просадку
        drawdown = (self.balance - self.initial_balance) / self.initial_balance
        if drawdown < -0.1:  # Более 10% убытка
            reward -= abs(drawdown) * 10
        
        # Переход к следующему шагу
        self.current_step += 1
        
        # Проверка завершения
        if self.current_step >= len(self.market_data) - 1:
            self.done = True
            # Закрываем открытую позицию
            if self.position != 0:
                final_price = self.market_data.iloc[-1]['close']
                final_pnl = (final_price - self.entry_price) * self.position
                self.balance += final_pnl
                reward += final_pnl / self.initial_balance * 100
        
        # Банкротство
        if self.balance <= self.initial_balance * 0.5:
            self.done = True
            reward -= 100  # Большой штраф за банкротство
        
        new_state = self._get_state()
        info['balance'] = self.balance
        info['position'] = self.position
        
        return new_state, reward, self.done, info


class DQNNetwork(nn.Module):
    """
    Deep Q-Network для оценки ценности действий
    """
    
    def __init__(self, state_size: int, action_size: int, hidden_size: int = 256):
        super(DQNNetwork, self).__init__()
        
        self.fc1 = nn.Linear(state_size, hidden_size)
        self.fc2 = nn.Linear(hidden_size, hidden_size)
        self.fc3 = nn.Linear(hidden_size, hidden_size // 2)
        self.fc4 = nn.Linear(hidden_size // 2, action_size)
        
        self.dropout = nn.Dropout(0.2)
        
    def forward(self, x):
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        x = F.relu(self.fc2(x))
        x = self.dropout(x)
        x = F.relu(self.fc3(x))
        x = self.fc4(x)
        return x


class PPOActor(nn.Module):
    """
    Actor network для PPO (Proximal Policy Optimization)
    """
    
    def __init__(self, state_size: int, action_size: int, hidden_size: int = 256):
        super(PPOActor, self).__init__()
        
        self.fc1 = nn.Linear(state_size, hidden_size)
        self.fc2 = nn.Linear(hidden_size, hidden_size)
        self.fc3 = nn.Linear(hidden_size, action_size)
        
    def forward(self, x):
        x = torch.tanh(self.fc1(x))
        x = torch.tanh(self.fc2(x))
        x = self.fc3(x)
        return F.softmax(x, dim=-1)


class PPOCritic(nn.Module):
    """
    Critic network для PPO
    """
    
    def __init__(self, state_size: int, hidden_size: int = 256):
        super(PPOCritic, self).__init__()
        
        self.fc1 = nn.Linear(state_size, hidden_size)
        self.fc2 = nn.Linear(hidden_size, hidden_size)
        self.fc3 = nn.Linear(hidden_size, 1)
        
    def forward(self, x):
        x = torch.tanh(self.fc1(x))
        x = torch.tanh(self.fc2(x))
        x = self.fc3(x)
        return x


class ReinforcementTradingAgent:
    """
    RL агент для адаптивной торговли
    """
    
    def __init__(self, state_size: int = 50, action_size: int = 3, 
                 algorithm: str = 'DQN', learning_rate: float = 0.001):
        self.state_size = state_size
        self.action_size = action_size
        self.algorithm = algorithm
        self.learning_rate = learning_rate
        
        # Инициализация сетей
        if algorithm == 'DQN':
            self.q_network = DQNNetwork(state_size, action_size)
            self.target_network = DQNNetwork(state_size, action_size)
            self.optimizer = optim.Adam(self.q_network.parameters(), lr=learning_rate)
            
            # Replay buffer
            self.memory = deque(maxlen=10000)
            self.batch_size = 32
            self.gamma = 0.99
            self.epsilon = 1.0
            self.epsilon_decay = 0.995
            self.epsilon_min = 0.01
            
        elif algorithm == 'PPO':
            self.actor = PPOActor(state_size, action_size)
            self.critic = PPOCritic(state_size)
            self.actor_optimizer = optim.Adam(self.actor.parameters(), lr=learning_rate)
            self.critic_optimizer = optim.Adam(self.critic.parameters(), lr=learning_rate * 2)
            
            # PPO параметры
            self.clip_param = 0.2
            self.ppo_epochs = 10
            self.value_loss_coef = 0.5
            self.entropy_coef = 0.01
            
        self.logger = SmartLogger(__name__)
        self.training_history = []
    
    def act(self, state: np.ndarray, training: bool = True) -> int:
        """
        Выбирает действие на основе текущего состояния
        
        Args:
            state: Текущее состояние
            training: Режим обучения или эксплуатации
            
        Returns:
            Действие (0: hold, 1: buy, 2: sell)
        """
        state_tensor = torch.FloatTensor(state).unsqueeze(0)
        
        if self.algorithm == 'DQN':
            # Epsilon-greedy policy
            if training and random.random() <= self.epsilon:
                return random.randint(0, self.action_size - 1)
            
            with torch.no_grad():
                q_values = self.q_network(state_tensor)
                return np.argmax(q_values.cpu().data.numpy())
                
        elif self.algorithm == 'PPO':
            with torch.no_grad():
                probs = self.actor(state_tensor)
                
                if training:
                    # Сэмплируем из распределения
                    dist = Categorical(probs)
                    action = dist.sample()
                    return action.item()
                else:
                    # Выбираем наиболее вероятное действие
                    return torch.argmax(probs).item()
    
    def remember(self, state: np.ndarray, action: int, reward: float, 
                 next_state: np.ndarray, done: bool):
        """Сохраняет опыт в памяти (для DQN)"""
        if self.algorithm == 'DQN':
            self.memory.append((state, action, reward, next_state, done))
    
    def replay(self):
        """Обучение на батче из памяти (DQN)"""
        if self.algorithm != 'DQN' or len(self.memory) < self.batch_size:
            return
        
        batch = random.sample(self.memory, self.batch_size)
        states = torch.FloatTensor([e[0] for e in batch])
        actions = torch.LongTensor([e[1] for e in batch]).unsqueeze(1)
        rewards = torch.FloatTensor([e[2] for e in batch]).unsqueeze(1)
        next_states = torch.FloatTensor([e[3] for e in batch])
        dones = torch.FloatTensor([e[4] for e in batch]).unsqueeze(1)
        
        current_q_values = self.q_network(states).gather(1, actions)
        
        with torch.no_grad():
            next_q_values = self.target_network(next_states).max(1)[0].unsqueeze(1)
            target_q_values = rewards + (self.gamma * next_q_values * (1 - dones))
        
        loss = F.mse_loss(current_q_values, target_q_values)
        
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.q_network.parameters(), 1.0)
        self.optimizer.step()
        
        # Decay epsilon
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
    
    def update_target_network(self):
        """Обновляет target network (DQN)"""
        if self.algorithm == 'DQN':
            self.target_network.load_state_dict(self.q_network.state_dict())
    
    def train_ppo(self, trajectories: List[Dict]):
        """
        Обучение PPO на собранных траекториях
        
        Args:
            trajectories: Список траекторий с состояниями, действиями, наградами
        """
        if self.algorithm != 'PPO' or not trajectories:
            return
        
        # Подготовка данных
        states = torch.FloatTensor([t['state'] for t in trajectories])
        actions = torch.LongTensor([t['action'] for t in trajectories])
        rewards = torch.FloatTensor([t['reward'] for t in trajectories])
        next_states = torch.FloatTensor([t['next_state'] for t in trajectories])
        dones = torch.FloatTensor([t['done'] for t in trajectories])
        
        # Вычисляем преимущества (advantages)
        with torch.no_grad():
            values = self.critic(states).squeeze()
            next_values = self.critic(next_states).squeeze()
            
            # GAE (Generalized Advantage Estimation)
            advantages = rewards + self.gamma * next_values * (1 - dones) - values
            returns = advantages + values
        
        # Нормализация преимуществ
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
        
        # PPO обновления
        for _ in range(self.ppo_epochs):
            # Actor loss
            probs = self.actor(states)
            dist = Categorical(probs)
            new_log_probs = dist.log_prob(actions)
            
            # Сохраненные log probabilities
            with torch.no_grad():
                old_probs = self.actor(states)
                old_dist = Categorical(old_probs)
                old_log_probs = old_dist.log_prob(actions)
            
            ratio = torch.exp(new_log_probs - old_log_probs)
            
            surr1 = ratio * advantages
            surr2 = torch.clamp(ratio, 1 - self.clip_param, 1 + self.clip_param) * advantages
            
            actor_loss = -torch.min(surr1, surr2).mean()
            entropy_loss = -dist.entropy().mean()
            
            total_actor_loss = actor_loss - self.entropy_coef * entropy_loss
            
            self.actor_optimizer.zero_grad()
            total_actor_loss.backward()
            torch.nn.utils.clip_grad_norm_(self.actor.parameters(), 0.5)
            self.actor_optimizer.step()
            
            # Critic loss
            values = self.critic(states).squeeze()
            critic_loss = F.mse_loss(values, returns.detach())
            
            self.critic_optimizer.zero_grad()
            critic_loss.backward()
            torch.nn.utils.clip_grad_norm_(self.critic.parameters(), 0.5)
            self.critic_optimizer.step()
    
    def train_on_history(self, market_data: pd.DataFrame, episodes: int = 100):
        """
        Обучение агента на исторических данных
        
        Args:
            market_data: Исторические данные рынка
            episodes: Количество эпизодов обучения
        """
        env = TradingEnvironment(market_data)
        
        for episode in range(episodes):
            state = env.reset()
            total_reward = 0
            trajectories = []
            
            while not env.done:
                action = self.act(state, training=True)
                next_state, reward, done, info = env.step(action)
                
                if self.algorithm == 'DQN':
                    self.remember(state, action, reward, next_state, done)
                    if len(self.memory) > self.batch_size:
                        self.replay()
                        
                elif self.algorithm == 'PPO':
                    trajectories.append({
                        'state': state,
                        'action': action,
                        'reward': reward,
                        'next_state': next_state,
                        'done': done
                    })
                
                state = next_state
                total_reward += reward
            
            # Обучение PPO в конце эпизода
            if self.algorithm == 'PPO':
                self.train_ppo(trajectories)
            
            # Обновление target network для DQN
            if self.algorithm == 'DQN' and episode % 10 == 0:
                self.update_target_network()
            
            # Логирование
            final_balance = env.balance
            profit_percent = (final_balance - env.initial_balance) / env.initial_balance * 100
            
            self.training_history.append({
                'episode': episode,
                'total_reward': total_reward,
                'final_balance': final_balance,
                'profit_percent': profit_percent,
                'epsilon': self.epsilon if self.algorithm == 'DQN' else 0
            })
            
            if episode % 10 == 0:
                self.logger.info(
                    f"Episode {episode}: Reward={total_reward:.2f}, "
                    f"Profit={profit_percent:.2f}%",
                    category='ml',
                    algorithm=self.algorithm,
                    episode=episode
                )
    
    def predict_action(self, state: np.ndarray, market_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Предсказывает оптимальное действие с учетом контекста
        
        Args:
            state: Текущее состояние
            market_context: Дополнительный контекст рынка
            
        Returns:
            Словарь с действием и метаданными
        """
        # Базовое предсказание
        action = self.act(state, training=False)
        
        # Получаем уверенность в действии
        state_tensor = torch.FloatTensor(state).unsqueeze(0)
        
        if self.algorithm == 'DQN':
            with torch.no_grad():
                q_values = self.q_network(state_tensor).squeeze().numpy()
                confidence = float(np.max(q_values) - np.mean(q_values))
                action_values = {
                    'hold': float(q_values[0]),
                    'buy': float(q_values[1]),
                    'sell': float(q_values[2])
                }
        else:  # PPO
            with torch.no_grad():
                probs = self.actor(state_tensor).squeeze().numpy()
                confidence = float(np.max(probs))
                action_values = {
                    'hold': float(probs[0]),
                    'buy': float(probs[1]),
                    'sell': float(probs[2])
                }
        
        # Корректировка на основе контекста
        if market_context.get('high_volatility', False) and confidence < 0.7:
            # В высокой волатильности с низкой уверенностью - лучше подождать
            action = 0  # Hold
            
        if market_context.get('news_sentiment', 0) < -0.5 and action == 1:
            # Негативные новости - пересматриваем покупку
            if action_values['hold'] > action_values['buy'] * 0.8:
                action = 0  # Hold вместо buy
        
        action_map = {0: 'hold', 1: 'buy', 2: 'sell'}
        
        return {
            'action': action_map[action],
            'action_id': action,
            'confidence': confidence,
            'action_values': action_values,
            'algorithm': self.algorithm,
            'context_adjusted': market_context.get('high_volatility', False) or 
                               market_context.get('news_sentiment', 0) < -0.5
        }
    
    def save_model(self, path: str):
        """Сохраняет модель"""
        model_data = {
            'algorithm': self.algorithm,
            'state_size': self.state_size,
            'action_size': self.action_size,
            'training_history': self.training_history,
            'timestamp': datetime.now().isoformat()
        }
        
        if self.algorithm == 'DQN':
            model_data['q_network_state'] = self.q_network.state_dict()
            model_data['target_network_state'] = self.target_network.state_dict()
            model_data['optimizer_state'] = self.optimizer.state_dict()
            model_data['epsilon'] = self.epsilon
        else:  # PPO
            model_data['actor_state'] = self.actor.state_dict()
            model_data['critic_state'] = self.critic.state_dict()
            model_data['actor_optimizer_state'] = self.actor_optimizer.state_dict()
            model_data['critic_optimizer_state'] = self.critic_optimizer.state_dict()
        
        torch.save(model_data, path)
        self.logger.info(f"Модель сохранена: {path}", category='ml')
    
    def load_model(self, path: str):
        """Загружает модель"""
        model_data = torch.load(path)
        
        self.algorithm = model_data['algorithm']
        self.training_history = model_data.get('training_history', [])
        
        if self.algorithm == 'DQN':
            self.q_network.load_state_dict(model_data['q_network_state'])
            self.target_network.load_state_dict(model_data['target_network_state'])
            self.optimizer.load_state_dict(model_data['optimizer_state'])
            self.epsilon = model_data.get('epsilon', 0.01)
        else:  # PPO
            self.actor.load_state_dict(model_data['actor_state'])
            self.critic.load_state_dict(model_data['critic_state'])
            self.actor_optimizer.load_state_dict(model_data['actor_optimizer_state'])
            self.critic_optimizer.load_state_dict(model_data['critic_optimizer_state'])
        
        self.logger.info(f"Модель загружена: {path}", category='ml')
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Получает метрики производительности"""
        if not self.training_history:
            return {}
        
        recent_history = self.training_history[-100:]  # Последние 100 эпизодов
        
        rewards = [h['total_reward'] for h in recent_history]
        profits = [h['profit_percent'] for h in recent_history]
        
        return {
            'avg_reward': np.mean(rewards),
            'std_reward': np.std(rewards),
            'max_reward': np.max(rewards),
            'min_reward': np.min(rewards),
            'avg_profit': np.mean(profits),
            'std_profit': np.std(profits),
            'win_rate': len([p for p in profits if p > 0]) / len(profits),
            'total_episodes': len(self.training_history),
            'algorithm': self.algorithm
        }


class AdaptiveRLController:
    """
    Контроллер для управления несколькими RL агентами
    """
    
    def __init__(self):
        self.agents = {
            'dqn': ReinforcementTradingAgent(algorithm='DQN'),
            'ppo': ReinforcementTradingAgent(algorithm='PPO')
        }
        self.performance_tracker = defaultdict(list)
        self.active_agent = 'dqn'
        self.logger = SmartLogger(__name__)
    
    def train_all_agents(self, market_data: pd.DataFrame, episodes: int = 50):
        """Обучает все агенты"""
        for agent_name, agent in self.agents.items():
            self.logger.info(f"Обучение {agent_name} агента", category='ml')
            agent.train_on_history(market_data, episodes)
            
            # Сохраняем производительность
            metrics = agent.get_performance_metrics()
            self.performance_tracker[agent_name].append({
                'timestamp': datetime.now(),
                'metrics': metrics
            })
    
    def select_best_agent(self) -> str:
        """Выбирает лучшего агента на основе производительности"""
        best_score = -np.inf
        best_agent = self.active_agent
        
        for agent_name, history in self.performance_tracker.items():
            if history:
                recent_metrics = history[-1]['metrics']
                # Комбинированная метрика
                score = (recent_metrics.get('avg_profit', 0) * 0.5 +
                        recent_metrics.get('win_rate', 0) * 50 -
                        recent_metrics.get('std_profit', 0) * 0.2)
                
                if score > best_score:
                    best_score = score
                    best_agent = agent_name
        
        self.active_agent = best_agent
        return best_agent
    
    def get_action(self, state: np.ndarray, market_context: Dict[str, Any]) -> Dict[str, Any]:
        """Получает действие от активного агента"""
        agent = self.agents[self.active_agent]
        prediction = agent.predict_action(state, market_context)
        prediction['active_agent'] = self.active_agent
        return prediction