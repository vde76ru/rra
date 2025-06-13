# Crypto Trading Bot v3.0

## 🚀 Быстрый старт

### 1. Проверка системы
```bash
cd /var/www/www-root/data/www/systemetech.ru
chmod +x *.sh
./check_system.sh
```

### 2. Настройка Redis (если требует пароль)
```bash
# Отключаем пароль для локального использования
sudo sed -i 's/^requirepass/#requirepass/' /etc/redis/redis.conf
sudo systemctl restart redis-server
```

### 3. Добавление API ключей
```bash
# Запускаем с sudo для доступа к /etc/crypto/config/.env
sudo python add_api_keys.py
```

**Где получить ключи:**
1. Зайдите на https://testnet.bybit.com
2. Зарегистрируйтесь или войдите
3. Перейдите в API Management
4. Создайте новый API ключ
5. Дайте права: **Read + Trade** (НЕ давайте права на вывод!)

### 4. Проверка подключения
```bash
# Активируем виртуальное окружение
source venv/bin/activate

# Проверяем API подключение
python test_bybit_connection.py

# Проверяем всю установку
python test_installation_fixed.py
```

### 5. Запуск бота
```bash
# Простой мониторинг цен (для начала)
python main_simple.py

# Веб-интерфейс
./start_web.sh
# Откройте: http://systemetech.ru:8000
```

## 📁 Структура проекта

```
/var/www/www-root/data/www/systemetech.ru/
├── app.py                    # Веб-интерфейс
├── main_simple.py           # Простой бот для тестирования
├── main.py                  # Основной торговый бот
├── src/
│   ├── core/
│   │   ├── database.py      # Подключение к БД
│   │   └── models.py        # Модели данных
│   ├── exchange/
│   │   └── bybit_client.py  # Клиент биржи с human behavior
│   └── strategies/
│       └── simple_momentum.py # Простая стратегия
├── logs/                    # Логи
├── venv/                    # Python окружение
└── .env -> /etc/crypto/config/.env  # Символическая ссылка
```

## 🔧 Конфигурация

Основной файл конфигурации: `/etc/crypto/config/.env`

```env
# API настройки
BYBIT_API_KEY=ваш_ключ
BYBIT_API_SECRET=ваш_секрет
BYBIT_TESTNET=true  # ВАЖНО: начинаем с testnet!

# База данных
DB_HOST=localhost
DB_NAME=crypto_top_bd_mysql
DB_USER=crypto_top_admin
DB_PASSWORD=LSM6_PqnuZ10nvEdzfe6

# Торговые параметры
TRADING_SYMBOL=BTCUSDT
MAX_POSITION_SIZE_PERCENT=2.0
```

## 🛡️ Безопасность

1. **API ключи хранятся в `/etc/crypto/config/.env`** с правами 600
2. **Используйте только TESTNET** для тестирования
3. **Никогда не давайте права на вывод средств** в API ключах
4. **Регулярно меняйте API ключи** (каждые 30 дней)

## 📊 Мониторинг

### Логи
```bash
# Основные логи
tail -f logs/trading.log

# Логи веб-интерфейса
tail -f logs/web.log
```

### Проверка процессов
```bash
# Проверка Python процессов
ps aux | grep python

# Проверка портов
sudo netstat -tlnp | grep 8000
```

## 🚨 Решение проблем

### Redis требует аутентификации
```bash
sudo sed -i 's/^requirepass/#requirepass/' /etc/redis/redis.conf
sudo systemctl restart redis-server
```

### Порт 8000 занят
```bash
# Найти процесс
sudo lsof -i :8000

# Убить процесс
sudo kill -9 <PID>
```

### API ключи не работают
1. Проверьте что используете TESTNET ключи
2. Проверьте права API ключей (Read + Trade)
3. Проверьте IP whitelist если включен

## 📈 Следующие шаги

1. **Тестирование на Testnet** - минимум 2 недели
2. **Изучение стратегий** в `src/strategies/`
3. **Настройка уведомлений** через Telegram
4. **Добавление новых стратегий**
5. **Переход на Mainnet** только после успешных тестов

## ⚠️ ВАЖНО

- Всегда начинайте с TESTNET
- Тестируйте минимум 2 недели
- Начинайте с малых сумм
- Следите за логами
- Делайте backup конфигурации

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи
2. Запустите `./check_system.sh`
3. Изучите документацию в `/docs/`

---
*Crypto Trading Bot v3.0 - Professional Edition*