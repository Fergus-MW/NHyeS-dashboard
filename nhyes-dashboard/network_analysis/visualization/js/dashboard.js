/**
 * NHS Network Analysis Dashboard Controller
 * Manages the overall dashboard state and coordinates between components
 */

class NHSDashboard {
    constructor() {
        this.apiClient = new NHSApiClient();
        this.networkViz = null;
        this.currentData = null;
        this.isInitialized = false;

        // UI elements
        this.elements = {
            initializeBtn: document.getElementById('initialize-btn'),
            refreshBtn: document.getElementById('refresh-btn'),
            statusIndicator: document.getElementById('status-indicator'),
            statusDot: document.getElementById('status-dot'),
            progressModal: document.getElementById('progress-modal'),
            riskFilter: document.getElementById('risk-filter'),
            nodeTypeFilter: document.getElementById('node-type-filter'),
            communityFilter: document.getElementById('community-filter'),
            totalNodes: document.getElementById('total-nodes'),
            totalEdges: document.getElementById('total-edges'),
            totalCommunities: document.getElementById('total-communities'),
            highRiskCommunities: document.getElementById('high-risk-communities'),
            lowRiskCommunities: document.getElementById('low-risk-communities'),
            insightsList: document.getElementById('insights-list'),
            riskChart: document.getElementById('risk-chart')
        };

        this.init();
    }

    async init() {
        // Set up event listeners
        this.setupEventListeners();

        // Check backend availability
        await this.checkBackendHealth();

        // Initialize network visualization
        this.networkViz = new NHSNetworkVisualization('network-viz');

        // Check if analysis is already completed
        await this.checkInitialStatus();

        console.log('NHS Dashboard initialized');
    }

    setupEventListeners() {
        // Initialize button
        this.elements.initializeBtn?.addEventListener('click', () => this.initializeAnalysis());

        // Refresh button
        this.elements.refreshBtn?.addEventListener('click', () => this.refreshData());

        // Filters
        this.elements.riskFilter?.addEventListener('change', (e) => this.applyFilters());
        this.elements.nodeTypeFilter?.addEventListener('change', (e) => this.applyFilters());
        this.elements.communityFilter?.addEventListener('change', (e) => this.applyFilters());

        // Custom events from network visualization
        window.addEventListener('nodeSelected', (event) => this.handleNodeSelection(event.detail));
        window.addEventListener('statisticsUpdated', (event) => this.updateFilteredStats(event.detail));

        // Handle window visibility changes
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden && this.isInitialized) {
                this.refreshStatus();
            }
        });
    }

    async checkBackendHealth() {
        const isHealthy = await this.apiClient.healthCheck();

        if (!isHealthy) {
            this.updateStatus('error', 'Backend not available');
            this.showError('FastAPI backend is not running. Please start the server with: cd network_analysis && python api.py');
            return false;
        }

        console.log('Backend health check passed');
        return true;
    }

    async checkInitialStatus() {
        try {
            const status = await this.apiClient.getStatus();

            if (status.initialized && status.progress === 'completed') {
                this.isInitialized = true;
                await this.loadVisualizationData();
                this.updateStatus('ready', 'Analysis complete');
                this.elements.refreshBtn.disabled = false;
            } else {
                this.updateStatus('not_initialized', 'Not initialized');
            }
        } catch (error) {
            console.warn('Could not check initial status:', error);
        }
    }

    async initializeAnalysis() {
        try {
            this.updateStatus('loading', 'Initializing...');
            this.showProgressModal();

            // Start the analysis
            const response = await this.apiClient.initializeAnalysis();
            console.log('Analysis initialization response:', response);

            // Start polling for progress
            this.apiClient.pollStatus((error, status) => {
                if (error) {
                    console.error('Status polling error:', error);
                    this.hideProgressModal();
                    this.updateStatus('error', 'Analysis failed');
                    return;
                }

                this.handleStatusUpdate(status);
            });

        } catch (error) {
            console.error('Failed to initialize analysis:', error);
            this.hideProgressModal();
            this.updateStatus('error', 'Initialization failed');
            this.showError('Failed to initialize analysis: ' + error.message);
        }
    }

    handleStatusUpdate(status) {
        console.log('Status update:', status);

        // Update progress UI
        updateProgressUI(status.progress);

        if (status.progress === 'completed') {
            setTimeout(async () => {
                await this.onAnalysisComplete(status);
            }, 1000);
        } else if (status.progress.startsWith('error:')) {
            this.hideProgressModal();
            this.updateStatus('error', 'Analysis failed');
            this.showError('Analysis failed: ' + status.progress.substring(6));
        }
    }

    async onAnalysisComplete(status) {
        try {
            this.hideProgressModal();
            this.isInitialized = true;

            // Load the visualization data
            await this.loadVisualizationData();

            // Update UI state
            this.updateStatus('ready', 'Analysis complete');
            this.elements.initializeBtn.textContent = 'Re-run Analysis';
            this.elements.refreshBtn.disabled = false;

            // Show success message
            this.showSuccess('NHS network analysis completed successfully!');

        } catch (error) {
            console.error('Failed to load visualization data:', error);
            this.updateStatus('error', 'Failed to load data');
            this.showError('Analysis completed but failed to load visualization data');
        }
    }

    async loadVisualizationData() {
        try {
            console.log('Loading visualization data...');

            // Load main graph data (might be large, so show loading)
            this.showLoadingMessage('Loading network data...');

            const data = await this.apiClient.getGraphData();
            this.currentData = data;

            // Load the visualization
            await this.networkViz.loadData(data);

            // Update dashboard statistics
            this.updateStatistics(data);

            // Load and display insights
            await this.loadInsights();

            // Populate community filter
            this.populateCommunityFilter(data.communities);

            // Create risk distribution chart
            this.createRiskChart(data.summary.risk_distribution);

            this.hideLoadingMessage();

            console.log('Visualization data loaded successfully');

        } catch (error) {
            this.hideLoadingMessage();
            throw error;
        }
    }

    async refreshData() {
        if (!this.isInitialized) return;

        try {
            this.elements.refreshBtn.disabled = true;
            this.elements.refreshBtn.textContent = 'Refreshing...';

            // Clear cache and reload
            this.apiClient.clearCache();
            await this.loadVisualizationData();

        } catch (error) {
            console.error('Failed to refresh data:', error);
            this.showError('Failed to refresh data: ' + error.message);
        } finally {
            this.elements.refreshBtn.disabled = false;
            this.elements.refreshBtn.textContent = 'Refresh Data';
        }
    }

    applyFilters() {
        if (!this.networkViz) return;

        const filters = {
            riskLevel: this.elements.riskFilter?.value || 'all',
            nodeType: this.elements.nodeTypeFilter?.value || 'all',
            community: this.elements.communityFilter?.value || 'all'
        };

        console.log('Applying filters:', filters);
        this.networkViz.applyFilters(filters);
    }

    updateStatistics(data) {
        if (!data) return;

        const { metadata, summary } = data;

        // Update main statistics
        if (this.elements.totalNodes) {
            this.elements.totalNodes.textContent = metadata.total_nodes.toLocaleString();
        }
        if (this.elements.totalEdges) {
            this.elements.totalEdges.textContent = metadata.total_edges.toLocaleString();
        }
        if (this.elements.totalCommunities) {
            this.elements.totalCommunities.textContent = metadata.total_communities;
        }
        if (this.elements.highRiskCommunities) {
            this.elements.highRiskCommunities.textContent = metadata.high_risk_communities;
        }
        if (this.elements.lowRiskCommunities) {
            this.elements.lowRiskCommunities.textContent = metadata.low_risk_communities;
        }
    }

    updateFilteredStats(stats) {
        // Update statistics based on filtered data
        console.log('Filtered stats:', stats);
    }

    async loadInsights() {
        try {
            const insights = await this.apiClient.getInsights();
            this.displayInsights(insights.insights);
        } catch (error) {
            console.warn('Failed to load insights:', error);
        }
    }

    displayInsights(insights) {
        if (!this.elements.insightsList || !insights) return;

        if (insights.length === 0) {
            this.elements.insightsList.innerHTML = '<p class="no-data">No insights available</p>';
            return;
        }

        const html = insights.map(insight => `
            <div class="insight-item">
                <div class="insight-priority">${insight.type} - ${insight.priority} Priority</div>
                <div class="insight-issue">${insight.key_issue}</div>
                <div class="insight-recommendation">${insight.recommendation}</div>
                ${insight.patients_affected ? `<div class="insight-impact">Impact: ${insight.patients_affected} patients</div>` : ''}
            </div>
        `).join('');

        this.elements.insightsList.innerHTML = html;
    }

    populateCommunityFilter(communities) {
        if (!this.elements.communityFilter || !communities) return;

        // Clear existing options (except "All")
        const allOption = this.elements.communityFilter.querySelector('option[value="all"]');
        this.elements.communityFilter.innerHTML = '';
        this.elements.communityFilter.appendChild(allOption);

        // Sort communities by risk level and size
        const sortedCommunities = [...communities].sort((a, b) => {
            const riskOrder = { 'High': 0, 'Medium': 1, 'Low': 2 };
            const riskDiff = riskOrder[a.risk_level] - riskOrder[b.risk_level];
            return riskDiff !== 0 ? riskDiff : b.patients - a.patients;
        });

        // Add community options
        sortedCommunities.forEach(community => {
            const option = document.createElement('option');
            option.value = community.id;
            option.textContent = `Community ${community.id} (${community.risk_level}, ${community.patients} patients)`;
            this.elements.communityFilter.appendChild(option);
        });
    }

    createRiskChart(riskDistribution) {
        if (!this.elements.riskChart || !riskDistribution) return;

        const data = Object.entries(riskDistribution).map(([risk, count]) => ({
            risk,
            count,
            color: risk === 'High' ? '#d32f2f' : risk === 'Medium' ? '#ff9800' : '#4caf50'
        }));

        // Simple bar chart with D3
        const margin = { top: 10, right: 10, bottom: 30, left: 40 };
        const width = 280 - margin.left - margin.right;
        const height = 150 - margin.bottom - margin.top;

        // Clear previous chart
        d3.select(this.elements.riskChart).selectAll('*').remove();

        const svg = d3.select(this.elements.riskChart)
            .append('svg')
            .attr('width', width + margin.left + margin.right)
            .attr('height', height + margin.top + margin.bottom);

        const g = svg.append('g')
            .attr('transform', `translate(${margin.left},${margin.top})`);

        const x = d3.scaleBand()
            .range([0, width])
            .domain(data.map(d => d.risk))
            .padding(0.1);

        const y = d3.scaleLinear()
            .range([height, 0])
            .domain([0, d3.max(data, d => d.count)]);

        g.selectAll('.bar')
            .data(data)
            .enter().append('rect')
            .attr('class', 'bar')
            .attr('x', d => x(d.risk))
            .attr('width', x.bandwidth())
            .attr('y', d => y(d.count))
            .attr('height', d => height - y(d.count))
            .attr('fill', d => d.color);

        g.append('g')
            .attr('transform', `translate(0,${height})`)
            .call(d3.axisBottom(x));

        g.append('g')
            .call(d3.axisLeft(y));
    }

    handleNodeSelection(detail) {
        console.log('Node selected:', detail.node);

        // Could show detailed node information in sidebar
        // Or highlight related communities, etc.
    }

    updateStatus(status, message) {
        const statusText = this.elements.statusIndicator?.querySelector('.status-text');
        const statusDot = this.elements.statusDot;

        if (statusText) {
            statusText.textContent = message || status;
        }

        if (statusDot) {
            statusDot.className = 'status-dot';
            if (status === 'ready') {
                statusDot.classList.add('ready');
            } else if (status === 'loading') {
                statusDot.classList.add('loading');
            } else if (status === 'error') {
                statusDot.classList.add('error');
            }
        }
    }

    showProgressModal() {
        this.elements.progressModal?.classList.remove('hidden');
    }

    hideProgressModal() {
        this.elements.progressModal?.classList.add('hidden');
    }

    showLoadingMessage(message) {
        const loadingEl = document.getElementById('loading-message');
        if (loadingEl) {
            loadingEl.style.display = 'block';
            const textEl = loadingEl.querySelector('p');
            if (textEl) textEl.textContent = message;
        }
    }

    hideLoadingMessage() {
        const loadingEl = document.getElementById('loading-message');
        if (loadingEl) {
            loadingEl.style.display = 'none';
        }
    }

    showError(message) {
        // Use the global error notification system
        showErrorNotification(message);
    }

    showSuccess(message) {
        // Create success notification
        let notification = document.createElement('div');
        notification.className = 'success-notification';
        notification.innerHTML = `
            <div class="success-content">
                <strong>Success:</strong> ${message}
                <button onclick="this.parentElement.parentElement.remove()" class="close-btn">&times;</button>
            </div>
        `;

        document.body.appendChild(notification);

        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }

    async refreshStatus() {
        try {
            const status = await this.apiClient.getStatus();
            if (status.initialized && status.progress === 'completed' && !this.isInitialized) {
                await this.loadVisualizationData();
                this.isInitialized = true;
                this.updateStatus('ready', 'Analysis complete');
            }
        } catch (error) {
            console.warn('Failed to refresh status:', error);
        }
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = NHSDashboard;
} else {
    window.NHSDashboard = NHSDashboard;
}
