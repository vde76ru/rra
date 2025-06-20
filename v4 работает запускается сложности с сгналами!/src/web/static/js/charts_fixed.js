/**
 * ИСПРАВЛЕННЫЙ JavaScript для графиков
 * Файл: src/web/static/js/charts_fixed.js
 */

class FixedChartManager {
    constructor() {
        this.charts = {};
        this.updateInterval = 30000; // 30 секунд
        this.balanceChart = null;
        this.priceChart = null;
        this.currentSymbol = 'BTCUSDT';
        this.isInitialized = false;
    }

    /**
     * Инициализация менеджера графиков
     */
    async init() {
        console.log('🚀 Инициализация FixedChartManager...');
        
        try {
            // Проверяем доступность Chart.js
            if (typeof Chart === 'undefined') {
                console.error('❌ Chart.js не загружен');
                this.showError('Библиотека Chart.js не загружена');
                return false;
            }

            // Создаем графики
            await this.createBalanceChart();
            await this.createPriceChart();
            await this.loadTradesTable();
            
            // Запускаем обновления
            this.startAutoUpdate();
            
            // Загружаем начальные данные
            await this.updateAllData();
            
            this.isInitialized = true;
            console.log('✅ FixedChartManager инициализирован');
            
            this.showSuccess('Графики загружены успешно');
            return true;
            
        } catch (error) {
            console.error('❌ Ошибка инициализации FixedChartManager:', error);
            this.showError('Ошибка инициализации графиков: ' + error.message);
            return false;
        }
    }

    /**
     * Создание графика баланса
     */
    async createBalanceChart() {
        console.log('📊 Создаем график баланса...');
        
        const ctx = document.getElementById('balanceChart');
        if (!ctx) {
            console.warn('⚠️ Элемент balanceChart не найден');
            return;
        }

        // Уничтожаем существующий график
        if (this.balanceChart) {
            this.balanceChart.destroy();
        }

        this.balanceChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Доступно', 'В позициях', 'P&L'],
                datasets: [{
                    data: [950, 50, 25],
                    backgroundColor: [
                        '#28a745',  // Зеленый для доступных
                        '#ffc107',  // Желтый для позиций
                        '#17a2b8'   // Синий для P&L
                    ],
                    borderWidth: 2,
                    borderColor: '#333'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#fff',
                            padding: 20
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.label + ': $' + context.parsed.toFixed(2);
                            }
                        }
                    }
                }
            }
        });

        console.log('✅ График баланса создан');
    }

    /**
     * Создание графика цены
     */
    async createPriceChart() {
        console.log('📈 Создаем график цены...');
        
        const ctx = document.getElementById('priceChart');
        if (!ctx) {
            console.warn('⚠️ Элемент priceChart не найден');
            return;
        }

        // Уничтожаем существующий график
        if (this.priceChart) {
            this.priceChart.destroy();
        }

        // Генерируем демо данные для начала
        const demoData = this.generateDemoData();

        this.priceChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: demoData.labels,
                datasets: [{
                    label: this.currentSymbol,
                    data: demoData.prices,
                    borderColor: '#007bff',
                    backgroundColor: 'rgba(0, 123, 255, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: {
                            color: '#fff'
                        }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            label: function(context) {
                                return context.dataset.label + ': $' + context.parsed.y.toFixed(2);
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        ticks: {
                            color: '#fff'
                        },
                        grid: {
                            color: '#444'
                        }
                    },
                    y: {
                        ticks: {
                            color: '#fff',
                            callback: function(value) {
                                return '$' + value.toFixed(0);
                            }
                        },
                        grid: {
                            color: '#444'
                        }
                    }
                },
                interaction: {
                    mode: 'nearest',
                    axis: 'x',
                    intersect: false
                }
            }
        });

        console.log('✅ График цены создан');
    }

    /**
     * Генерация демо данных для графика
     */
    generateDemoData() {
        const labels = [];
        const prices = [];
        const now = new Date();
        let basePrice = 67800;

        for (let i = 23; i >= 0; i--) {
            const time = new Date(now.getTime() - i * 60 * 60 * 1000);
            labels.push(time.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' }));
            
            // Простая симуляция движения цены
            const change = (Math.random() - 0.5) * 1000;
            basePrice += change;
            prices.push(Math.max(60000, Math.min(70000, basePrice)));
        }

        return { labels, prices };
    }

    /**
     * Загрузка таблицы сделок
     */
    async loadTradesTable() {
        console.log('📋 Загружаем таблицу сделок...');
        
        try {
            const response = await this.fetchWithTimeout('/api/charts/trades', 5000);
            const data = await response.json();
            
            if (data.success) {
                this.updateTradesTable(data.trades);
            } else {
                throw new Error(data.error || 'Неизвестная ошибка API');
            }
            
        } catch (error) {
            console.warn('⚠️ Не удалось загрузить сделки с API, используем демо данные:', error);
            
            // Демо данные сделок
            const demoTrades = [
                {
                    id: 1,
                    symbol: 'BTCUSDT',
                    side: 'BUY',
                    entry_price: 67500,
                    profit: 125.50,
                    status: 'CLOSED',
                    created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString()
                },
                {
                    id: 2,
                    symbol: 'ETHUSDT',
                    side: 'SELL',
                    entry_price: 3450,
                    profit: -45.20,
                    status: 'CLOSED',
                    created_at: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString()
                },
                {
                    id: 3,
                    symbol: 'BNBUSDT',
                    side: 'BUY',
                    entry_price: 640,
                    profit: 0,
                    status: 'OPEN',
                    created_at: new Date(Date.now() - 30 * 60 * 1000).toISOString()
                }
            ];
            
            this.updateTradesTable(demoTrades);
        }
    }

    /**
     * Обновление таблицы сделок
     */
    updateTradesTable(trades) {
        const tbody = document.getElementById('tradesTableBody');
        if (!tbody) {
            console.warn('⚠️ Элемент tradesTableBody не найден');
            return;
        }

        tbody.innerHTML = '';
        
        trades.slice(0, 10).forEach(trade => {
            const row = document.createElement('tr');
            
            const time = new Date(trade.created_at).toLocaleTimeString('ru-RU');
            const profitClass = trade.profit > 0 ? 'text-success' : 
                               trade.profit < 0 ? 'text-danger' : 'text-warning';
            const profitText = trade.profit !== null ? 
                              `$${trade.profit.toFixed(2)}` : 'В процессе';
            
            row.innerHTML = `
                <td>${time}</td>
                <td><span class="badge bg-primary">${trade.symbol}</span></td>
                <td><span class="badge bg-${trade.side === 'BUY' ? 'success' : 'danger'}">${trade.side}</span></td>
                <td>$${trade.entry_price.toFixed(2)}</td>
                <td class="${profitClass}">${profitText}</td>
            `;
            
            tbody.appendChild(row);
        });

        console.log(`✅ Таблица сделок обновлена (${trades.length} записей)`);
    }

    /**
     * Обновление всех данных
     */
    async updateAllData() {
        console.log('🔄 Обновляем все данные...');
        
        try {
            // Обновляем баланс
            await this.updateBalance();
            
            // Обновляем цену
            await this.updatePrice();
            
            // Обновляем сделки
            await this.loadTradesTable();
            
            // Обновляем статистику
            await this.updateStats();
            
            console.log('✅ Все данные обновлены');
            
        } catch (error) {
            console.error('❌ Ошибка обновления данных:', error);
        }
    }

    /**
     * Обновление баланса
     */
    async updateBalance() {
        try {
            const response = await this.fetchWithTimeout('/api/charts/balance', 5000);
            const data = await response.json();
            
            if (data.success && this.balanceChart) {
                this.balanceChart.data.datasets[0].data = [
                    data.available_usdt,
                    data.in_positions,
                    Math.abs(data.pnl_today)
                ];
                this.balanceChart.update();
                
                // Обновляем числовые индикаторы
                this.updateBalanceIndicators(data);
            }
            
        } catch (error) {
            console.warn('⚠️ Не удалось обновить баланс:', error);
        }
    }

    /**
     * Обновление индикаторов баланса
     */
    updateBalanceIndicators(data) {
        const indicators = {
            'totalBalance': data.total_usdt,
            'availableBalance': data.available_usdt,
            'pnlToday': data.pnl_today,
            'pnlPercent': data.pnl_percent
        };

        Object.entries(indicators).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                if (id.includes('pnl')) {
                    element.textContent = (value >= 0 ? '+' : '') + value.toFixed(2) + 
                                        (id.includes('Percent') ? '%' : '');
                    element.className = value >= 0 ? 'text-success' : 'text-danger';
                } else {
                    element.textContent = '$' + value.toFixed(2);
                }
            }
        });
    }

    /**
     * Обновление цены
     */
    async updatePrice() {
        try {
            const response = await this.fetchWithTimeout(`/api/charts/price/${this.currentSymbol}`, 5000);
            const data = await response.json();
            
            if (data.success && this.priceChart) {
                // Добавляем новую точку данных
                const now = new Date();
                const timeLabel = now.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
                
                this.priceChart.data.labels.push(timeLabel);
                this.priceChart.data.datasets[0].data.push(data.price);
                
                // Ограничиваем количество точек
                if (this.priceChart.data.labels.length > 24) {
                    this.priceChart.data.labels.shift();
                    this.priceChart.data.datasets[0].data.shift();
                }
                
                this.priceChart.update();
                
                // Обновляем текущую цену в интерфейсе
                this.updatePriceIndicators(data);
            }
            
        } catch (error) {
            console.warn('⚠️ Не удалось обновить цену:', error);
        }
    }

    /**
     * Обновление индикаторов цены
     */
    updatePriceIndicators(data) {
        const priceElement = document.getElementById('currentPrice');
        const changeElement = document.getElementById('priceChange');
        const volumeElement = document.getElementById('volume24h');

        if (priceElement) {
            priceElement.textContent = '$' + data.price.toFixed(2);
        }

        if (changeElement) {
            changeElement.textContent = (data.change_24h >= 0 ? '+' : '') + data.change_24h.toFixed(2) + '%';
            changeElement.className = data.change_24h >= 0 ? 'text-success' : 'text-danger';
        }

        if (volumeElement) {
            volumeElement.textContent = '$' + (data.volume_24h / 1000000).toFixed(1) + 'M';
        }
    }

    /**
     * Обновление статистики
     */
    async updateStats() {
        try {
            const response = await this.fetchWithTimeout('/api/charts/stats', 5000);
            const data = await response.json();
            
            if (data.success) {
                const statsElements = {
                    'activePairs': data.active_pairs,
                    'openPositions': data.open_positions,
                    'tradesToday': data.trades_today,
                    'cyclesCompleted': data.cycles_completed
                };

                Object.entries(statsElements).forEach(([id, value]) => {
                    const element = document.getElementById(id);
                    if (element) {
                        element.textContent = value;
                    }
                });
            }
            
        } catch (error) {
            console.warn('⚠️ Не удалось обновить статистику:', error);
        }
    }

    /**
     * Запуск автоматических обновлений
     */
    startAutoUpdate() {
        // Останавливаем предыдущий интервал
        if (this.updateTimer) {
            clearInterval(this.updateTimer);
        }

        // Запускаем новый интервал
        this.updateTimer = setInterval(() => {
            if (this.isInitialized) {
                this.updateAllData();
            }
        }, this.updateInterval);

        console.log(`🔄 Автообновление запущено (каждые ${this.updateInterval/1000} сек)`);
    }

    /**
     * Fetch с таймаутом
     */
    async fetchWithTimeout(url, timeout = 5000) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeout);
        
        try {
            const response = await fetch(url, {
                signal: controller.signal,
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            clearTimeout(timeoutId);
            return response;
        } catch (error) {
            clearTimeout(timeoutId);
            throw error;
        }
    }

    /**
     * Показ уведомления об успехе
     */
    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    /**
     * Показ уведомления об ошибке
     */
    showError(message) {
        this.showNotification(message, 'error');
    }

    /**
     * Показ уведомления
     */
    showNotification(message, type = 'info') {
        const alertClass = type === 'success' ? 'alert-success' : 
                          type === 'error' ? 'alert-danger' : 'alert-info';
        
        const notification = document.createElement('div');
        notification.className = `alert ${alertClass} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Автоматически удаляем через 5 секунд
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
    }

    /**
     * Смена торговой пары
     */
    changeSymbol(symbol) {
        this.currentSymbol = symbol;
        console.log(`📊 Переключились на ${symbol}`);
        
        // Обновляем название графика
        if (this.priceChart) {
            this.priceChart.data.datasets[0].label = symbol;
            this.priceChart.update();
        }
        
        // Обновляем данные
        this.updatePrice();
    }

    /**
     * Обновление интервала автообновления
     */
    setUpdateInterval(seconds) {
        this.updateInterval = seconds * 1000;
        this.startAutoUpdate();
        console.log(`🔄 Интервал обновления изменен на ${seconds} секунд`);
    }

    /**
     * Уничтожение менеджера
     */
    destroy() {
        if (this.updateTimer) {
            clearInterval(this.updateTimer);
        }
        
        if (this.balanceChart) {
            this.balanceChart.destroy();
        }
        
        if (this.priceChart) {
            this.priceChart.destroy();
        }
        
        this.isInitialized = false;
        console.log('🗑️ FixedChartManager уничтожен');
    }
}

// Глобальная инициализация
let chartManager = null;

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', async function() {
    console.log('🚀 Страница загружена, инициализируем графики...');
    
    try {
        chartManager = new FixedChartManager();
        const success = await chartManager.init();
        
        if (success) {
            console.log('✅ Графики успешно инициализированы');
            
            // Привязываем обработчики событий
            setupEventHandlers();
        } else {
            console.error('❌ Не удалось инициализировать графики');
        }
        
    } catch (error) {
        console.error('❌ Критическая ошибка инициализации:', error);
    }
});

/**
 * Настройка обработчиков событий
 */
function setupEventHandlers() {
    // Кнопки смены символов
    document.querySelectorAll('.symbol-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const symbol = e.target.dataset.symbol;
            if (symbol && chartManager) {
                chartManager.changeSymbol(symbol);
            }
        });
    });

    // Кнопка обновления
    const refreshBtn = document.getElementById('refreshChartsBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            if (chartManager) {
                chartManager.updateAllData();
                chartManager.showSuccess('Графики обновлены');
            }
        });
    }

    // Селектор интервала обновления
    const intervalSelect = document.getElementById('updateInterval');
    if (intervalSelect) {
        intervalSelect.addEventListener('change', (e) => {
            const seconds = parseInt(e.target.value);
            if (chartManager && seconds > 0) {
                chartManager.setUpdateInterval(seconds);
            }
        });
    }
}

// Экспортируем для глобального доступа
window.chartManager = chartManager;