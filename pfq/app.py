"""PfqApp — Textual TUI entry point.

Coordinates navigation, editing, and structural mutations.
All rendering is delegated to render.py; all view-model building to view.py.
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.coordinate import Coordinate
from textual.widgets import DataTable, Footer, Static

from pfq.companion import CompanionPanel
from pfq.config import FIELDS
from pfq.disk_io import (
    DEFAULT_VAULT_PATH,
    create_node,
    delete_node_file,
    load_vault,
    save_node_fields,
    save_vault,
)
from pfq.modals import CreateModal, DeleteModal, EditModal, LinkModal, StatusModal
from pfq.render import PALETTE, render_to_table, render_to_text
from pfq.view import ViewRow, build_home_view, build_node_view


class PfqApp(App):
    TITLE = "pfq"
    LAYERS = ["default", "overlay"]
    CSS = f"""
    DataTable {{
        background: $background;
    }}
    DataTable:focus {{
        background-tint: transparent;
    }}
    DataTable > .datatable--header {{
        background: transparent;
        color: $foreground 30%;
        text-style: none;
    }}
    DataTable > .datatable--even-row {{
        background: $background;
    }}
    DataTable:focus > .datatable--cursor {{
        background: {PALETTE['cell_bg']};
        color: {PALETTE['cell_fg']};
    }}
    DataTable > .datatable--cursor {{
        background: $background;
        color: $foreground;
        text-style: none;
    }}
    DataTable {{
        margin: 1 1 1 3;
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
        Binding("y", "yank_view", "Copy view"),
        Binding("f2", "toggle_companion", "AI", show=True),
    ]

    def __init__(self, vault_path: Path = DEFAULT_VAULT_PATH):
        super().__init__()
        self.vault_path = vault_path
        self.graph = load_vault(vault_path)
        self.current_node_id: Optional[str] = None
        self.history: List[Optional[str]] = []
        self._last_view: list[ViewRow] = []

    def compose(self) -> ComposeResult:
        yield Static(
            f"[bold reverse] p f q [/]  vault: {self.vault_path.name}/", id="app-header"
        )
        table = DataTable(cursor_type="cell", show_header=True)
        table.add_column("status", key="status", width=10)
        table.add_column("", key="margin", width=1)
        table.add_column("description", key="desc", width=50)
        table.add_column("also", key="also", width=24)
        table.add_column("type", key="type", width=0)
        yield table
        yield CompanionPanel(id="companion")
        yield Footer()

    def on_mount(self) -> None:
        self._show_home()

    def _table(self) -> DataTable:
        return self.query_one(DataTable)

    # ── Views ──────────────────────────────────────────────────────────────────

    def _show_home(self) -> None:
        self.current_node_id = None
        rows = build_home_view(self.graph)
        self._last_view = rows
        render_to_table(rows, self._table())

    def _show_node(self, node_id: str, *, cursor_row: Optional[int] = None) -> None:
        self.current_node_id = node_id
        col = self._table().cursor_coordinate.column
        rows = build_node_view(self.graph, node_id)
        self._last_view = rows
        render_to_table(rows, self._table())
        selected_row = next(i for i, r in enumerate(rows) if r.role == "selected")
        self._table().move_cursor(
            row=cursor_row if cursor_row is not None else selected_row,
            column=col,
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
        if col_key == "status":
            self.push_screen(StatusModal(node, self.graph), lambda r: self._on_edit_done(r, saved_row))
        else:
            self.push_screen(EditModal(node, col_key), lambda r: self._on_edit_done(r, saved_row))

    def _on_edit_done(self, result: Optional[dict], cursor_row: int) -> None:
        t = self._table()
        if result is None:
            t.move_cursor(row=cursor_row)
            t.focus()
            return
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
        """Append a new node relative to the cursor.

        Home view: create root. Selected row: append child at end.
        Child row: append sibling after focused node, under its visible parent.
        """
        t = self._table()

        if self.current_node_id is None:
            self.push_screen(CreateModal("(root)"), self._on_create_root)
            return

        row_key = str(t.coordinate_to_cell_key(t.cursor_coordinate).row_key.value)
        if row_key == "__home__" or row_key not in self.graph.nodes:
            return

        focused_row = next(
            (r for r in self._last_view if r.node and r.node.node_id == row_key), None
        )
        if focused_row is None or focused_row.role == "parent":
            return

        if focused_row.role == "selected":
            actual_parent_id = self.current_node_id
            position = len(self.graph.get_children_ids(self.current_node_id))
        else:  # child
            visible_parent_id = focused_row.visible_parent_id or self.current_node_id
            siblings = self.graph.get_children_ids(visible_parent_id)
            position = siblings.index(row_key) + 1 if row_key in siblings else len(siblings)
            actual_parent_id = visible_parent_id

        label = self.graph.get_node(actual_parent_id).description or actual_parent_id
        self.push_screen(
            CreateModal(label),
            lambda desc: self._on_create_child(desc, position, actual_parent_id),
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
        if self.current_node_id is None:
            return
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
        self.graph.link_child(parent_id, child_id, len(self.graph.get_children_ids(parent_id)))
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
        parent_id = next(
            (r.visible_parent_id for r in self._last_view
             if r.node and r.node.node_id == row_key and r.role == "child"),
            None,
        )
        if parent_id is None:
            return
        self.graph.reorder_child(parent_id, row_key, delta)
        save_vault(self.graph)
        rows = build_node_view(self.graph, self.current_node_id)
        new_pos = next(
            (i for i, r in enumerate(rows) if r.node and r.node.node_id == row_key), None
        )
        self._show_node(self.current_node_id, cursor_row=new_pos)

    def action_reorder_up(self) -> None:
        self._action_reorder(-1)

    def action_reorder_down(self) -> None:
        self._action_reorder(1)

    # ── Yank ───────────────────────────────────────────────────────────────────

    def action_yank_view(self) -> None:
        try:
            import pyperclip
        except ImportError:
            self.notify("pyperclip not installed — run: pip install pyperclip", severity="error")
            return
        text = render_to_text(self._last_view)
        try:
            pyperclip.copy(text)
            self.notify("View copied to clipboard")
        except pyperclip.PyperclipException:
            self.notify(
                "Clipboard not available — install xclip or xsel (Linux)",
                severity="error",
            )

    # ── Companion ──────────────────────────────────────────────────────────────

    def action_toggle_companion(self) -> None:
        panel = self.query_one("#companion", CompanionPanel)
        panel.toggle_class("visible")
        if panel.has_class("visible"):
            panel.start_thinking()
        else:
            panel.stop_thinking()

    # ── Delete link / Delete node ───────────────────────────────────────────────

    def action_delete_link(self) -> None:
        if self.current_node_id is None:
            return
        t = self._table()
        row_key = str(t.coordinate_to_cell_key(t.cursor_coordinate).row_key.value)
        if row_key in (self.current_node_id, "__home__") or row_key not in self.graph.nodes:
            return
        parent_id = next(
            (r.visible_parent_id for r in self._last_view
             if r.node and r.node.node_id == row_key and r.role == "child"),
            None,
        )
        if parent_id is None:
            return
        parent_label = self.graph.get_node(parent_id).description or parent_id
        child_label = self.graph.get_node(row_key).description or row_key
        self.push_screen(
            DeleteModal(f'{child_label}  (unlink from "{parent_label}")'),
            lambda confirmed: self._on_unlink_confirmed(confirmed, parent_id, row_key),
        )

    def _on_unlink_confirmed(self, confirmed: bool, parent_id: str, child_id: str) -> None:
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
        self.push_screen(
            DeleteModal(node.description or row_key),
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
