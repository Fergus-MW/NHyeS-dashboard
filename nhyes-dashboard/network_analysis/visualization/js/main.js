/**
 * NHS Network Analysis Dashboard - Main Application Entry Point
 */

// Global application state
let dashboard = null;

// Application initialization
document.addEventListener('DOMContentLoaded', async function() {
    console.log('NHS Network Analysis Dashboard starting...');

    try {
        // Initialize the dashboard
        dashboard = new NHSDashboard();

        // Add any global event listeners or setup here
        setupGlobalErrorHandling();
        setupKeyboardShortcuts();

        console.log('NHS Network Analysis Dashboard initialized successfully');

    } catch (error) {
        console.error('Failed to initialize dashboard:', error);
        showCriticalError('Failed to initialize the dashboard. Please refresh the page and try again.');
    }
});

/**
 * Setup global error handling
 */
function setupGlobalErrorHandling() {
    // Handle unhandled promise rejections
    window.addEventListener('unhandledrejection', function(event) {
        console.error('Unhandled promise rejection:', event.reason);
        showErrorNotification('An unexpected error occurred: ' + event.reason.message);
    });

    // Handle general JavaScript errors
    window.addEventListener('error', function(event) {
        console.error('JavaScript error:', event.error);
        if (event.error && event.error.stack) {
            console.error('Stack trace:', event.error.stack);
        }
    });
}

/**
 * Setup keyboard shortcuts
 */
function setupKeyboardShortcuts() {
    document.addEventListener('keydown', function(event) {
        // Only handle shortcuts when not in an input field
        if (event.target.tagName === 'INPUT' || event.target.tagName === 'SELECT' || event.target.tagName === 'TEXTAREA') {
            return;
        }

        switch(event.code) {
            case 'KeyI':
                if (event.ctrlKey || event.metaKey) {
                    event.preventDefault();
                    const initBtn = document.getElementById('initialize-btn');
                    if (initBtn && !initBtn.disabled) {
                        initBtn.click();
                    }
                }
                break;

            case 'KeyR':
                if (event.ctrlKey || event.metaKey) {
                    event.preventDefault();
                    const refreshBtn = document.getElementById('refresh-btn');
                    if (refreshBtn && !refreshBtn.disabled) {
                        refreshBtn.click();
                    }
                }
                break;

            case 'KeyF':
                if (event.ctrlKey || event.metaKey) {
                    event.preventDefault();
                    // Focus on the first filter
                    const firstFilter = document.getElementById('risk-filter');
                    if (firstFilter) {
                        firstFilter.focus();
                    }
                }
                break;

            case 'Escape':
                // Close any open modals
                const modal = document.getElementById('progress-modal');
                if (modal && !modal.classList.contains('hidden')) {
                    // Only close if not in progress
                    const progressText = document.getElementById('progress-text');
                    if (progressText && progressText.textContent.includes('complete')) {
                        modal.classList.add('hidden');
                    }
                }

                // Clear any notifications
                document.querySelectorAll('.error-notification, .success-notification').forEach(notification => {
                    notification.remove();
                });
                break;
        }
    });
}

/**
 * Show critical error that prevents app from functioning
 */
function showCriticalError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'critical-error';
    errorDiv.innerHTML = `
        <div class="critical-error-content">
            <h2>Critical Error</h2>
            <p>${message}</p>
            <button onclick="location.reload()" class="btn btn-primary">Reload Page</button>
        </div>
    `;

    // Add critical error styles
    errorDiv.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.8);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 10000;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
    `;

    const contentStyle = `
        background: white;
        padding: 2rem;
        border-radius: 8px;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
        max-width: 500px;
        text-align: center;
    `;

    errorDiv.querySelector('.critical-error-content').style.cssText = contentStyle;

    document.body.appendChild(errorDiv);
}

/**
 * Add CSS for notifications if not already present
 */
function ensureNotificationStyles() {
    if (document.getElementById('notification-styles')) return;

    const style = document.createElement('style');
    style.id = 'notification-styles';
    style.textContent = `
        .error-notification,
        .success-notification {
            position: fixed;
            top: 20px;
            right: 20px;
            max-width: 400px;
            z-index: 1000;
            border-radius: 4px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            animation: slideIn 0.3s ease-out;
        }

        .error-notification {
            background: #f44336;
            color: white;
        }

        .success-notification {
            background: #4caf50;
            color: white;
        }

        .error-content,
        .success-content {
            padding: 1rem;
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 1rem;
        }

        .close-btn {
            background: none;
            border: none;
            color: inherit;
            font-size: 1.5rem;
            cursor: pointer;
            padding: 0;
            line-height: 1;
        }

        .close-btn:hover {
            opacity: 0.7;
        }

        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }

        .critical-error h2 {
            color: #d32f2f;
            margin-bottom: 1rem;
        }

        .critical-error p {
            margin-bottom: 1.5rem;
            line-height: 1.5;
        }
    `;

    document.head.appendChild(style);
}

// Ensure notification styles are loaded
ensureNotificationStyles();

/**
 * Global utility functions
 */
window.nhsUtils = {
    formatNumber: function(num) {
        return new Intl.NumberFormat().format(num);
    },

    formatPercentage: function(num) {
        return (num * 100).toFixed(1) + '%';
    },

    formatDate: function(dateString) {
        return new Intl.DateTimeFormat('en-GB').format(new Date(dateString));
    },

    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
};

// Export dashboard instance for console debugging
window.dashboard = dashboard;
