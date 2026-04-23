"""Rendering layer — converts ViewRow lists into Rich Text or DataTable rows.

No NodeGraph dependency: all graph-derived data (bullet, is_leaf, is_root,
also_labels) is precomputed in view.py.
"""
from __future__ import annotations

from rich.text import Text
from textual.widgets import DataTable

from pfq.config import INFERRED_STATE_STYLES, STATUS_GLYPHS
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


def _state_rich(state: str, depth: int) -> Text:
    """State cell: glyph + color, no text label."""
    if not state:
        return Text()
    glyph = STATUS_GLYPHS.get(state, "?")
    color = INFERRED_STATE_STYLES.get(state)
    if depth == 0:
        style = f"bold {color}" if color else "bold"
    elif depth == 2:
        style = f"dim {color}" if color else "dim"
    else:
        style = color or ""
    return Text(f"{glyph} {state}", style=style)


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
    """Description cell: connector prefix (if any) + bullet + description text.

    Selected row gets a left-gutter '▶ '; all other rows are padded by 2 spaces
    so tree connectors stay aligned.
    """
    raw = node.description or ""
    if role == "selected":
        t = Text()
        t.append("▶ ", style="bold")
        t.append((bullet + " " if bullet else "") + raw, style="bold")
        return t
    if role == "home_root":
        t = Text()
        t.append("  ")
        t.append(bullet + (" " if bullet else "") + raw, style="bold")
        return t

    t = Text()
    t.append("  ")
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
            table.add_row(Text(), Text("  ─ root", style="dim"), Text(), key="__home__")
            continue
        node = row.node
        when_text = Text(row.when_label, style="dim cyan") if row.when_label else Text()
        table.add_row(
            _state_rich(row.status_label, row.depth),
            _desc_cell(row.role, row.depth, node, row.bullet,
                       index=row.index, items=row.items),
            when_text,
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
        state_suffix = ("  (" + row.status_label + ")") if row.status_label else ""
        if row.role == "home_root":
            b = row.bullet
            lines.append(b + (" " if b else "") + (node.description or "") + state_suffix)
        elif row.role == "selected":
            b = row.bullet
            lines.append("▶ " + (b + " " if b else "") + (node.description or "") + state_suffix)
        else:  # "parent" or "child"
            segs = _tree_prefix_segments(
                row.depth, row.index, row.items,
                reverse=(row.role == "parent"), bullet=row.bullet,
            )
            prefix = "".join(s for s, _ in segs)
            lines.append(prefix + (" " if row.bullet else "") + (node.description or "") + state_suffix)
    return "\n".join(lines)
