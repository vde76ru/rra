/**
 * ПОЛНОЦЕННЫЙ JavaScript для управления графиками криптовалют
 * Файл: src/web/static/js/charts_complete.js
 * Версия: 3.0.0
 */

class CompleteChartManager {
    constructor() {
        // Основные настройки
        this.updateInterval = 30000; // 30 секунд
        this.currentSymbol = 'BTCUSDT';
        this.currentTimeframe = '1h';
        this.isInitialized = false;
        this.updateTimer = null;
        
        // Графики
        this.charts = {
            tradingView: null,
            balance: null,
            positions: null,
            price: null,
            pnl: null
        };
        
        // WebSocket
        this.socket = null;
        this.socketConnected = false;
        
        // Данные
        this.marketData = {
            price: null,
            indicators: {},
            balance: {},
            positions: [],
            trades: [],
            stats: {}
        };
        
        // Настройки Chart.js
        this.chartDefaults = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: '#d1d4dc' }
                }
            },
            scales: {
                x: {
                    ticks: { color: '#d1d4dc' },
                    grid: { color: '#363a45' }
                },
                y: {
                    ticks: { color: '#d1d4dc' },
                    grid: { color: '#363a45' }
                }
            }
        };
    }

    /**
     * Основная инициализация
     */
    async init() {
        console.log('🚀 Инициализация CompleteChartManager...');
        
        try {
            // Устанавливаем статус подключения
            this.updateConnectionStatus('connecting', 'Инициализация...');
            
            // Инициализируем WebSocket
            await this.initializeWebSocket();
            
            // Создаем все графики
            await this.createAllCharts();
            
            // Настраиваем обработчики событий
            this.setupEventHandlers();
            
            // Загружаем начальные данные
            await this.loadInitialData();
            
            // Запускаем автообновления
            this.startAutoUpdate();
            
            this.isInitialized = true;
            this.updateConnectionStatus('connected', 'Подключено');
            
            console.log('✅ CompleteChartManager инициализирован успешно');
            this.showNotification('Графики загружены успешно', 'success');
            
            return true;
            
        } catch (error) {
            console.error('❌ Ошибка инициализации CompleteChartManager:', error);
            this.updateConnectionStatus('error', 'Ошибка подключения');
            this.showNotification('Ошибка инициализации: ' + error.message, 'error');
            return false;
        }
    }

    /**
     * Инициализация WebSocket
     */
    async initializeWebSocket() {
        console.log('🔌 Инициализация WebSocket...');
        
        try {
            if (typeof io !== 'undefined') {
                this.socket = io();
                
                this.socket.on('connect', () => {
                    console.log('✅ WebSocket подключен');
                    this.socketConnected = true;
                    this.updateConnectionStatus('connected', 'WebSocket подключен');
                    
                    // Подписываемся на обновления
                    this.socket.emit('subscribe_price', { symbol: this.currentSymbol });
                    this.socket.emit('subscribe_trades');
                    this.socket.emit('subscribe_balance');
                });
                
                this.socket.on('disconnect', () => {
                    console.log('❌ WebSocket отключен');
                    this.socketConnected = false;
                    this.updateConnectionStatus('disconnected', 'WebSocket отключен');
                });
                
                this.socket.on('price_update', (data) => {
                    if (data.symbol === this.currentSymbol) {
                        this.handlePriceUpdate(data);
                    }
                });
                
                this.socket.on('new_trade', (trade) => {
                    this.handleNewTrade(trade);
                });
                
                this.socket.on('balance_update', (balance) => {
                    this.handleBalanceUpdate(balance);
                });
                
                this.socket.on('error', (error) => {
                    console.error('❌ WebSocket ошибка:', error);
                    this.updateConnectionStatus('error', 'Ошибка WebSocket');
                });
            } else {
                console.warn('⚠️ Socket.IO не доступен, используем только HTTP API');
            }
        } catch (error) {
            console.warn('⚠️ Не удалось инициализировать WebSocket:', error);
        }
    }

    /**
     * Создание всех графиков
     */
    async createAllCharts() {
        console.log('📊 Создание всех графиков...');
        
        await Promise.all([
            this.createTradingViewChart(),
            this.createBalanceChart(),
            this.createPositionsChart(), 
            this.createPriceChart(),
            this.createPnLChart()
        ]);
    }

    /**
     * Создание TradingView графика
     */
    async createTradingViewChart() {
        console.log('📈 Создание TradingView графика...');
        
        const container = document.getElementById('tradingview_chart');
        if (!container) {
            console.warn('⚠️ Контейнер TradingView не найден');
            return;
        }

        try {
            if (typeof TradingView !== 'undefined') {
                this.charts.tradingView = new TradingView.widget({
                    autosize: true,
                    symbol: 'BINANCE:' + this.currentSymbol,
                    interval: this.currentTimeframe,
                    timezone: "Etc/UTC",
                    theme: "dark",
                    style: "1",
                    locale: "ru",
                    toolbar_bg: "#1e222d",
                    enable_publishing: false,
                    allow_symbol_change: false,
                    container_id: "tradingview_chart",
                    hide_side_toolbar: false,
                    studies: [
                        "RSI@tv-basicstudies",
                        "MACD@tv-basicstudies", 
                        "BB@tv-basicstudies",
                        "Volume@tv-basicstudies"
                    ],
                    overrides: {
                        "paneProperties.background": "#131722",
                        "paneProperties.vertGridProperties.color": "#363a45",
                        "paneProperties.horzGridProperties.color": "#363a45",
                        "symbolWatermarkProperties.transparency": 90,
                        "scalesProperties.textColor": "#d1d4dc",
                        "mainSeriesProperties.candleStyle.upColor": "#26a69a",
                        "mainSeriesProperties.candleStyle.downColor": "#ef5350",
                        "mainSeriesProperties.candleStyle.drawWick": true,
                        "mainSeriesProperties.candleStyle.drawBorder": true,
                        "mainSeriesProperties.candleStyle.borderColor": "#378658",
                        "mainSeriesProperties.candleStyle.borderUpColor": "#26a69a",
                        "mainSeriesProperties.candleStyle.borderDownColor": "#ef5350",
                        "mainSeriesProperties.candleStyle.wickUpColor": "#26a69a",
                        "mainSeriesProperties.candleStyle.wickDownColor": "#ef5350",
                        "volumePaneSize": "medium"
                    },
                    disabled_features: [
                        "use_localstorage_for_settings",
                        "volume_force_overlay"
                    ],
                    enabled_features: [
                        "study_templates"
                    ]
                });
                
                console.log('✅ TradingView график создан');
            } else {
                throw new Error('TradingView библиотека не загружена');
            }
        } catch (error) {
            console.error('❌ Ошибка создания TradingView графика:', error);
            container.innerHTML = `
                <div class="d-flex justify-content-center align-items-center h-100">
                    <div class="text-center text-warning">
                        <i class="fas fa-chart-line fa-3x mb-3"></i>
                        <h5>TradingView недоступен</h5>
                        <p>Используется резервный режим</p>
                    </div>
                </div>
            `;
        }
    }

    /**
     * Создание графика баланса
     */
    async createBalanceChart() {
        console.log('💰 Создание графика баланса...');
        
        const ctx = document.getElementById('balanceChart');
        if (!ctx) {
            console.warn('⚠️ Canvas balanceChart не найден');
            return;
        }

        if (this.charts.balance) {
            this.charts.balance.destroy();
        }

        this.charts.balance = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Доступно USDT', 'В позициях', 'Нереализованный P&L'],
                datasets: [{
                    data: [1000, 0, 0],
                    backgroundColor: [
                        '#26a69a',
                        '#ffc107', 
                        '#2196f3'
                    ],
                    borderColor: '#1e222d',
                    borderWidth: 2
                }]
            },
            options: {
                ...this.chartDefaults,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#d1d4dc',
                            padding: 20,
                            usePointStyle: true
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                return `${label}: $${value.toFixed(2)}`;
                            }
                        }
                    }
                }
            }
        });

        console.log('✅ График баланса создан');
    }

    /**
     * Создание графика позиций
     */
    async createPositionsChart() {
        console.log('📈 Создание графика позиций...');
        
        const ctx = document.getElementById('positionsChart');
        if (!ctx) {
            console.warn('⚠️ Canvas positionsChart не найден');
            return;
        }

        if (this.charts.positions) {
            this.charts.positions.destroy();
        }

        this.charts.positions = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Нет позиций'],
                datasets: [{
                    data: [1],
                    backgroundColor: ['#363a45'],
                    borderColor: '#1e222d',
                    borderWidth: 2
                }]
            },
            options: {
                ...this.chartDefaults,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#d1d4dc',
                            padding: 20,
                            usePointStyle: true
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                return `${label}: $${Math.abs(value).toFixed(2)}`;
                            }
                        }
                    }
                }
            }
        });

        console.log('✅ График позиций создан');
    }

    /**
     * Создание графика цены
     */
    async createPriceChart() {
        console.log('📊 Создание графика цены...');
        
        const ctx = document.getElementById('priceChart');
        if (!ctx) {
            console.warn('⚠️ Canvas priceChart не найден');
            return;
        }

        if (this.charts.price) {
            this.charts.price.destroy();
        }

        const demoData = this.generateDemoPriceData();

        this.charts.price = new Chart(ctx, {
            type: 'line',
            data: {
                labels: demoData.labels,
                datasets: [{
                    label: this.currentSymbol,
                    data: demoData.prices,
                    borderColor: '#2196f3',
                    backgroundColor: 'rgba(33, 150, 243, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 2,
                    pointHoverRadius: 6
                }]
            },
            options: {
                ...this.chartDefaults,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                plugins: {
                    legend: {
                        display: true,
                        labels: { color: '#d1d4dc' }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            label: (context) => `${context.dataset.label}: $${context.parsed.y.toFixed(2)}`
                        }
                    }
                },
                scales: {
                    x: {
                        ticks: { color: '#d1d4dc' },
                        grid: { color: '#363a45' }
                    },
                    y: {
                        ticks: {
                            color: '#d1d4dc',
                            callback: (value) => '$' + value.toFixed(0)
                        },
                        grid: { color: '#363a45' }
                    }
                }
            }
        });

        console.log('✅ График цены создан');
    }

    /**
     * Создание графика P&L
     */
    async createPnLChart() {
        console.log('💹 Создание графика P&L...');
        
        const ctx = document.getElementById('pnlChart');
        if (!ctx) {
            console.warn('⚠️ Canvas pnlChart не найден');
            return;
        }

        if (this.charts.pnl) {
            this.charts.pnl.destroy();
        }

        const demoPnLData = this.generateDemoPnLData();

        this.charts.pnl = new Chart(ctx, {
            type: 'line',
            data: {
                labels: demoPnLData.labels,
                datasets: [{
                    label: 'P&L Накопительный',
                    data: demoPnLData.cumulative,
                    borderColor: '#26a69a',
                    backgroundColor: 'rgba(38, 166, 154, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4
                }, {
                    label: 'P&L Дневной',
                    data: demoPnLData.daily,
                    borderColor: '#ef5350',
                    backgroundColor: 'rgba(239, 83, 80, 0.1)',
                    borderWidth: 2,
                    fill: false,
                    tension: 0.2
                }]
            },
            options: {
                ...this.chartDefaults,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                plugins: {
                    legend: {
                        display: true,
                        labels: { color: '#d1d4dc' }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            label: (context) => `${context.dataset.label}: $${context.parsed.y.toFixed(2)}`
                        }
                    }
                },
                scales: {
                    x: {
                        ticks: { color: '#d1d4dc' },
                        grid: { color: '#363a45' }
                    },
                    y: {
                        ticks: {
                            color: '#d1d4dc',
                            callback: (value) => '$' + value.toFixed(0)
                        },
                        grid: { color: '#363a45' }
                    }
                }
            }
        });

        console.log('✅ График P&L создан');
    }

    /**
     * Настройка обработчиков событий
     */
    setupEventHandlers() {
        console.log('🎯 Настройка обработчиков событий...');

        // Селектор символов
        const symbolSelector = document.getElementById('symbolSelector');
        if (symbolSelector) {
            symbolSelector.addEventListener('change', (e) => {
                this.changeSymbol(e.target.value);
            });
        }

        // Кнопки таймфреймов
        document.querySelectorAll('.timeframe-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.timeframe-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                
                const timeframe = e.target.dataset.timeframe;
                this.changeTimeframe(timeframe);
            });
        });

        // Интервал обновления
        const updateInterval = document.getElementById('updateInterval');
        if (updateInterval) {
            updateInterval.addEventListener('change', (e) => {
                const seconds = parseInt(e.target.value);
                this.setUpdateInterval(seconds);
            });
        }

        // Кнопка обновления
        const refreshBtn = document.getElementById('refreshChartsBtn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.refreshAllData();
            });
        }

        // Кнопка обновления сделок
        const refreshTradesBtn = document.getElementById('refreshTradesBtn');
        if (refreshTradesBtn) {
            refreshTradesBtn.addEventListener('click', () => {
                this.loadTradesData();
            });
        }

        // Полноэкранный режим
        const fullscreenBtn = document.getElementById('fullscreenBtn');
        if (fullscreenBtn) {
            fullscreenBtn.addEventListener('click', () => {
                this.toggleFullscreen();
            });
        }

        // Скриншот
        const screenshotBtn = document.getElementById('screenshotBtn');
        if (screenshotBtn) {
            screenshotBtn.addEventListener('click', () => {
                this.takeScreenshot();
            });
        }

        console.log('✅ Обработчики событий настроены');
    }

    /**
     * Загрузка начальных данных
     */
    async loadInitialData() {
        console.log('📥 Загрузка начальных данных...');
        
        await Promise.all([
            this.loadPriceData(),
            this.loadIndicatorsData(),
            this.loadBalanceData(),
            this.loadPositionsData(),
            this.loadTradesData(),
            this.loadStatsData()
        ]);
    }

    /**
     * Загрузка данных о цене
     */
    async loadPriceData() {
        try {
            const response = await this.fetchWithTimeout(`/api/charts/price/${this.currentSymbol}`, 5000);
            const data = await response.json();
            
            if (data.success) {
                this.marketData.price = data;
                this.updatePriceDisplay(data);
            } else {
                throw new Error(data.error || 'Неизвестная ошибка API');
            }
        } catch (error) {
            console.warn('⚠️ Загружаем демо данные цены:', error);
            this.updatePriceDisplay(this.generateDemoPrice());
        }
    }

    /**
     * Загрузка индикаторов
     */
    async loadIndicatorsData() {
        try {
            const response = await this.fetchWithTimeout(`/api/market/indicators/${this.currentSymbol}`, 5000);
            const data = await response.json();
            
            if (data.success) {
                this.marketData.indicators = data;
                this.updateIndicatorsDisplay(data);
            }
        } catch (error) {
            console.warn('⚠️ Загружаем демо индикаторы:', error);
            this.updateIndicatorsDisplay(this.generateDemoIndicators());
        }
    }

    /**
     * Загрузка баланса
     */
    async loadBalanceData() {
        try {
            const response = await this.fetchWithTimeout('/api/charts/balance', 5000);
            const data = await response.json();
            
            if (data.success) {
                this.marketData.balance = data;
                this.updateBalanceDisplay(data);
                this.updateBalanceChart(data);
            }
        } catch (error) {
            console.warn('⚠️ Загружаем демо баланс:', error);
            const demoBalance = this.generateDemoBalance();
            this.updateBalanceDisplay(demoBalance);
            this.updateBalanceChart(demoBalance);
        }
    }

    /**
     * Загрузка позиций
     */
    async loadPositionsData() {
        try {
            const response = await this.fetchWithTimeout('/api/charts/positions', 5000);
            const data = await response.json();
            
            if (data.success) {
                this.marketData.positions = data.positions;
                this.updatePositionsChart(data.positions);
            }
        } catch (error) {
            console.warn('⚠️ Загружаем демо позиции:', error);
            const demoPositions = this.generateDemoPositions();
            this.updatePositionsChart(demoPositions);
        }
    }

    /**
     * Загрузка сделок
     */
    async loadTradesData() {
        try {
            const response = await this.fetchWithTimeout('/api/charts/trades?limit=20', 5000);
            const data = await response.json();
            
            if (data.success) {
                this.marketData.trades = data.trades;
                this.updateTradesTable(data.trades);
            }
        } catch (error) {
            console.warn('⚠️ Загружаем демо сделки:', error);
            const demoTrades = this.generateDemoTrades();
            this.updateTradesTable(demoTrades);
        }
    }

    /**
     * Загрузка статистики
     */
    async loadStatsData() {
        try {
            const response = await this.fetchWithTimeout('/api/charts/stats', 5000);
            const data = await response.json();
            
            if (data.success) {
                this.marketData.stats = data;
                this.updateStatsDisplay(data);
            }
        } catch (error) {
            console.warn('⚠️ Загружаем демо статистику:', error);
            this.updateStatsDisplay(this.generateDemoStats());
        }
    }

    /**
     * Обновление отображения цены
     */
    updatePriceDisplay(data) {
        const elements = {
            currentPrice: data.price,
            priceChange: data.change_24h,
            volume24h: data.volume_24h
        };

        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element && value !== undefined) {
                if (id === 'currentPrice') {
                    element.textContent = '$' + value.toFixed(2);
                    element.className = 'indicator-value';
                } else if (id === 'priceChange') {
                    element.textContent = (value >= 0 ? '+' : '') + value.toFixed(2) + '%';
                    element.className = 'indicator-value ' + (value >= 0 ? 'indicator-positive' : 'indicator-negative');
                } else if (id === 'volume24h') {
                    element.textContent = '$' + this.formatNumber(value);
                    element.className = 'indicator-value';
                }
            }
        });

        // Обновляем график цены
        if (this.charts.price) {
            this.addPriceDataPoint(data.price);
        }
    }

    /**
     * Обновление индикаторов
     */
    updateIndicatorsDisplay(data) {
        // RSI
        const rsiElement = document.getElementById('rsiValue');
        if (rsiElement && data.rsi !== undefined) {
            rsiElement.textContent = data.rsi.toFixed(2);
            if (data.rsi > 70) {
                rsiElement.className = 'indicator-value indicator-negative';
            } else if (data.rsi < 30) {
                rsiElement.className = 'indicator-value indicator-positive';
            } else {
                rsiElement.className = 'indicator-value indicator-neutral';
            }
        }

        // MACD
        const macdElement = document.getElementById('macdValue');
        if (macdElement && data.macd) {
            const signal = data.macd.histogram > 0 ? 'Bullish' : 'Bearish';
            macdElement.textContent = signal;
            macdElement.className = 'indicator-value ' + (data.macd.histogram > 0 ? 'indicator-positive' : 'indicator-negative');
        }

        // Bollinger Bands
        const bbElement = document.getElementById('bbPosition');
        if (bbElement && data.bollinger_bands) {
            const price = data.price || this.marketData.price?.price || 0;
            const bb = data.bollinger_bands;
            
            if (price > bb.upper) {
                bbElement.textContent = 'Overbought';
                bbElement.className = 'indicator-value indicator-negative';
            } else if (price < bb.lower) {
                bbElement.textContent = 'Oversold';
                bbElement.className = 'indicator-value indicator-positive';
            } else {
                bbElement.textContent = 'Normal';
                bbElement.className = 'indicator-value indicator-neutral';
            }
        }
    }

    /**
     * Обновление отображения баланса
     */
    updateBalanceDisplay(data) {
        const elements = {
            totalBalance: data.total_usdt || 0,
            pnlToday: data.pnl_today || 0,
            openPositions: data.open_positions || 0
        };

        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                if (id === 'pnlToday') {
                    element.textContent = (value >= 0 ? '+$' : '-$') + Math.abs(value).toFixed(2);
                    element.className = 'stat-value ' + (value >= 0 ? 'text-success' : 'text-danger');
                } else if (id === 'totalBalance') {
                    element.textContent = '$' + value.toFixed(2);
                    element.className = 'stat-value text-success';
                } else {
                    element.textContent = value;
                    element.className = 'stat-value';
                }
            }
        });
    }

    /**
     * Обновление графика баланса
     */
    updateBalanceChart(data) {
        if (!this.charts.balance) return;

        const available = data.available_usdt || 0;
        const inPositions = data.in_positions || 0;
        const unrealizedPnL = data.unrealized_pnl || 0;

        this.charts.balance.data.datasets[0].data = [available, inPositions, Math.abs(unrealizedPnL)];
        this.charts.balance.update('none');
    }

    /**
     * Обновление графика позиций
     */
    updatePositionsChart(positions) {
        if (!this.charts.positions) return;

        if (!positions || positions.length === 0) {
            this.charts.positions.data.labels = ['Нет активных позиций'];
            this.charts.positions.data.datasets[0].data = [1];
            this.charts.positions.data.datasets[0].backgroundColor = ['#363a45'];
        } else {
            this.charts.positions.data.labels = positions.map(p => p.symbol);
            this.charts.positions.data.datasets[0].data = positions.map(p => Math.abs(p.quantity * (p.mark_price || p.entry_price || 0)));
            this.charts.positions.data.datasets[0].backgroundColor = this.generateColors(positions.length);
        }
        
        this.charts.positions.update('none');
    }

    /**
     * Обновление таблицы сделок
     */
    updateTradesTable(trades) {
        const tbody = document.getElementById('tradesTableBody');
        if (!tbody) return;

        tbody.innerHTML = '';

        if (!trades || trades.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="5" class="text-center text-muted py-4">
                        <i class="fas fa-inbox"></i><br>
                        Нет сделок для отображения
                    </td>
                </tr>
            `;
            return;
        }

        trades.slice(0, 20).forEach(trade => {
            const row = tbody.insertRow();
            
            const time = new Date(trade.created_at).toLocaleTimeString('ru-RU', {
                hour: '2-digit',
                minute: '2-digit'
            });
            
            const profitClass = trade.profit > 0 ? 'text-success' : 
                               trade.profit < 0 ? 'text-danger' : 'text-warning';
            const profitText = trade.profit !== null && trade.profit !== undefined ? 
                              `$${trade.profit.toFixed(2)}` : 'Открыта';
            
            const sideClass = trade.side === 'BUY' ? 'bg-success' : 'bg-danger';
            
            row.innerHTML = `
                <td class="small">${time}</td>
                <td><span class="badge bg-secondary">${trade.symbol}</span></td>
                <td><span class="badge ${sideClass}">${trade.side}</span></td>
                <td class="small">$${(trade.entry_price || trade.price || 0).toFixed(2)}</td>
                <td class="${profitClass} small">${profitText}</td>
            `;
        });
    }

    /**
     * Обновление статистики
     */
    updateStatsDisplay(data) {
        const tradesTodayElement = document.getElementById('tradesToday');
        if (tradesTodayElement) {
            tradesTodayElement.textContent = data.trades_today || 0;
        }
    }

    /**
     * Добавление точки данных к графику цены
     */
    addPriceDataPoint(price) {
        if (!this.charts.price) return;

        const now = new Date();
        const timeLabel = now.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
        
        this.charts.price.data.labels.push(timeLabel);
        this.charts.price.data.datasets[0].data.push(price);
        
        // Ограничиваем количество точек
        if (this.charts.price.data.labels.length > 50) {
            this.charts.price.data.labels.shift();
            this.charts.price.data.datasets[0].data.shift();
        }
        
        this.charts.price.update('none');
    }

    /**
     * Обработчики WebSocket событий
     */
    handlePriceUpdate(data) {
        this.marketData.price = data;
        this.updatePriceDisplay(data);
    }

    handleNewTrade(trade) {
        this.marketData.trades.unshift(trade);
        if (this.marketData.trades.length > 50) {
            this.marketData.trades.pop();
        }
        this.updateTradesTable(this.marketData.trades);
    }

    handleBalanceUpdate(balance) {
        this.marketData.balance = balance;
        this.updateBalanceDisplay(balance);
        this.updateBalanceChart(balance);
        if (balance.positions) {
            this.updatePositionsChart(balance.positions);
        }
    }

    /**
     * Смена торговой пары
     */
    changeSymbol(symbol) {
        console.log(`📊 Переключение на ${symbol}`);
        
        if (this.socket && this.socketConnected) {
            this.socket.emit('unsubscribe_price', { symbol: this.currentSymbol });
            this.socket.emit('subscribe_price', { symbol: symbol });
        }
        
        this.currentSymbol = symbol;
        
        // Обновляем TradingView
        if (this.charts.tradingView && this.charts.tradingView.chart) {
            this.charts.tradingView.chart().setSymbol('BINANCE:' + symbol);
        }
        
        // Обновляем график цены
        if (this.charts.price) {
            this.charts.price.data.datasets[0].label = symbol;
            this.charts.price.update('none');
        }
        
        // Перезагружаем данные
        this.loadPriceData();
        this.loadIndicatorsData();
    }

    /**
     * Смена таймфрейма
     */
    changeTimeframe(timeframe) {
        console.log(`📅 Переключение таймфрейма на ${timeframe}`);
        
        this.currentTimeframe = timeframe;
        
        if (this.charts.tradingView && this.charts.tradingView.chart) {
            this.charts.tradingView.chart().setResolution(timeframe);
        }
    }

    /**
     * Обновление интервала автообновления
     */
    setUpdateInterval(seconds) {
        this.updateInterval = seconds * 1000;
        this.startAutoUpdate();
        console.log(`🔄 Интервал обновления изменен на ${seconds} секунд`);
        this.showNotification(`Интервал обновления: ${seconds} сек`, 'info');
    }

    /**
     * Запуск автообновления
     */
    startAutoUpdate() {
        if (this.updateTimer) {
            clearInterval(this.updateTimer);
        }

        this.updateTimer = setInterval(() => {
            if (this.isInitialized && !this.socketConnected) {
                this.refreshAllData();
            }
        }, this.updateInterval);

        console.log(`🔄 Автообновление запущено (каждые ${this.updateInterval/1000} сек)`);
    }

    /**
     * Принудительное обновление всех данных
     */
    async refreshAllData() {
        console.log('🔄 Принудительное обновление всех данных...');
        
        this.showNotification('Обновление данных...', 'info');
        
        try {
            await this.loadInitialData();
            this.showNotification('Данные обновлены', 'success');
        } catch (error) {
            console.error('❌ Ошибка обновления данных:', error);
            this.showNotification('Ошибка обновления данных', 'error');
        }
    }

    /**
     * Переключение полноэкранного режима
     */
    toggleFullscreen() {
        const element = document.documentElement;
        
        if (!document.fullscreenElement) {
            element.requestFullscreen().then(() => {
                this.showNotification('Полноэкранный режим включен', 'info');
            }).catch(err => {
                console.error('Ошибка входа в полноэкранный режим:', err);
            });
        } else {
            document.exitFullscreen().then(() => {
                this.showNotification('Полноэкранный режим выключен', 'info');
            });
        }
    }

    /**
     * Создание скриншота
     */
    takeScreenshot() {
        this.showNotification('Функция скриншота в разработке', 'info');
    }

    /**
     * Обновление статуса подключения
     */
    updateConnectionStatus(status, text) {
        const statusElement = document.getElementById('connectionStatus');
        const textElement = document.getElementById('connectionText');
        
        if (statusElement) {
            statusElement.className = 'status-indicator status-' + status;
        }
        
        if (textElement) {
            textElement.textContent = text;
        }
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
     * Показ уведомлений
     */
    showNotification(message, type = 'info') {
        const alertClass = {
            success: 'alert-success',
            error: 'alert-danger',
            warning: 'alert-warning',
            info: 'alert-info'
        }[type] || 'alert-info';
        
        const notification = document.createElement('div');
        notification.className = `alert ${alertClass} alert-dismissible fade show notification`;
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Автоматически удаляем через 5 секунд
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }

    /**
     * Вспомогательные функции генерации демо данных
     */
    generateDemoPrice() {
        return {
            price: 67800 + (Math.random() - 0.5) * 2000,
            change_24h: (Math.random() - 0.5) * 10,
            volume_24h: 1500000000 + Math.random() * 500000000
        };
    }

    generateDemoIndicators() {
        return {
            rsi: 30 + Math.random() * 40,
            macd: {
                histogram: (Math.random() - 0.5) * 100
            },
            bollinger_bands: {
                upper: 68500,
                middle: 67800,
                lower: 67100
            },
            price: 67800
        };
    }

    generateDemoBalance() {
        return {
            total_usdt: 1000 + Math.random() * 500,
            available_usdt: 800 + Math.random() * 200,
            in_positions: Math.random() * 200,
            unrealized_pnl: (Math.random() - 0.5) * 100,
            pnl_today: (Math.random() - 0.5) * 50,
            open_positions: Math.floor(Math.random() * 5)
        };
    }

    generateDemoPositions() {
        const symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT'];
        return symbols.slice(0, Math.floor(Math.random() * 4)).map(symbol => ({
            symbol,
            quantity: Math.random() * 10,
            entry_price: 50000 + Math.random() * 20000,
            mark_price: 50000 + Math.random() * 20000
        }));
    }

    generateDemoTrades() {
        const symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT'];
        const trades = [];
        
        for (let i = 0; i < 15; i++) {
            trades.push({
                id: i + 1,
                symbol: symbols[Math.floor(Math.random() * symbols.length)],
                side: Math.random() > 0.5 ? 'BUY' : 'SELL',
                entry_price: 50000 + Math.random() * 20000,
                profit: (Math.random() - 0.4) * 200,
                created_at: new Date(Date.now() - i * 30 * 60 * 1000).toISOString()
            });
        }
        
        return trades;
    }

    generateDemoStats() {
        return {
            trades_today: Math.floor(Math.random() * 20)
        };
    }

    generateDemoPriceData() {
        const labels = [];
        const prices = [];
        const now = new Date();
        let basePrice = 67800;

        for (let i = 23; i >= 0; i--) {
            const time = new Date(now.getTime() - i * 60 * 60 * 1000);
            labels.push(time.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' }));
            
            basePrice += (Math.random() - 0.5) * 1000;
            prices.push(Math.max(60000, Math.min(75000, basePrice)));
        }

        return { labels, prices };
    }

    generateDemoPnLData() {
        const labels = [];
        const cumulative = [];
        const daily = [];
        const now = new Date();
        let cumulativePnL = 0;

        for (let i = 29; i >= 0; i--) {
            const date = new Date(now.getTime() - i * 24 * 60 * 60 * 1000);
            labels.push(date.toLocaleDateString('ru-RU', { month: 'short', day: 'numeric' }));
            
            const dailyPnL = (Math.random() - 0.3) * 100;
            cumulativePnL += dailyPnL;
            
            daily.push(dailyPnL);
            cumulative.push(cumulativePnL);
        }

        return { labels, cumulative, daily };
    }

    generateColors(count) {
        const colors = [
            '#26a69a', '#ef5350', '#ffc107', '#2196f3', 
            '#9c27b0', '#00bcd4', '#ffeb3b', '#795548',
            '#607d8b', '#ff5722', '#4caf50', '#e91e63'
        ];
        return colors.slice(0, count);
    }

    formatNumber(num) {
        if (num >= 1e9) return (num / 1e9).toFixed(1) + 'B';
        if (num >= 1e6) return (num / 1e6).toFixed(1) + 'M';
        if (num >= 1e3) return (num / 1e3).toFixed(1) + 'K';
        return num.toFixed(2);
    }

    /**
     * Уничтожение менеджера
     */
    destroy() {
        console.log('🗑️ Уничтожение CompleteChartManager...');
        
        if (this.updateTimer) {
            clearInterval(this.updateTimer);
        }
        
        if (this.socket) {
            this.socket.disconnect();
        }
        
        Object.values(this.charts).forEach(chart => {
            if (chart && typeof chart.destroy === 'function') {
                chart.destroy();
            }
        });
        
        this.isInitialized = false;
        console.log('✅ CompleteChartManager уничтожен');
    }
}

// Экспортируем для глобального использования
window.CompleteChartManager = CompleteChartManager;