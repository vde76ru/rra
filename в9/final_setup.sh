#!/bin/bash
# final_setup.sh - Финальная настройка и проверка

cd /var/www/www-root/data/www/systemetech.ru

echo "🔧 Финальная настройка Crypto Trading Bot"
echo "========================================="

# 1. Проверка символической ссылки на конфиг
echo -e "\n1️⃣ Проверка конфигурации..."
if [ -L ".env" ] && [ -e ".env" ]; then
    echo "✅ Символическая ссылка на .env существует"
    echo "   Ссылка указывает на: $(readlink -f .env)"
else
    echo "⚠️  Создаем символическую ссылку на конфигурацию..."
    ln -sf /etc/crypto/config/.env .env
    echo "✅ Ссылка создана"
fi

# 2. Проверка основных переменных
echo -e "\n2️⃣ Проверка ключевых переменных из .env..."
source .env
if [ -n "$DB_NAME" ]; then
    echo "✅ DB_NAME: $DB_NAME"
else
    echo "❌ DB_NAME не установлен!"
fi

if [ -n "$DB_USER" ]; then
    echo "✅ DB_USER: $DB_USER"
else
    echo "❌ DB_USER не установлен!"
fi

if [ "$BYBIT_TESTNET" = "true" ]; then
    echo "✅ BYBIT_TESTNET: true (безопасный режим)"
else
    echo "⚠️  BYBIT_TESTNET: false (реальная торговля!)"
fi

# 3. Активация виртуального окружения
echo -e "\n3️⃣ Активация виртуального окружения..."
source venv/bin/activate
echo "✅ Python: $(which python)"

# 4. Создание основных файлов если их нет
echo -e "\n4️⃣ Проверка основных файлов..."
if [ ! -f "src/core/database.py" ]; then
    echo "⚠️  Создаем основные файлы..."
    bash create_main_files.sh
else
    echo "✅ Основные файлы существуют"
fi

# 5. Проверка и создание таблиц БД
echo -e "\n5️⃣ Проверка базы данных..."
python check_database.py

# 6. Создание простого файла запуска веб-интерфейса
echo -e "\n6️⃣ Создание файла веб-интерфейса..."
cat > app.py << 'EOF'
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import json
from datetime import datetime
import asyncio

from src.core.database import SessionLocal
from src.core.models import Trade

app = FastAPI(title="Crypto Trading Bot")

# HTML страница дашборда
html = """
<!DOCTYPE html>
<html>
<head>
    <title>Crypto Bot Dashboard</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #1a1a1a;
            color: #fff;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .metric {
            background: #2a2a2a;
            padding: 20px;
            margin: 10px;
            border-radius: 8px;
            display: inline-block;
            min-width: 200px;
        }
        .profit { color: #4caf50; }
        .loss { color: #f44336; }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #444;
        }
        th {
            background-color: #333;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Crypto Trading Bot Dashboard</h1>
        
        <div id="metrics">
            <div class="metric">
                <h3>Баланс</h3>
                <div id="balance">Загрузка...</div>
            </div>
            <div class="metric">
                <h3>Дневная прибыль</h3>
                <div id="daily-pnl">Загрузка...</div>
            </div>
            <div class="metric">
                <h3>Открытые позиции</h3>
                <div id="open-positions">0</div>
            </div>
            <div class="metric">
                <h3>Всего сделок</h3>
                <div id="total-trades">0</div>
            </div>
        </div>
        
        <h2>Последние сделки</h2>
        <table id="trades-table">
            <thead>
                <tr>
                    <th>Время</th>
                    <th>Символ</th>
                    <th>Сторона</th>
                    <th>Цена входа</th>
                    <th>Цена выхода</th>
                    <th>Прибыль</th>
                    <th>Статус</th>
                </tr>
            </thead>
            <tbody id="trades-tbody">
            </tbody>
        </table>
    </div>
    
    <script>
        const ws = new WebSocket(`ws://${window.location.host}/ws`);
        
        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            updateDashboard(data);
        };
        
        function updateDashboard(data) {
            document.getElementById('balance').textContent = '$' + data.balance.toFixed(2);
            document.getElementById('daily-pnl').textContent = '$' + data.daily_pnl.toFixed(2);
            document.getElementById('open-positions').textContent = data.open_positions;
            document.getElementById('total-trades').textContent = data.total_trades;
            
            // Обновление цвета P&L
            const pnlElement = document.getElementById('daily-pnl');
            pnlElement.className = data.daily_pnl >= 0 ? 'profit' : 'loss';
            
            // Обновление таблицы сделок
            updateTradesTable(data.recent_trades);
        }
        
        function updateTradesTable(trades) {
            const tbody = document.getElementById('trades-tbody');
            tbody.innerHTML = '';
            
            trades.forEach(trade => {
                const row = tbody.insertRow();
                row.insertCell(0).textContent = new Date(trade.created_at).toLocaleString();
                row.insertCell(1).textContent = trade.symbol;
                row.insertCell(2).textContent = trade.side;
                row.insertCell(3).textContent = '$' + trade.entry_price.toFixed(2);
                row.insertCell(4).textContent = trade.exit_price ? '$' + trade.exit_price.toFixed(2) : '-';
                
                const profitCell = row.insertCell(5);
                if (trade.profit !== null) {
                    profitCell.textContent = '$' + trade.profit.toFixed(2);
                    profitCell.className = trade.profit >= 0 ? 'profit' : 'loss';
                } else {
                    profitCell.textContent = '-';
                }
                
                row.insertCell(6).textContent = trade.status;
            });
        }
    </script>
</body>
</html>
"""

@app.get("/")
async def get():
    return HTMLResponse(html)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Получаем данные из БД
            db = SessionLocal()
            
            # Статистика
            total_trades = db.query(Trade).count()
            open_positions = db.query(Trade).filter(Trade.status == 'OPEN').count()
            
            # Дневная прибыль
            today_trades = db.query(Trade).filter(
                Trade.status == 'CLOSED',
                Trade.closed_at >= datetime.utcnow().date()
            ).all()
            daily_pnl = sum(trade.profit or 0 for trade in today_trades)
            
            # Последние сделки
            recent_trades = db.query(Trade).order_by(Trade.created_at.desc()).limit(10).all()
            
            db.close()
            
            # Отправляем данные
            data = {
                'balance': 10000,  # Заглушка - потом получать из API
                'daily_pnl': daily_pnl,
                'open_positions': open_positions,
                'total_trades': total_trades,
                'recent_trades': [
                    {
                        'created_at': trade.created_at.isoformat(),
                        'symbol': trade.symbol,
                        'side': trade.side,
                        'entry_price': trade.entry_price,
                        'exit_price': trade.exit_price,
                        'profit': trade.profit,
                        'status': trade.status
                    }
                    for trade in recent_trades
                ]
            }
            
            await websocket.send_text(json.dumps(data))
            await asyncio.sleep(5)  # Обновление каждые 5 секунд
            
    except Exception as e:
        print(f"WebSocket error: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
EOF

echo "✅ Файл app.py создан"

# 7. Запуск финальной проверки
echo -e "\n7️⃣ Запуск финальной проверки..."
python test_installation.py

echo -e "\n✅ Настройка завершена!"
echo ""
echo "📝 Следующие шаги:"
echo "1. Добавьте API ключи Bybit в /etc/crypto/config/.env"
echo "   - Получите их на https://testnet.bybit.com"
echo "   - Установите BYBIT_API_KEY и BYBIT_API_SECRET"
echo ""
echo "2. Запустите простой тест подключения:"
echo "   python main_simple.py"
echo ""
echo "3. Запустите веб-интерфейс:"
echo "   python app.py"
echo ""
echo "4. Откройте в браузере:"
echo "   http://systemetech.ru:8000"