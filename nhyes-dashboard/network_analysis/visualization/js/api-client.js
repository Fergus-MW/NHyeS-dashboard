/**
 * NHS Network Analysis API Client
 * Handles communication with the FastAPI backend
 */

class NHSApiClient {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
        this.cache = new Map();
        this.cacheTimeout = 5 * 60 * 1000; // 5 minutes
    }

    /**
     * Generic API request handler with error handling and caching
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const cacheKey = `${endpoint}_${JSON.stringify(options)}`;

        // Check cache first for GET requests
        if (!options.method || options.method === 'GET') {
            const cached = this.cache.get(cacheKey);
            if (cached && Date.now() - cached.timestamp < this.cacheTimeout) {
                console.log(`Cache hit for ${endpoint}`);
                return cached.data;
            }
        }

        try {
            console.log(`Fetching ${url}`);
            const response = await fetch(url, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP ${response.status}: ${errorText}`);
            }

            const data = await response.json();

            // Cache successful GET responses
            if (!options.method || options.method === 'GET') {
                this.cache.set(cacheKey, {
                    data,
                    timestamp: Date.now()
                });
            }

            return data;
        } catch (error) {
            console.error(`API request failed for ${endpoint}:`, error);
            throw new Error(`Failed to fetch ${endpoint}: ${error.message}`);
        }
    }

    /**
     * Get API root information
     */
    async getRoot() {
        return this.request('/');
    }

    /**
     * Get analysis status
     */
    async getStatus() {
        return this.request('/status');
    }

    /**
     * Initialize the network analysis
     */
    async initializeAnalysis() {
        this.clearCache(); // Clear cache when starting new analysis
        return this.request('/initialize', { method: 'POST' });
    }

    /**
     * Get complete graph data for D3.js visualization
     */
    async getGraphData() {
        return this.request('/graph/data');
    }

    /**
     * Get graph metadata only (faster for status updates)
     */
    async getGraphMetadata() {
        return this.request('/graph/metadata');
    }

    /**
     * Get sample graph data for testing (limited nodes)
     */
    async getSampleGraph(size = 100) {
        return this.request(`/graph/sample/${size}`);
    }

    /**
     * Get community analysis results
     */
    async getCommunities() {
        return this.request('/communities');
    }

    /**
     * Get detailed information about a specific community
     */
    async getCommunityDetails(communityId) {
        return this.request(`/communities/${communityId}`);
    }

    /**
     * Get actionable insights from the analysis
     */
    async getInsights() {
        return this.request('/insights');
    }

    /**
     * Poll for status updates during analysis
     */
    async pollStatus(callback, interval = 2000) {
        const poll = async () => {
            try {
                const status = await this.getStatus();
                callback(null, status);

                // Continue polling if analysis is in progress
                if (status.progress !== 'completed' && status.progress !== 'not_started' && !status.progress.startsWith('error:')) {
                    setTimeout(poll, interval);
                }
            } catch (error) {
                callback(error, null);
            }
        };

        poll();
    }

    /**
     * Clear the request cache
     */
    clearCache() {
        this.cache.clear();
    }

    /**
     * Check if backend is available
     */
    async healthCheck() {
        try {
            await this.getRoot();
            return true;
        } catch (error) {
            console.warn('Backend health check failed:', error);
            return false;
        }
    }
}

// Progress step mapping for UI updates
const PROGRESS_STEPS = {
    'loading_data': { step: 'step-loading', progress: 10, text: 'Loading NHS data files...' },
    'sampling_data': { step: 'step-sampling', progress: 20, text: 'Sampling data for analysis...' },
    'cleaning_data': { step: 'step-cleaning', progress: 30, text: 'Cleaning and preprocessing...' },
    'creating_graph': { step: 'step-graph', progress: 50, text: 'Creating bipartite network graph...' },
    'detecting_communities': { step: 'step-communities', progress: 70, text: 'Running Leiden algorithm...' },
    'analyzing_communities': { step: 'step-analysis', progress: 85, text: 'Analyzing DNA patterns...' },
    'identifying_risk': { step: 'step-analysis', progress: 90, text: 'Identifying risk communities...' },
    'exporting_data': { step: 'step-export', progress: 95, text: 'Exporting data for visualization...' },
    'completed': { step: null, progress: 100, text: 'Analysis complete!' }
};

/**
 * Helper function to update progress UI
 */
function updateProgressUI(progress, progressText) {
    const progressInfo = PROGRESS_STEPS[progress] || {
        step: null,
        progress: 0,
        text: progress.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())
    };

    // Update progress bar
    const progressFill = document.getElementById('progress-fill');
    const progressTextEl = document.getElementById('progress-text');

    if (progressFill) {
        progressFill.style.width = `${progressInfo.progress}%`;
    }

    if (progressTextEl) {
        progressTextEl.textContent = progressText || progressInfo.text;
    }

    // Update step indicators
    document.querySelectorAll('.step').forEach(step => {
        step.classList.remove('active', 'completed');
    });

    if (progressInfo.step) {
        const currentStep = document.getElementById(progressInfo.step);
        if (currentStep) {
            currentStep.classList.add('active');

            // Mark previous steps as completed
            const allSteps = Array.from(document.querySelectorAll('.step'));
            const currentIndex = allSteps.indexOf(currentStep);

            allSteps.slice(0, currentIndex).forEach(step => {
                step.classList.add('completed');
            });
        }
    }

    // Handle completion
    if (progress === 'completed') {
        document.querySelectorAll('.step').forEach(step => {
            step.classList.add('completed');
            step.classList.remove('active');
        });
    }
}

/**
 * Helper function to handle API errors gracefully
 */
function handleApiError(error, context = 'API call') {
    console.error(`${context} failed:`, error);

    const errorMessages = {
        'Failed to fetch': 'Backend server is not running. Please start the FastAPI server.',
        'HTTP 400': 'Analysis not initialized. Please run initialization first.',
        'HTTP 500': 'Server error occurred. Check server logs for details.'
    };

    const userMessage = Object.keys(errorMessages).find(key => error.message.includes(key));
    const displayMessage = userMessage ? errorMessages[userMessage] : error.message;

    // Show error in UI (implement based on your UI framework)
    showErrorNotification(displayMessage);

    return displayMessage;
}

/**
 * Show error notification to user
 */
function showErrorNotification(message) {
    // Create or update error notification
    let notification = document.getElementById('error-notification');

    if (!notification) {
        notification = document.createElement('div');
        notification.id = 'error-notification';
        notification.className = 'error-notification';
        document.body.appendChild(notification);
    }

    notification.innerHTML = `
        <div class="error-content">
            <strong>Error:</strong> ${message}
            <button onclick="this.parentElement.parentElement.remove()" class="close-btn">&times;</button>
        </div>
    `;

    // Auto-remove after 10 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 10000);
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { NHSApiClient, updateProgressUI, handleApiError };
} else {
    // Browser global
    window.NHSApiClient = NHSApiClient;
    window.updateProgressUI = updateProgressUI;
    window.handleApiError = handleApiError;
}
