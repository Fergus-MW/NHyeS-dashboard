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

try:
    from sklearn.cluster import KMeans, SpectralClustering
    from sklearn.preprocessing import StandardScaler
    sklearn_available = True
except ImportError:
    print("Warning: scikit-learn not available for advanced clustering")
    sklearn_available = False

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

def create_backbone(G, alpha=0.05):
    """Create backbone using disparity filter"""
    backbone = G.copy()
    edges_to_remove = []

    for node in G.nodes():
        if G.degree(node) > 1:  # Only apply to nodes with multiple connections
            neighbors = list(G.neighbors(node))
            weights = [G[node][neighbor]['weight'] for neighbor in neighbors]
            total_weight = sum(weights)

            for neighbor in neighbors:
                edge_weight = G[node][neighbor]['weight']
                # Simplified disparity filter
                p_value = (edge_weight / total_weight) ** (len(neighbors) - 1)

                if p_value < alpha:  # Keep significant edges
                    continue
                else:
                    edges_to_remove.append((node, neighbor))

    backbone.remove_edges_from(edges_to_remove)
    return backbone

def detect_communities_with_stats(G, min_community_size=10):
    """Run multiple community detection algorithms and show comparative stats"""
    print("🔬 Running multiple community detection algorithms...")
    print("="*60)

    results = {}

    # Algorithm 1: NetworkX Greedy Modularity
    print("1️⃣  NetworkX Greedy Modularity...")
    try:
        from networkx.algorithms import community
        greedy_comms = community.greedy_modularity_communities(G)
        greedy_modularity = nx.algorithms.community.modularity(G, greedy_comms)

        result = CommunityResult([list(c) for c in greedy_comms], 'greedy_modularity')
        results['Greedy Modularity'] = {
            'result': result,
            'communities': len(result.communities),
            'modularity': greedy_modularity,
            'largest_community': max(len(c) for c in result.communities),
            'avg_community_size': np.mean([len(c) for c in result.communities])
        }
        print(f"   ✅ {len(result.communities)} communities, modularity: {greedy_modularity:.3f}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Algorithm 2: NetworkX Label Propagation
    print("2️⃣  NetworkX Label Propagation...")
    try:
        from networkx.algorithms import community
        label_comms = list(community.label_propagation_communities(G, seed=42))
        label_modularity = nx.algorithms.community.modularity(G, label_comms)

        result = CommunityResult([list(c) for c in label_comms], 'label_propagation')
        results['Label Propagation'] = {
            'result': result,
            'communities': len(result.communities),
            'modularity': label_modularity,
            'largest_community': max(len(c) for c in result.communities),
            'avg_community_size': np.mean([len(c) for c in result.communities])
        }
        print(f"   ✅ {len(result.communities)} communities, modularity: {label_modularity:.3f}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Algorithm 3: cdlib Leiden (if available)
    if algorithms is not None:
        print("3️⃣  cdlib Leiden Algorithm...")
        try:
            leiden_result = algorithms.leiden(G, randomness=0.1)
            leiden_modularity = evaluation.newman_girvan_modularity(G, leiden_result).score

            results['Leiden'] = {
                'result': leiden_result,
                'communities': len(leiden_result.communities),
                'modularity': leiden_modularity,
                'largest_community': max(len(c) for c in leiden_result.communities),
                'avg_community_size': np.mean([len(c) for c in leiden_result.communities])
            }
            print(f"   ✅ {len(leiden_result.communities)} communities, modularity: {leiden_modularity:.3f}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

    # Algorithm 4: cdlib Louvain (if available)
    if algorithms is not None:
        print("4️⃣  cdlib Louvain Algorithm...")
        try:
            louvain_result = algorithms.louvain(G, randomness=0.1)
            louvain_modularity = evaluation.newman_girvan_modularity(G, louvain_result).score

            results['Louvain'] = {
                'result': louvain_result,
                'communities': len(louvain_result.communities),
                'modularity': louvain_modularity,
                'largest_community': max(len(c) for c in louvain_result.communities),
                'avg_community_size': np.mean([len(c) for c in louvain_result.communities])
            }
            print(f"   ✅ {len(louvain_result.communities)} communities, modularity: {louvain_modularity:.3f}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

    # Algorithm 5: Spectral Clustering (if sklearn available)
    if sklearn_available and len(G.nodes()) < 5000:  # Only for smaller networks
        print("5️⃣  Scikit-learn Spectral Clustering...")
        try:
            # Convert to adjacency matrix
            adj_matrix = nx.adjacency_matrix(G).toarray()

            # Try different numbers of clusters
            best_k = None
            best_score = -1

            for k in [10, 20, 50, min(100, len(G.nodes())//50)]:
                if k < len(G.nodes()):
                    spectral = SpectralClustering(n_clusters=k, random_state=42, affinity='precomputed')
                    labels = spectral.fit_predict(adj_matrix)

                    # Convert to communities
                    communities = {}
                    nodes = list(G.nodes())
                    for i, label in enumerate(labels):
                        if label not in communities:
                            communities[label] = []
                        communities[label].append(nodes[i])

                    community_list = list(communities.values())
                    modularity = nx.algorithms.community.modularity(G, community_list)

                    if modularity > best_score:
                        best_score = modularity
                        best_k = k
                        best_communities = community_list

            if best_k:
                result = CommunityResult(best_communities, f'spectral_k{best_k}')
                results['Spectral Clustering'] = {
                    'result': result,
                    'communities': len(result.communities),
                    'modularity': best_score,
                    'largest_community': max(len(c) for c in result.communities),
                    'avg_community_size': np.mean([len(c) for c in result.communities])
                }
                print(f"   ✅ {len(result.communities)} communities (k={best_k}), modularity: {best_score:.3f}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

    # Display comparison table
    print("\n📊 ALGORITHM COMPARISON")
    print("="*80)
    print(f"{'Algorithm':<20} {'Communities':<12} {'Modularity':<12} {'Largest':<10} {'Avg Size':<10}")
    print("-"*80)

    best_modularity = -1
    best_algorithm = None

    for name, stats in results.items():
        print(f"{name:<20} {stats['communities']:<12} {stats['modularity']:<12.3f} {stats['largest_community']:<10} {stats['avg_community_size']:<10.1f}")

        if stats['modularity'] > best_modularity:
            best_modularity = stats['modularity']
            best_algorithm = name

    print("-"*80)
    print(f"🏆 Best algorithm: {best_algorithm} (modularity: {best_modularity:.3f})")

    # Filter the best result by community size
    if best_algorithm and best_algorithm in results:
        best_result = results[best_algorithm]['result']
        filtered_result = filter_communities_by_size(best_result, min_community_size)
        print(f"🔽 After filtering (min size {min_community_size}): {len(filtered_result.communities)} communities")
        return filtered_result
    else:
        # Fallback to greedy if available
        if 'Greedy Modularity' in results:
            fallback_result = results['Greedy Modularity']['result']
            filtered_result = filter_communities_by_size(fallback_result, min_community_size)
            print(f"🔄 Using fallback: {len(filtered_result.communities)} communities")
            return filtered_result
        else:
            raise RuntimeError("No community detection algorithms succeeded")


def filter_communities_by_size(community_result, min_size):
    """Filter communities by minimum size and merge small ones"""
    large_communities = []
    small_nodes = []

    for comm in community_result.communities:
        if len(comm) >= min_size:
            large_communities.append(comm)
        else:
            small_nodes.extend(comm)

    # Merge small nodes with largest community
    if small_nodes and large_communities:
        largest_idx = max(range(len(large_communities)), key=lambda i: len(large_communities[i]))
        large_communities[largest_idx].extend(small_nodes)
    elif small_nodes and len(small_nodes) >= min_size:
        large_communities.append(small_nodes)

    return CommunityResult(large_communities, f'filtered_{community_result.method_name}')


class CommunityResult:
    """Simple class to hold community detection results"""
    def __init__(self, communities, method_name):
        self.communities = communities
        self.method_name = method_name

def basic_community_detection(G):
    """Fallback community detection using NetworkX"""
    from networkx.algorithms import community

    print("Using basic NetworkX community detection")
    communities_nx = community.greedy_modularity_communities(G)

    # Convert to cdlib-like format
    class BasicCommunity:
        def __init__(self, communities):
            self.communities = [list(c) for c in communities]
            self.method_name = 'greedy_networkx'

    return {'greedy_networkx': BasicCommunity(communities_nx)}

def create_consensus_clustering(communities_dict, G, threshold=0.3):
    """Create consensus clustering from multiple community detection results"""
    print(f"\nCreating consensus clustering (threshold: {threshold})...")

    # Filter to similar algorithms (modularity-based ones)
    similar_algorithms = ['leiden', 'louvain', 'greedy', 'spinglass']
    filtered_communities = {k: v for k, v in communities_dict.items()
                          if k in similar_algorithms and k in communities_dict}

    if len(filtered_communities) < 2:
        print("Not enough algorithms for consensus, using best single result")
        best_comm = max(communities_dict.values(),
                       key=lambda x: len(x.communities) if hasattr(x, 'communities') else 0)
        return best_comm

    # Create consensus matrix
    nodes = list(G.nodes())
    node_to_idx = {node: i for i, node in enumerate(nodes)}
    n_nodes = len(nodes)
    consensus_matrix = np.zeros((n_nodes, n_nodes))
    n_algorithms = len(filtered_communities)

    # Build consensus matrix
    for comm_result in filtered_communities.values():
        for community in comm_result.communities:
            for node_i in community:
                for node_j in community:
                    if node_i in node_to_idx and node_j in node_to_idx:
                        i_idx = node_to_idx[node_i]
                        j_idx = node_to_idx[node_j]
                        consensus_matrix[i_idx][j_idx] += 1

    # Normalize and apply threshold
    consensus_matrix = consensus_matrix / n_algorithms
    consensus_matrix[consensus_matrix <= threshold] = 0

    # Create consensus graph and detect communities
    G_consensus = nx.from_numpy_array(consensus_matrix)

    # Map back original node labels
    mapping = {i: nodes[i] for i in range(len(nodes))}
    G_consensus = nx.relabel_nodes(G_consensus, mapping)

    # Detect communities on consensus graph
    if algorithms is not None:
        try:
            consensus_communities = algorithms.greedy_modularity(G_consensus)
        except:
            from networkx.algorithms import community
            consensus_comms = community.greedy_modularity_communities(G_consensus)

            class ConsensusCommunity:
                def __init__(self, communities):
                    self.communities = [list(c) for c in communities]
                    self.method_name = 'consensus'

            consensus_communities = ConsensusCommunity(consensus_comms)
    else:
        from networkx.algorithms import community
        consensus_comms = community.greedy_modularity_communities(G_consensus)

        class ConsensusCommunity:
            def __init__(self, communities):
                self.communities = [list(c) for c in communities]
                self.method_name = 'consensus'

        consensus_communities = ConsensusCommunity(consensus_comms)

    print(f"Consensus clustering: {len(consensus_communities.communities)} communities")
    return consensus_communities

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

def identify_high_low_risk_communities(community_df, high_threshold=0.3, low_threshold=0.1):
    """Identify high-risk and low-risk communities"""
    print("\n=== HIGH vs LOW RISK COMMUNITIES ===")

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

def visualize_community_analysis(G, community_df, communities):
    """Create comprehensive community analysis visualizations"""
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))

    # Network summary
    axes[0,0].text(0.1, 0.9, "Network & Community Summary", fontsize=12, fontweight='bold')
    axes[0,0].text(0.1, 0.8, f"Total Nodes: {G.number_of_nodes()}")
    axes[0,0].text(0.1, 0.7, f"Total Edges: {G.number_of_edges()}")
    axes[0,0].text(0.1, 0.6, f"Communities: {len(community_df)}")
    axes[0,0].text(0.1, 0.5, f"Patients: {len([n for n in G.nodes() if G.nodes[n]['node_type'] == 'patient'])}")
    axes[0,0].text(0.1, 0.4, f"Sites: {len([n for n in G.nodes() if G.nodes[n]['node_type'] == 'site'])}")
    axes[0,0].set_xlim(0, 1)
    axes[0,0].set_ylim(0, 1)
    axes[0,0].axis('off')

    # Community size distribution
    axes[0,1].hist(community_df['patients_count'], bins=15, alpha=0.7, color='skyblue', edgecolor='black')
    axes[0,1].set_xlabel('Patients per Community')
    axes[0,1].set_ylabel('Number of Communities')
    axes[0,1].set_title('Community Size Distribution')

    # Community risk scores
    axes[0,2].hist(community_df['risk_score'], bins=15, alpha=0.7, color='red', edgecolor='black')
    axes[0,2].set_xlabel('Community Risk Score')
    axes[0,2].set_ylabel('Number of Communities')
    axes[0,2].set_title('Community Risk Distribution')

    # DNA rate vs community size
    axes[1,0].scatter(community_df['patients_count'], community_df['avg_dna_rate'],
                     c=community_df['risk_score'], cmap='Reds', alpha=0.7, s=60)
    axes[1,0].set_xlabel('Community Size (Patients)')
    axes[1,0].set_ylabel('Average DNA Rate')
    axes[1,0].set_title('Community Size vs DNA Rate')
    cbar = plt.colorbar(axes[1,0].collections[0], ax=axes[1,0])
    cbar.set_label('Risk Score')

    # Age group distribution across communities
    age_groups = community_df['dominant_age_group'].value_counts()
    axes[1,1].pie(age_groups.values, labels=age_groups.index, autopct='%1.1f%%', startangle=90)
    axes[1,1].set_title('Dominant Age Groups in Communities')

    # Risk category summary
    risk_data = {
        'High Risk': community_df['high_risk_patients'].sum(),
        'Medium Risk': community_df['medium_risk_patients'].sum(),
        'Low Risk': community_df['low_risk_patients'].sum()
    }
    axes[1,2].bar(risk_data.keys(), risk_data.values(), color=['red', 'orange', 'green'], alpha=0.7)
    axes[1,2].set_ylabel('Number of Patients')
    axes[1,2].set_title('Patients by Risk Category')
    axes[1,2].tick_params(axis='x', rotation=45)

    plt.tight_layout()

    # Save the plot
    plt.savefig('network_analysis/plots/community_analysis.png', dpi=300, bbox_inches='tight')
    print("Community analysis plot saved to: network_analysis/plots/community_analysis.png")
    plt.show()

def draw_community_network(G, communities, max_communities=5):
    """Draw network with community coloring"""
    print(f"\nVisualizing top {max_communities} communities...")

    plt.figure(figsize=(12, 8))

    # Create color map for communities
    colors = plt.cm.Set3(np.linspace(0, 1, min(len(communities.communities), max_communities)))

    # Position nodes
    pos = nx.spring_layout(G, k=0.5, iterations=50)

    # Draw communities with different colors
    for i, community in enumerate(communities.communities[:max_communities]):
        # Separate patients and sites
        patients = [n for n in community if G.nodes[n]['node_type'] == 'patient']
        sites = [n for n in community if G.nodes[n]['node_type'] == 'site']

        # Draw patient nodes
        if patients:
            nx.draw_networkx_nodes(G, pos, nodelist=patients,
                                 node_color=[colors[i]], node_size=30,
                                 node_shape='o', alpha=0.7)

        # Draw site nodes
        if sites:
            nx.draw_networkx_nodes(G, pos, nodelist=sites,
                                 node_color=[colors[i]], node_size=100,
                                 node_shape='s', alpha=0.9)

    # Draw edges
    nx.draw_networkx_edges(G, pos, alpha=0.2, width=0.5, edge_color='gray')

    plt.title(f'Network Communities (Top {max_communities})')
    plt.axis('off')

    # Create legend
    legend_elements = []
    for i in range(min(len(communities.communities), max_communities)):
        legend_elements.append(plt.Line2D([0], [0], marker='o', color='w',
                                        markerfacecolor=colors[i], markersize=8,
                                        label=f'Community {i+1}'))

    plt.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(1.15, 1))
    plt.tight_layout()

    # Save the plot
    plt.savefig('network_analysis/plots/network_communities.png', dpi=300, bbox_inches='tight')
    print("Network communities plot saved to: network_analysis/plots/network_communities.png")
    plt.show()

# ======================== MAIN EXECUTION ========================

if __name__ == "__main__":
    # Sample data for manageable analysis on M4 MacBook Pro
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

    # Create backbone (optional - for reducing complexity)
    print("\nCreating network backbone...")
    G_backbone = create_backbone(G, alpha=0.05)
    print(f"Backbone has {G_backbone.number_of_edges()} edges (reduced from {G.number_of_edges()})")

    # Community Detection Analysis
    print("\n" + "="*50)
    print("COMMUNITY DETECTION & DNA ANALYSIS")
    print("="*50)

    # Detect communities using multiple algorithms with comparison stats
    consensus_communities = detect_communities_with_stats(G, min_community_size=10)

    # Analyze communities for DNA patterns
    community_df = analyze_community_dna_patterns(G, consensus_communities, network_data)

    # Identify high vs low risk communities
    risk_communities = identify_high_low_risk_communities(community_df)

    # Generate actionable insights
    insights = generate_community_insights(community_df, risk_communities)

    # Visualize results
    print("\nCreating community visualizations...")
    visualize_community_analysis(G, community_df, consensus_communities)

    # Draw community network (for smaller samples)
    if len(G.nodes()) < 1000:
        draw_community_network(G, consensus_communities)

    print("\n" + "="*50)
    print("COMMUNITY-BASED DNA ANALYSIS COMPLETE")
    print("="*50)
    print("\nKey Findings:")
    print(f"• Identified {len(community_df)} distinct patient-site communities")
    print(f"• {len(risk_communities['high_risk'])} high-risk communities requiring urgent intervention")
    print(f"• {len(risk_communities['low_risk'])} low-risk communities with good attendance patterns")

    print("\nNext Steps:")
    print("1. Deploy targeted interventions for high-risk communities")
    print("2. Analyze temporal evolution of community risk")
    print("3. Implement community-specific booking strategies")
    print("4. Monitor community risk scores over time")
    print("5. Scale successful low-risk community practices")
