/**
 * Модуль для работы с графиками TradingView и real-time обновлениями
 * Файл: src/web/static/js/charts.js
 */

class ChartManager {
    constructor() {
        this.charts = {};
        this.widgets = {};
        this.activeSymbols = new Set();
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
    }

    /**
     * Инициализация менеджера графиков
     */
    async init() {
        console.log('Инициализация ChartManager...');
        
        // Подключаемся к WebSocket
        await this.connectWebSocket();
        
        // Загружаем активные символы
        await this.loadActiveSymbols();
        
        // Создаем основной график
        this.createMainChart();
        
        // Создаем мини-графики для активных пар
        this.createMiniCharts();
        
        // Настраиваем обработчики событий
        this.setupEventHandlers();
    }

    /**
     * Подключение к WebSocket серверу
     */
    async connectWebSocket() {
        const wsUrl = `ws://${window.location.host}/ws`;
        
        try {
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => {
                console.log('WebSocket подключен');
                this.reconnectAttempts = 0;
                
                // Подписываемся на обновления
                this.subscribeToUpdates();
            };
            
            this.ws.onmessage = (event) => {
                this.handleWebSocketMessage(JSON.parse(event.data));
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket ошибка:', error);
            };
            
            this.ws.onclose = () => {
                console.log('WebSocket отключен');
                this.handleReconnect();
            };
            
        } catch (error) {
            console.error('Ошибка подключения WebSocket:', error);
            this.handleReconnect();
        }
    }

    /**
     * Обработка переподключения
     */
    handleReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
            
            console.log(`Переподключение через ${delay/1000} сек...`);
            
            setTimeout(() => {
                this.connectWebSocket();
            }, delay);
        } else {
            console.error('Превышено количество попыток переподключения');
            this.showConnectionError();
        }
    }

    /**
     * Создание основного графика TradingView
     */
    createMainChart() {
        const container = document.getElementById('main-chart-container');
        if (!container) return;

        // Конфигурация TradingView Widget
        const widgetConfig = {
            container_id: "main-chart-container",
            width: "100%",
            height: 600,
            symbol: "BINANCE:BTCUSDT",
            interval: "15",
            timezone: "Etc/UTC",
            theme: "dark",
            style: "1",
            locale: "ru",
            toolbar_bg: "#1e222d",
            enable_publishing: false,
            allow_symbol_change: true,
            watchlist: Array.from(this.activeSymbols),
            details: true,
            hotlist: true,
            calendar: true,
            studies: [
                "MASimple@tv-basicstudies",
                "RSI@tv-basicstudies",
                "MACD@tv-basicstudies"
            ],
            save_image: false,
            show_popup_button: true,
            popup_width: "1000",
            popup_height: "650"
        };

        // Создаем виджет
        this.widgets.main = new TradingView.widget(widgetConfig);
        
        // Сохраняем референс на график
        this.widgets.main.onChartReady(() => {
            this.charts.main = this.widgets.main.chart();
            this.setupChartCallbacks();
            this.addTradeMarkers();
        });
    }

    /**
     * Создание мини-графиков для активных пар
     */
    createMiniCharts() {
        const container = document.getElementById('mini-charts-container');
        if (!container) return;

        container.innerHTML = '';
        
        this.activeSymbols.forEach((symbol, index) => {
            const chartDiv = document.createElement('div');
            chartDiv.className = 'mini-chart';
            chartDiv.id = `mini-chart-${index}`;
            container.appendChild(chartDiv);

            const miniWidget = new TradingView.widget({
                container_id: chartDiv.id,
                width: "100%",
                height: 200,
                symbol: `BINANCE:${symbol}`,
                interval: "5",
                timezone: "Etc/UTC",
                theme: "dark",
                style: "1",
                locale: "ru",
                toolbar_bg: "#1e222d",
                enable_publishing: false,
                hide_side_toolbar: true,
                hide_top_toolbar: true,
                allow_symbol_change: false,
                save_image: false
            });

            this.widgets[symbol] = miniWidget;
        });
    }

    /**
     * Загрузка активных торговых пар
     */
    async loadActiveSymbols() {
        try {
            const response = await fetch('/api/active-symbols');
            const data = await response.json();
            
            this.activeSymbols = new Set(data.symbols || ['BTCUSDT', 'ETHUSDT']);
            
        } catch (error) {
            console.error('Ошибка загрузки активных символов:', error);
            // Используем дефолтные значения
            this.activeSymbols = new Set(['BTCUSDT', 'ETHUSDT', 'BNBUSDT']);
        }
    }

    /**
     * Добавление маркеров сделок на график
     */
    async addTradeMarkers() {
        if (!this.charts.main) return;

        try {
            const response = await fetch('/api/recent-trades');
            const trades = await response.json();

            trades.forEach(trade => {
                const shape = trade.side === 'buy' ? 
                    this.charts.main.createShape({
                        time: trade.timestamp,
                        price: trade.price
                    }, {
                        shape: 'arrow_up',
                        text: `Buy: ${trade.quantity}`,
                        lock: true,
                        disableSelection: true,
                        disableSave: true,
                        disableUndo: true,
                        overrides: {
                            color: '#26a69a',
                            textcolor: '#26a69a',
                            fontsize: 12
                        }
                    }) :
                    this.charts.main.createShape({
                        time: trade.timestamp,
                        price: trade.price
                    }, {
                        shape: 'arrow_down',
                        text: `Sell: ${trade.quantity}`,
                        lock: true,
                        disableSelection: true,
                        disableSave: true,
                        disableUndo: true,
                        overrides: {
                            color: '#ef5350',
                            textcolor: '#ef5350',
                            fontsize: 12
                        }
                    });
            });
            
        } catch (error) {
            console.error('Ошибка загрузки маркеров сделок:', error);
        }
    }

    /**
     * Обработка WebSocket сообщений
     */
    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'trade_update':
                this.handleTradeUpdate(data.payload);
                break;
                
            case 'price_update':
                this.handlePriceUpdate(data.payload);
                break;
                
            case 'signal_generated':
                this.handleNewSignal(data.payload);
                break;
                
            case 'balance_update':
                this.updateBalance(data.payload);
                break;
                
            default:
                console.log('Неизвестный тип сообщения:', data.type);
        }
    }

    /**
     * Обработка обновления сделки
     */
    handleTradeUpdate(trade) {
        // Добавляем маркер на основной график
        if (this.charts.main && trade.symbol === this.getCurrentSymbol()) {
            const shape = trade.action === 'open' ?
                this.charts.main.createShape({
                    time: Date.now() / 1000,
                    price: trade.price
                }, {
                    shape: 'arrow_up',
                    text: `${trade.side}: ${trade.quantity}`,
                    overrides: {
                        color: trade.side === 'buy' ? '#26a69a' : '#ef5350'
                    }
                }) : null;
        }

        // Обновляем статистику
        this.updateTradeStats(trade);
        
        // Показываем уведомление
        this.showNotification({
            title: 'Новая сделка',
            message: `${trade.action} ${trade.side} ${trade.quantity} ${trade.symbol} @ ${trade.price}`,
            type: trade.action === 'open' ? 'info' : trade.profit > 0 ? 'success' : 'warning'
        });
    }

    /**
     * Обработка нового сигнала
     */
    handleNewSignal(signal) {
        // Показываем алерт на графике
        if (this.charts.main && signal.symbol === this.getCurrentSymbol()) {
            this.charts.main.createMultipointShape([{
                time: Date.now() / 1000,
                price: signal.price
            }], {
                shape: 'callout',
                text: `${signal.action} Signal (${(signal.confidence * 100).toFixed(0)}%)`,
                overrides: {
                    color: signal.action === 'buy' ? '#4caf50' : '#f44336',
                    bordercolor: signal.action === 'buy' ? '#4caf50' : '#f44336'
                }
            });
        }

        // Показываем уведомление
        this.showNotification({
            title: 'Новый сигнал',
            message: `${signal.strategy}: ${signal.action} ${signal.symbol} (уверенность: ${(signal.confidence * 100).toFixed(0)}%)`,
            type: 'info',
            duration: 10000
        });
    }

    /**
     * Обновление статистики сделок
     */
    updateTradeStats(trade) {
        // Обновляем счетчики
        const openTradesEl = document.getElementById('open-trades-count');
        const todayTradesEl = document.getElementById('today-trades-count');
        const winRateEl = document.getElementById('win-rate');
        
        if (trade.action === 'open' && openTradesEl) {
            const count = parseInt(openTradesEl.textContent) || 0;
            openTradesEl.textContent = count + 1;
        } else if (trade.action === 'close' && openTradesEl) {
            const count = parseInt(openTradesEl.textContent) || 0;
            openTradesEl.textContent = Math.max(0, count - 1);
        }
    }

    /**
     * Получение текущего символа с основного графика
     */
    getCurrentSymbol() {
        return this.charts.main ? this.charts.main.symbol() : 'BTCUSDT';
    }

    /**
     * Подписка на обновления через WebSocket
     */
    subscribeToUpdates() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                action: 'subscribe',
                channels: ['trades', 'signals', 'prices', 'balance'],
                symbols: Array.from(this.activeSymbols)
            }));
        }
    }

    /**
     * Настройка обработчиков событий
     */
    setupEventHandlers() {
        // Смена временного интервала
        document.querySelectorAll('.timeframe-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const interval = e.target.dataset.interval;
                if (this.charts.main) {
                    this.charts.main.setInterval(interval);
                }
            });
        });

        // Добавление новой пары
        const addSymbolBtn = document.getElementById('add-symbol-btn');
        if (addSymbolBtn) {
            addSymbolBtn.addEventListener('click', () => {
                this.showAddSymbolDialog();
            });
        }

        // Обновление графиков
        const refreshBtn = document.getElementById('refresh-charts-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.refreshAllCharts();
            });
        }
    }

    /**
     * Обновление всех графиков
     */
    refreshAllCharts() {
        // Перезагружаем маркеры сделок
        this.addTradeMarkers();
        
        // Обновляем мини-графики
        this.createMiniCharts();
        
        // Показываем уведомление
        this.showNotification({
            title: 'Графики обновлены',
            type: 'success',
            duration: 2000
        });
    }

    /**
     * Показ уведомления
     */
    showNotification(options) {
        const {title, message, type = 'info', duration = 5000} = options;
        
        // Создаем элемент уведомления
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-header">${title}</div>
            <div class="notification-body">${message}</div>
        `;
        
        // Добавляем в контейнер
        const container = document.getElementById('notifications-container') || document.body;
        container.appendChild(notification);
        
        // Анимация появления
        setTimeout(() => notification.classList.add('show'), 100);
        
        // Автоматическое скрытие
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, duration);
    }

    /**
     * Показ ошибки подключения
     */
    showConnectionError() {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'connection-error';
        errorDiv.innerHTML = `
            <i class="fas fa-exclamation-triangle"></i>
            <span>Потеряно соединение с сервером</span>
            <button onclick="location.reload()">Обновить страницу</button>
        `;
        document.body.appendChild(errorDiv);
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    window.chartManager = new ChartManager();
    window.chartManager.init();
});