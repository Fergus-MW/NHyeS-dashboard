"use client";

import { useEffect, useRef, useState } from "react";
import * as d3 from "d3";

interface NetworkNode {
  id: string;
  type: "patient" | "site";
  community: number;
  risk_level: string;
  dna_rate?: number;
  age_group?: string;
  age?: number;
  appointments?: number;
  dna_count?: number;
  unique_sites?: number;
  postcode?: string;
  risk_category?: string;
  site_name?: string;
  patient_count?: number;
  avg_dna_rate?: number;
  x?: number;
  y?: number;
  fx?: number;
  fy?: number;
}

interface NetworkLink {
  source: string | NetworkNode;
  target: string | NetworkNode;
  weight: number;
}

interface NetworkData {
  metadata: {
    total_nodes: number;
    total_edges: number;
    total_communities: number;
    high_risk_communities: number;
    medium_risk_communities: number;
    low_risk_communities: number;
    thresholds: {
      high: number;
      low: number;
    };
  };
  nodes: NetworkNode[];
  links: NetworkLink[];
}

interface NetworkVisualizationProps {
  className?: string;
}

export function NetworkVisualization({ className = "" }: NetworkVisualizationProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [data, setData] = useState<NetworkData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showLegend, setShowLegend] = useState(true);

  // Load network data
  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        const response = await fetch('/network-export.json');
        if (!response.ok) {
          throw new Error('Failed to load network data');
        }
        const networkData = await response.json();
        setData(networkData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load network data');
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  // Initialize D3 visualization
  useEffect(() => {
    if (!data || !svgRef.current || !containerRef.current) return;

    const container = containerRef.current;
    const svg = d3.select(svgRef.current);
    const containerRect = container.getBoundingClientRect();
    
    const width = containerRect.width;
    const height = containerRect.height;

    // Clear previous content
    svg.selectAll("*").remove();

    // Set up SVG dimensions
    svg.attr("width", width).attr("height", height);

    // Create zoom behavior
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 10])
      .on("zoom", (event) => {
        zoomGroup.attr("transform", event.transform);
      });

    svg.call(zoom);

    // Create zoom group
    const zoomGroup = svg.append("g").attr("class", "zoom-group");

    // Create layers
    const linkLayer = zoomGroup.append("g").attr("class", "links");
    const nodeLayer = zoomGroup.append("g").attr("class", "nodes");

    // Color scale for communities
    const communityColors = d3.scaleOrdinal(d3.schemeCategory10);

    // Risk level colors
    const riskColors = {
      "High": "#dc2626", // red-600
      "Medium": "#ea580c", // orange-600
      "Low": "#16a34a" // green-600
    };

    // Node radius scale
    const getNodeRadius = (node: NetworkNode) => {
      if (node.type === "patient") {
        return Math.max(3, Math.min(12, (node.appointments || 1) * 2));
      } else {
        return Math.max(8, Math.min(20, (node.patient_count || 1) * 0.5));
      }
    };

    // Create simulation
    const simulation = d3.forceSimulation<NetworkNode>(data.nodes)
      .force("link", d3.forceLink<NetworkNode, NetworkLink>(data.links)
        .id((d) => d.id)
        .distance(50)
        .strength(0.1))
      .force("charge", d3.forceManyBody().strength(-100))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide<NetworkNode>().radius((d) => getNodeRadius(d) + 2));

    // Create links
    const links = linkLayer.selectAll<SVGLineElement, NetworkLink>("line")
      .data(data.links)
      .enter()
      .append("line")
      .attr("stroke", "#999")
      .attr("stroke-opacity", 0.3)
      .attr("stroke-width", (d) => Math.sqrt(d.weight || 1));

    // Create tooltip
    const tooltip = d3.select("body")
      .append("div")
      .attr("class", "network-tooltip")
      .style("position", "absolute")
      .style("padding", "8px")
      .style("background", "rgba(0, 0, 0, 0.8)")
      .style("color", "white")
      .style("border-radius", "4px")
      .style("font-size", "12px")
      .style("pointer-events", "none")
      .style("opacity", 0)
      .style("z-index", 1000);

    // Create nodes
    const nodes = nodeLayer.selectAll<SVGCircleElement, NetworkNode>("circle")
      .data(data.nodes)
      .enter()
      .append("circle")
      .attr("r", getNodeRadius)
      .attr("fill", (d) => {
        if (d.type === "patient") {
          return riskColors[d.risk_level as keyof typeof riskColors] || "#6b7280";
        } else {
          return communityColors(d.community.toString());
        }
      })
      .attr("stroke", "#fff")
      .attr("stroke-width", 1.5)
      .style("cursor", "pointer")
      .on("mouseover", (event, d) => {
        tooltip.transition().duration(200).style("opacity", 1);
        
        const tooltipContent = d.type === "patient" 
          ? `<strong>Patient ${d.id}</strong><br/>
             Risk: ${d.risk_level}<br/>
             Age: ${d.age}<br/>
             DNA Rate: ${((d.dna_rate || 0) * 100).toFixed(1)}%<br/>
             Community: ${d.community}`
          : `<strong>Site ${d.id}</strong><br/>
             Name: ${d.site_name || 'Unknown'}<br/>
             Patients: ${d.patient_count || 0}<br/>
             Avg DNA Rate: ${((d.avg_dna_rate || 0) * 100).toFixed(1)}%<br/>
             Community: ${d.community}`;
        
        tooltip.html(tooltipContent)
          .style("left", (event.pageX + 10) + "px")
          .style("top", (event.pageY - 10) + "px");
      })
      .on("mouseout", () => {
        tooltip.transition().duration(200).style("opacity", 0);
      });

    // Add drag behavior
    const drag = d3.drag<SVGCircleElement, NetworkNode>()
      .on("start", (event, d) => {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
      })
      .on("drag", (event, d) => {
        d.fx = event.x;
        d.fy = event.y;
      })
      .on("end", (event, d) => {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = undefined;
        d.fy = undefined;
      });

    nodes.call(drag);

    // Update positions on simulation tick
    simulation.on("tick", () => {
      links
        .attr("x1", (d) => (d.source as NetworkNode).x || 0)
        .attr("y1", (d) => (d.source as NetworkNode).y || 0)
        .attr("x2", (d) => (d.target as NetworkNode).x || 0)
        .attr("y2", (d) => (d.target as NetworkNode).y || 0);

      nodes
        .attr("cx", (d) => d.x || 0)
        .attr("cy", (d) => d.y || 0);
    });

    // Cleanup function
    return () => {
      tooltip.remove();
      simulation.stop();
    };
  }, [data]);

  // Handle resize
  useEffect(() => {
    const handleResize = () => {
      // Trigger re-render on resize
      const event = new Event('resize');
      window.dispatchEvent(event);
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  if (loading) {
    return (
      <div className={`flex items-center justify-center h-full ${className}`}>
        <div className="text-nhs-mid-grey">Loading network visualization...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`flex items-center justify-center h-full ${className}`}>
        <div className="text-red-600">Error: {error}</div>
      </div>
    );
  }

  return (
    <div ref={containerRef} className={`relative w-full h-full ${className}`}>
      <svg ref={svgRef} className="w-full h-full" />
      
      {/* Legend Overlay */}
      {showLegend && (
        <div className="absolute top-4 right-4 bg-white/90 backdrop-blur-sm rounded-lg shadow-lg p-4 max-w-xs">
          <div className="flex justify-between items-center mb-3">
            <h3 className="font-semibold text-sm text-nhs-black">Network Legend</h3>
            <button
              onClick={() => setShowLegend(false)}
              className="text-nhs-mid-grey hover:text-nhs-black text-xs"
            >
              ✕
            </button>
          </div>
          
          <div className="space-y-3 text-xs">
            {/* Risk Levels */}
            <div>
              <h4 className="font-medium mb-1 text-nhs-black">Risk Levels</h4>
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-red-600"></div>
                  <span>High Risk</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-orange-600"></div>
                  <span>Medium Risk</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-green-600"></div>
                  <span>Low Risk</span>
                </div>
              </div>
            </div>
            
            {/* Node Types */}
            <div>
              <h4 className="font-medium mb-1 text-nhs-black">Node Types</h4>
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-gray-400"></div>
                  <span>Patients (small)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 rounded-full bg-blue-500"></div>
                  <span>Sites (large)</span>
                </div>
              </div>
            </div>

            {/* Stats */}
            {data && (
              <div>
                <h4 className="font-medium mb-1 text-nhs-black">Statistics</h4>
                <div className="text-xs text-nhs-mid-grey space-y-0.5">
                  <div>Nodes: {data.metadata.total_nodes.toLocaleString()}</div>
                  <div>Links: {data.metadata.total_edges.toLocaleString()}</div>
                  <div>Communities: {data.metadata.total_communities}</div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Show Legend Button (when hidden) */}
      {!showLegend && (
        <button
          onClick={() => setShowLegend(true)}
          className="absolute top-4 right-4 bg-white/90 backdrop-blur-sm rounded-lg shadow-lg px-3 py-2 text-xs font-medium text-nhs-black hover:bg-white"
        >
          Show Legend
        </button>
      )}
    </div>
  );
}
