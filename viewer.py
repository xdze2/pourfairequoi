#!/usr/bin/env python3
"""pfq viewer — read-only two-panel tree navigator (UI/UX mockup)

Navigation:
  ↑/↓     move cursor in left panel
  Enter   select node under cursor → re-center tree around it
  Esc     go back to previous node
  q       quit
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Footer, Header, Label, ListItem, ListView, Static

sys.path.insert(0, str(Path(__file__).parent))
from pfq.config import STATUSES, TYPES
from pfq.model import Store, get_how, get_task_id

VAULT = Path(__file__).parent / "data"
MAX_DEPTH = 3

STATUS_STYLE: dict[str, str] = {k: v[1] for k, v in STATUSES.items()}
TYPE_STYLE: dict[str, str] = {k: v[1] for k, v in TYPES.items()}


# ── Data ──────────────────────────────────────────────────────────────────────


@dataclass
class TreeLine:
    path: Optional[Path]       # None for ellipsis or root-line placeholder
    description: str
    node_type: str
    status: str
    depth: int                 # negative = ancestor level, 0 = current, positive = descendant level
    is_ellipsis: bool = False
    is_root_header: bool = False
    margin: str = ""           # override margin label (e.g. "why", "how")


def _ancestors(store: Store, start: Path, max_depth: int) -> list[TreeLine]:
    """Return ancestor lines ordered root-to-parent (closest last).
    BFS upward, limit depth. Returns reversed so closest is just above current."""
    id_to_path = {get_task_id(p): p for p in store}

    def parents(path: Path) -> list[Path]:
        path_id = get_task_id(path).upper()
        result = []
        for p, data in store.items():
            if p == path:
                continue
            for entry in get_how(data):
                if (entry.get("target_node") or "").upper() == path_id:
                    result.append(p)
                    break
        return result

    visited: dict[Path, int] = {}  # path → depth (1 = direct parent)
    queue: list[tuple[Path, int]] = []
    for p in parents(start):
        if p not in visited:
            visited[p] = 1
            queue.append((p, 1))

    head = 0
    while head < len(queue):
        current, d = queue[head]
        head += 1
        if d < max_depth:
            for p in parents(current):
                if p not in visited:
                    visited[p] = d + 1
                    queue.append((p, d + 1))

    has_deeper = any(v >= max_depth for v in visited.values()) and any(
        len(parents(p)) > 0 for p, v in visited.items() if v == max_depth
    )

    lines: list[TreeLine] = []
    if has_deeper:
        lines.append(TreeLine(None, "…", "", "", -max_depth - 1, is_ellipsis=True))

    by_depth: dict[int, list[Path]] = {}
    for p, d in visited.items():
        by_depth.setdefault(d, []).append(p)

    for d in sorted(by_depth.keys(), reverse=True):
        for p in sorted(by_depth[d], key=lambda x: x.name):
            data = store.get(p) or {}
            lines.append(TreeLine(
                path=p,
                description=str(data.get("description") or get_task_id(p)),
                node_type=str(data.get("type") or ""),
                status=str(data.get("status") or ""),
                depth=-d,
            ))

    return lines


def _descendants(store: Store, start: Path, max_depth: int) -> list[TreeLine]:
    """Return descendant lines in BFS order (closest first)."""
    id_to_path = {get_task_id(p): p for p in store}

    def children(path: Path) -> list[Path]:
        result = []
        data = store.get(path) or {}
        for entry in get_how(data):
            tid = (entry.get("target_node") or "").upper()
            if tid:
                tp = id_to_path.get(tid)
                if tp and tp != path:
                    result.append(tp)
        return result

    visited: dict[Path, int] = {}
    queue: list[tuple[Path, int]] = []
    for p in children(start):
        if p not in visited:
            visited[p] = 1
            queue.append((p, 1))

    head = 0
    while head < len(queue):
        current, d = queue[head]
        head += 1
        if d < max_depth:
            for p in children(current):
                if p not in visited:
                    visited[p] = d + 1
                    queue.append((p, d + 1))

    # Check if any node at max_depth has children (need ellipsis)
    nodes_with_hidden_children = set()
    for p, d in visited.items():
        if d == max_depth and children(p):
            nodes_with_hidden_children.add(p)

    lines: list[TreeLine] = []
    for path, d in queue:
        data = store.get(path) or {}
        lines.append(TreeLine(
            path=path,
            description=str(data.get("description") or get_task_id(path)),
            node_type=str(data.get("type") or ""),
            status=str(data.get("status") or ""),
            depth=d,
        ))
        if path in nodes_with_hidden_children:
            lines.append(TreeLine(None, "…", "", "", d + 1, is_ellipsis=True))

    return lines


def build_tree_lines(store: Store, current: Path) -> list[TreeLine]:
    """Build the full list of tree lines for the left panel."""
    data = store.get(current) or {}
    lines: list[TreeLine] = []

    anc = _ancestors(store, current, MAX_DEPTH)
    desc = _descendants(store, current, MAX_DEPTH)

    # Root header line
    lines.append(TreeLine(None, "root", "", "", -99, is_root_header=True))

    # Ancestors: first displayed = furthest (most negative depth) → gets "why" margin
    for i, line in enumerate(anc):
        if not line.is_ellipsis:
            line.margin = "why  " if i == 0 else " │   "
    lines.extend(anc)

    # Current node
    lines.append(TreeLine(
        path=current,
        description=str(data.get("description") or get_task_id(current)),
        node_type=str(data.get("type") or ""),
        status=str(data.get("status") or ""),
        depth=0,
    ))

    # Descendants: last displayed = deepest → gets "how" margin
    non_ellipsis_desc = [l for l in desc if not l.is_ellipsis]
    for i, line in enumerate(non_ellipsis_desc):
        line.margin = "how  " if i == len(non_ellipsis_desc) - 1 else " │   "
    lines.extend(desc)

    return lines


# ── Rendering helpers ─────────────────────────────────────────────────────────

_TYPE_W = 12
_STATUS_W = 10


def _chip(text: str, style: str, width: int) -> Text:
    padded = text[:width].ljust(width)
    return Text(padded, style=style)


def render_tree_line(line: TreeLine, is_cursor: bool) -> Text:
    t = Text()

    if line.is_root_header:
        t.append("     root", style="bold dim")
        return t

    if line.is_ellipsis:
        indent = "  " * max(0, abs(line.depth) - 1)
        t.append(f"  │  {indent}└── …", style="dim")
        return t

    # Left margin indicator
    if line.depth == 0:
        margin = " ▶   "
    elif line.margin:
        margin = line.margin
    elif line.depth < 0:
        margin = " │   "
    else:
        margin = " │   "

    if line.depth == 0:
        margin_style = "bold cyan"
    elif line.depth < 0:
        margin_style = "dim cyan"
    else:
        margin_style = "dim green"
    t.append(margin, style=margin_style)

    # Tree connector + indentation
    depth = abs(line.depth)
    if line.depth == 0:
        connector = "    "
    elif line.depth < 0:
        connector = "┌── "
    else:
        indent = "  " * (line.depth - 1)
        connector = indent + "├── "

    t.append(connector, style="dim")

    # Description
    desc = line.description[:40]
    if line.depth == 0:
        status_style = STATUS_STYLE.get(line.status, "white")
        desc_style = status_style if status_style else "bold white"
        t.append(f"{desc:<42}", style="bold " + desc_style if "bold" not in desc_style else desc_style)
    else:
        t.append(f"{desc:<42}", style="white" if not is_cursor else "bold white")

    # Type chip
    type_style = TYPE_STYLE.get(line.node_type, "dim")
    t.append(_chip(line.node_type, type_style, _TYPE_W))
    t.append("  ")

    # Status chip
    status_style = STATUS_STYLE.get(line.status, "dim")
    t.append(_chip(line.status, status_style, _STATUS_W))

    return t


# ── Left panel widget ─────────────────────────────────────────────────────────


class TreePanel(Widget):
    """Left panel: navigable tree around current node."""

    BINDINGS = [
        Binding("up", "cursor_up", "Up", show=False),
        Binding("down", "cursor_down", "Down", show=False),
        Binding("enter", "select", "Select", show=False),
    ]

    cursor_index: reactive[int] = reactive(0)

    def __init__(self, store: Store, **kwargs):
        super().__init__(**kwargs)
        self.store = store
        self._lines: list[TreeLine] = []
        self._navigable: list[int] = []  # indices in _lines that are navigable

    def set_lines(self, lines: list[TreeLine], focus_current: bool = True) -> None:
        self._lines = lines
        # Navigable = has a path (not ellipsis, not root header)
        self._navigable = [i for i, l in enumerate(lines) if l.path is not None]
        if focus_current:
            # Find the current node line (depth == 0)
            for nav_i, line_i in enumerate(self._navigable):
                if lines[line_i].depth == 0:
                    self.cursor_index = nav_i
                    break
        self.refresh()

    def _current_line_index(self) -> int:
        if not self._navigable:
            return 0
        return self._navigable[min(self.cursor_index, len(self._navigable) - 1)]

    def watch_cursor_index(self) -> None:
        self.refresh()

    def render_line(self, y: int) -> "Strip":
        from textual.strip import Strip
        from rich.segment import Segment
        from rich.style import Style

        if y >= len(self._lines):
            return Strip([Segment(" " * self.size.width)])

        line = self._lines[y]
        nav_indices_for_line = [
            nav_i for nav_i, line_i in enumerate(self._navigable) if line_i == y
        ]
        is_cursor = bool(nav_indices_for_line) and nav_indices_for_line[0] == self.cursor_index

        text = render_tree_line(line, is_cursor)

        if is_cursor:
            # Highlight cursor row
            from rich.console import Console
            console = Console(width=self.size.width)
            segments = list(text.render(console))
            cursor_style = Style(reverse=True)
            segments = [Segment(s.text, cursor_style + (s.style or Style())) for s in segments]
        else:
            from rich.console import Console
            console = Console(width=self.size.width)
            segments = list(text.render(console))

        # Pad to width
        total = sum(len(s.text) for s in segments)
        if total < self.size.width:
            segments.append(Segment(" " * (self.size.width - total)))

        return Strip(segments)

    def get_content_height(self, container_size, viewport, width):
        return len(self._lines)

    def action_cursor_up(self) -> None:
        if self.cursor_index > 0:
            self.cursor_index -= 1
            self._scroll_to_cursor()
            self._preview_cursor()

    def action_cursor_down(self) -> None:
        if self.cursor_index < len(self._navigable) - 1:
            self.cursor_index += 1
            self._scroll_to_cursor()
            self._preview_cursor()

    def _scroll_to_cursor(self) -> None:
        if not self._navigable:
            return
        line_y = self._navigable[self.cursor_index]
        self.scroll_visible(self)  # rough — just keep widget in view
        # Scroll the parent ScrollableContainer
        parent = self.parent
        if hasattr(parent, "scroll_to"):
            line_height = 1
            parent.scroll_to(y=max(0, line_y - self.size.height // 2), animate=False)

    def _preview_cursor(self) -> None:
        if not self._navigable:
            return
        line = self._lines[self._navigable[self.cursor_index]]
        if line.path:
            self.app.preview_node(line.path)

    def action_select(self) -> None:
        if not self._navigable:
            return
        line = self._lines[self._navigable[self.cursor_index]]
        if line.path:
            self.app.navigate_to(line.path)


# ── Right panel widget ────────────────────────────────────────────────────────


class DetailPanel(Static):
    """Right panel: node details."""

    def show_node(self, store: Store, path: Path) -> None:
        data = store.get(path) or {}
        id_to_path = {get_task_id(p): p for p in store}

        t = Text()

        # Header
        desc = str(data.get("description") or get_task_id(path))
        t.append(f"{desc}\n", style="bold white")
        t.append(f"  {get_task_id(path)}\n\n", style="dim")

        # Scalar fields
        for field_name in ("type", "status", "horizon", "start_date", "due_date"):
            val = data.get(field_name)
            if val:
                style = "dim"
                if field_name == "status":
                    style = STATUS_STYLE.get(str(val), "white")
                elif field_name == "type":
                    style = TYPE_STYLE.get(str(val), "white")
                t.append(f"  {field_name:<14}", style="dim")
                t.append(f"{val}\n", style=style)

        # Why (backlinks)
        why_paths = []
        path_id = get_task_id(path).upper()
        for p, pdata in store.items():
            if p == path:
                continue
            for entry in get_how(pdata):
                if (entry.get("target_node") or "").upper() == path_id:
                    why_paths.append(p)
                    break

        if why_paths:
            t.append("\n  why\n", style="dim cyan")
            for wp in why_paths:
                wd = store.get(wp) or {}
                wdesc = str(wd.get("description") or get_task_id(wp))
                wstatus = str(wd.get("status") or "")
                wtype = str(wd.get("type") or "")
                t.append(f"    ← {wdesc:<36}", style="white")
                t.append(_chip(wtype, TYPE_STYLE.get(wtype, "dim"), _TYPE_W))
                t.append("  ")
                t.append(_chip(wstatus, STATUS_STYLE.get(wstatus, "dim"), _STATUS_W))
                t.append("\n")

        # How (children)
        how_entries = get_how(data)
        if how_entries:
            t.append("\n  how\n", style="dim green")
            for entry in how_entries:
                tid = (entry.get("target_node") or "").upper()
                inline_desc = entry.get("description", "")
                if tid:
                    cp = id_to_path.get(tid)
                    if cp:
                        cd = store.get(cp) or {}
                        cdesc = str(cd.get("description") or tid)
                        cstatus = str(cd.get("status") or "")
                        ctype = str(cd.get("type") or "")
                        t.append(f"    → {cdesc:<36}", style="white")
                        t.append(_chip(ctype, TYPE_STYLE.get(ctype, "dim"), _TYPE_W))
                        t.append("  ")
                        t.append(_chip(cstatus, STATUS_STYLE.get(cstatus, "dim"), _STATUS_W))
                        if inline_desc:
                            t.append(f"  ({inline_desc})", style="dim")
                        t.append("\n")
                    else:
                        t.append(f"    → {tid} (not found)\n", style="dim red")
                elif inline_desc:
                    t.append(f"    → {inline_desc}\n", style="dim")

        # Notes
        notes = data.get("notes")
        if notes:
            t.append("\n  notes\n", style="dim")
            for note_line in str(notes).splitlines():
                t.append(f"    {note_line}\n", style="dim white")

        # Conclusion
        conclusion = data.get("conclusion")
        if conclusion:
            t.append("\n  conclusion\n", style="dim magenta")
            for cl in str(conclusion).splitlines():
                t.append(f"    {cl}\n", style="white")

        self.update(t)


# ── App ───────────────────────────────────────────────────────────────────────


class ViewerApp(App):
    CSS = """
    Screen {
        layout: horizontal;
    }
    #left {
        width: 1fr;
        border-right: solid $panel-lighten-1;
    }
    #left-scroll {
        height: 100%;
        overflow-y: auto;
    }
    #right {
        width: 2fr;
        padding: 1 2;
        overflow-y: auto;
    }
    TreePanel {
        height: auto;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("escape", "go_back", "Back"),
    ]

    def __init__(self, vault: Path = VAULT):
        super().__init__()
        self.store = Store(vault)
        self._history: list[Path] = []
        self._current: Optional[Path] = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Horizontal():
            with ScrollableContainer(id="left-scroll"):
                yield TreePanel(self.store, id="left")
            yield DetailPanel("", id="right")
        yield Footer()

    def on_mount(self) -> None:
        # Start with first root node (no parents)
        roots = self._find_roots()
        if roots:
            self._current = roots[0]
            self._refresh_tree()
            self._update_detail(roots[0])
        self.query_one(TreePanel).focus()

    def _find_roots(self) -> list[Path]:
        has_parent: set[Path] = set()
        id_to_path = {get_task_id(p): p for p in self.store}
        for p, data in self.store.items():
            for entry in get_how(data):
                tid = (entry.get("target_node") or "").upper()
                if tid:
                    tp = id_to_path.get(tid)
                    if tp:
                        has_parent.add(tp)
        return sorted(p for p in self.store if p not in has_parent)

    def _refresh_tree(self, focus_current: bool = True) -> None:
        if not self._current:
            return
        lines = build_tree_lines(self.store, self._current)
        panel = self.query_one(TreePanel)
        panel.set_lines(lines, focus_current=focus_current)

    def _update_detail(self, path: Path) -> None:
        detail = self.query_one(DetailPanel)
        detail.show_node(self.store, path)

    def navigate_to(self, path: Path) -> None:
        if self._current and self._current != path:
            self._history.append(self._current)
        self._current = path
        self._refresh_tree()
        self._update_detail(path)

    def preview_node(self, path: Path) -> None:
        self._update_detail(path)

    def action_go_back(self) -> None:
        if self._history:
            prev = self._history.pop()
            self._current = prev
            self._refresh_tree()
            self._update_detail(prev)


def main():
    vault = Path(sys.argv[1]) if len(sys.argv) > 1 else VAULT
    app = ViewerApp(vault=vault)
    app.run()


if __name__ == "__main__":
    main()
