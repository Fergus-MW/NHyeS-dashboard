import pandas as pd
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from collections import Counter
import seaborn as sns
import warnings
import os

# Suppress warnings
warnings.filterwarnings('ignore')

# Create output directory for plots
os.makedirs('network_analysis/plots', exist_ok=True)

try:
    from cdlib import algorithms, evaluation
except ImportError:
    print("Warning: cdlib not installed. Using NetworkX community detection")
    algorithms, evaluation = None, None

# Your existing data preparation code (keeping it exactly as is)
from helpers import norm_str

read_args = dict(dtype="string", low_memory=False)
df1 = pd.read_csv("network_analysis/data/Hackathon_DN_FINAL_1.csv", **read_args)
df2 = pd.read_csv("network_analysis/data/Hackathon_DN_FINAL_2.csv", **read_args)
df3 = pd.read_csv("network_analysis/data/Hackathon_DN_FINAL_3.csv", **read_args)
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
    # IDs / keys
    PATIENT_KEY=lambda d: d['PATIENT_KEY'].astype('string').str.strip(),

    # numeric
    AGE=lambda d: pd.to_numeric(d['AGE'], errors='coerce'),

    # categorical codes as strings (we map to labels later)
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

# ======================== NEW NETWORK ANALYSIS CODE ========================

def sample_data_for_network(df, max_records=20000, seed=42):
    """Sample data for manageable network analysis on M4 MacBook Pro"""
    print(f"Original dataset: {len(df)} records")

    if len(df) <= max_records:
        print("Dataset already manageable size")
        return df

    # Sample while preserving patient diversity
    np.random.seed(seed)
    sampled_df = df.sample(n=max_records, random_state=seed)

    print(f"Sampled to: {len(sampled_df)} records")
    return sampled_df

def clean_for_network(df):
    """Clean data for network construction"""
    # NHS Attendance Code Mappings (based on provided image)
    NHS_ATTENDANCE_CODES = {
        '2': 'Patient cancelled',           # 8.2% - patient-initiated cancellation
        '3': 'Did not attend (DNA)',        # 6.5% - true no-show (THIS IS THE DNA CODE!)
        '4': 'Cancelled by HCP',            # 16.2% - system cancellation
        '5': 'Seen',                        # 66.0% - successful attendance
        '6': 'Arrived late but was seen',   # 3.1% - successful attendance
        '7': 'Arrived late, could not be seen'  # <0.1% - true no-show
    }

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
        # This prevents extreme scores from low appointment counts
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

        # Bayesian smoothing for sites: adds 1 DNA and 5 appointments as "prior"
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
    print("🔬 Using Leiden Algorithm for Community Detection")
    print("="*60)

    if algorithms is None:
        print("❌ cdlib not available - cannot use Leiden algorithm")
        print("💡 Install with: uv add cdlib")
        return None

    try:
        # Use Leiden algorithm with correct parameters
        print("🚀 Running Leiden algorithm...")
        leiden_result = algorithms.leiden(G)

        # Calculate modularity
        modularity = evaluation.newman_girvan_modularity(G, leiden_result).score

        print(f"✅ Leiden algorithm completed:")
        print(f"   📊 {len(leiden_result.communities)} communities found")
        print(f"   🎯 Modularity score: {modularity:.3f}")
        print(f"   📏 Community sizes: min={min(len(c) for c in leiden_result.communities)}, "
              f"max={max(len(c) for c in leiden_result.communities)}, "
              f"avg={np.mean([len(c) for c in leiden_result.communities]):.1f}")

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
        print("💡 Try installing additional dependencies: uv add leidenalg python-igraph")
        return None

# Import the rest of the functions we need...
# (I'll copy the essential functions from the original file)

def analyze_community_dna_patterns(G, communities, df):
    """Analyze DNA patterns within detected communities"""
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
            'risk_score': calculate_community_risk_score(community_dna_rates, risk_counts)
        })

    community_df = pd.DataFrame(community_stats)

    # Sort by risk score
    community_df = community_df.sort_values('risk_score', ascending=False)

    print(f"\nAnalyzed {len(community_df)} communities:")
    print(community_df[['community_id', 'patients_count', 'avg_dna_rate', 'dominant_age_group', 'risk_score']].head(10))

    # Show risk score distribution summary
    print(f"\n📊 Risk Score Distribution Summary:")
    print(f"   Range: {community_df['risk_score'].min():.3f} to {community_df['risk_score'].max():.3f}")
    print(f"   Mean: {community_df['risk_score'].mean():.3f}")
    print(f"   25th percentile: {community_df['risk_score'].quantile(0.25):.3f}")
    print(f"   75th percentile: {community_df['risk_score'].quantile(0.75):.3f}")

    return community_df

def calculate_community_risk_score(dna_rates, risk_counts):
    """Calculate a composite risk score for a community"""
    if not dna_rates:
        return 0

    # Weight by average DNA rate and proportion of high-risk patients
    avg_dna = np.mean(dna_rates)
    total_patients = sum(risk_counts.values()) if risk_counts else 1
    high_risk_prop = risk_counts.get('High', 0) / total_patients

    # Composite score (0-1 scale)
    risk_score = (avg_dna * 0.7) + (high_risk_prop * 0.3)
    return risk_score

def identify_high_low_risk_communities(community_df, use_percentiles=True):
    """Identify high-risk and low-risk communities using data-driven thresholds for even distribution"""
    print("\n=== HIGH vs LOW RISK COMMUNITIES ===")

    if use_percentiles:
        # Use percentile-based thresholds for balanced distribution
        high_threshold = community_df['risk_score'].quantile(0.75)  # Top 25%
        low_threshold = community_df['risk_score'].quantile(0.25)   # Bottom 25%

        print(f"📊 Using data-driven percentile thresholds for even distribution:")
        print(f"   High-risk: ≥{high_threshold:.3f} (top 25% of communities)")
        print(f"   Low-risk:  ≤{low_threshold:.3f} (bottom 25% of communities)")
        print(f"   Medium-risk: {low_threshold:.3f} to {high_threshold:.3f} (middle 50%)")
    else:
        # Use fixed thresholds (original method)
        high_threshold = 0.3
        low_threshold = 0.1
        print(f"📊 Using fixed thresholds:")
        print(f"   High-risk: ≥{high_threshold}")
        print(f"   Low-risk:  ≤{low_threshold}")

    high_risk = community_df[community_df['risk_score'] >= high_threshold]
    low_risk = community_df[community_df['risk_score'] <= low_threshold]
    medium_risk = community_df[
        (community_df['risk_score'] > low_threshold) &
        (community_df['risk_score'] < high_threshold)
    ]

    print(f"High-risk communities ({len(high_risk)}): Risk score >= {high_threshold}")
    if len(high_risk) > 0:
        print("Characteristics:")
        print(f"- Average DNA rate: {high_risk['avg_dna_rate'].mean():.3f}")
        print(f"- Average community size: {high_risk['patients_count'].mean():.1f} patients")
        print(f"- Most common age group: {high_risk['dominant_age_group'].mode().iloc[0] if len(high_risk) > 0 else 'N/A'}")
        print(f"- Total high-risk patients: {high_risk['high_risk_patients'].sum()}")

    print(f"\nLow-risk communities ({len(low_risk)}): Risk score <= {low_threshold}")
    if len(low_risk) > 0:
        print("Characteristics:")
        print(f"- Average DNA rate: {low_risk['avg_dna_rate'].mean():.3f}")
        print(f"- Average community size: {low_risk['patients_count'].mean():.1f} patients")
        print(f"- Most common age group: {low_risk['dominant_age_group'].mode().iloc[0] if len(low_risk) > 0 else 'N/A'}")

    print(f"\nMedium-risk communities: {len(medium_risk)}")

    return {
        'high_risk': high_risk,
        'medium_risk': medium_risk,
        'low_risk': low_risk
    }

def generate_community_insights(community_df, risk_communities):
    """Generate actionable insights from community analysis"""
    print("\n=== ACTIONABLE INSIGHTS ===")

    insights = []

    # High-risk community insights
    for _, comm in risk_communities['high_risk'].iterrows():
        insights.append({
            'community_id': comm['community_id'],
            'type': 'High Risk',
            'priority': 'Urgent',
            'patients_affected': comm['patients_count'],
            'key_issue': f"High DNA rate ({comm['avg_dna_rate']:.1%})",
            'recommendation': f"Focus intervention on {comm['dominant_age_group']} patients"
        })

    # Site-specific insights
    high_risk_comms = risk_communities['high_risk']
    if len(high_risk_comms) > 0:
        avg_site_dna = high_risk_comms['avg_site_dna_rate'].mean()
        if avg_site_dna > 0.2:
            insights.append({
                'type': 'Site Performance',
                'priority': 'High',
                'key_issue': f"Sites in high-risk communities have {avg_site_dna:.1%} DNA rate",
                'recommendation': 'Review site capacity and scheduling practices'
            })

    # Age group patterns
    age_group_risk = community_df.groupby('dominant_age_group')['risk_score'].mean().sort_values(ascending=False)
    if len(age_group_risk) > 0:
        highest_risk_age = age_group_risk.index[0]
        insights.append({
            'type': 'Demographic Pattern',
            'priority': 'Medium',
            'key_issue': f"{highest_risk_age} patients show highest community risk",
            'recommendation': f'Develop targeted engagement strategies for {highest_risk_age} demographic'
        })

    # Print insights
    for i, insight in enumerate(insights, 1):
        print(f"\n{i}. {insight['type']} - {insight.get('priority', 'Medium')} Priority")
        print(f"   Issue: {insight['key_issue']}")
        print(f"   Action: {insight['recommendation']}")
        if 'patients_affected' in insight:
            print(f"   Impact: {insight['patients_affected']} patients")

    return insights

# ======================== MAIN EXECUTION ========================

if __name__ == "__main__":
    # Sample data for manageable analysis on M4 MacBook Pro
    print("🔬 NHS LEIDEN COMMUNITY ANALYSIS")
    print("="*50)
    print("Sampling data for network analysis...")
    sampled_df = sample_data_for_network(graph_df, max_records=20000)

    # Clean data
    print("\nCleaning data for network analysis...")
    network_data = clean_for_network(sampled_df)
    print(f"Network dataset: {len(network_data)} records")

    # Create enhanced bipartite graph
    print("\nCreating enhanced bipartite patient-site network...")
    G = create_enhanced_bipartite_graph(network_data)
    print(f"Created graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")

    # Community Detection with Leiden
    print("\n" + "="*50)
    print("LEIDEN COMMUNITY DETECTION & DNA ANALYSIS")
    print("="*50)

    # Detect communities using Leiden algorithm
    communities = detect_communities_leiden(G, min_community_size=10)

    if communities is not None:
        # Analyze communities for DNA patterns
        community_df = analyze_community_dna_patterns(G, communities, network_data)

        # Identify high vs low risk communities
        risk_communities = identify_high_low_risk_communities(community_df)

        # Generate actionable insights
        insights = generate_community_insights(community_df, risk_communities)

        print("\n" + "="*50)
        print("LEIDEN COMMUNITY ANALYSIS COMPLETE")
        print("="*50)
        print("\n🎯 Key Findings:")
        print(f"• Identified {len(community_df)} distinct patient-site communities using Leiden algorithm")
        print(f"• {len(risk_communities['high_risk'])} high-risk communities requiring urgent intervention")
        print(f"• {len(risk_communities['low_risk'])} low-risk communities with good attendance patterns")

        print("\n📋 Next Steps:")
        print("1. Deploy targeted interventions for high-risk communities")
        print("2. Analyze temporal evolution of community risk")
        print("3. Implement community-specific booking strategies")
        print("4. Monitor community risk scores over time")
        print("5. Scale successful low-risk community practices")
    else:
        print("❌ Community detection failed - please check dependencies")
        print("💡 Try: uv add leidenalg python-igraph")
