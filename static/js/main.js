// Email Guardian Main JavaScript

class EmailGuardian {
    constructor() {
        this.init();
    }

    init() {
        this.setupGlobalEventListeners();
        this.initializeTooltips();
        this.setupFormValidation();
        this.initializeDatatables();
        this.setupThemeToggle();
    }

    setupGlobalEventListeners() {
        // Mobile sidebar toggle
        this.setupMobileSidebar();
        
        // Form submissions
        this.setupFormSubmissions();
        
        // Keyboard shortcuts
        this.setupKeyboardShortcuts();
        
        // Auto-hide alerts
        this.setupAutoHideAlerts();
    }

    setupMobileSidebar() {
        // Create mobile menu button if not exists
        const navbarBrand = document.querySelector('.sidebar h4');
        if (navbarBrand && window.innerWidth <= 768) {
            const menuBtn = document.createElement('button');
            menuBtn.className = 'btn btn-outline-light btn-sm mobile-menu-btn';
            menuBtn.innerHTML = '<i class="fas fa-bars"></i>';
            menuBtn.onclick = this.toggleMobileSidebar;
            navbarBrand.appendChild(menuBtn);
        }

        // Handle responsive behavior
        window.addEventListener('resize', () => {
            if (window.innerWidth > 768) {
                document.querySelector('.sidebar')?.classList.remove('show');
            }
        });
    }

    toggleMobileSidebar() {
        const sidebar = document.querySelector('.sidebar');
        if (sidebar) {
            sidebar.classList.toggle('show');
        }
    }

    initializeTooltips() {
        // Initialize Bootstrap tooltips
        const tooltipTriggerList = [].slice.call(
            document.querySelectorAll('[data-bs-toggle="tooltip"]')
        );
        tooltipTriggerList.map(tooltipTriggerEl => {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    setupFormValidation() {
        // Custom form validation
        const forms = document.querySelectorAll('.needs-validation');
        Array.from(forms).forEach(form => {
            form.addEventListener('submit', event => {
                if (!form.checkValidity()) {
                    event.preventDefault();
                    event.stopPropagation();
                }
                form.classList.add('was-validated');
            });
        });

        // Email validation
        const emailInputs = document.querySelectorAll('input[type="email"]');
        emailInputs.forEach(input => {
            input.addEventListener('blur', () => {
                this.validateEmail(input);
            });
        });

        // File upload validation
        const fileInputs = document.querySelectorAll('input[type="file"]');
        fileInputs.forEach(input => {
            input.addEventListener('change', () => {
                this.validateFileUpload(input);
            });
        });
    }

    validateEmail(input) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        const isValid = emailRegex.test(input.value);
        
        if (input.value && !isValid) {
            input.setCustomValidity('Please enter a valid email address');
            input.classList.add('is-invalid');
        } else {
            input.setCustomValidity('');
            input.classList.remove('is-invalid');
        }
    }

    validateFileUpload(input) {
        const file = input.files[0];
        if (!file) return;

        const maxSize = 16 * 1024 * 1024; // 16MB
        const allowedTypes = ['text/csv'];

        if (file.size > maxSize) {
            this.showAlert('File size must be less than 16MB', 'danger');
            input.value = '';
            return false;
        }

        if (!allowedTypes.includes(file.type) && !file.name.endsWith('.csv')) {
            this.showAlert('Please select a CSV file', 'danger');
            input.value = '';
            return false;
        }

        return true;
    }

    setupFormSubmissions() {
        // Add loading states to form submissions
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            form.addEventListener('submit', (e) => {
                const submitBtn = form.querySelector('button[type="submit"]');
                if (submitBtn && !form.classList.contains('no-loading')) {
                    this.setButtonLoading(submitBtn, true);
                    
                    // Reset after 30 seconds as fallback
                    setTimeout(() => {
                        this.setButtonLoading(submitBtn, false);
                    }, 30000);
                }
            });
        });
    }

    setButtonLoading(button, loading) {
        if (loading) {
            button.disabled = true;
            button.setAttribute('data-original-text', button.innerHTML);
            button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
        } else {
            button.disabled = false;
            const originalText = button.getAttribute('data-original-text');
            if (originalText) {
                button.innerHTML = originalText;
                button.removeAttribute('data-original-text');
            }
        }
    }

    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + K for search
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                const searchInput = document.querySelector('.dataTables_filter input');
                if (searchInput) {
                    searchInput.focus();
                }
            }

            // Escape to close modals
            if (e.key === 'Escape') {
                const openModal = document.querySelector('.modal.show');
                if (openModal) {
                    const modal = bootstrap.Modal.getInstance(openModal);
                    modal?.hide();
                }
            }
        });
    }

    setupAutoHideAlerts() {
        // Auto-hide success alerts after 5 seconds
        const successAlerts = document.querySelectorAll('.alert-success');
        successAlerts.forEach(alert => {
            setTimeout(() => {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }, 5000);
        });
    }

    initializeDatatables() {
        // Default DataTable configuration
        $.extend(true, $.fn.dataTable.defaults, {
            responsive: true,
            pageLength: 25,
            lengthMenu: [[10, 25, 50, 100, -1], [10, 25, 50, 100, "All"]],
            language: {
                search: "Search:",
                lengthMenu: "Show _MENU_ entries",
                info: "Showing _START_ to _END_ of _TOTAL_ entries",
                paginate: {
                    first: "First",
                    last: "Last",
                    next: "Next",
                    previous: "Previous"
                }
            },
            dom: '<"row"<"col-sm-12 col-md-6"l><"col-sm-12 col-md-6"f>>rt<"row"<"col-sm-12 col-md-5"i><"col-sm-12 col-md-7"p>>',
        });

        // Initialize all tables with data-table class
        $('table[data-table]').each(function() {
            $(this).DataTable();
        });
    }

    setupThemeToggle() {
        // Theme toggle functionality
        const themeToggle = document.querySelector('.theme-toggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => {
                this.toggleTheme();
            });
        }

        // Apply saved theme
        const savedTheme = localStorage.getItem('email-guardian-theme');
        if (savedTheme) {
            document.body.setAttribute('data-theme', savedTheme);
        }
    }

    toggleTheme() {
        const currentTheme = document.body.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        document.body.setAttribute('data-theme', newTheme);
        localStorage.setItem('email-guardian-theme', newTheme);
        
        // Update charts if they exist
        if (window.Chart) {
            Chart.defaults.color = newTheme === 'dark' ? '#ffffff' : '#666666';
        }
    }

    showAlert(message, type = 'info', duration = 5000) {
        const alertHtml = `
            <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                <i class="fas fa-${this.getAlertIcon(type)}"></i> ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        const container = document.querySelector('main .container-fluid') || document.body;
        const alertDiv = document.createElement('div');
        alertDiv.innerHTML = alertHtml;
        
        container.insertBefore(alertDiv.firstElementChild, container.firstChild);
        
        // Auto-hide if duration specified
        if (duration > 0) {
            setTimeout(() => {
                const alert = container.querySelector('.alert');
                if (alert) {
                    const bsAlert = new bootstrap.Alert(alert);
                    bsAlert.close();
                }
            }, duration);
        }
    }

    getAlertIcon(type) {
        const icons = {
            'success': 'check-circle',
            'danger': 'exclamation-triangle',
            'warning': 'exclamation-triangle',
            'info': 'info-circle',
            'primary': 'info-circle'
        };
        return icons[type] || 'info-circle';
    }

    // Utility functions
    formatBytes(bytes, decimals = 2) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    }

    formatDate(date, format = 'short') {
        const options = {
            short: { year: 'numeric', month: 'short', day: 'numeric' },
            long: { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' },
            time: { hour: '2-digit', minute: '2-digit' }
        };
        
        return new Intl.DateTimeFormat('en-US', options[format]).format(new Date(date));
    }

    debounce(func, wait, immediate) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                timeout = null;
                if (!immediate) func(...args);
            };
            const callNow = immediate && !timeout;
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
            if (callNow) func(...args);
        };
    }

    // API helper functions
    async apiRequest(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        };

        const config = { ...defaultOptions, ...options };
        
        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            this.showAlert('Request failed. Please try again.', 'danger');
            throw error;
        }
    }

    // Export functionality
    exportTable(tableId, filename = 'export') {
        const table = document.getElementById(tableId);
        if (!table) return;

        const rows = Array.from(table.querySelectorAll('tr'));
        const csv = rows.map(row => {
            const cells = Array.from(row.querySelectorAll('td, th'));
            return cells.map(cell => {
                let text = cell.textContent.trim();
                // Escape quotes and wrap in quotes if contains comma
                if (text.includes(',') || text.includes('"')) {
                    text = '"' + text.replace(/"/g, '""') + '"';
                }
                return text;
            }).join(',');
        }).join('\n');

        const blob = new Blob([csv], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${filename}-${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    // Progress tracking
    updateProgress(progressBar, percentage, text = '') {
        if (progressBar) {
            progressBar.style.width = percentage + '%';
            progressBar.setAttribute('aria-valuenow', percentage);
            if (text) {
                progressBar.textContent = text;
            }
        }
    }
}

// Initialize Email Guardian when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.emailGuardian = new EmailGuardian();
});

// Global utility functions
function showAlert(message, type = 'info', duration = 5000) {
    if (window.emailGuardian) {
        window.emailGuardian.showAlert(message, type, duration);
    }
}

function exportTable(tableId, filename = 'export') {
    if (window.emailGuardian) {
        window.emailGuardian.exportTable(tableId, filename);
    }
}

// Service Worker registration removed - not needed for local development
