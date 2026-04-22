from dataclasses import dataclass, field
from typing import List, NamedTuple, Optional


def _fuzzy_score(query: str, target: str) -> Optional[int]:
    """Return a match score (higher = better) or None if query doesn't match target.

    Subsequence match: every character of query must appear in order in target.
    Bonus for consecutive runs of matching characters.
    Both query and target should be pre-lowercased by the caller.
    """
    if not query:
        return 0
    qi = 0
    score = 0
    consecutive = 0
    for ch in target:
        if ch == query[qi]:
            consecutive += 1
            score += consecutive
            qi += 1
            if qi == len(query):
                return score * 1000 - len(target)
        else:
            consecutive = 0
    return None


class Link(NamedTuple):
    parent_id: str
    child_id: str


@dataclass
class Event:
    type: str
    date: str = None   # ISO date string (machine-readable, resolved at save time)
    when: str = None   # raw user input e.g. "tomorrow", "april 2027" (display only)
    text: str = None
    extra: dict = field(default_factory=dict)  # catches unknown keys (from, to, etc.)


@dataclass
class Node:
    node_id: str
    description: str = None
    type: str = None
    status: str = None
    note: str = None
    filepath: str = None
    timeline: list = field(default_factory=list)  # list[Event]


class NodeGraph:
    def __init__(self):
        self.nodes: dict[str, Node] = {}
        self.links: set[Link] = set()
        # Tracks child insertion order per parent: parent_id → [child_id, ...]
        self._child_order: dict[str, list[str]] = {}

    def get_node(self, node_id: str) -> Node:
        return self.nodes[node_id]

    def get_parent_ids(self, node_id: str) -> List[str]:
        """Return the IDs of all direct parents of node_id."""
        return [lnk.parent_id for lnk in self.links if lnk.child_id == node_id]

    def get_children_ids(self, node_id: str) -> List[str]:
        """Return the IDs of all direct children of node_id, in insertion order."""
        return self._child_order.get(node_id, [])

    def add_node(self, node: "Node") -> None:
        self.nodes[node.node_id] = node

    def link_child(self, parent_id: str, child_id: str, position: int) -> None:
        self.links.add(Link(parent_id, child_id))
        order = self._child_order.setdefault(parent_id, [])
        if child_id not in order:
            order.insert(position, child_id)

    def reorder_child(self, parent_id: str, child_id: str, delta: int) -> None:
        """Move child_id up (delta=-1) or down (delta=+1) among its siblings."""
        order = self._child_order.get(parent_id)
        if not order or child_id not in order:
            return
        i = order.index(child_id)
        j = i + delta
        if 0 <= j < len(order):
            order[i], order[j] = order[j], order[i]

    def unlink_child(self, parent_id: str, child_id: str) -> None:
        self.links.discard(Link(parent_id, child_id))
        if parent_id in self._child_order:
            self._child_order[parent_id] = [
                c for c in self._child_order[parent_id] if c != child_id
            ]

    def remove_node(self, node_id: str) -> None:
        if node_id not in self.nodes:
            return
        self.links = {lnk for lnk in self.links if lnk.parent_id != node_id and lnk.child_id != node_id}
        for order in self._child_order.values():
            if node_id in order:
                order.remove(node_id)
        self._child_order.pop(node_id, None)
        del self.nodes[node_id]

    def get_roots(self) -> List[str]:
        children = {lnk.child_id for lnk in self.links}
        return [nid for nid in self.nodes if nid not in children]

    def _dfs_tree(self, node_id: str, neighbors_fn, max_depth: int) -> List[tuple["Node", int]]:
        result, visited = [], {node_id}
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

    def search_nodes(self, query: str) -> List["Node"]:
        """Return nodes whose description matches query, ranked by fuzzy score.

        Uses subsequence matching with consecutive-run bonus (no external deps).
        Nodes with no description are excluded.
        """
        q = query.lower()
        scored: list[tuple[int, Node]] = []
        for node in self.nodes.values():
            desc = node.description or ""
            score = _fuzzy_score(q, desc.lower())
            if score is not None:
                scored.append((score, node))
        scored.sort(reverse=True, key=lambda x: x[0])
        return [node for _, node in scored]

    def get_parents_tree(self, node_id: str, max_depth: int = 2) -> List[tuple["Node", int]]:
        return self._dfs_tree(node_id, self.get_parent_ids, max_depth)

    def get_childrens_tree(self, node_id: str, max_depth: int = 2) -> List[tuple["Node", int]]:
        return self._dfs_tree(node_id, self.get_children_ids, max_depth)

    def nodes_unanchored_after_removal(self, node_ids: set) -> set:
        """Return nodes that would lose all paths to any root if node_ids were removed."""
        remaining = set(self.nodes.keys()) - node_ids
        # Seed BFS from nodes that are roots in the original graph and survive removal
        reachable: set[str] = set()
        queue = [nid for nid in remaining if not self.get_parent_ids(nid)]
        while queue:
            nid = queue.pop()
            if nid in reachable:
                continue
            reachable.add(nid)
            queue.extend(
                lnk.child_id for lnk in self.links
                if lnk.parent_id == nid and lnk.child_id in remaining
            )
        return remaining - reachable

    def deletion_set(self, node_id: str, mode: str) -> set:
        """Compute the set of node_ids to delete for a given mode.

        mode "node" : only the node itself
        mode "soft" : node + whatever becomes unanchored after its removal
        mode "hard" : node + all descendants (full DFS, ignoring other parents)
        """
        if mode == "node":
            return {node_id}
        if mode == "soft":
            initial = {node_id}
            # iterate: newly unanchored nodes may themselves unanchor more
            to_delete = initial
            while True:
                unanchored = self.nodes_unanchored_after_removal(to_delete)
                new_set = to_delete | unanchored
                if new_set == to_delete:
                    break
                to_delete = new_set
            return to_delete
        if mode == "hard":
            result = {node_id}
            stack = list(self.get_children_ids(node_id))
            while stack:
                nid = stack.pop()
                if nid in result:
                    continue
                result.add(nid)
                stack.extend(self.get_children_ids(nid))
            return result
        raise ValueError(f"Unknown mode: {mode}")
