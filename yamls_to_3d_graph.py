#!/usr/bin/env python3
"""Convert pfq vault data to graph formats (JSON and Graphviz dot)."""

import json
from pathlib import Path
from pfq.disk_io import load_vault

# Configuration
NODE_SIZE = 5
NODE_COLOR = "#1f77b4"  # Default blue color


def vault_to_3d_graph_json(vault_path: Path = Path("data")) -> dict:
    """Load vault and convert to 3D graph JSON format."""
    graph = load_vault(vault_path)

    # Create nodes list with consistent size and color
    nodes = []
    for node_id in sorted(graph.nodes.keys()):
        node = graph.nodes[node_id]
        nodes.append({
            "id": node_id,
            "label": node.description or node_id,
            "group": 1  # All nodes in same group for now
        })

    # Create links list from the graph
    links = []
    for link in graph.links:
        links.append({
            "source": link.parent_id,
            "target": link.child_id,
            "value": 1  # All connections have same weight
        })

    return {
        "nodes": nodes,
        "links": links
    }


def vault_to_dot(vault_path: Path = Path("data")) -> str:
    """Load vault and convert to Graphviz dot format."""
    graph = load_vault(vault_path)

    lines = ["digraph vault {"]
    lines.append('  rankdir=LR;')
    lines.append('  node [shape=box];')

    # Add nodes with descriptions as labels
    for node_id in sorted(graph.nodes.keys()):
        node = graph.nodes[node_id]
        label = node.description or node_id
        lines.append(f'  "{node_id}" [label="{label}"];')

    lines.append("")

    # Add edges
    for link in graph.links:
        lines.append(f'  "{link.parent_id}" -> "{link.child_id}";')

    lines.append("}")

    return "\n".join(lines)


if __name__ == "__main__":
    # Load and convert
    data = vault_to_3d_graph_json()

    # Write JSON output
    json_output = Path("vault_graph.json")
    json_output.write_text(json.dumps(data, indent=2))
    print(f"✓ Converted vault to {json_output}")
    print(f"  Nodes: {len(data['nodes'])}")
    print(f"  Links: {len(data['links'])}")

    # Write dot output
    dot_content = vault_to_dot()
    dot_output = Path("vault_graph.dot")
    dot_output.write_text(dot_content)
    print(f"✓ Converted vault to {dot_output}")

    # Count dot elements
    node_count = len([l for l in dot_content.split("\n") if '[label=' in l])
    edge_count = len([l for l in dot_content.split("\n") if '->' in l])
    print(f"  Nodes: {node_count}")
    print(f"  Edges: {edge_count}")
