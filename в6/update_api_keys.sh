#!/bin/bash
# update_api_keys.sh - Безопасное обновление API ключей

CONFIG_FILE="/etc/crypto/config/.env"

echo "🔐 Обновление API ключей Bybit"
echo "==============================="
echo ""
echo "⚠️  ВАЖНО: Используйте только TESTNET ключи для начала!"
echo "Получите их на: https://testnet.bybit.com"
echo ""

# Проверка прав доступа
if [ ! -w "$CONFIG_FILE" ]; then
    echo "❌ Нет прав на запись в $CONFIG_FILE"
    echo "Запустите скрипт с sudo"
    exit 1
fi

# Ввод API ключа
read -p "Введите BYBIT_API_KEY: " API_KEY
if [ -z "$API_KEY" ]; then
    echo "❌ API ключ не может быть пустым"
    exit 1
fi

# Ввод API секрета
read -s -p "Введите BYBIT_API_SECRET (ввод скрыт): " API_SECRET
echo ""
if [ -z "$API_SECRET" ]; then
    echo "❌ API секрет не может быть пустым"
    exit 1
fi

# Создание временного файла
TEMP_FILE=$(mktemp)

# Обновление значений в конфиге
while IFS= read -r line; do
    if [[ $line == BYBIT_API_KEY=* ]]; then
        echo "BYBIT_API_KEY=$API_KEY" >> "$TEMP_FILE"
    elif [[ $line == BYBIT_API_SECRET=* ]]; then
        echo "BYBIT_API_SECRET=$API_SECRET" >> "$TEMP_FILE"
    else
        echo "$line" >> "$TEMP_FILE"
    fi
done < "$CONFIG_FILE"

# Замена оригинального файла
mv "$TEMP_FILE" "$CONFIG_FILE"
chmod 600 "$CONFIG_FILE"  # Только владелец может читать/писать

echo "✅ API ключи обновлены!"
echo ""
echo "📝 Проверьте подключение:"
echo "cd /var/www/www-root/data/www/systemetech.ru"
echo "source venv/bin/activate"
echo "python main_simple.py"