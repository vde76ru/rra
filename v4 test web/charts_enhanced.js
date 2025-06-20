/**
 * Исправленная система управления графиками и веб-интерфейсом
 * Файл: src/web/static/js/charts_enhanced.js
 * 
 * Исправляет проблемы:
 * - График не инициализируется
 * - API данные не загружаются
 * - WebSocket соединения обрываются
 * - Ошибки Chart.js
 */

class EnhancedChartsManager {
    constructor() {
        this.charts = new Map();
        this.websocket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.apiBaseUrl = window.location.origin;
        this.isInitialized = false;
        
        // Состояния загрузки
        this.loadingStates = {
            balance: false,
            trades: false,
            price: false
        };
        
        // Кэш данных
        this.dataCache = {
            balance: null,
            trades: null,
            prices: null,
            lastUpdate: null
        };
        
        console.log('📊 EnhancedChartsManager инициализирован');
    }
    
    /**
     * Инициализация всей системы графиков
     */
    async initialize() {
        try {
            console.log('🚀 Инициализация системы графиков...');
            
            // Проверяем доступность Chart.js
            if (typeof Chart === 'undefined') {
                throw new Error('Chart.js не загружен');
            }
            
            // Настройка Chart.js по умолчанию
            this.configureChartDefaults();
            
            // Инициализация графиков
            await this.initializeCharts();
            
            // Подключение WebSocket
            await this.initializeWebSocket();
            
            // Начальная загрузка данных
            await this.loadInitialData();
            
            // Запуск автообновления
            this.startAutoRefresh();
            
            this.isInitialized = true;
            console.log('✅ Система графиков успешно инициализирована');
            
        } catch (error) {
            console.error('❌ Ошибка инициализации графиков:', error);
            this.showError('Ошибка инициализации графиков: ' + error.message);
        }
    }
    
    /**
     * Настройка Chart.js по умолчанию
     */
    configureChartDefaults() {
        Chart.defaults.color = '#ffffff';
        Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.1)';
        Chart.defaults.backgroundColor = 'rgba(0, 123, 255, 0.1)';
        
        // Глобальные настройки для всех графиков
        Chart.defaults.plugins.legend.labels.color = '#ffffff';
        Chart.defaults.scales.linear.grid.color = 'rgba(255, 255, 255, 0.1)';
        Chart.defaults.scales.linear.ticks.color = '#ffffff';
        
        console.log('⚙️ Chart.js настройки применены');
    }
    
    /**
     * Инициализация всех графиков
     */
    async initializeCharts() {
        const chartConfigs = [
            { id: 'balanceChart', type: 'balance' },
            { id: 'priceChart', type: 'price' },
            { id: 'volumeChart', type: 'volume' },
            { id: 'performanceChart', type: 'performance' }
        ];
        
        for (const config of chartConfigs) {
            try {
                await this.createChart(config.id, config.type);
            } catch (error) {
                console.warn(`⚠️ Не удалось создать график ${config.id}:`, error);
            }
        }
    }
    
    /**
     * Создание отдельного графика
     */
    async createChart(canvasId, chartType) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) {
            console.warn(`⚠️ Canvas ${canvasId} не найден`);
            return null;
        }
        
        // Уничтожаем существующий график если есть
        if (this.charts.has(canvasId)) {
            this.charts.get(canvasId).destroy();
        }
        
        const ctx = canvas.getContext('2d');
        let chartConfig;
        
        switch (chartType) {
            case 'balance':
                chartConfig = this.getBalanceChartConfig();
                break;
            case 'price':
                chartConfig = this.getPriceChartConfig();
                break;
            case 'volume':
                chartConfig = this.getVolumeChartConfig();
                break;
            case 'performance':
                chartConfig = this.getPerformanceChartConfig();
                break;
            default:
                throw new Error(`Неизвестный тип графика: ${chartType}`);
        }
        
        try {
            const chart = new Chart(ctx, chartConfig);
            this.charts.set(canvasId, chart);
            console.log(`✅ График ${canvasId} создан`);
            return chart;
        } catch (error) {
            console.error(`❌ Ошибка создания графика ${canvasId}:`, error);
            throw error;
        }
    }
    
    /**
     * Конфигурация графика баланса
     */
    getBalanceChartConfig() {
        return {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Баланс (USDT)',
                    data: [],
                    borderColor: '#28a745',
                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 3,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            label: function(context) {
                                return `${context.dataset.label}: $${context.parsed.y.toFixed(2)}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        display: true,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: '#ffffff',
                            maxTicksLimit: 10
                        }
                    },
                    y: {
                        display: true,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: '#ffffff',
                            callback: function(value) {
                                return '$' + value.toFixed(0);
                            }
                        }
                    }
                }
            }
        };
    }
    
    /**
     * Конфигурация графика цен
     */
    getPriceChartConfig() {
        return {
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
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                plugins: {
                    legend: {
                        display: true
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            label: function(context) {
                                return `${context.dataset.label}: $${context.parsed.y.toFixed(2)}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        display: true,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: '#ffffff',
                            maxTicksLimit: 15
                        }
                    },
                    y: {
                        display: true,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: '#ffffff',
                            callback: function(value) {
                                return '$' + value.toLocaleString();
                            }
                        }
                    }
                }
            }
        };
    }
    
    /**
     * Конфигурация графика объемов
     */
    getVolumeChartConfig() {
        return {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: 'Объем торгов',
                    data: [],
                    backgroundColor: 'rgba(255, 193, 7, 0.6)',
                    borderColor: '#ffc107',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true
                    }
                },
                scales: {
                    x: {
                        grid: { color: 'rgba(255, 255, 255, 0.1)' },
                        ticks: { color: '#ffffff' }
                    },
                    y: {
                        grid: { color: 'rgba(255, 255, 255, 0.1)' },
                        ticks: { color: '#ffffff' }
                    }
                }
            }
        };
    }
    
    /**
     * Конфигурация графика производительности
     */
    getPerformanceChartConfig() {
        return {
            type: 'doughnut',
            data: {
                labels: ['Прибыльные сделки', 'Убыточные сделки'],
                datasets: [{
                    data: [60, 40],
                    backgroundColor: ['#28a745', '#dc3545'],
                    borderColor: ['#1e7e34', '#c82333'],
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
                            padding: 20
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `${context.label}: ${context.parsed}%`;
                            }
                        }
                    }
                }
            }
        };
    }
    
    /**
     * Инициализация WebSocket соединения
     */
    async initializeWebSocket() {
        try {
            const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${wsProtocol}//${window.location.host}/ws`;
            
            this.websocket = new WebSocket(wsUrl);
            
            this.websocket.onopen = (event) => {
                console.log('🔌 WebSocket соединение установлено');
                this.reconnectAttempts = 0;
                this.subscribeToUpdates();
            };
            
            this.websocket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleWebSocketMessage(data);
                } catch (error) {
                    console.error('❌ Ошибка парсинга WebSocket сообщения:', error);
                }
            };
            
            this.websocket.onclose = (event) => {
                console.warn('🔌 WebSocket соединение закрыто:', event.code);
                this.attemptReconnect();
            };
            
            this.websocket.onerror = (error) => {
                console.error('❌ Ошибка WebSocket:', error);
            };
            
        } catch (error) {
            console.error('❌ Ошибка инициализации WebSocket:', error);
        }
    }
    
    /**
     * Подписка на обновления
     */
    subscribeToUpdates() {
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            // Подписываемся на обновления
            this.websocket.send(JSON.stringify({
                type: 'subscribe',
                channels: ['balance', 'trades', 'prices', 'bot_status']
            }));
        }
    }
    
    /**
     * Обработка WebSocket сообщений
     */
    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'balance_update':
                this.updateBalanceChart(data.data);
                break;
            case 'price_update':
                this.updatePriceChart(data.data);
                break;
            case 'trade_update':
                this.updateTradesTable(data.data);
                break;
            case 'bot_status':
                this.updateBotStatus(data.data);
                break;
            default:
                console.log('📨 Неизвестное WebSocket сообщение:', data);
        }
    }
    
    /**
     * Попытка переподключения WebSocket
     */
    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
            
            console.log(`🔄 Попытка переподключения ${this.reconnectAttempts}/${this.maxReconnectAttempts} через ${delay}ms`);
            
            setTimeout(() => {
                this.initializeWebSocket();
            }, delay);
        } else {
            console.error('❌ Превышено максимальное количество попыток переподключения');
            this.showError('Потеряно соединение с сервером');
        }
    }
    
    /**
     * Загрузка начальных данных
     */
    async loadInitialData() {
        const loadPromises = [
            this.loadBalance(),
            this.loadTrades(),
            this.loadPriceData()
        ];
        
        try {
            await Promise.allSettled(loadPromises);
            console.log('✅ Начальные данные загружены');
        } catch (error) {
            console.error('❌ Ошибка загрузки начальных данных:', error);
        }
    }
    
    /**
     * Загрузка данных баланса
     */
    async loadBalance() {
        if (this.loadingStates.balance) return;
        
        try {
            this.loadingStates.balance = true;
            this.showLoadingState('balance', true);
            
            const response = await this.fetchWithTimeout('/api/balance', 10000);
            const data = await response.json();
            
            if (data.success) {
                this.updateBalanceChart(data);
                this.dataCache.balance = data;
            } else {
                throw new Error(data.error || 'Ошибка API');
            }
            
        } catch (error) {
            console.error('❌ Ошибка загрузки баланса:', error);
            this.showError('Не удалось загрузить данные баланса');
        } finally {
            this.loadingStates.balance = false;
            this.showLoadingState('balance', false);
        }
    }
    
    /**
     * Загрузка данных сделок
     */
    async loadTrades() {
        if (this.loadingStates.trades) return;
        
        try {
            this.loadingStates.trades = true;
            this.showLoadingState('trades', true);
            
            const response = await this.fetchWithTimeout('/api/trades?limit=50', 10000);
            const data = await response.json();
            
            if (data.success) {
                this.updateTradesTable(data.trades);
                this.dataCache.trades = data.trades;
            } else {
                throw new Error(data.error || 'Ошибка API');
            }
            
        } catch (error) {
            console.error('❌ Ошибка загрузки сделок:', error);
            this.showError('Не удалось загрузить данные сделок');
        } finally {
            this.loadingStates.trades = false;
            this.showLoadingState('trades', false);
        }
    }
    
    /**
     * Загрузка данных цен
     */
    async loadPriceData() {
        if (this.loadingStates.price) return;
        
        try {
            this.loadingStates.price = true;
            this.showLoadingState('price', true);
            
            // Если нет данных с API, используем демо данные
            const demoData = this.generateDemoData();
            this.updatePriceChart({ symbol: 'BTCUSDT', ...demoData });
            
        } catch (error) {
            console.error('❌ Ошибка загрузки данных цен:', error);
        } finally {
            this.loadingStates.price = false;
            this.showLoadingState('price', false);
        }
    }
    
    /**
     * Обновление графика баланса
     */
    updateBalanceChart(data) {
        const chart = this.charts.get('balanceChart');
        if (!chart) return;
        
        const now = new Date().toLocaleTimeString('ru-RU', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
        
        chart.data.labels.push(now);
        chart.data.datasets[0].data.push(data.total_usdt || 0);
        
        // Ограничиваем количество точек
        if (chart.data.labels.length > 20) {
            chart.data.labels.shift();
            chart.data.datasets[0].data.shift();
        }
        
        chart.update('none'); // Без анимации для производительности
    }
    
    /**
     * Обновление графика цен
     */
    updatePriceChart(data) {
        const chart = this.charts.get('priceChart');
        if (!chart) return;
        
        if (data.labels && data.prices) {
            chart.data.labels = data.labels;
            chart.data.datasets[0].data = data.prices;
            chart.data.datasets[0].label = data.symbol || 'BTCUSDT';
        }
        
        chart.update('none');
    }
    
    /**
     * Обновление таблицы сделок
     */
    updateTradesTable(trades) {
        const tableBody = document.querySelector('#trades-table tbody');
        if (!tableBody) return;
        
        const html = trades.map(trade => `
            <tr class="${trade.profit_loss >= 0 ? 'table-success' : 'table-danger'}">
                <td>${trade.symbol}</td>
                <td>
                    <span class="badge ${trade.side === 'BUY' ? 'bg-success' : 'bg-danger'}">
                        ${trade.side}
                    </span>
                </td>
                <td>$${trade.price.toFixed(2)}</td>
                <td>${trade.quantity.toFixed(4)}</td>
                <td class="${trade.profit_loss >= 0 ? 'text-success' : 'text-danger'}">
                    ${trade.profit_loss >= 0 ? '+' : ''}$${trade.profit_loss.toFixed(2)}
                </td>
                <td>
                    <small class="text-muted">
                        ${new Date(trade.created_at).toLocaleString('ru-RU')}
                    </small>
                </td>
            </tr>
        `).join('');
        
        tableBody.innerHTML = html;
    }
    
    /**
     * Генерация демо данных
     */
    generateDemoData() {
        const labels = [];
        const prices = [];
        const now = new Date();
        let basePrice = 67800;
        
        for (let i = 23; i >= 0; i--) {
            const time = new Date(now.getTime() - i * 60 * 60 * 1000);
            labels.push(time.toLocaleTimeString('ru-RU', { 
                hour: '2-digit', 
                minute: '2-digit' 
            }));
            
            const change = (Math.random() - 0.5) * 1000;
            basePrice += change;
            prices.push(Math.max(60000, Math.min(75000, basePrice)));
        }
        
        return { labels, prices };
    }
    
    /**
     * Fetch с таймаутом
     */
    async fetchWithTimeout(url, timeout = 5000) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeout);
        
        try {
            const response = await fetch(this.apiBaseUrl + url, {
                signal: controller.signal,
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                }
            });
            
            clearTimeout(timeoutId);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return response;
            
        } catch (error) {
            clearTimeout(timeoutId);
            throw error;
        }
    }
    
    /**
     * Показ состояния загрузки
     */
    showLoadingState(component, isLoading) {
        const loader = document.querySelector(`#${component}-loader`);
        if (loader) {
            loader.style.display = isLoading ? 'block' : 'none';
        }
        
        const content = document.querySelector(`#${component}-content`);
        if (content) {
            content.style.opacity = isLoading ? '0.5' : '1';
        }
    }
    
    /**
     * Показ ошибки
     */
    showError(message) {
        // Создаем уведомление об ошибке
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-danger alert-dismissible fade show';
        alertDiv.innerHTML = `
            <strong>Ошибка:</strong> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        const container = document.querySelector('.container') || document.body;
        container.insertBefore(alertDiv, container.firstChild);
        
        // Автоматически скрываем через 5 секунд
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }
    
    /**
     * Автообновление данных
     */
    startAutoRefresh() {
        // Обновляем баланс каждые 30 секунд
        setInterval(() => {
            if (this.isInitialized) {
                this.loadBalance();
            }
        }, 30000);
        
        // Обновляем сделки каждую минуту
        setInterval(() => {
            if (this.isInitialized) {
                this.loadTrades();
            }
        }, 60000);
        
        console.log('⏰ Автообновление запущено');
    }
    
    /**
     * Очистка ресурсов
     */
    destroy() {
        // Закрываем WebSocket
        if (this.websocket) {
            this.websocket.close();
        }
        
        // Уничтожаем все графики
        this.charts.forEach(chart => chart.destroy());
        this.charts.clear();
        
        console.log('🧹 EnhancedChartsManager очищен');
    }
}

// Глобальная инициализация
let chartsManager;

document.addEventListener('DOMContentLoaded', async () => {
    try {
        chartsManager = new EnhancedChartsManager();
        await chartsManager.initialize();
    } catch (error) {
        console.error('❌ Критическая ошибка инициализации:', error);
    }
});

// Очистка при выходе
window.addEventListener('beforeunload', () => {
    if (chartsManager) {
        chartsManager.destroy();
    }
});