import json
import numpy as np
import pandas as pd
from datetime import datetime

def export_for_d3js(G, communities, community_df, output_path='visualization/data/network-export.json'):
    """
    Convert NetworkX graph and community analysis to D3.js-ready JSON format.

    Args:
        G: NetworkX bipartite graph with patient and site nodes
        communities: Community detection result from Leiden algorithm
        community_df: DataFrame with community analysis results
        output_path: Path to save the JSON file

    Returns:
        dict: D3.js-ready data structure
    """

    # Create node to community mapping
    node_to_community = {}
    for i, community in enumerate(communities.communities):
        for node in community:
            node_to_community[node] = i

    # Calculate risk thresholds from community data
    high_threshold = community_df['risk_score'].quantile(0.75)
    low_threshold = community_df['risk_score'].quantile(0.25)

    # Count communities by risk level
    high_risk_count = len(community_df[community_df['risk_score'] >= high_threshold])
    low_risk_count = len(community_df[community_df['risk_score'] <= low_threshold])

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

        # Add patient-specific attributes
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

        # Add site-specific attributes
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
            "strength": min(edge_data.get('weight', 1) / 10.0, 1.0)  # Normalize for D3 force strength
        }

        # Add optional edge attributes
        if 'treatment_function' in edge_data:
            link['treatment_function'] = edge_data['treatment_function']
        if 'outcome' in edge_data:
            link['outcome'] = edge_data['outcome']

        links.append(link)

    # Convert community data to D3.js format
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
            "high_risk_communities": high_risk_count,
            "medium_risk_communities": len(community_df) - high_risk_count - low_risk_count,
            "low_risk_communities": low_risk_count,
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

    # Ensure output directory exists
    import os
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Save to JSON file
    with open(output_path, 'w') as f:
        json.dump(export_data, f, indent=2, default=str)

    print(f"✅ D3.js data exported to {output_path}")
    print(f"📊 Exported {len(nodes)} nodes, {len(links)} links, {len(communities_data)} communities")

    return export_data

def create_sample_export(sample_size=1000):
    """
    Create a smaller sample export for testing D3.js visualization.
    Useful for development and testing.
    """
    # This function would be called with a subset of the full data
    # for rapid development iteration
    pass
