from pathlib import Path
from typing import List, Literal, Optional

from rich.text import Text
from textual.app import App, ComposeResult
from textual.coordinate import Coordinate
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import DataTable, Footer, Input, Label, Select, Static

from pfq.config import FIELDS, STATUS_STYLES
from pfq.disk_io import (
    DEFAULT_VAULT_PATH,
    create_node,
    delete_node_file,
    load_vault,
    save_node_fields,
    save_vault,
)
from pfq.model import Node, NodeGraph

INDENT = "   "  # per depth level

# ── Color palette ──────────────────────────────────────────────────────────────
PALETTE = {
    "row_bg": "#1c2d40",  # selected row  — dark slate-blue (reserved, not yet applied)
    "cell_bg": "#1a5276",  # cursor cell   — brighter blue
    "cell_fg": "#eaf2ff",  # cursor cell text — near-white
}

NodeRole = Literal["parent", "selected", "child"]


def _rich(text: str, depth: int) -> Text:
    """Plain string → Rich Text with depth styling: 0 → bold, 2 → dim, else plain."""
    t = Text(text)
    if depth == 0:
        t.stylize("bold")
    elif depth == 2:
        t.stylize("dim")
    return t


def _status_rich(status: str, depth: int) -> Text:
    """Like _rich() but also applies STATUS_STYLES color when the status is known."""
    color = STATUS_STYLES.get(status.lower()) if status else None
    if color:
        if depth == 0:
            return Text.from_markup(f"[bold {color}]{status}[/]")
        elif depth == 2:
            return Text.from_markup(f"[dim {color}]{status}[/]")
        else:
            return Text.from_markup(f"[{color}]{status}[/]")
    return _rich(status, depth)


def _margin_cell(role: NodeRole, boundary: bool) -> str:
    if role == "selected":
        return "▶"
    return " "


def _tree_prefix_segments(
    depth: int, index: int, items: list, *, reverse: bool = False, bullet: str = ""
) -> list[tuple[str, int]]:
    """Return prefix as a list of (text, level) segments for independent styling.

    Each segment's level indicates which depth it belongs to (for styling).
    reverse=True is used for parent lists (displayed farthest-first, tree grows upward).
    bullet replaces the trailing space of the terminal connector, e.g. '└──(' or '└──['.
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

    # terminal connector: replace trailing space with bullet (or keep space if no bullet)
    end = bullet if bullet else " "
    segments: list[tuple[str, int]] = []
    for lvl in range(1, depth):
        segments.append(("│   " if has_sibling_at(lvl) else "    ", lvl))
    if reverse:
        segments.append(("├──" + end if has_sibling_at(depth) else "╭──" + end, depth))
    else:
        segments.append(("├──" + end if has_sibling_at(depth) else "╰──" + end, depth))
    return segments


def _node_bullet(node: Node, graph: NodeGraph, depth: int = 0) -> str:
    """Return a single char bullet (or '' for depth-1 middle nodes):
    - roots always '@', at any depth
    - depth 1, non-root: '' (connector is enough, keeps alignment)
    - depth 2+, non-root: '○' for leaf, '<' for middle
    """
    is_root = len(graph.get_parent_ids(node.node_id)) == 0
    is_leaf = len(graph.get_children_ids(node.node_id)) == 0
    if is_root:
        return "@"
    if depth <= 1:
        return ""
    return "○" if is_leaf else "<"


def _desc_cell(
    role: NodeRole, depth: int, node: Node, graph: NodeGraph, index: int = 0, items: list = ()
) -> Text:
    bullet = _node_bullet(node, graph, depth)
    raw = node.description or ""
    if role == "selected":
        return _rich(bullet + (" " if bullet else "") + raw, depth)

    t = Text()
    for seg, lvl in _tree_prefix_segments(
        depth, index, list(items), reverse=(role == "parent"), bullet=bullet
    ):
        style = "dim" if lvl >= 2 else ""
        t.append(seg, style=style)
    desc_style = "bold" if depth == 0 else ("dim" if depth >= 2 else "")
    # when bullet is set, it replaces the connector's trailing space → add space before description
    # when no bullet, connector already ends with a space → append description directly
    t.append((" " if bullet else "") + raw, style=desc_style)
    return t


# ── Create modal ──────────────────────────────────────────────────────────────


class CreateModal(ModalScreen):
    """Prompt for a description, then dismiss with the string (or None on cancel)."""

    CSS = """
    CreateModal {
        align: center middle;
    }
    #dialog {
        background: $surface;
        border: thick $primary;
        padding: 1 2;
        width: 52;
        height: auto;
    }
    #dialog Label {
        color: $text-muted;
        margin-bottom: 1;
    }
    """
    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def __init__(self, parent_label: str):
        super().__init__()
        self.parent_label = parent_label

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label(f"New child of: {self.parent_label}")
            yield Input(placeholder="Description…", id="widget")

    def on_mount(self) -> None:
        self.query_one("#widget").focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        value = event.value.strip()
        self.dismiss(value if value else None)

    def action_cancel(self) -> None:
        self.dismiss(None)


# ── Delete modal ───────────────────────────────────────────────────────────────


class DeleteModal(ModalScreen):
    """Confirmation prompt before deleting a node."""

    CSS = """
    DeleteModal {
        align: center middle;
    }
    #dialog {
        background: $surface;
        border: thick $error;
        padding: 1 2;
        width: 52;
        height: auto;
    }
    #dialog Label {
        margin-bottom: 1;
    }
    #hint {
        color: $text-muted;
    }
    """
    BINDINGS = [
        Binding("y", "confirm", "Yes, delete"),
        Binding("n", "cancel", "Cancel"),
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(self, node_label: str):
        super().__init__()
        self.node_label = node_label

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label(f'Delete "{self.node_label}" ?')
            yield Label("\\[y] confirm    \\[n / Esc] cancel", id="hint")

    def action_confirm(self) -> None:
        self.dismiss(True)

    def action_cancel(self) -> None:
        self.dismiss(False)


# ── Link modal ─────────────────────────────────────────────────────────────────


class LinkModal(ModalScreen):
    """Search existing nodes or create a new one, then link it as a parent."""

    CSS = """
    LinkModal {
        align: center middle;
    }
    #dialog {
        background: $surface;
        border: thick $primary;
        padding: 1 2;
        width: 60;
        height: auto;
    }
    #dialog Label {
        color: $text-muted;
        margin-bottom: 1;
    }
    #results {
        height: auto;
        max-height: 12;
        overflow-y: auto;
        margin-top: 1;
    }
    #hint {
        color: $text-muted;
        margin-top: 1;
    }
    """
    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("up", "move_up", "Up"),
        Binding("down", "move_down", "Down"),
        Binding("enter", "confirm", "Confirm"),
    ]

    def __init__(self, current_node_id: str, graph: NodeGraph):
        super().__init__()
        self.current_node_id = current_node_id
        self.graph = graph
        self._matches: list[tuple[str, str]] = []  # [(node_id, description)]
        self._selected: int = 0  # index into _matches, or -1 = "create new"

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("Link to parent — search or create")
            yield Input(placeholder="Type to search…", id="widget")
            yield DataTable(cursor_type="row", show_header=False, id="results")
            yield Label("↑↓ select  Enter confirm  Esc cancel", id="hint")

    def on_mount(self) -> None:
        t = self.query_one("#results", DataTable)
        t.add_column("desc", width=54)
        self.query_one("#widget", Input).focus()

    def _update_results(self, query: str) -> None:
        t = self.query_one("#results", DataTable)
        t.clear()
        self._matches = []
        self._selected = 0

        if query:
            results = self.graph.search_nodes(query)
            self._matches = [
                (n.node_id, n.description or "")
                for n in results
                if n.node_id != self.current_node_id
            ][:10]

        for node_id, desc in self._matches:
            t.add_row(Text(desc), key=node_id)

        # Always add "create new" option at the bottom when query is non-empty
        if query.strip():
            t.add_row(
                Text(f'+ Create new: "{query.strip()}"', style="italic green"),
                key="__create__",
            )
            if not self._matches:
                self._selected = -1  # default to create
        self._highlight()

    def _highlight(self) -> None:
        t = self.query_one("#results", DataTable)
        if t.row_count == 0:
            return
        row = len(self._matches) if self._selected == -1 else self._selected
        row = max(0, min(row, t.row_count - 1))
        t.move_cursor(row=row)

    def on_input_changed(self, event: Input.Changed) -> None:
        self._update_results(event.value)

    def action_move_up(self) -> None:
        total = len(self._matches) + (1 if self._create_row_shown() else 0)
        if total == 0:
            return
        idx = len(self._matches) if self._selected == -1 else self._selected
        idx = (idx - 1) % total
        self._selected = -1 if idx == len(self._matches) else idx
        self._highlight()

    def action_move_down(self) -> None:
        total = len(self._matches) + (1 if self._create_row_shown() else 0)
        if total == 0:
            return
        idx = len(self._matches) if self._selected == -1 else self._selected
        idx = (idx + 1) % total
        self._selected = -1 if idx == len(self._matches) else idx
        self._highlight()

    def _create_row_shown(self) -> bool:
        query = self.query_one("#widget", Input).value.strip()
        return bool(query)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.action_confirm()

    def action_confirm(self) -> None:
        query = self.query_one("#widget", Input).value.strip()
        if self._selected == -1 and query:
            # Create new node as parent
            self.dismiss({"action": "create", "description": query})
        elif self._matches and 0 <= self._selected < len(self._matches):
            node_id, _ = self._matches[self._selected]
            self.dismiss({"action": "link", "node_id": node_id})
        elif not self._matches and not query:
            self.dismiss(None)

    def action_cancel(self) -> None:
        self.dismiss(None)


# ── Edit modal ─────────────────────────────────────────────────────────────────


class EditModal(ModalScreen):
    """Single-field edit modal. Driven by FIELDS config — no hardcoded field logic."""

    CSS = """
    EditModal {
        align: center middle;
    }
    #dialog {
        background: $surface;
        border: thick $primary;
        padding: 1 2;
        width: 52;
        height: auto;
    }
    #dialog Label {
        color: $text-muted;
        margin-bottom: 1;
    }
    #suggestions {
        height: 1;
        margin-top: 1;
        color: $text-muted;
    }
    #hint {
        color: $text-muted;
        margin-top: 1;
    }
    """
    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("tab", "pick_suggestion", "Pick", show=False),
    ]

    def __init__(self, node: Node, col_key: str):
        super().__init__()
        self.node = node
        self.col_key = col_key
        self.field = FIELDS[col_key]

    def compose(self) -> ComposeResult:
        current = getattr(self.node, self.field["attr"]) or ""
        with Vertical(id="dialog"):
            yield Label(self.field["label"])
            if self.field["kind"] == "select":
                options = self.field["options"]
                extra = {"value": current} if current in options else {}
                yield Select(
                    [(o, o) for o in options],
                    allow_blank=True,
                    id="widget",
                    **extra,
                )
            else:
                yield Input(value=current, id="widget")
                if self.col_key == "status":
                    yield Static("", id="suggestions")
                    yield Static("[dim]\\[enter] confirm  [/][dim]\\[tab] pick  [/][dim]\\[esc] cancel[/]", id="hint", markup=True)
                else:
                    yield Static("[dim]\\[enter] confirm  [/][dim]\\[esc] cancel[/]", id="hint", markup=True)

    def on_mount(self) -> None:
        self._matches: list[str] = []
        self.query_one("#widget").focus()
        if self.col_key == "status":
            self._refresh_suggestions(getattr(self.node, self.field["attr"]) or "")

    def _refresh_suggestions(self, query: str) -> None:
        q = query.lower()
        self._matches = [s for s in STATUS_STYLES if q in s]
        t = Text()
        for i, status in enumerate(self._matches):
            if i:
                t.append("  ")
            color = STATUS_STYLES[status]
            style = f"{color} underline" if i == 0 else color
            t.append(status, style=style)
        self.query_one("#suggestions", Static).update(t)

    def _dismiss_with_value(self, value: Optional[str]) -> None:
        self.dismiss({"attr": self.field["attr"], "value": value or None})

    def on_input_changed(self, event: Input.Changed) -> None:
        if self.col_key == "status":
            self._refresh_suggestions(event.value)

    # text field: Enter submits
    def on_input_submitted(self, event: Input.Submitted) -> None:
        self._dismiss_with_value(event.value.strip())

    # select field: auto-dismiss on selection (treat falsy/sentinel as blank)
    def on_select_changed(self, event: Select.Changed) -> None:
        options = self.field.get("options", [])
        value = event.value if event.value in options else None
        self._dismiss_with_value(value)

    def action_pick_suggestion(self) -> None:
        # Tab picks the first match, or the one that exactly matches current input
        inp = self.query_one("#widget", Input).value.strip().lower()
        if not hasattr(self, "_matches") or not self._matches:
            return
        exact = [s for s in self._matches if s == inp]
        self._dismiss_with_value(exact[0] if exact else self._matches[0])

    def action_cancel(self) -> None:
        self.dismiss(None)


# ── Main app ───────────────────────────────────────────────────────────────────


class PfqApp(App):
    TITLE = "pfq"
    CSS = f"""
    DataTable > .datatable--cursor {{
        background: {PALETTE['cell_bg']};
        color: {PALETTE['cell_fg']};
    }}
    #app-header {{
        dock: top;
        height: 1;
        background: $panel;
        color: $foreground;
        content-align: left middle;
        padding: 0 1;
    }}
    """
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("h", "go_home", "Home"),
        Binding("escape", "go_back", "Back"),
        Binding("e", "edit_node", "Edit"),
        Binding("a", "append_node", "Append"),
        Binding("z", "link_parent", "Link parent"),
        Binding("d", "delete_link", "Unlink"),
        Binding("D", "delete_node", "Delete node"),
        Binding("shift+up", "reorder_up", "Move up", show=False),
        Binding("shift+down", "reorder_down", "Move down", show=False),
    ]

    def __init__(self, vault_path: Path = DEFAULT_VAULT_PATH):
        super().__init__()
        self.vault_path = vault_path
        self.graph = load_vault(vault_path)
        self.current_node_id: Optional[str] = None
        self.history: List[Optional[str]] = []

    def compose(self) -> ComposeResult:
        yield Static(
            f"[bold reverse] p f q [/]  {self.vault_path.name}/", id="app-header"
        )
        table = DataTable(cursor_type="cell", show_header=True)
        table.add_column("", key="margin", width=1)
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

    def _add_row(
        self,
        role: NodeRole,
        depth: int,
        node: Node,
        *,
        boundary: bool = False,
        index: int = 0,
        items: list = (),
    ) -> None:
        self._table().add_row(
            _margin_cell(role, boundary),
            _desc_cell(role, depth, node, self.graph, index=index, items=items),
            _rich(node.type or "", depth),
            _status_rich(node.status or "", depth),
            key=node.node_id,
        )

    # ── Views ──────────────────────────────────────────────────────────────────

    def _show_home(self) -> None:
        self.current_node_id = None
        t = self._table()
        t.clear()
        for node_id in sorted(self.graph.get_roots()):
            node = self.graph.get_node(node_id)
            bullet = _node_bullet(node, self.graph, 0)
            t.add_row(
                "",
                _rich(bullet + (" " if bullet else "") + (node.description or ""), 0),
                _rich(node.type or "", 0),
                _status_rich(node.status or "", 0),
                key=node.node_id,
            )

    def _show_node(self, node_id: str, *, cursor_row: Optional[int] = None) -> None:
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
            self._add_row(
                "parent", depth, node, boundary=(i == 0), index=i, items=parents
            )

        # Current node
        self._add_row("selected", 0, self.graph.get_node(node_id))
        selected_row = 1 + len(parents)

        # Children — closest first; last gets "how" boundary label
        # exclude nodes already shown as parents (cycle-like graphs)
        seen = {node_id} | {n.node_id for n, _ in parents}
        filtered_children = [(n, d) for n, d in children if n.node_id not in seen]
        for i, (node, depth) in enumerate(filtered_children):
            self._add_row(
                "child",
                depth,
                node,
                boundary=(i == len(filtered_children) - 1),
                index=i,
                items=filtered_children,
            )

        t.move_cursor(
            row=cursor_row if cursor_row is not None else selected_row, column=col
        )

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

    # ── Editing ────────────────────────────────────────────────────────────────

    def action_edit_node(self) -> None:
        t = self._table()
        cell_key = t.coordinate_to_cell_key(t.cursor_coordinate)
        row_key = str(cell_key.row_key.value)
        col_key = str(cell_key.column_key.value)
        if row_key == "__home__" or row_key not in self.graph.nodes:
            return
        if col_key not in FIELDS:
            return
        node = self.graph.get_node(row_key)
        saved_row = t.cursor_coordinate.row
        self.push_screen(EditModal(node, col_key), lambda r: self._on_edit_done(r, saved_row))

    def _on_edit_done(self, result: Optional[dict], cursor_row: int) -> None:
        t = self._table()
        if result is None:
            t.move_cursor(row=cursor_row)
            t.focus()
            return
        # result = {"attr": "description"|"type"|"status", "value": str|None}
        # We derive node_id from the saved row, not the current cursor
        row_key = str(t.coordinate_to_cell_key(Coordinate(cursor_row, 0)).row_key.value)
        node = self.graph.get_node(row_key)
        setattr(node, result["attr"], result["value"])
        save_node_fields(node)
        if self.current_node_id is None:
            self._show_home()
        else:
            self._show_node(self.current_node_id, cursor_row=cursor_row)
        t.focus()

    # ── Append ─────────────────────────────────────────────────────────────────

    def action_append_node(self) -> None:
        t = self._table()

        if self.current_node_id is None:
            # Home view: create a new root (table may be empty)
            self.push_screen(CreateModal("(root)"), self._on_create_root)
            return

        row_key = str(t.coordinate_to_cell_key(t.cursor_coordinate).row_key.value)

        if row_key == "__home__" or row_key not in self.graph.nodes:
            return

        # Parent row: ignore
        parents = [
            n.node_id for n, _ in self.graph.get_parents_tree(self.current_node_id)
        ]
        if row_key in parents:
            return

        # Determine actual parent and insertion position.
        # If cursor is on a depth-1 child → parent is current_node_id, insert after it.
        # If cursor is on a depth-2 child → parent is the depth-1 node above it.
        # If cursor is on current node itself → parent is current_node_id, insert at 0.
        if row_key == self.current_node_id:
            actual_parent_id = self.current_node_id
            position = 0
        elif row_key in self.graph.get_children_ids(self.current_node_id):
            # depth-1: insert after this child
            siblings = self.graph.get_children_ids(self.current_node_id)
            position = siblings.index(row_key) + 1
            actual_parent_id = self.current_node_id
        else:
            # depth-2: find which depth-1 child owns this node
            actual_parent_id = self.current_node_id
            position = len(self.graph.get_children_ids(self.current_node_id))
            for cid in self.graph.get_children_ids(self.current_node_id):
                siblings = self.graph.get_children_ids(cid)
                if row_key in siblings:
                    actual_parent_id = cid
                    position = siblings.index(row_key) + 1
                    break

        parent_node = self.graph.get_node(actual_parent_id)
        label = parent_node.description or actual_parent_id
        self.push_screen(
            CreateModal(label), lambda desc: self._on_create_child(desc, position, actual_parent_id)
        )

    def _on_create_root(self, description: Optional[str]) -> None:
        if not description:
            return
        node = create_node(description, self.vault_path)
        self.graph.add_node(node)
        self._show_home()

    def _on_create_child(self, description: Optional[str], position: int, parent_id: str) -> None:
        if not description:
            return
        node = create_node(description, self.vault_path)
        self.graph.add_node(node)
        self.graph.link_child(parent_id, node.node_id, position)
        save_vault(self.graph)
        self._show_node(self.current_node_id)

    # ── Link parent ────────────────────────────────────────────────────────────

    def action_link_parent(self) -> None:
        """z — open LinkModal to attach a parent to the current node."""
        if self.current_node_id is None:
            return  # home view: no node to reparent
        t = self._table()
        row_key = str(t.coordinate_to_cell_key(t.cursor_coordinate).row_key.value)
        if row_key not in self.graph.nodes:
            return
        self.push_screen(
            LinkModal(row_key, self.graph),
            lambda result: self._on_link_parent_done(result, row_key),
        )

    def _on_link_parent_done(self, result: Optional[dict], child_id: str) -> None:
        if result is None:
            return
        if result["action"] == "create":
            parent = create_node(result["description"], self.vault_path)
            self.graph.add_node(parent)
            parent_id = parent.node_id
        else:
            parent_id = result["node_id"]

        self.graph.link_child(
            parent_id, child_id, len(self.graph.get_children_ids(parent_id))
        )
        save_vault(self.graph)
        self._show_node(self.current_node_id)

    # ── Reorder ────────────────────────────────────────────────────────────────

    def _action_reorder(self, delta: int) -> None:
        if self.current_node_id is None:
            return
        t = self._table()
        row_key = str(t.coordinate_to_cell_key(t.cursor_coordinate).row_key.value)
        if row_key in (self.current_node_id, "__home__"):
            return
        # find which visible parent owns this node as a direct child
        parent_id = None
        for candidate in [self.current_node_id] + self.graph.get_children_ids(
            self.current_node_id
        ):
            if row_key in self.graph.get_children_ids(candidate):
                parent_id = candidate
                break
        if parent_id is None:
            return
        self.graph.reorder_child(parent_id, row_key, delta)
        save_vault(self.graph)
        # find the new row index by scanning the flat children list _show_node will build
        parents = list(reversed(self.graph.get_parents_tree(self.current_node_id)))
        children = self.graph.get_childrens_tree(self.current_node_id)
        seen = {self.current_node_id} | {n.node_id for n, _ in parents}
        filtered_children = [(n, d) for n, d in children if n.node_id not in seen]
        child_ids = [n.node_id for n, _ in filtered_children]
        if row_key not in child_ids:
            self._show_node(self.current_node_id)
            return
        new_pos = child_ids.index(row_key)
        parents_count = len(parents)
        self._show_node(
            self.current_node_id, cursor_row=1 + parents_count + 1 + new_pos
        )

    def action_reorder_up(self) -> None:
        self._action_reorder(-1)

    def action_reorder_down(self) -> None:
        self._action_reorder(1)

    # ── Delete link / Delete node ───────────────────────────────────────────────

    def _visible_parent_of(self, node_id: str) -> Optional[str]:
        """Return the ID of the node that is the visible parent of node_id in the
        current view (i.e. the node whose how-link draws the tree connector)."""
        for candidate in [self.current_node_id] + self.graph.get_children_ids(
            self.current_node_id
        ):
            if node_id in self.graph.get_children_ids(candidate):
                return candidate
        return None

    def action_delete_link(self) -> None:
        if self.current_node_id is None:
            return
        t = self._table()
        row_key = str(t.coordinate_to_cell_key(t.cursor_coordinate).row_key.value)
        if (
            row_key in (self.current_node_id, "__home__")
            or row_key not in self.graph.nodes
        ):
            return
        parent_id = self._visible_parent_of(row_key)
        if parent_id is None:
            return
        parent_label = self.graph.get_node(parent_id).description or parent_id
        child_label = self.graph.get_node(row_key).description or row_key
        self.push_screen(
            DeleteModal(f'{child_label}  (unlink from "{parent_label}")'),
            lambda confirmed: self._on_unlink_confirmed(confirmed, parent_id, row_key),
        )

    def _on_unlink_confirmed(
        self, confirmed: bool, parent_id: str, child_id: str
    ) -> None:
        if not confirmed:
            return
        self.graph.unlink_child(parent_id, child_id)
        save_vault(self.graph)
        self._show_node(self.current_node_id)

    def action_delete_node(self) -> None:
        t = self._table()
        row_key = str(t.coordinate_to_cell_key(t.cursor_coordinate).row_key.value)

        if row_key == "__home__" or row_key not in self.graph.nodes:
            return

        node = self.graph.get_node(row_key)
        label = node.description or row_key
        self.push_screen(
            DeleteModal(label),
            lambda confirmed: self._on_delete_confirmed(confirmed, row_key),
        )

    def _on_delete_confirmed(self, confirmed: bool, node_id: str) -> None:
        if not confirmed:
            return
        node = self.graph.get_node(node_id)
        navigating_away = node_id == self.current_node_id
        self.graph.remove_node(node_id)
        save_vault(self.graph)
        delete_node_file(node)
        if navigating_away:
            if self.history:
                prev = self.history.pop()
                if prev is None or prev not in self.graph.nodes:
                    self._show_home()
                else:
                    self._show_node(prev)
            else:
                self._show_home()
        elif self.current_node_id is None:
            self._show_home()
        else:
            self._show_node(self.current_node_id)
