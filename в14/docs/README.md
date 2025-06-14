# Crypto Trading Bot v3.0

## Структура проекта

```
src/
├── core/          # Ядро системы
├── bot/           # Торговый бот
├── exchange/      # Работа с биржей
├── strategies/    # Торговые стратегии
├── analysis/      # Анализ рынка
├── notifications/ # Уведомления
└── web/           # Веб-интерфейс
```

## Запуск

```bash
# Полная система
python main.py

# Только бот
python main.py --mode bot

# Только веб
python main.py --mode web
```
