from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import json
import os
import pandas as pd
import networkx as nx
from datetime import datetime
import asyncio
from pathlib import Path

# Import our analysis modules directly from data_prep_leiden.py
from data_prep_leiden import (
    sample_data_for_network, clean_for_network, create_enhanced_bipartite_graph,
    detect_communities_leiden, analyze_community_dna_patterns,
    identify_high_low_risk_communities, generate_community_insights
)
from d3_export import export_for_d3js
from helpers import norm_str

# Initialize FastAPI app
app = FastAPI(
    title="NHS Network Analysis API",
    description="API for NHS patient-site network analysis and community detection using Leiden algorithm",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables to store analysis state
analysis_state = {
    "graph": None,
    "communities": None,
    "community_df": None,
    "network_data": None,
    "risk_communities": None,
    "initialized": False,
    "last_updated": None,
    "analysis_progress": "not_started"
}

# Data directory paths
DATA_DIR = Path("data")  # Relative to network_analysis directory
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

# Pydantic models for API responses
class AnalysisStatus(BaseModel):
    initialized: bool
    last_updated: Optional[str]
    progress: str
    node_count: Optional[int]
    edge_count: Optional[int]
    community_count: Optional[int]

class GraphMetadata(BaseModel):
    total_nodes: int
    total_edges: int
    total_communities: int
    high_risk_communities: int
    medium_risk_communities: int
    low_risk_communities: int
    thresholds: Dict[str, float]
    generated_at: str

class GraphData(BaseModel):
    metadata: GraphMetadata
    nodes: List[Dict[str, Any]]
    links: List[Dict[str, Any]]
    communities: List[Dict[str, Any]]
    summary: Dict[str, Any]

class CommunityInsight(BaseModel):
    community_id: Optional[int]
    type: str
    priority: str
    patients_affected: Optional[int]
    key_issue: str
    recommendation: str

def load_and_preprocess_data():
    """Load and preprocess NHS data using the exact logic from data_prep_leiden.py"""
    try:
        # Use the exact same data loading logic as in data_prep_leiden.py
        read_args = dict(dtype="string", low_memory=False)
        df1 = pd.read_csv(DATA_DIR / "Hackathon_DN_FINAL_1.csv", **read_args)
        df2 = pd.read_csv(DATA_DIR / "Hackathon_DN_FINAL_2.csv", **read_args)
        df3 = pd.read_csv(DATA_DIR / "Hackathon_DN_FINAL_3.csv", **read_args)
        df = pd.concat([df1, df2, df3], ignore_index=True)

        # Use the exact preprocessing from data_prep_leiden.py
        cols = [
            'PATIENT_KEY','AGE','ORG_CODE_LOCAL_PATIENT_IDENTIFIER',
            'ATTENDED_OR_DID_NOT_ATTEND','OUTCOME_OF_ATTENDANCE',
            'POSTCODE_SECTOR_OF_USUAL_ADDRESS','APPOINTMENT_DATE',
            'ORGANISATION_CODE_CODE_OF_PROVIDER','SITE_CODE_OF_TREATMENT',
            'PROVIDER_LOCATION','TREATMENT_FUNCTION_CODE',
            'REFERRING_ORGANISATION_CODE','REFERRAL_REQUEST_RECEIVED_DATE'
        ]

        graph_df = df.loc[:, cols].copy()

        graph_df = graph_df.assign(
            # IDs / keys
            PATIENT_KEY=lambda d: d['PATIENT_KEY'].astype('string').str.strip(),
            # numeric
            AGE=lambda d: pd.to_numeric(d['AGE'], errors='coerce'),
            # categorical codes as strings
            ATTENDED_OR_DID_NOT_ATTEND=lambda d: d['ATTENDED_OR_DID_NOT_ATTEND'].astype('string').str.strip(),
            OUTCOME_OF_ATTENDANCE=lambda d: d['OUTCOME_OF_ATTENDANCE'].astype('string').str.strip(),
            # codes & locations as normalized strings
            ORG_CODE_LOCAL_PATIENT_IDENTIFIER=lambda d: norm_str(d['ORG_CODE_LOCAL_PATIENT_IDENTIFIER']),
            POSTCODE_SECTOR_OF_USUAL_ADDRESS=lambda d: norm_str(d['POSTCODE_SECTOR_OF_USUAL_ADDRESS']),
            ORGANISATION_CODE_CODE_OF_PROVIDER=lambda d: norm_str(d['ORGANISATION_CODE_CODE_OF_PROVIDER']),
            SITE_CODE_OF_TREATMENT=lambda d: norm_str(d['SITE_CODE_OF_TREATMENT']),
            PROVIDER_LOCATION=lambda d: norm_str(d['PROVIDER_LOCATION']),
            TREATMENT_FUNCTION_CODE=lambda d: norm_str(d['TREATMENT_FUNCTION_CODE']),
            REFERRING_ORGANISATION_CODE=lambda d: norm_str(d['REFERRING_ORGANISATION_CODE']),
            # dates
            APPOINTMENT_DATE=lambda d: pd.to_datetime(d['APPOINTMENT_DATE'], dayfirst=True, errors='coerce'),
            REFERRAL_REQUEST_RECEIVED_DATE=lambda d: pd.to_datetime(d['REFERRAL_REQUEST_RECEIVED_DATE'], dayfirst=True, errors='coerce'),
        )

        return graph_df

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load raw data: {str(e)}")

async def run_analysis():
    """Run the complete network analysis pipeline"""
    global analysis_state

    try:
        analysis_state["analysis_progress"] = "loading_data"

        # Load and preprocess data using exact logic from data_prep_leiden.py
        print("Loading and preprocessing NHS data...")
        processed_df = load_and_preprocess_data()

        analysis_state["analysis_progress"] = "sampling_data"

        # Sample data for manageable analysis
        print("Sampling data for network analysis...")
        sampled_df = sample_data_for_network(processed_df, max_records=20000)

        analysis_state["analysis_progress"] = "cleaning_data"

        # Clean data for network construction
        print("Cleaning data for network analysis...")
        network_data = clean_for_network(sampled_df)

        analysis_state["analysis_progress"] = "creating_graph"

        # Create bipartite graph
        print("Creating enhanced bipartite patient-site network...")
        G = create_enhanced_bipartite_graph(network_data)

        analysis_state["analysis_progress"] = "detecting_communities"

        # Detect communities using Leiden algorithm
        print("Detecting communities using Leiden algorithm...")
        communities = detect_communities_leiden(G, min_community_size=10)

        if communities is None:
            raise Exception("Community detection failed - check dependencies")

        analysis_state["analysis_progress"] = "analyzing_communities"

        # Analyze communities for DNA patterns
        print("Analyzing community DNA patterns...")
        community_df = analyze_community_dna_patterns(G, communities, network_data)

        analysis_state["analysis_progress"] = "identifying_risk"

        # Identify high vs low risk communities
        print("Identifying risk communities...")
        risk_communities = identify_high_low_risk_communities(community_df)

        analysis_state["analysis_progress"] = "exporting_data"

        # Export data for D3.js
        print("Exporting data for D3.js visualization...")
        export_data = export_for_d3js(G, communities, community_df,
                                     output_path=str(OUTPUT_DIR / "network-export.json"))

        # Update global state
        analysis_state.update({
            "graph": G,
            "communities": communities,
            "community_df": community_df,
            "network_data": network_data,
            "risk_communities": risk_communities,
            "initialized": True,
            "last_updated": datetime.now().isoformat(),
            "analysis_progress": "completed"
        })

        print("✅ Analysis completed successfully!")
        return True

    except Exception as e:
        analysis_state["analysis_progress"] = f"error: {str(e)}"
        print(f"❌ Analysis failed: {str(e)}")
        raise

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "NHS Network Analysis API",
        "version": "1.0.0",
        "endpoints": {
            "status": "/status",
            "initialize": "/initialize",
            "graph_data": "/graph/data",
            "communities": "/communities",
            "insights": "/insights"
        }
    }

@app.get("/status", response_model=AnalysisStatus)
async def get_status():
    """Get the current status of the network analysis"""
    return AnalysisStatus(
        initialized=analysis_state["initialized"],
        last_updated=analysis_state["last_updated"],
        progress=analysis_state["analysis_progress"],
        node_count=analysis_state["graph"].number_of_nodes() if analysis_state["graph"] else None,
        edge_count=analysis_state["graph"].number_of_edges() if analysis_state["graph"] else None,
        community_count=len(analysis_state["communities"].communities) if analysis_state["communities"] else None
    )

@app.post("/initialize")
async def initialize_analysis(background_tasks: BackgroundTasks):
    """Initialize the network analysis (runs in background)"""
    if analysis_state["analysis_progress"] in ["loading_data", "sampling_data", "cleaning_data",
                                              "creating_graph", "detecting_communities",
                                              "analyzing_communities", "identifying_risk", "exporting_data"]:
        return {"message": "Analysis already in progress", "status": analysis_state["analysis_progress"]}

    if analysis_state["initialized"]:
        return {"message": "Analysis already completed", "status": "completed"}

    # Run analysis in background
    background_tasks.add_task(run_analysis)

    return {"message": "Analysis started", "status": "initiated"}

@app.get("/graph/data", response_model=GraphData)
async def get_graph_data():
    """Get the complete graph data for D3.js visualization"""
    if not analysis_state["initialized"]:
        raise HTTPException(status_code=400, detail="Analysis not initialized. Call /initialize first.")

    # Load exported JSON data
    export_path = OUTPUT_DIR / "network-export.json"
    if not export_path.exists():
        raise HTTPException(status_code=500, detail="Export data not found. Re-run initialization.")

    with open(export_path, 'r') as f:
        data = json.load(f)

    return GraphData(**data)

@app.get("/graph/metadata")
async def get_graph_metadata():
    """Get graph metadata only (faster than full data)"""
    if not analysis_state["initialized"]:
        raise HTTPException(status_code=400, detail="Analysis not initialized. Call /initialize first.")

    export_path = OUTPUT_DIR / "network-export.json"
    if not export_path.exists():
        raise HTTPException(status_code=500, detail="Export data not found.")

    with open(export_path, 'r') as f:
        data = json.load(f)

    return {
        "metadata": data["metadata"],
        "summary": data["summary"]
    }

@app.get("/communities")
async def get_communities():
    """Get community analysis results"""
    if not analysis_state["initialized"]:
        raise HTTPException(status_code=400, detail="Analysis not initialized. Call /initialize first.")

    export_path = OUTPUT_DIR / "network-export.json"
    with open(export_path, 'r') as f:
        data = json.load(f)

    return {
        "communities": data["communities"],
        "summary": {
            "total": len(data["communities"]),
            "risk_distribution": data["summary"]["risk_distribution"]
        }
    }

@app.get("/communities/{community_id}")
async def get_community_details(community_id: int):
    """Get detailed information about a specific community"""
    if not analysis_state["initialized"]:
        raise HTTPException(status_code=400, detail="Analysis not initialized.")

    export_path = OUTPUT_DIR / "network-export.json"
    with open(export_path, 'r') as f:
        data = json.load(f)

    # Find the community
    community = next((c for c in data["communities"] if c["id"] == community_id), None)
    if not community:
        raise HTTPException(status_code=404, detail=f"Community {community_id} not found")

    # Get nodes in this community
    community_nodes = [n for n in data["nodes"] if n["community"] == community_id]
    community_links = [l for l in data["links"]
                      if any(n["id"] == l["source"] and n["community"] == community_id for n in data["nodes"]) or
                         any(n["id"] == l["target"] and n["community"] == community_id for n in data["nodes"])]

    return {
        "community": community,
        "nodes": community_nodes,
        "links": community_links,
        "stats": {
            "node_count": len(community_nodes),
            "link_count": len(community_links),
            "patients": len([n for n in community_nodes if n["type"] == "patient"]),
            "sites": len([n for n in community_nodes if n["type"] == "site"])
        }
    }

@app.get("/insights")
async def get_insights():
    """Get actionable insights from the community analysis"""
    if not analysis_state["initialized"]:
        raise HTTPException(status_code=400, detail="Analysis not initialized.")

    # Generate insights from current analysis
    if "risk_communities" not in analysis_state:
        raise HTTPException(status_code=500, detail="Risk analysis not available.")

    insights = generate_community_insights(
        analysis_state["community_df"],
        analysis_state["risk_communities"]
    )

    return {"insights": insights}

@app.get("/graph/sample/{size}")
async def get_sample_graph(size: int = 100):
    """Get a sample of the graph data for testing (limited nodes/edges)"""
    if not analysis_state["initialized"]:
        raise HTTPException(status_code=400, detail="Analysis not initialized.")

    export_path = OUTPUT_DIR / "network-export.json"
    with open(export_path, 'r') as f:
        data = json.load(f)

    # Sample nodes and corresponding edges
    sampled_nodes = data["nodes"][:size]
    sampled_node_ids = {n["id"] for n in sampled_nodes}

    sampled_links = [l for l in data["links"]
                    if l["source"] in sampled_node_ids and l["target"] in sampled_node_ids]

    return {
        "metadata": data["metadata"],
        "nodes": sampled_nodes,
        "links": sampled_links,
        "communities": data["communities"],
        "summary": data["summary"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
