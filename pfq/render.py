"""Rendering layer — converts ViewRow lists into Rich Text or DataTable rows.

No NodeGraph dependency: all graph-derived data (bullet, is_leaf, is_root,
also_labels) is precomputed in view.py.
"""
from __future__ import annotations

from rich.text import Text
from textual.widgets import DataTable

from pfq.config import LEAF_STATUSES, NODE_STATUSES, STATUS_GLYPHS, STATUS_MISMATCH_BG, STATUS_STYLES
from pfq.view import NodeRole, ViewRow

PALETTE = {
    "row_bg":  "#1c2d40",   # selected row  — reserved, not yet applied
    "cell_bg": "#2e2600",   # cursor cell   — dark yellow
    "cell_fg": "#f0ead0",   # cursor cell text — warm white
}


# ── Rich text helpers ──────────────────────────────────────────────────────────


def _rich(text: str, depth: int) -> Text:
    """Plain string → Rich Text: depth 0 → bold, depth 2 → dim, else plain."""
    t = Text(text)
    if depth == 0:
        t.stylize("bold")
    elif depth == 2:
        t.stylize("dim")
    return t


def _status_rich(
    status: str, depth: int, *, is_leaf: bool = False, is_root: bool = False, indent: int = 0
) -> Text:
    """Status cell: colored, glyphed, with mismatch background when role/status disagree."""
    prefix = "  " * indent
    if not status:
        return Text(prefix)
    s = status.lower()
    color = STATUS_STYLES.get(s)
    mismatch = (
        (is_leaf and s in NODE_STATUSES) or
        ((is_root or not is_leaf) and s in LEAF_STATUSES)
    )
    glyph = STATUS_GLYPHS.get(s, "·" if indent else "")
    glyph_str = (glyph + " ") if glyph else ""
    bg = f" on {STATUS_MISMATCH_BG}" if mismatch else ""
    if depth == 0:
        style      = f"bold {color}{bg}" if color else f"bold{bg}"
        glyph_style = f"bold {color}"    if color else "bold"
    elif depth == 2:
        style      = f"dim {color}{bg}"  if color else f"dim{bg}"
        glyph_style = f"dim {color}"     if color else "dim"
    else:
        style      = f"{color}{bg}"      if color else bg
        glyph_style = color or ""
    if mismatch and not color:
        style = f"on {STATUS_MISMATCH_BG}"
    t = Text()
    t.append(glyph_str, style=glyph_style or None)
    t.append(status, style=style or None)
    return t


def _tree_prefix_segments(
    depth: int, index: int, items: list, *, reverse: bool = False, bullet: str = ""
) -> list[tuple[str, int]]:
    """Compute the tree connector prefix as (text, level) segments.

    Each segment's level is used by the caller to apply depth-based styling.
    reverse=True is used for parent rows (tree grows upward).
    bullet replaces the trailing space of the terminal connector.
    """
    depths = [d for (_, d) in items]
    scan = range(index - 1, -1, -1) if reverse else range(index + 1, len(items))

    def has_sibling_at(lvl: int) -> bool:
        for j in scan:
            if depths[j] < lvl:
                return False
            if depths[j] == lvl:
                return True
        return False

    end = bullet if bullet else " "
    segments: list[tuple[str, int]] = []
    for lvl in range(1, depth):
        segments.append(("│   " if has_sibling_at(lvl) else "    ", lvl))
    if reverse:
        segments.append(("├──" + end if has_sibling_at(depth) else "╭──" + end, depth))
    else:
        segments.append(("├──" + end if has_sibling_at(depth) else "╰──" + end, depth))
    return segments


def _desc_cell(
    role: NodeRole, depth: int, node, bullet: str, *, index: int = 0, items: list = ()
) -> Text:
    """Description cell: connector prefix (if any) + bullet + description text."""
    raw = node.description or ""
    if role in ("selected", "home_root"):
        return _rich(bullet + (" " if bullet else "") + raw, depth)

    t = Text()
    for seg, lvl in _tree_prefix_segments(depth, index, list(items), reverse=(role == "parent"), bullet=bullet):
        t.append(seg, style="dim" if lvl >= 2 else "")
    desc_style = "bold" if depth == 0 else ("dim" if depth >= 2 else "")
    t.append((" " if bullet else "") + raw, style=desc_style)
    return t


# ── Renderers ──────────────────────────────────────────────────────────────────


def render_to_table(rows: list[ViewRow], table: DataTable) -> None:
    """Populate a DataTable from a ViewRow list. Clears the table first."""
    table.clear()
    for row in rows:
        if row.role == "sentinel":
            table.add_row("", "─", Text("root", style="dim"), Text(), Text(), Text(), key="__home__")
            continue
        node = row.node
        also_text = (
            Text("← " + ", ".join(row.also_labels), style="dim cyan")
            if row.also_labels else Text()
        )
        margin = "▶" if row.role == "selected" else ("" if row.role == "home_root" else " ")
        last_ev = Text(row.last_event, style="dim") if row.last_event else Text()
        next_ev = Text(row.next_event, style="dim cyan") if row.next_event else Text()
        table.add_row(
            _status_rich(node.status or "", row.depth,
                         is_leaf=row.is_leaf, is_root=row.is_root, indent=row.depth),
            margin,
            _desc_cell(row.role, row.depth, node, row.bullet,
                       index=row.index, items=row.items),
            also_text,
            last_ev,
            next_ev,
            key=node.node_id,
        )


def render_to_text(rows: list[ViewRow]) -> str:
    """Serialize a ViewRow list to a plain-text tree representation (for yank)."""
    lines = []
    for row in rows:
        if row.role == "sentinel":
            lines.append("─ root")
            continue
        node = row.node
        status_suffix = ("  (" + node.status + ")") if node.status else ""
        if row.role == "home_root":
            b = row.bullet
            lines.append(b + (" " if b else "") + (node.description or "") + status_suffix)
        elif row.role == "selected":
            b = row.bullet
            lines.append("▶ " + (b + " " if b else "") + (node.description or "") + status_suffix)
        else:  # "parent" or "child"
            segs = _tree_prefix_segments(
                row.depth, row.index, row.items,
                reverse=(row.role == "parent"), bullet=row.bullet,
            )
            prefix = "".join(s for s, _ in segs)
            lines.append(prefix + (" " if row.bullet else "") + (node.description or "") + status_suffix)
    return "\n".join(lines)
