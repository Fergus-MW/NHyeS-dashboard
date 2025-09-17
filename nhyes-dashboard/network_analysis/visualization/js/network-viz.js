/**
 * NHS Network Visualization using D3.js
 * Force-directed graph with risk-based styling and community clustering
 */

class NHSNetworkVisualization {
    constructor(containerId, options = {}) {
        this.containerId = containerId;
        this.container = d3.select(`#${containerId}`);

        // Configuration
        this.config = {
            width: 1200,
            height: 800,
            nodeRadius: {
                patient: { min: 3, max: 12 },
                site: { min: 8, max: 20 }
            },
            linkStrength: 0.1,
            chargeStrength: -100,
            linkDistance: 50,
            ...options
        };

        // Data storage
        this.data = null;
        this.filteredData = null;
        this.filters = {
            riskLevel: 'all',
            nodeType: 'all',
            community: 'all'
        };

        // D3 elements
        this.svg = null;
        this.simulation = null;
        this.tooltip = d3.select('#tooltip');

        // Initialize the visualization
        this.init();
    }

    init() {
        const container = this.container.node();
        const containerRect = container.getBoundingClientRect();

        this.config.width = containerRect.width;
        this.config.height = containerRect.height;

        // Create SVG
        this.svg = this.container.append('svg')
            .attr('width', this.config.width)
            .attr('height', this.config.height);

        // Add zoom behavior
        const zoom = d3.zoom()
            .scaleExtent([0.1, 10])
            .on('zoom', (event) => {
                this.svg.select('.zoom-group')
                    .attr('transform', event.transform);
            });

        this.svg.call(zoom);

        // Create zoom group
        this.zoomGroup = this.svg.append('g').attr('class', 'zoom-group');

        // Create layers
        this.linkLayer = this.zoomGroup.append('g').attr('class', 'links');
        this.nodeLayer = this.zoomGroup.append('g').attr('class', 'nodes');

        // Initialize simulation
        this.simulation = d3.forceSimulation()
            .force('link', d3.forceLink().id(d => d.id).distance(this.config.linkDistance))
            .force('charge', d3.forceManyBody().strength(this.config.chargeStrength))
            .force('center', d3.forceCenter(this.config.width / 2, this.config.height / 2))
            .force('collision', d3.forceCollide().radius(d => this.getNodeRadius(d) + 2));

        // Handle window resize
        window.addEventListener('resize', () => this.handleResize());
    }

    /**
     * Load and render network data
     */
    async loadData(data) {
        try {
            this.data = data;
            this.filteredData = this.filterData(data);
            this.render();
        } catch (error) {
            console.error('Error loading network data:', error);
            this.showError('Failed to load network data');
        }
    }

    /**
     * Filter data based on current filters
     */
    filterData(data) {
        if (!data) return null;

        let filteredNodes = [...data.nodes];
        let filteredLinks = [...data.links];

        // Filter by risk level
        if (this.filters.riskLevel !== 'all') {
            filteredNodes = filteredNodes.filter(node => node.risk_level === this.filters.riskLevel);
        }

        // Filter by node type
        if (this.filters.nodeType !== 'all') {
            filteredNodes = filteredNodes.filter(node => node.type === this.filters.nodeType);
        }

        // Filter by community
        if (this.filters.community !== 'all') {
            const communityId = parseInt(this.filters.community);
            filteredNodes = filteredNodes.filter(node => node.community === communityId);
        }

        // Filter links to only include those between filtered nodes
        const nodeIds = new Set(filteredNodes.map(node => node.id));
        filteredLinks = filteredLinks.filter(link =>
            nodeIds.has(link.source.id || link.source) &&
            nodeIds.has(link.target.id || link.target)
        );

        return {
            nodes: filteredNodes,
            links: filteredLinks,
            communities: data.communities,
            metadata: data.metadata,
            summary: data.summary
        };
    }

    /**
     * Render the network visualization
     */
    render() {
        if (!this.filteredData) return;

        // Clear existing elements
        this.linkLayer.selectAll('.link').remove();
        this.nodeLayer.selectAll('.node').remove();

        // Create links
        const links = this.linkLayer
            .selectAll('.link')
            .data(this.filteredData.links)
            .enter()
            .append('line')
            .attr('class', 'link')
            .attr('stroke-width', d => this.getLinkWidth(d))
            .attr('stroke-opacity', d => this.getLinkOpacity(d));

        // Create nodes
        const nodes = this.nodeLayer
            .selectAll('.node')
            .data(this.filteredData.nodes)
            .enter()
            .append('circle')
            .attr('class', d => `node ${d.type} ${d.risk_level?.toLowerCase()}-risk`)
            .attr('r', d => this.getNodeRadius(d))
            .attr('fill', d => this.getNodeColor(d))
            .call(this.createDragBehavior())
            .on('mouseover', (event, d) => this.showTooltip(event, d))
            .on('mouseout', () => this.hideTooltip())
            .on('click', (event, d) => this.onNodeClick(event, d));

        // Update simulation
        this.simulation.nodes(this.filteredData.nodes);
        this.simulation.force('link').links(this.filteredData.links);

        // Restart simulation
        this.simulation.alpha(1).restart();

        // Update positions on tick
        this.simulation.on('tick', () => {
            links
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);

            nodes
                .attr('cx', d => d.x)
                .attr('cy', d => d.y);
        });

        console.log(`Rendered ${this.filteredData.nodes.length} nodes and ${this.filteredData.links.length} links`);
    }

    /**
     * Get node radius based on type and appointment volume
     */
    getNodeRadius(node) {
        const config = this.config.nodeRadius[node.type];
        if (!config) return 5;

        const appointments = node.appointments || 1;
        const maxAppointments = node.type === 'patient' ? 20 : 500; // Reasonable max values
        const scale = Math.min(appointments / maxAppointments, 1);

        return config.min + (config.max - config.min) * scale;
    }

    /**
     * Get node color based on type and risk level
     */
    getNodeColor(node) {
        if (node.type === 'patient') {
            switch (node.risk_level) {
                case 'High': return '#d32f2f';
                case 'Medium': return '#ff9800';
                case 'Low': return '#4caf50';
                default: return '#757575';
            }
        } else if (node.type === 'site') {
            return '#2196f3';
        }
        return '#757575';
    }

    /**
     * Get link width based on appointment frequency
     */
    getLinkWidth(link) {
        const weight = link.weight || 1;
        return Math.min(1 + Math.log(weight), 5);
    }

    /**
     * Get link opacity based on DNA rate
     */
    getLinkOpacity(link) {
        const dnaRate = link.dna_rate || 0;
        return 0.3 + (dnaRate * 0.5); // Higher DNA rate = more visible
    }

    /**
     * Create drag behavior for nodes
     */
    createDragBehavior() {
        return d3.drag()
            .on('start', (event, d) => {
                if (!event.active) this.simulation.alphaTarget(0.3).restart();
                d.fx = d.x;
                d.fy = d.y;
            })
            .on('drag', (event, d) => {
                d.fx = event.x;
                d.fy = event.y;
            })
            .on('end', (event, d) => {
                if (!event.active) this.simulation.alphaTarget(0);
                d.fx = null;
                d.fy = null;
            });
    }

    /**
     * Show tooltip with node information
     */
    showTooltip(event, node) {
        const tooltipContent = this.generateTooltipContent(node);

        this.tooltip
            .classed('visible', true)
            .html(tooltipContent)
            .style('left', (event.pageX + 10) + 'px')
            .style('top', (event.pageY - 10) + 'px');
    }

    /**
     * Hide tooltip
     */
    hideTooltip() {
        this.tooltip.classed('visible', false);
    }

    /**
     * Generate tooltip content based on node type
     */
    generateTooltipContent(node) {
        if (node.type === 'patient') {
            return `
                <strong>Patient ${node.id}</strong><br>
                <strong>Risk Level:</strong> ${node.risk_level}<br>
                <strong>DNA Rate:</strong> ${(node.dna_rate * 100).toFixed(1)}%<br>
                <strong>Age Group:</strong> ${node.age_group}<br>
                <strong>Appointments:</strong> ${node.appointments}<br>
                <strong>Community:</strong> ${node.community}
            `;
        } else if (node.type === 'site') {
            return `
                <strong>Healthcare Site</strong><br>
                <strong>ID:</strong> ${node.id}<br>
                <strong>Location:</strong> ${node.location}<br>
                <strong>DNA Rate:</strong> ${(node.dna_rate * 100).toFixed(1)}%<br>
                <strong>Patients:</strong> ${node.unique_patients}<br>
                <strong>Appointments:</strong> ${node.appointments}<br>
                <strong>Community:</strong> ${node.community}
            `;
        }
        return `<strong>${node.id}</strong>`;
    }

    /**
     * Handle node click events
     */
    onNodeClick(event, node) {
        console.log('Node clicked:', node);

        // Highlight connected nodes and links
        this.highlightNode(node);

        // Dispatch custom event for external handling
        window.dispatchEvent(new CustomEvent('nodeSelected', {
            detail: { node, event }
        }));
    }

    /**
     * Highlight a node and its connections
     */
    highlightNode(selectedNode) {
        const connectedNodes = new Set();
        const connectedLinks = new Set();

        // Find connected nodes and links
        this.filteredData.links.forEach(link => {
            const sourceId = link.source.id || link.source;
            const targetId = link.target.id || link.target;

            if (sourceId === selectedNode.id) {
                connectedNodes.add(targetId);
                connectedLinks.add(link);
            } else if (targetId === selectedNode.id) {
                connectedNodes.add(sourceId);
                connectedLinks.add(link);
            }
        });

        // Apply highlighting styles
        this.nodeLayer.selectAll('.node')
            .style('opacity', d =>
                d.id === selectedNode.id || connectedNodes.has(d.id) ? 1 : 0.3
            );

        this.linkLayer.selectAll('.link')
            .style('opacity', d => connectedLinks.has(d) ? 0.8 : 0.1);

        // Remove highlighting after delay
        setTimeout(() => this.clearHighlight(), 3000);
    }

    /**
     * Clear node highlighting
     */
    clearHighlight() {
        this.nodeLayer.selectAll('.node').style('opacity', 1);
        this.linkLayer.selectAll('.link').style('opacity', null);
    }

    /**
     * Apply filters and re-render
     */
    applyFilters(filters) {
        Object.assign(this.filters, filters);
        this.filteredData = this.filterData(this.data);
        this.render();

        // Update statistics
        this.updateStatistics();
    }

    /**
     * Update statistics display
     */
    updateStatistics() {
        if (!this.filteredData) return;

        const stats = {
            nodes: this.filteredData.nodes.length,
            links: this.filteredData.links.length,
            patients: this.filteredData.nodes.filter(n => n.type === 'patient').length,
            sites: this.filteredData.nodes.filter(n => n.type === 'site').length
        };

        // Dispatch event for dashboard to update
        window.dispatchEvent(new CustomEvent('statisticsUpdated', {
            detail: stats
        }));
    }

    /**
     * Zoom to fit all nodes
     */
    zoomToFit() {
        if (!this.filteredData.nodes.length) return;

        const bounds = this.calculateBounds();
        const padding = 50;

        const scale = Math.min(
            this.config.width / (bounds.width + 2 * padding),
            this.config.height / (bounds.height + 2 * padding)
        );

        const centerX = this.config.width / 2;
        const centerY = this.config.height / 2;

        this.svg.transition().duration(750).call(
            d3.zoom().transform,
            d3.zoomIdentity
                .translate(centerX, centerY)
                .scale(scale)
                .translate(-(bounds.x + bounds.width / 2), -(bounds.y + bounds.height / 2))
        );
    }

    /**
     * Calculate bounds of all nodes
     */
    calculateBounds() {
        const nodes = this.filteredData.nodes;
        if (!nodes.length) return { x: 0, y: 0, width: 0, height: 0 };

        const xs = nodes.map(d => d.x).filter(x => x !== undefined);
        const ys = nodes.map(d => d.y).filter(y => y !== undefined);

        return {
            x: Math.min(...xs),
            y: Math.min(...ys),
            width: Math.max(...xs) - Math.min(...xs),
            height: Math.max(...ys) - Math.min(...ys)
        };
    }

    /**
     * Handle window resize
     */
    handleResize() {
        const container = this.container.node();
        const containerRect = container.getBoundingClientRect();

        this.config.width = containerRect.width;
        this.config.height = containerRect.height;

        this.svg
            .attr('width', this.config.width)
            .attr('height', this.config.height);

        this.simulation
            .force('center', d3.forceCenter(this.config.width / 2, this.config.height / 2))
            .restart();
    }

    /**
     * Show error message
     */
    showError(message) {
        const errorDiv = this.container
            .append('div')
            .attr('class', 'error-message')
            .style('position', 'absolute')
            .style('top', '50%')
            .style('left', '50%')
            .style('transform', 'translate(-50%, -50%)')
            .style('background', '#f44336')
            .style('color', 'white')
            .style('padding', '1rem')
            .style('border-radius', '4px')
            .html(message);

        setTimeout(() => errorDiv.remove(), 5000);
    }

    /**
     * Cleanup visualization
     */
    destroy() {
        if (this.simulation) {
            this.simulation.stop();
        }
        this.container.selectAll('*').remove();
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = NHSNetworkVisualization;
} else {
    window.NHSNetworkVisualization = NHSNetworkVisualization;
}
