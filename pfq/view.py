"""View model — pure data layer between the graph and the renderer.

build_node_view() and build_home_view() translate a NodeGraph into a flat
list of ViewRow objects. Each row carries everything the renderer needs
(bullet, is_leaf, is_root, also_labels) so that render.py has zero graph
dependency.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Literal, Optional

from pfq.dates import format_date
from pfq.model import Node, NodeGraph

NodeRole = Literal["parent", "selected", "child", "home_root", "sentinel"]


def _parse_iso(s: str) -> Optional[date]:
    try:
        return date.fromisoformat(s)
    except (ValueError, TypeError):
        return None


def _duration_label(days: int) -> str:
    if days < 1:
        return "today"
    if days < 7:
        return f"{days}d"
    if days < 30:
        return f"{days // 7}w"
    if days < 365:
        return f"{days // 30}mo"
    return f"{days // 365}y"


def _due_label(node: Node, today: date) -> str:
    """target column: closed_at + duration (+ late suffix) for closed; estimated_closing_date for open."""
    if node.is_closed:
        closed = _parse_iso(node.closed_at)
        if closed is None:
            return ""
        parts = [format_date(closed, today)]
        opened = _parse_iso(node.opened_at)
        if opened is not None:
            days = (closed - opened).days
            if days < 1:
                duration = "same day"
            elif days < 7:
                duration = f"{days}d"
            elif days < 28:
                duration = f"{days // 7}w"
            elif days < 365:
                duration = f"{days // 30}mo"
            else:
                duration = f"{days // 365}y"
            parts.append(f"({duration})")
        if node.estimated_closing_date:
            planned = _parse_iso(node.estimated_closing_date)
            if planned is not None and closed > planned:
                parts.append(f"· was {format_date(planned, today)}")
        return "  ".join(parts)

    if node.estimated_closing_date:
        d = _parse_iso(node.estimated_closing_date)
        if d is not None:
            delta = (d - today).days
            if delta < 14:
                glyph = "→"
            elif delta < 60:
                glyph = "⇒"
            elif delta < 365:
                glyph = "☽"
            else:
                glyph = "☀"
            return f"{glyph} {format_date(d, today)}"
    return ""


def _pulse_label(node: Node, today: date) -> str:
    """pulse column: !!! overdue / ! forgotten / ↻ active — empty otherwise."""
    from datetime import timedelta
    if node.is_closed:
        return ""
    if node._is_overdue:
        d = _parse_iso(node.estimated_closing_date)
        days = (today - d).days
        return f"!!! {_duration_label(days)}"
    if node._is_active is False:
        days = (today - node._last_update).days
        return f"  ! {_duration_label(days)}"
    if node._is_active is True:
        next_check = node._last_update + timedelta(days=node.update_period)
        return f"  ↻ {format_date(next_check, today)}"
    # _is_active is None but tracking is configured: first period, no alarm yet
    if node._last_update is not None:
        next_check = node._last_update + timedelta(days=node.update_period)
        return f"  ↻ {format_date(next_check, today)}"
    return ""


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
    when_label: str = ""   # target close date (or closed_at + duration + late suffix)
    pulse_label: str = ""  # !!! overdue / ! forgotten / ↻ active


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
    today: date,
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
        when_label=_due_label(node, today),
        pulse_label=_pulse_label(node, today),
    )


# ── Public builders ────────────────────────────────────────────────────────────


def build_node_view(graph: NodeGraph, node_id: str, today: date = None) -> list[ViewRow]:
    """Build the node-view row list: sentinel / parents / selected / children."""
    if today is None:
        today = date.today()
    rows: list[ViewRow] = []

    rows.append(ViewRow(role="sentinel", depth=0))

    parents = list(reversed(graph.get_parents_tree(node_id)))
    for i, (node, depth) in enumerate(parents):
        rows.append(_make_row(graph, node, "parent", depth,
                              today=today, boundary=(i == 0), index=i, items=parents))

    rows.append(_make_row(graph, graph.get_node(node_id), "selected", 0, today=today))

    children = graph.get_childrens_tree(node_id)
    seen = {node_id} | {n.node_id for n, _ in parents}
    filtered = [(n, d) for n, d in children if n.node_id not in seen]
    prev_by_depth: dict[int, str] = {0: node_id}
    for i, (node, depth) in enumerate(filtered):
        visible_parent_id = prev_by_depth.get(depth - 1)
        prev_by_depth[depth] = node.node_id
        rows.append(_make_row(
            graph, node, "child", depth,
            today=today,
            boundary=(i == len(filtered) - 1),
            index=i, items=filtered,
            visible_parent_id=visible_parent_id,
        ))

    return rows


def build_home_view(graph: NodeGraph, today: date = None) -> list[ViewRow]:
    """Build the home-view row list: roots with their depth-1 children."""
    if today is None:
        today = date.today()
    rows: list[ViewRow] = []
    seen: set[str] = set()

    roots = sorted(
        graph.get_roots(),
        key=lambda rid: len(graph.get_childrens_tree(rid, max_depth=None)),
        reverse=True,
    )
    for root_id in roots:
        root = graph.get_node(root_id)
        rows.append(_make_row(graph, root, "home_root", 0, today=today))
        seen.add(root_id)

        children = graph.get_childrens_tree(root_id, max_depth=1)
        children = [(n, d) for n, d in children if n.node_id not in seen]
        for i, (node, depth) in enumerate(children):
            rows.append(_make_row(
                graph, node, "child", depth,
                today=today,
                boundary=(i == len(children) - 1),
                index=i, items=children,
                visible_parent_id=root_id,
            ))
            seen.add(node.node_id)

    return rows
