/**
 * ИСПРАВЛЕННАЯ система управления графиками
 * Файл: charts_enhanced_fixed.js
 */

class FixedChartsManager {
    constructor() {
        this.charts = new Map();
        this.isInitialized = false;
        this.updateInterval = 30000;
        
        console.log('📊 FixedChartsManager создан');
    }
    
    /**
     * Безопасная инициализация всей системы
     */
    async initialize() {
        try {
            console.log('🚀 Начинаем инициализацию графиков...');
            
            // Проверяем доступность Chart.js
            if (typeof Chart === 'undefined') {
                throw new Error('Chart.js не загружен. Убедитесь, что библиотека подключена.');
            }
            
            // Настраиваем Chart.js ПРАВИЛЬНО
            this.setupChartDefaults();
            
            // Инициализируем графики последовательно
            await this.initializeAllCharts();
            
            // Загружаем начальные данные
            await this.loadInitialData();
            
            // Запускаем автообновление
            this.startAutoUpdate();
            
            this.isInitialized = true;
            console.log('✅ Все графики успешно инициализированы');
            this.showSuccess('Графики загружены');
            
        } catch (error) {
            console.error('❌ Критическая ошибка инициализации:', error);
            this.showError('Ошибка инициализации: ' + error.message);
        }
    }
    
    /**
     * ИСПРАВЛЕННАЯ настройка Chart.js по умолчанию
     */
    setupChartDefaults() {
        // ПРАВИЛЬНЫЙ способ настройки Chart.js 3.x+
        Chart.defaults.font = {
            ...Chart.defaults.font,
            family: 'Arial, sans-serif'
        };
        
        // Настройки цветов для темной темы
        Chart.defaults.color = '#ffffff';
        Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.1)';
        Chart.defaults.backgroundColor = 'rgba(255, 255, 255, 0.1)';
        
        console.log('⚙️ Chart.js настройки применены');
    }
    
    /**
     * Инициализация всех графиков
     */
    async initializeAllCharts() {
        const chartsToCreate = [
            { canvasId: 'balanceChart', type: 'balance' },
            { canvasId: 'priceChart', type: 'price' },
            { canvasId: 'positionsChart', type: 'positions' },
            { canvasId: 'tradingview_chart', type: 'tradingview' }
        ];
        
        for (const chartConfig of chartsToCreate) {
            await this.createSingleChart(chartConfig.canvasId, chartConfig.type);
        }
    }
    
    /**
     * Создание одного графика с проверками
     */
    async createSingleChart(canvasId, chartType) {
        try {
            const canvas = document.getElementById(canvasId);
            if (!canvas) {
                console.warn(`⚠️ Canvas '${canvasId}' не найден, пропускаем`);
                return null;
            }
            
            // Проверяем, не создан ли уже график
            if (this.charts.has(canvasId)) {
                console.log(`📊 График '${canvasId}' уже существует, пересоздаем`);
                this.charts.get(canvasId).destroy();
            }
            
            const ctx = canvas.getContext('2d');
            let chart = null;
            
            switch (chartType) {
                case 'balance':
                    chart = this.createBalanceChart(ctx);
                    break;
                case 'price':
                    chart = this.createPriceChart(ctx);
                    break;
                case 'positions':
                    chart = this.createPositionsChart(ctx);
                    break;
                case 'tradingview':
                    // TradingView обрабатывается отдельно
                    this.initializeTradingView(canvasId);
                    return;
                default:
                    console.warn(`⚠️ Неизвестный тип графика: ${chartType}`);
                    return null;
            }
            
            if (chart) {
                this.charts.set(canvasId, chart);
                console.log(`✅ График '${canvasId}' создан успешно`);
            }
            
            return chart;
            
        } catch (error) {
            console.error(`❌ Ошибка создания графика '${canvasId}':`, error);
            return null;
        }
    }
    
    /**
     * ИСПРАВЛЕННЫЙ график баланса
     */
    createBalanceChart(ctx) {
        return new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Баланс USDT',
                    data: [],
                    borderColor: '#28a745',
                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#28a745',
                    pointBorderColor: '#ffffff',
                    pointRadius: 4,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            color: '#ffffff',
                            font: {
                                size: 14
                            }
                        }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        borderColor: '#28a745',
                        borderWidth: 1,
                        callbacks: {
                            label: function(context) {
                                return `Баланс: $${context.parsed.y.toFixed(2)}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        display: true,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)',
                            drawBorder: false
                        },
                        ticks: {
                            color: '#ffffff',
                            maxTicksLimit: 8
                        }
                    },
                    y: {
                        display: true,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)',
                            drawBorder: false
                        },
                        ticks: {
                            color: '#ffffff',
                            callback: function(value) {
                                return '$' + value.toFixed(0);
                            }
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
    }
    
    /**
     * ИСПРАВЛЕННЫЙ график цен
     */
    createPriceChart(ctx) {
        return new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'BTCUSDT',
                    data: [],
                    borderColor: '#007bff',
                    backgroundColor: 'rgba(0, 123, 255, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#007bff',
                    pointBorderColor: '#ffffff',
                    pointRadius: 3,
                    pointHoverRadius: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        labels: {
                            color: '#ffffff'
                        }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        callbacks: {
                            label: function(context) {
                                return `${context.dataset.label}: $${context.parsed.y.toLocaleString()}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { color: 'rgba(255, 255, 255, 0.1)' },
                        ticks: { color: '#ffffff', maxTicksLimit: 12 }
                    },
                    y: {
                        grid: { color: 'rgba(255, 255, 255, 0.1)' },
                        ticks: { 
                            color: '#ffffff',
                            callback: function(value) {
                                return '$' + value.toLocaleString();
                            }
                        }
                    }
                }
            }
        });
    }
    
    /**
     * ИСПРАВЛЕННЫЙ график позиций
     */
    createPositionsChart(ctx) {
        return new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Нет активных позиций'],
                datasets: [{
                    data: [1],
                    backgroundColor: ['#6c757d'],
                    borderColor: ['#495057'],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#ffffff',
                            padding: 20,
                            font: {
                                size: 12
                            }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        callbacks: {
                            label: function(context) {
                                return `${context.label}: $${context.parsed.toFixed(2)}`;
                            }
                        }
                    }
                }
            }
        });
    }
    
    /**
     * Инициализация TradingView (если доступно)
     */
    initializeTradingView(containerId) {
        if (typeof TradingView !== 'undefined') {
            try {
                new TradingView.widget({
                    autosize: true,
                    symbol: 'BINANCE:BTCUSDT',
                    interval: '1h',
                    timezone: 'Etc/UTC',
                    theme: 'dark',
                    style: '1',
                    locale: 'ru',
                    toolbar_bg: '#1e1e1e',
                    enable_publishing: false,
                    allow_symbol_change: true,
                    container_id: containerId
                });
                console.log('✅ TradingView график инициализирован');
            } catch (error) {
                console.error('❌ Ошибка TradingView:', error);
            }
        } else {
            console.warn('⚠️ TradingView недоступен');
        }
    }
    
    /**
     * Загрузка начальных данных
     */
    async loadInitialData() {
        console.log('📥 Загружаем начальные данные...');
        
        // Генерируем демо данные для начала
        this.updateBalanceWithDemo();
        this.updatePriceWithDemo();
        this.updatePositionsWithDemo();
        
        console.log('✅ Демо данные загружены');
    }
    
    /**
     * Обновление графика баланса демо данными
     */
    updateBalanceWithDemo() {
        const chart = this.charts.get('balanceChart');
        if (!chart) return;
        
        const now = new Date();
        const labels = [];
        const data = [];
        let balance = 1000;
        
        for (let i = 9; i >= 0; i--) {
            const time = new Date(now.getTime() - i * 60 * 60 * 1000);
            labels.push(time.toLocaleTimeString('ru-RU', { 
                hour: '2-digit', 
                minute: '2-digit' 
            }));
            
            balance += (Math.random() - 0.5) * 50;
            data.push(Math.max(900, balance));
        }
        
        chart.data.labels = labels;
        chart.data.datasets[0].data = data;
        chart.update('none');
    }
    
    /**
     * Обновление графика цен демо данными
     */
    updatePriceWithDemo() {
        const chart = this.charts.get('priceChart');
        if (!chart) return;
        
        const now = new Date();
        const labels = [];
        const data = [];
        let price = 67800;
        
        for (let i = 23; i >= 0; i--) {
            const time = new Date(now.getTime() - i * 60 * 60 * 1000);
            labels.push(time.toLocaleTimeString('ru-RU', { 
                hour: '2-digit', 
                minute: '2-digit' 
            }));
            
            price += (Math.random() - 0.5) * 1000;
            data.push(Math.max(60000, Math.min(75000, price)));
        }
        
        chart.data.labels = labels;
        chart.data.datasets[0].data = data;
        chart.update('none');
    }
    
    /**
     * Обновление позиций демо данными
     */
    updatePositionsWithDemo() {
        const chart = this.charts.get('positionsChart');
        if (!chart) return;
        
        chart.data.labels = ['BTC/USDT', 'ETH/USDT', 'Available'];
        chart.data.datasets[0].data = [450, 350, 200];
        chart.data.datasets[0].backgroundColor = ['#f7931e', '#627eea', '#28a745'];
        chart.data.datasets[0].borderColor = ['#d4761a', '#4f63d2', '#1e7e34'];
        chart.update('none');
    }
    
    /**
     * Автообновление данных
     */
    startAutoUpdate() {
        setInterval(() => {
            if (this.isInitialized) {
                this.updateBalanceWithDemo();
                this.updatePriceWithDemo();
            }
        }, this.updateInterval);
        
        console.log(`⏰ Автообновление запущено (${this.updateInterval/1000}с)`);
    }
    
    /**
     * Показ уведомлений
     */
    showSuccess(message) {
        this.showNotification(message, 'success');
    }
    
    showError(message) {
        this.showNotification(message, 'error');
    }
    
    showNotification(message, type = 'info') {
        const alertClass = {
            'success': 'alert-success',
            'error': 'alert-danger', 
            'info': 'alert-info'
        }[type];
        
        const notification = document.createElement('div');
        notification.className = `alert ${alertClass} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        notification.innerHTML = `
            <strong>${type === 'error' ? 'Ошибка' : 'Успех'}:</strong> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }
    
    /**
     * Очистка ресурсов
     */
    destroy() {
        this.charts.forEach(chart => {
            try {
                chart.destroy();
            } catch (error) {
                console.warn('⚠️ Ошибка при уничтожении графика:', error);
            }
        });
        this.charts.clear();
        this.isInitialized = false;
        console.log('🧹 FixedChartsManager очищен');
    }
}

// Глобальная переменная для менеджера
let globalChartsManager = null;

// Безопасная инициализация при загрузке DOM
document.addEventListener('DOMContentLoaded', async function() {
    try {
        console.log('🚀 DOM загружен, инициализируем графики...');
        
        // Ждем полной загрузки библиотек
        await new Promise(resolve => {
            if (typeof Chart !== 'undefined') {
                resolve();
            } else {
                const checkLibraries = setInterval(() => {
                    if (typeof Chart !== 'undefined') {
                        clearInterval(checkLibraries);
                        resolve();
                    }
                }, 100);
            }
        });
        
        globalChartsManager = new FixedChartsManager();
        await globalChartsManager.initialize();
        
    } catch (error) {
        console.error('❌ Критическая ошибка инициализации графиков:', error);
    }
});

// Очистка при выходе
window.addEventListener('beforeunload', () => {
    if (globalChartsManager) {
        globalChartsManager.destroy();
    }
});

// Экспорт для глобального доступа
window.chartsManager = globalChartsManager;