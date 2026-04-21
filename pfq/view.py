"""View model — pure data layer between the graph and the renderer.

build_node_view() and build_home_view() translate a NodeGraph into a flat
list of ViewRow objects. Each row carries everything the renderer needs
(bullet, is_leaf, is_root, also_labels) so that render.py has zero graph
dependency.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional

from pfq.model import Node, NodeGraph

NodeRole = Literal["parent", "selected", "child", "home_root", "sentinel"]


@dataclass
class ViewRow:
    role: NodeRole
    depth: int
    node: Optional[Node] = None         # None only for sentinel rows
    is_leaf: bool = False
    is_root: bool = False
    bullet: str = ""                    # "@", "○", "<", or ""
    boundary: bool = False              # last item in its peer group
    index: int = 0                      # position within peer group (for connector)
    items: list = field(default_factory=list)   # [(Node, int)] peer group
    visible_parent_id: Optional[str] = None
    also_labels: list[str] = field(default_factory=list)  # other-parent descriptions


# ── Internal helpers ───────────────────────────────────────────────────────────


def _bullet(is_root: bool, is_leaf: bool, depth: int) -> str:
    if is_root:
        return "@"
    if depth <= 1:
        return ""
    return "○" if is_leaf else "<"


def _make_row(
    graph: NodeGraph,
    node: Node,
    role: NodeRole,
    depth: int,
    *,
    boundary: bool = False,
    index: int = 0,
    items: list = (),
    visible_parent_id: Optional[str] = None,
) -> ViewRow:
    is_root = len(graph.get_parent_ids(node.node_id)) == 0
    is_leaf = len(graph.get_children_ids(node.node_id)) == 0
    also_labels: list[str] = []
    if visible_parent_id is not None:
        others = [p for p in graph.get_parent_ids(node.node_id) if p != visible_parent_id]
        also_labels = [graph.get_node(p).description or p for p in others]
    return ViewRow(
        role=role, depth=depth, node=node,
        is_leaf=is_leaf, is_root=is_root,
        bullet=_bullet(is_root, is_leaf, depth),
        boundary=boundary, index=index, items=list(items),
        visible_parent_id=visible_parent_id, also_labels=also_labels,
    )


# ── Public builders ────────────────────────────────────────────────────────────


def build_node_view(graph: NodeGraph, node_id: str) -> list[ViewRow]:
    """Build the node-view row list: sentinel / parents / selected / children."""
    rows: list[ViewRow] = []

    rows.append(ViewRow(role="sentinel", depth=0))

    parents = list(reversed(graph.get_parents_tree(node_id)))
    for i, (node, depth) in enumerate(parents):
        rows.append(_make_row(graph, node, "parent", depth,
                              boundary=(i == 0), index=i, items=parents))

    rows.append(_make_row(graph, graph.get_node(node_id), "selected", 0))

    children = graph.get_childrens_tree(node_id)
    seen = {node_id} | {n.node_id for n, _ in parents}
    filtered = [(n, d) for n, d in children if n.node_id not in seen]
    prev_by_depth: dict[int, str] = {0: node_id}
    for i, (node, depth) in enumerate(filtered):
        visible_parent_id = prev_by_depth.get(depth - 1)
        prev_by_depth[depth] = node.node_id
        rows.append(_make_row(
            graph, node, "child", depth,
            boundary=(i == len(filtered) - 1),
            index=i, items=filtered,
            visible_parent_id=visible_parent_id,
        ))

    return rows


def build_home_view(graph: NodeGraph) -> list[ViewRow]:
    """Build the home-view row list: roots with their depth-1 children."""
    rows: list[ViewRow] = []
    seen: set[str] = set()

    for root_id in sorted(graph.get_roots()):
        root = graph.get_node(root_id)
        rows.append(_make_row(graph, root, "home_root", 0))
        seen.add(root_id)

        children = graph.get_childrens_tree(root_id, max_depth=1)
        children = [(n, d) for n, d in children if n.node_id not in seen]
        for i, (node, depth) in enumerate(children):
            rows.append(_make_row(
                graph, node, "child", depth,
                boundary=(i == len(children) - 1),
                index=i, items=children,
            ))
            seen.add(node.node_id)

    return rows
