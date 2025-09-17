from fastapi import FastAPI, Request, Form, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import json
import os
from pathlib import Path
import pandas as pd
import networkx as nx
from datetime import datetime
import asyncio

# Only import the functions we need, not the full module
import sys
sys.path.append(str(Path(__file__).parent))

# Import individual functions to avoid module-level data loading
from helpers import norm_str

app = FastAPI(title="NHS Network Analysis", description="Simple NHS network visualization")

# Get the directory where this script is located
BASE_DIR = Path(__file__).parent

# Create directories relative to script location
(BASE_DIR / "templates").mkdir(exist_ok=True)
(BASE_DIR / "static").mkdir(exist_ok=True)
(BASE_DIR / "output").mkdir(exist_ok=True)

# Setup templates and static files
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# Global state for analysis
analysis_state = {
    "status": "not_started",
    "progress": 0,
    "message": "Ready to start",
    "data": None,
    "settings": {
        "sample_size": 20000,
        "min_community_size": 10,
        "use_sample": True
    }
}

# Import analysis functions individually to avoid module-level execution
def import_analysis_functions():
    """Lazy import of analysis functions to avoid module-level data loading"""
    try:
        # Import cdlib here to avoid issues
        from cdlib import algorithms, evaluation
    except ImportError:
        print("Warning: cdlib not installed. Community detection will fail")
        algorithms, evaluation = None, None

    return algorithms, evaluation

def sample_data_for_network(df, max_records=20000, seed=42):
    """Sample data for manageable network analysis"""
    print(f"Original dataset: {len(df)} records")

    if len(df) <= max_records:
        print("Dataset already manageable size")
        return df

    # Sample while preserving patient diversity
    import numpy as np
    np.random.seed(seed)
    sampled_df = df.sample(n=max_records, random_state=seed)

    print(f"Sampled to: {len(sampled_df)} records")
    return sampled_df

def clean_for_network(df):
    """Clean data for network construction"""
    from collections import Counter

    # Remove rows with missing essential data
    network_df = df.dropna(subset=['PATIENT_KEY', 'SITE_CODE_OF_TREATMENT']).copy()

    # Display attendance code distribution
    print("NHS Attendance Code Distribution:")
    print(network_df['ATTENDED_OR_DID_NOT_ATTEND'].value_counts(dropna=False))

    # Fill NaN values with '0' (unknown/other)
    network_df['ATTENDED_OR_DID_NOT_ATTEND'] = network_df['ATTENDED_OR_DID_NOT_ATTEND'].fillna('0')

    # Create DNA flag - TRUE DNA includes:
    # Code 3: Did not attend (primary DNA)
    # Code 7: Arrived late, couldn't be seen (also counts as DNA)
    network_df['DNA_FLAG'] = (
        (network_df['ATTENDED_OR_DID_NOT_ATTEND'] == '3') |  # Primary DNA
        (network_df['ATTENDED_OR_DID_NOT_ATTEND'] == '7')    # Late arrival, not seen
    ).astype(int)

    print(f"\nDNA Analysis:")
    print(f"Total appointments: {len(network_df)}")
    print(f"DNA appointments: {network_df['DNA_FLAG'].sum()}")
    print(f"DNA rate: {network_df['DNA_FLAG'].mean():.1%}")

    return network_df

def create_enhanced_bipartite_graph(df):
    """Create enhanced bipartite graph with rich metadata for community detection"""
    G = nx.Graph()

    # Add nodes with comprehensive attributes
    patients = df['PATIENT_KEY'].unique()
    sites = df['SITE_CODE_OF_TREATMENT'].unique()

    # Add patient nodes with enhanced metadata
    for patient in patients:
        patient_data = df[df['PATIENT_KEY'] == patient]
        first_record = patient_data.iloc[0]

        # Calculate patient-specific metrics with Bayesian smoothing
        total_appointments = len(patient_data)
        total_dnas = patient_data['DNA_FLAG'].sum()

        # Bayesian smoothing: adds 1 DNA and 5 appointments as "prior"
        dna_rate = (total_dnas + 1) / (total_appointments + 5)

        unique_sites = patient_data['SITE_CODE_OF_TREATMENT'].nunique()

        # Age group classification
        age = first_record['AGE']
        age_group = 'Unknown'
        if pd.notna(age):
            age = float(age)
            if age < 18:
                age_group = 'Child'
            elif age < 35:
                age_group = 'Young Adult'
            elif age < 65:
                age_group = 'Adult'
            else:
                age_group = 'Senior'

        G.add_node(f"P_{patient}",
                  bipartite=0,
                  node_type='patient',
                  age=age,
                  age_group=age_group,
                  postcode=first_record['POSTCODE_SECTOR_OF_USUAL_ADDRESS'],
                  org_code=first_record['ORG_CODE_LOCAL_PATIENT_IDENTIFIER'],
                  total_appointments=total_appointments,
                  total_dnas=total_dnas,
                  dna_rate=dna_rate,
                  unique_sites=unique_sites,
                  risk_category='High' if dna_rate > 0.3 else 'Medium' if dna_rate > 0.1 else 'Low')

    # Add site nodes with enhanced metadata
    for site in sites:
        site_data = df[df['SITE_CODE_OF_TREATMENT'] == site]
        first_record = site_data.iloc[0]

        # Calculate site-specific metrics with Bayesian smoothing
        total_appointments = len(site_data)
        total_dnas = site_data['DNA_FLAG'].sum()

        # Bayesian smoothing for sites
        site_dna_rate = (total_dnas + 1) / (total_appointments + 5)

        unique_patients = site_data['PATIENT_KEY'].nunique()

        G.add_node(f"S_{site}",
                  bipartite=1,
                  node_type='site',
                  provider_location=first_record['PROVIDER_LOCATION'],
                  org_code=first_record['ORGANISATION_CODE_CODE_OF_PROVIDER'],
                  treatment_function=first_record['TREATMENT_FUNCTION_CODE'],
                  total_appointments=total_appointments,
                  total_dnas=total_dnas,
                  site_dna_rate=site_dna_rate,
                  unique_patients=unique_patients)

    # Add edges with appointment metadata
    for _, row in df.iterrows():
        patient_node = f"P_{row['PATIENT_KEY']}"
        site_node = f"S_{row['SITE_CODE_OF_TREATMENT']}"

        # If edge exists, increment weight and track DNA
        if G.has_edge(patient_node, site_node):
            G[patient_node][site_node]['weight'] += 1
            G[patient_node][site_node]['dna_count'] += row['DNA_FLAG']
        else:
            G.add_edge(patient_node, site_node,
                      weight=1,
                      dna_count=row['DNA_FLAG'],
                      appointment_date=row['APPOINTMENT_DATE'],
                      treatment_function=row['TREATMENT_FUNCTION_CODE'],
                      referring_org=row['REFERRING_ORGANISATION_CODE'],
                      outcome=row['OUTCOME_OF_ATTENDANCE'])

    # Calculate DNA rate for each edge
    for u, v, d in G.edges(data=True):
        d['dna_rate'] = d['dna_count'] / d['weight']

    return G

def detect_communities_leiden(G, min_community_size=10):
    """Use Leiden algorithm for community detection"""
    algorithms, evaluation = import_analysis_functions()

    print("🔬 Using Leiden Algorithm for Community Detection")
    print("="*60)

    if algorithms is None:
        print("❌ cdlib not available - cannot use Leiden algorithm")
        return None

    try:
        # Use Leiden algorithm
        print("🚀 Running Leiden algorithm...")
        leiden_result = algorithms.leiden(G)

        # Calculate modularity
        modularity = evaluation.newman_girvan_modularity(G, leiden_result).score

        print(f"✅ Leiden algorithm completed:")
        print(f"   📊 {len(leiden_result.communities)} communities found")
        print(f"   🎯 Modularity score: {modularity:.3f}")

        # Filter by minimum community size
        large_communities = []
        small_nodes = []

        for community in leiden_result.communities:
            if len(community) >= min_community_size:
                large_communities.append(community)
            else:
                small_nodes.extend(community)

        # Merge small nodes with largest community
        if small_nodes and large_communities:
            import numpy as np
            largest_idx = max(range(len(large_communities)), key=lambda i: len(large_communities[i]))
            large_communities[largest_idx].extend(small_nodes)
            print(f"🔗 Merged {len(small_nodes)} nodes from small communities into largest community")

        # Create filtered result
        class LeidenResult:
            def __init__(self, communities):
                self.communities = communities
                self.method_name = 'leiden_filtered'

        filtered_result = LeidenResult(large_communities)
        print(f"🎯 Final result: {len(filtered_result.communities)} communities (min size: {min_community_size})")

        return filtered_result

    except Exception as e:
        print(f"❌ Leiden algorithm failed: {e}")
        return None

def analyze_community_dna_patterns(G, communities, df):
    """Analyze DNA patterns within detected communities"""
    import numpy as np
    from collections import Counter

    print("\n=== COMMUNITY DNA ANALYSIS ===")

    community_stats = []

    for i, community in enumerate(communities.communities):
        # Separate patients and sites in community
        patients_in_comm = [n for n in community if G.nodes[n]['node_type'] == 'patient']
        sites_in_comm = [n for n in community if G.nodes[n]['node_type'] == 'site']

        if len(patients_in_comm) == 0:
            continue

        # Aggregate community metrics
        community_dna_rates = [G.nodes[p]['dna_rate'] for p in patients_in_comm]
        community_ages = [G.nodes[p]['age'] for p in patients_in_comm if pd.notna(G.nodes[p]['age'])]
        community_appointments = [G.nodes[p]['total_appointments'] for p in patients_in_comm]

        # Age group distribution
        age_groups = [G.nodes[p]['age_group'] for p in patients_in_comm]
        age_group_counts = Counter(age_groups)
        dominant_age_group = max(age_group_counts.items(), key=lambda x: x[1])[0] if age_group_counts else 'Unknown'

        # Risk category distribution
        risk_categories = [G.nodes[p]['risk_category'] for p in patients_in_comm]
        risk_counts = Counter(risk_categories)

        # Site characteristics
        site_dna_rates = [G.nodes[s]['site_dna_rate'] for s in sites_in_comm if 'site_dna_rate' in G.nodes[s]]

        # Calculate risk score
        avg_dna = np.mean(community_dna_rates) if community_dna_rates else 0
        total_patients = sum(risk_counts.values()) if risk_counts else 1
        high_risk_prop = risk_counts.get('High', 0) / total_patients
        risk_score = (avg_dna * 0.7) + (high_risk_prop * 0.3)

        community_stats.append({
            'community_id': i,
            'size': len(community),
            'patients_count': len(patients_in_comm),
            'sites_count': len(sites_in_comm),
            'avg_dna_rate': np.mean(community_dna_rates) if community_dna_rates else 0,
            'median_dna_rate': np.median(community_dna_rates) if community_dna_rates else 0,
            'std_dna_rate': np.std(community_dna_rates) if community_dna_rates else 0,
            'avg_age': np.mean(community_ages) if community_ages else None,
            'dominant_age_group': dominant_age_group,
            'avg_appointments': np.mean(community_appointments) if community_appointments else 0,
            'high_risk_patients': risk_counts.get('High', 0),
            'medium_risk_patients': risk_counts.get('Medium', 0),
            'low_risk_patients': risk_counts.get('Low', 0),
            'avg_site_dna_rate': np.mean(site_dna_rates) if site_dna_rates else 0,
            'risk_score': risk_score
        })

    community_df = pd.DataFrame(community_stats)
    community_df = community_df.sort_values('risk_score', ascending=False)

    print(f"\nAnalyzed {len(community_df)} communities")
    return community_df

def identify_high_low_risk_communities(community_df, use_percentiles=True):
    """Identify high-risk and low-risk communities"""
    print("\n=== HIGH vs LOW RISK COMMUNITIES ===")

    if use_percentiles:
        high_threshold = community_df['risk_score'].quantile(0.75)
        low_threshold = community_df['risk_score'].quantile(0.25)
        print(f"📊 Using percentile thresholds: High≥{high_threshold:.3f}, Low≤{low_threshold:.3f}")
    else:
        high_threshold = 0.3
        low_threshold = 0.1

    high_risk = community_df[community_df['risk_score'] >= high_threshold]
    low_risk = community_df[community_df['risk_score'] <= low_threshold]
    medium_risk = community_df[
        (community_df['risk_score'] > low_threshold) &
        (community_df['risk_score'] < high_threshold)
    ]

    return {
        'high_risk': high_risk,
        'medium_risk': medium_risk,
        'low_risk': low_risk
    }

def load_and_preprocess_data(sample_size=20000):
    """Load and preprocess NHS data"""
    try:
        read_args = dict(dtype="string", low_memory=False)
        data_dir = BASE_DIR / "data"
        df1 = pd.read_csv(data_dir / "Hackathon_DN_FINAL_1.csv", **read_args)
        df2 = pd.read_csv(data_dir / "Hackathon_DN_FINAL_2.csv", **read_args)
        df3 = pd.read_csv(data_dir / "Hackathon_DN_FINAL_3.csv", **read_args)
        df = pd.concat([df1, df2, df3], ignore_index=True)

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
            PATIENT_KEY=lambda d: d['PATIENT_KEY'].astype('string').str.strip(),
            AGE=lambda d: pd.to_numeric(d['AGE'], errors='coerce'),
            ATTENDED_OR_DID_NOT_ATTEND=lambda d: d['ATTENDED_OR_DID_NOT_ATTEND'].astype('string').str.strip(),
            OUTCOME_OF_ATTENDANCE=lambda d: d['OUTCOME_OF_ATTENDANCE'].astype('string').str.strip(),
            ORG_CODE_LOCAL_PATIENT_IDENTIFIER=lambda d: norm_str(d['ORG_CODE_LOCAL_PATIENT_IDENTIFIER']),
            POSTCODE_SECTOR_OF_USUAL_ADDRESS=lambda d: norm_str(d['POSTCODE_SECTOR_OF_USUAL_ADDRESS']),
            ORGANISATION_CODE_CODE_OF_PROVIDER=lambda d: norm_str(d['ORGANISATION_CODE_CODE_OF_PROVIDER']),
            SITE_CODE_OF_TREATMENT=lambda d: norm_str(d['SITE_CODE_OF_TREATMENT']),
            PROVIDER_LOCATION=lambda d: norm_str(d['PROVIDER_LOCATION']),
            TREATMENT_FUNCTION_CODE=lambda d: norm_str(d['TREATMENT_FUNCTION_CODE']),
            REFERRING_ORGANISATION_CODE=lambda d: norm_str(d['REFERRING_ORGANISATION_CODE']),
            APPOINTMENT_DATE=lambda d: pd.to_datetime(d['APPOINTMENT_DATE'], dayfirst=True, errors='coerce'),
            REFERRAL_REQUEST_RECEIVED_DATE=lambda d: pd.to_datetime(d['REFERRAL_REQUEST_RECEIVED_DATE'], dayfirst=True, errors='coerce'),
        )

        if sample_size and len(graph_df) > sample_size:
            graph_df = sample_data_for_network(graph_df, max_records=sample_size)

        return graph_df

    except Exception as e:
        raise Exception(f"Failed to load data: {str(e)}")

def export_for_d3js(G, communities, community_df, output_path):
    """Export data for D3.js visualization"""
    import numpy as np

    # Create node to community mapping
    node_to_community = {}
    for i, community in enumerate(communities.communities):
        for node in community:
            node_to_community[node] = i

    # Calculate risk thresholds
    high_threshold = community_df['risk_score'].quantile(0.75)
    low_threshold = community_df['risk_score'].quantile(0.25)

    # Convert nodes to D3.js format
    nodes = []
    for node_id in G.nodes():
        node_data = G.nodes[node_id]
        community_id = node_to_community.get(node_id, -1)

        # Get community risk level
        if community_id >= 0:
            comm_data = community_df[community_df['community_id'] == community_id]
            if len(comm_data) > 0:
                risk_score = comm_data.iloc[0]['risk_score']
                if risk_score >= high_threshold:
                    risk_level = "High"
                elif risk_score <= low_threshold:
                    risk_level = "Low"
                else:
                    risk_level = "Medium"
            else:
                risk_level = "Medium"
        else:
            risk_level = "Medium"

        # Create node object
        node = {
            "id": node_id,
            "type": node_data['node_type'],
            "community": community_id,
            "risk_level": risk_level
        }

        # Add type-specific attributes
        if node_data['node_type'] == 'patient':
            node.update({
                "dna_rate": float(node_data.get('dna_rate', 0)),
                "age_group": node_data.get('age_group', 'Unknown'),
                "age": float(node_data.get('age', 0)) if pd.notna(node_data.get('age')) else None,
                "appointments": int(node_data.get('total_appointments', 0)),
                "dna_count": int(node_data.get('total_dnas', 0)),
                "unique_sites": int(node_data.get('unique_sites', 0)),
                "postcode": node_data.get('postcode', ''),
                "risk_category": node_data.get('risk_category', 'Medium')
            })
        elif node_data['node_type'] == 'site':
            node.update({
                "dna_rate": float(node_data.get('site_dna_rate', 0)),
                "location": node_data.get('provider_location', ''),
                "appointments": int(node_data.get('total_appointments', 0)),
                "dna_count": int(node_data.get('total_dnas', 0)),
                "unique_patients": int(node_data.get('unique_patients', 0)),
                "treatment_function": node_data.get('treatment_function', ''),
                "org_code": node_data.get('org_code', '')
            })

        nodes.append(node)

    # Convert edges to D3.js format
    links = []
    for source, target, edge_data in G.edges(data=True):
        link = {
            "source": source,
            "target": target,
            "weight": int(edge_data.get('weight', 1)),
            "dna_count": int(edge_data.get('dna_count', 0)),
            "dna_rate": float(edge_data.get('dna_rate', 0)),
            "strength": min(edge_data.get('weight', 1) / 10.0, 1.0)
        }
        links.append(link)

    # Convert community data
    communities_data = []
    for _, comm_data in community_df.iterrows():
        community = {
            "id": int(comm_data['community_id']),
            "patients": int(comm_data['patients_count']),
            "sites": int(comm_data['sites_count']),
            "avg_dna_rate": float(comm_data['avg_dna_rate']),
            "risk_score": float(comm_data['risk_score']),
            "dominant_age": comm_data['dominant_age_group'],
            "high_risk_patients": int(comm_data.get('high_risk_patients', 0)),
            "medium_risk_patients": int(comm_data.get('medium_risk_patients', 0)),
            "low_risk_patients": int(comm_data.get('low_risk_patients', 0))
        }

        # Determine risk level
        if comm_data['risk_score'] >= high_threshold:
            community['risk_level'] = "High"
        elif comm_data['risk_score'] <= low_threshold:
            community['risk_level'] = "Low"
        else:
            community['risk_level'] = "Medium"

        communities_data.append(community)

    # Create the complete D3.js data structure
    export_data = {
        "metadata": {
            "total_nodes": G.number_of_nodes(),
            "total_edges": G.number_of_edges(),
            "total_communities": len(communities.communities),
            "high_risk_communities": len([c for c in communities_data if c['risk_level'] == 'High']),
            "medium_risk_communities": len([c for c in communities_data if c['risk_level'] == 'Medium']),
            "low_risk_communities": len([c for c in communities_data if c['risk_level'] == 'Low']),
            "thresholds": {
                "high": float(high_threshold),
                "low": float(low_threshold)
            },
            "generated_at": datetime.now().isoformat(),
            "algorithm": "leiden"
        },
        "nodes": nodes,
        "links": links,
        "communities": communities_data,
        "summary": {
            "total_patients": len([n for n in nodes if n['type'] == 'patient']),
            "total_sites": len([n for n in nodes if n['type'] == 'site']),
            "overall_dna_rate": np.mean([n['dna_rate'] for n in nodes if 'dna_rate' in n]),
            "age_groups": {
                age_group: len([n for n in nodes if n.get('age_group') == age_group])
                for age_group in set(n.get('age_group', 'Unknown') for n in nodes if n['type'] == 'patient')
            },
            "risk_distribution": {
                "High": len([c for c in communities_data if c['risk_level'] == 'High']),
                "Medium": len([c for c in communities_data if c['risk_level'] == 'Medium']),
                "Low": len([c for c in communities_data if c['risk_level'] == 'Low'])
            }
        }
    }

    # Save to JSON file
    with open(output_path, 'w') as f:
        json.dump(export_data, f, indent=2, default=str)

    print(f"✅ D3.js data exported to {output_path}")
    return export_data

async def run_analysis():
    """Run the complete analysis pipeline"""
    global analysis_state

    try:
        settings = analysis_state["settings"]

        analysis_state["status"] = "loading"
        analysis_state["progress"] = 10
        analysis_state["message"] = "Loading NHS data..."

        # Load and preprocess
        processed_df = load_and_preprocess_data(
            sample_size=settings["sample_size"] if settings["use_sample"] else None
        )

        analysis_state["progress"] = 30
        analysis_state["message"] = "Cleaning data..."

        # Clean for network
        network_data = clean_for_network(processed_df)

        analysis_state["progress"] = 50
        analysis_state["message"] = "Creating network graph..."

        # Create graph
        G = create_enhanced_bipartite_graph(network_data)

        analysis_state["progress"] = 70
        analysis_state["message"] = "Detecting communities with Leiden algorithm..."

        # Detect communities
        communities = detect_communities_leiden(G, min_community_size=settings["min_community_size"])

        if communities is None:
            raise Exception("Community detection failed")

        analysis_state["progress"] = 85
        analysis_state["message"] = "Analyzing community patterns..."

        # Analyze communities
        community_df = analyze_community_dna_patterns(G, communities, network_data)
        risk_communities = identify_high_low_risk_communities(community_df)

        analysis_state["progress"] = 95
        analysis_state["message"] = "Exporting visualization data..."

        # Export for D3.js
        export_data = export_for_d3js(G, communities, community_df,
                                     output_path=str(BASE_DIR / "output" / "network-export.json"))

        analysis_state["status"] = "completed"
        analysis_state["progress"] = 100
        analysis_state["message"] = f"Analysis complete! Found {len(communities.communities)} communities"
        analysis_state["data"] = export_data

    except Exception as e:
        analysis_state["status"] = "error"
        analysis_state["message"] = f"Analysis failed: {str(e)}"

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    return templates.TemplateResponse("settings.html", {
        "request": request,
        "settings": analysis_state["settings"]
    })

@app.post("/settings")
async def update_settings(
    sample_size: int = Form(20000),
    min_community_size: int = Form(10),
    use_sample: bool = Form(False)
):
    analysis_state["settings"].update({
        "sample_size": sample_size,
        "min_community_size": min_community_size,
        "use_sample": use_sample
    })
    return {"message": "Settings updated successfully"}

@app.get("/visualization", response_class=HTMLResponse)
async def visualization(request: Request):
    has_data = analysis_state["status"] == "completed" and analysis_state["data"] is not None
    return templates.TemplateResponse("visualization.html", {
        "request": request,
        "has_data": has_data,
        "status": analysis_state["status"],
        "message": analysis_state["message"]
    })

@app.post("/start-analysis")
async def start_analysis(background_tasks: BackgroundTasks):
    if analysis_state["status"] == "loading":
        return {"message": "Analysis already in progress"}

    analysis_state["status"] = "loading"
    analysis_state["progress"] = 0
    analysis_state["message"] = "Starting analysis..."

    background_tasks.add_task(run_analysis)
    return {"message": "Analysis started"}

@app.get("/status")
async def get_status():
    return {
        "status": analysis_state["status"],
        "progress": analysis_state["progress"],
        "message": analysis_state["message"]
    }

@app.get("/graph-data")
async def get_graph_data():
    if analysis_state["status"] != "completed" or not analysis_state["data"]:
        return {"error": "No data available. Please run analysis first."}
    return analysis_state["data"]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
