from dataclasses import dataclass, field
from pathlib import Path
from typing import List

import yaml


def filename_to_node_id(filename: str) -> str:
    return filename.split("_")[0].upper()


@dataclass
class Node:
    node_id: str
    description: str = None
    type: str = None
    status: str = None
    how: List[str] = field(default_factory=list)
    filepath: str = None


class NodeGraph:
    def __init__(self):
        self.nodes: dict[str, Node] = {}
        self._parents: dict[str, List[str]] = {}  # node_id → list of parent node_ids

    @classmethod
    def load_from_disk(cls, vault_path: Path) -> "NodeGraph":
        graph = cls()
        for path in sorted(vault_path.glob("*.yaml")):
            node_id = filename_to_node_id(path.stem)
            raw = yaml.safe_load(path.read_text()) or {}
            how = [
                filename_to_node_id(entry["target_node"])
                for entry in (raw.get("how") or [])
                if isinstance(entry, dict) and "target_node" in entry
            ]
            graph.nodes[node_id] = Node(
                node_id=node_id,
                description=raw.get("description"),
                type=raw.get("type"),
                status=raw.get("status"),
                how=how,
                filepath=str(path),
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

    def add_node(self, node: "Node") -> None:
        """Register a newly created node (no links yet)."""
        self.nodes[node.node_id] = node
        self._parents[node.node_id] = []

    def link_child(self, parent_id: str, child_id: str, position: int) -> None:
        """Insert child_id into parent's how list at position (in-memory)."""
        parent = self.nodes[parent_id]
        parent.how.insert(position, child_id)
        self._parents.setdefault(child_id, [])
        if parent_id not in self._parents[child_id]:
            self._parents[child_id].append(parent_id)

    def unlink_child(self, parent_id: str, child_id: str) -> None:
        """Remove child_id from parent's how list (in-memory)."""
        parent = self.nodes[parent_id]
        parent.how = [c for c in parent.how if c != child_id]
        if child_id in self._parents:
            self._parents[child_id] = [p for p in self._parents[child_id] if p != parent_id]

    def remove_node(self, node_id: str) -> None:
        """Remove node and all links to/from it (in-memory). Orphans children."""
        if node_id not in self.nodes:
            return
        # Remove from all parents' how lists
        for parent_id in list(self._parents.get(node_id, [])):
            self.nodes[parent_id].how = [c for c in self.nodes[parent_id].how if c != node_id]
        # Remove node's children's back-references
        for child_id in self.nodes[node_id].how:
            if child_id in self._parents:
                self._parents[child_id] = [p for p in self._parents[child_id] if p != node_id]
        del self.nodes[node_id]
        del self._parents[node_id]

    def get_roots(self) -> List[str]:
        return [nid for nid, parents in self._parents.items() if not parents]

    def _dfs_tree(
        self, node_id: str, neighbors_fn, max_depth: int
    ) -> List[tuple["Node", int]]:
        """Generic DFS pre-order traversal. neighbors_fn(node_id) -> List[str].
        Each node appears immediately before its subtree (correct for tree views)."""
        result, visited = [], {node_id}
        # Push in reverse so first neighbor is processed first
        stack = [(nid, 1) for nid in reversed(neighbors_fn(node_id))]
        while stack:
            current_id, depth = stack.pop()
            if current_id in visited or current_id not in self.nodes:
                continue
            visited.add(current_id)
            result.append((self.nodes[current_id], depth))
            if depth < max_depth:
                stack += [
                    (nid, depth + 1)
                    for nid in reversed(neighbors_fn(current_id))
                    if nid not in visited
                ]
        return result

    def get_parents_tree(
        self, node_id: str, max_depth: int = 2
    ) -> List[tuple["Node", int]]:
        """DFS upward. Returns [(node, depth), ...] closest-first, current node excluded.
        Depth 1 = immediate parent. Diamond DAGs: node appears at shallowest depth."""
        return self._dfs_tree(node_id, self.get_node_parents, max_depth)

    def get_childrens_tree(
        self, node_id: str, max_depth: int = 2
    ) -> List[tuple["Node", int]]:
        """DFS downward. Returns [(node, depth), ...] pre-order, current node excluded.
        Depth 1 = immediate child. Each child appears immediately after its parent. Dangling references silently skipped."""
        return self._dfs_tree(node_id, self.get_node_childrens, max_depth)
