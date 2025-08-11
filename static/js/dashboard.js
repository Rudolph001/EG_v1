// Dashboard JavaScript
class EmailGuardianDashboard {
    constructor() {
        this.charts = {};
        this.refreshInterval = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadDashboardData();
        this.startAutoRefresh();
    }

    setupEventListeners() {
        // Refresh button
        const refreshBtn = document.querySelector('[onclick="refreshDashboard()"]');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.refreshDashboard());
        }

        // Real-time updates toggle
        document.addEventListener('DOMContentLoaded', () => {
            this.initializeCharts();
        });
    }

    async loadDashboardData() {
        try {
            const response = await fetch('/api/dashboard-data');
            if (!response.ok) throw new Error('Failed to fetch dashboard data');
            
            const data = await response.json();
            this.updateCharts(data);
        } catch (error) {
            console.error('Error loading dashboard data:', error);
            this.showError('Failed to load dashboard data');
        }
    }

    initializeCharts() {
        this.initializeDailyProcessingChart();
        this.initializeSeverityChart();
        this.initializeThreatTrendsChart();
    }

    initializeDailyProcessingChart() {
        const ctx = document.getElementById('dailyProcessingChart');
        if (!ctx) return;

        this.charts.dailyProcessing = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Emails Processed',
                    data: [],
                    borderColor: '#007bff',
                    backgroundColor: 'rgba(0, 123, 255, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }, {
                    label: 'Cases Generated',
                    data: [],
                    borderColor: '#dc3545',
                    backgroundColor: 'rgba(220, 53, 69, 0.1)',
                    borderWidth: 2,
                    fill: false,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Daily Email Processing'
                    },
                    legend: {
                        position: 'top'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                }
            }
        });
    }

    initializeSeverityChart() {
        const ctx = document.getElementById('severityChart');
        if (!ctx) return;

        this.charts.severity = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Low', 'Medium', 'High', 'Critical'],
                datasets: [{
                    data: [0, 0, 0, 0],
                    backgroundColor: [
                        '#28a745',
                        '#ffc107',
                        '#fd7e14',
                        '#dc3545'
                    ],
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Case Severity Distribution'
                    },
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }

    initializeThreatTrendsChart() {
        const ctx = document.getElementById('threatTrendsChart');
        if (!ctx) return;

        this.charts.threatTrends = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Phishing', 'Malware', 'Spam', 'Social Engineering', 'Data Exfiltration'],
                datasets: [{
                    label: 'Detected Threats',
                    data: [12, 8, 15, 6, 3],
                    backgroundColor: [
                        'rgba(255, 99, 132, 0.8)',
                        'rgba(54, 162, 235, 0.8)',
                        'rgba(255, 206, 86, 0.8)',
                        'rgba(75, 192, 192, 0.8)',
                        'rgba(153, 102, 255, 0.8)'
                    ],
                    borderColor: [
                        'rgba(255, 99, 132, 1)',
                        'rgba(54, 162, 235, 1)',
                        'rgba(255, 206, 86, 1)',
                        'rgba(75, 192, 192, 1)',
                        'rgba(153, 102, 255, 1)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Threat Type Distribution'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    updateCharts(data) {
        // Update daily processing chart
        if (this.charts.dailyProcessing && data.daily_processing) {
            this.charts.dailyProcessing.data.labels = data.daily_processing.labels;
            this.charts.dailyProcessing.data.datasets[0].data = data.daily_processing.data;
            this.charts.dailyProcessing.update();
        }

        // Update severity distribution chart
        if (this.charts.severity && data.severity_distribution) {
            this.charts.severity.data.datasets[0].data = data.severity_distribution.data;
            this.charts.severity.update();
        }
    }

    refreshDashboard() {
        this.showLoading(true);
        this.loadDashboardData().finally(() => {
            this.showLoading(false);
        });
    }

    startAutoRefresh() {
        // Refresh every 5 minutes
        this.refreshInterval = setInterval(() => {
            this.loadDashboardData();
        }, 5 * 60 * 1000);
    }

    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }

    showLoading(show) {
        const refreshBtn = document.querySelector('[onclick="refreshDashboard()"]');
        if (refreshBtn) {
            if (show) {
                refreshBtn.disabled = true;
                refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Refreshing...';
            } else {
                refreshBtn.disabled = false;
                refreshBtn.innerHTML = '<i class="fas fa-sync-alt"></i> Refresh';
            }
        }
    }

    showError(message) {
        const alertHtml = `
            <div class="alert alert-danger alert-dismissible fade show" role="alert">
                <i class="fas fa-exclamation-triangle"></i> ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        const container = document.querySelector('main .container-fluid');
        if (container) {
            container.insertAdjacentHTML('afterbegin', alertHtml);
        }
    }

    // Real-time updates via WebSocket (if needed in future)
    initializeWebSocket() {
        // WebSocket implementation for real-time updates
        // This would connect to a WebSocket endpoint for live data
    }

    // Export dashboard data
    exportDashboardData() {
        const data = {
            timestamp: new Date().toISOString(),
            charts: {}
        };

        // Export chart data
        Object.keys(this.charts).forEach(chartName => {
            const chart = this.charts[chartName];
            data.charts[chartName] = {
                labels: chart.data.labels,
                datasets: chart.data.datasets
            };
        });

        // Download as JSON
        const blob = new Blob([JSON.stringify(data, null, 2)], {
            type: 'application/json'
        });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `dashboard-data-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
}

// Initialize dashboard when DOM is loaded
let dashboardInstance;

function initializeDashboardCharts() {
    dashboardInstance = new EmailGuardianDashboard();
}

// Global functions for compatibility
function refreshDashboard() {
    if (dashboardInstance) {
        dashboardInstance.refreshDashboard();
    }
}

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (dashboardInstance) {
        dashboardInstance.stopAutoRefresh();
    }
});
