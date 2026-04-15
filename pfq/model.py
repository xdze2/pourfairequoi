from dataclasses import dataclass, field
from pathlib import Path
from typing import List

import yaml


@dataclass
class Node:
    node_id: str
    description: str = None
    type: str = None
    status: str = None
    how: List[str] = field(default_factory=list)


class NodeGraph:
    def __init__(self):
        self.nodes: dict[str, Node] = {}
        self._parents: dict[str, List[str]] = {}  # node_id → list of parent node_ids

    @classmethod
    def load_from_disk(cls, vault_path: Path) -> "NodeGraph":
        graph = cls()
        for path in sorted(vault_path.glob("*.yaml")):
            node_id = path.stem
            raw = yaml.safe_load(path.read_text()) or {}
            how = [
                entry["target_node"]
                for entry in (raw.get("how") or [])
                if isinstance(entry, dict) and "target_node" in entry
            ]
            graph.nodes[node_id] = Node(
                node_id=node_id,
                description=raw.get("description"),
                type=raw.get("type"),
                status=raw.get("status"),
                how=how,
            )

        # Build reverse index
        graph._parents = {node_id: [] for node_id in graph.nodes}
        for node in graph.nodes.values():
            for child_id in node.how:
                if child_id in graph._parents:
                    graph._parents[child_id].append(node.node_id)

        return graph

    def get_node(self, node_id: str) -> Node:
        return self.nodes[node_id]

    def get_node_parents(self, node_id: str) -> List[str]:
        return self._parents.get(node_id, [])

    def get_node_childrens(self, node_id: str) -> List[str]:
        return self.nodes[node_id].how if node_id in self.nodes else []

    def get_roots(self) -> List[str]:
        return [nid for nid, parents in self._parents.items() if not parents]

    def _bfs_tree(self, node_id: str, neighbors_fn, max_depth: int) -> List[tuple["Node", int]]:
        """Generic BFS traversal. neighbors_fn(node_id) -> List[str]."""
        result, visited = [], {node_id}
        queue = [(nid, 1) for nid in neighbors_fn(node_id)]
        while queue:
            current_id, depth = queue.pop(0)
            if current_id in visited or current_id not in self.nodes:
                continue
            visited.add(current_id)
            result.append((self.nodes[current_id], depth))
            if depth < max_depth:
                queue += [(nid, depth + 1) for nid in neighbors_fn(current_id) if nid not in visited]
        return result

    def get_parents_tree(self, node_id: str, max_depth: int = 2) -> List[tuple["Node", int]]:
        """BFS upward. Returns [(node, depth), ...] closest-first, current node excluded.
        Depth 1 = immediate parent. Diamond DAGs: node appears at shallowest depth."""
        return self._bfs_tree(node_id, self.get_node_parents, max_depth)

    def get_childrens_tree(self, node_id: str, max_depth: int = 2) -> List[tuple["Node", int]]:
        """BFS downward. Returns [(node, depth), ...] closest-first, current node excluded.
        Depth 1 = immediate child. Dangling references silently skipped."""
        return self._bfs_tree(node_id, self.get_node_childrens, max_depth)
