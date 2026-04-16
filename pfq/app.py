from pathlib import Path
from typing import Literal

from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import DataTable, Footer

from pfq.disk_io import DEFAULT_VAULT_PATH
from pfq.model import Node, NodeGraph

INDENT = "   "  # per depth level

# ── Color palette ──────────────────────────────────────────────────────────────
PALETTE = {
    "row_bg":  "#1c2d40",  # selected row  — dark slate-blue (reserved, not yet applied)
    "cell_bg": "#1a5276",  # cursor cell   — brighter blue
    "cell_fg": "#eaf2ff",  # cursor cell text — near-white
}

NodeRole = Literal["parent", "selected", "child"]

_ROLE_CONNECTOR      = {"parent": "┌─", "child": "└─"}
_ROLE_BOUNDARY_LABEL = {"parent": "why", "child": "how"}


def _rich(text: str, depth: int) -> Text:
    """Plain string → Rich Text with depth styling: 0 → bold, 2 → dim, else plain."""
    t = Text(text)
    if depth == 0:
        t.stylize("bold")
    elif depth == 2:
        t.stylize("dim")
    return t


def _margin_cell(role: NodeRole, boundary: bool) -> str:
    if role == "selected":
        return "▶"
    return _ROLE_BOUNDARY_LABEL[role] if boundary else "│"


def _desc_cell(role: NodeRole, depth: int, node: Node) -> Text:
    raw = node.description or ""
    if role == "selected":
        content = raw
    else:
        content = f"{INDENT * (depth - 1)}{_ROLE_CONNECTOR[role]} {raw}"
    return _rich(content, depth)


class PfqApp(App):
    TITLE = "pfq"
    CSS = f"""
    DataTable > .datatable--cursor {{
        background: {PALETTE['cell_bg']};
        color: {PALETTE['cell_fg']};
    }}
    """
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("h", "go_home", "Home"),
        Binding("escape", "go_back", "Back"),
    ]

    def __init__(self, vault_path: Path = DEFAULT_VAULT_PATH):
        super().__init__()
        self.graph = NodeGraph.load_from_disk(vault_path)
        self.current_node_id: str | None = None
        self.history: list[str | None] = []

    def compose(self) -> ComposeResult:
        table = DataTable(cursor_type="cell", show_header=False)
        table.add_column("", key="margin", width=4)
        table.add_column("description", key="desc", width=44)
        table.add_column("type", key="type", width=12)
        table.add_column("status", key="status", width=10)
        yield table
        yield Footer()

    def on_mount(self) -> None:
        self._show_home()

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _table(self) -> DataTable:
        return self.query_one(DataTable)

    def _add_row(self, role: NodeRole, depth: int, node: Node, *, boundary: bool = False) -> None:
        self._table().add_row(
            _margin_cell(role, boundary),
            _desc_cell(role, depth, node),
            _rich(node.type or "", depth),
            _rich(node.status or "", depth),
            key=node.node_id,
        )

    # ── Views ──────────────────────────────────────────────────────────────────

    def _show_home(self) -> None:
        self.current_node_id = None
        t = self._table()
        t.clear()
        for node_id in sorted(self.graph.get_roots()):
            node = self.graph.get_node(node_id)
            t.add_row(
                "",
                _rich(node.description or "", 0),
                _rich(node.type or "", 0),
                _rich(node.status or "", 0),
                key=node.node_id,
            )

    def _show_node(self, node_id: str) -> None:
        self.current_node_id = node_id
        t = self._table()
        col = t.cursor_coordinate.column  # preserve column across refresh
        t.clear()

        parents = list(reversed(self.graph.get_parents_tree(node_id)))
        children = self.graph.get_childrens_tree(node_id)

        # Root line
        t.add_row("─", Text("root", style="dim"), "", "", key="__home__")

        # Parents — farthest first; farthest gets "why" boundary label
        for i, (node, depth) in enumerate(parents):
            self._add_row("parent", depth, node, boundary=(i == 0))

        # Current node
        self._add_row("selected", 0, self.graph.get_node(node_id))
        selected_row = 1 + len(parents)

        # Children — closest first; last gets "how" boundary label
        for i, (node, depth) in enumerate(children):
            self._add_row("child", depth, node, boundary=(i == len(children) - 1))

        t.move_cursor(row=selected_row, column=col)

    # ── Navigation ─────────────────────────────────────────────────────────────

    def _navigate_to(self, node_id: str) -> None:
        self.history.append(self.current_node_id)
        self._show_node(node_id)

    def on_data_table_cell_selected(self, event: DataTable.CellSelected) -> None:
        row_key = str(event.cell_key.row_key.value)
        if row_key == "__home__":
            self.action_go_home()
        elif row_key != self.current_node_id:
            self._navigate_to(row_key)

    def action_go_home(self) -> None:
        if self.current_node_id is not None:
            self.history.append(self.current_node_id)
            self._show_home()

    def action_go_back(self) -> None:
        if self.history:
            prev = self.history.pop()
            if prev is None:
                self._show_home()
            else:
                self._show_node(prev)
