"""Check a vault for cycles using DFS with a recursion stack (white/gray/black coloring)."""

import sys
from pathlib import Path

from pfq.disk_io import load_vault


def find_cycles(graph):
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {nid: WHITE for nid in graph.nodes}
    cycles = []

    def dfs(nid, path):
        color[nid] = GRAY
        path.append(nid)
        for child_id in graph.get_children_ids(nid):
            if child_id not in color:
                continue
            if color[child_id] == GRAY:
                cycle_start = path.index(child_id)
                cycles.append(path[cycle_start:] + [child_id])
            elif color[child_id] == WHITE:
                dfs(child_id, path)
        path.pop()
        color[nid] = BLACK

    for nid in graph.nodes:
        if color[nid] == WHITE:
            dfs(nid, [])

    return cycles


def node_label(graph, nid):
    node = graph.nodes.get(nid)
    desc = node.description or "" if node else ""
    return f"{nid} ({desc})" if desc else nid


def main():
    vault_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data")
    if not vault_path.exists():
        print(f"Vault not found: {vault_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Loading vault: {vault_path}")
    graph = load_vault(vault_path)
    print(f"  {len(graph.nodes)} nodes, {len(graph.links)} links")

    cycles = find_cycles(graph)

    if not cycles:
        print("No cycles found.")
    else:
        print(f"\n{len(cycles)} cycle(s) found:\n")
        for i, cycle in enumerate(cycles, 1):
            chain = " -> ".join(node_label(graph, nid) for nid in cycle)
            print(f"  Cycle {i}: {chain}")
        sys.exit(1)


if __name__ == "__main__":
    main()
