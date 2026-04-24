"""PfqApp — Textual TUI entry point.

Coordinates navigation, editing, and structural mutations.
All rendering is delegated to render.py; all view-model building to view.py.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import List, Optional

from textual.app import App, ComposeResult
from textual.binding import Binding
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
from pfq.modals import (
    CreateModal,
    DeleteModal,
    EditModal,
    HelpModal,
    NodePickerModal,
    SyncModal,
    TargetModal,
    UpdateModal,
)
from pfq.sync import (
    commit_and_push,
    get_remote_name,
    has_remote,
    has_uncommitted_changes,
    is_git_repo,
    pull,
)
from pfq.render import PALETTE, render_to_table, render_to_text
from pfq.view import ViewRow, build_home_view, build_node_view


class PfqApp(App):
    ENABLE_COMMAND_PALETTE = False
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
        margin: 1 1 1 1;
    }}
    #axis-label {{
        color: $foreground 30%;
        margin: 0 1 1 1;
        height: 1;
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
        Binding("q", "request_quit", "Quit"),
        Binding("escape", "go_back", "Back", show=False),
        Binding(
            "not_a_key",
            "noop",
            "nav",
            key_display="↑↓←→ ↵ esc",
            group=Binding.Group("navigate"),
        ),  # Hack
        Binding("s", "jump", "Search"),
        Binding("e", "edit_node", "Edit"),
        Binding("a", "append_node", "Append"),
        Binding("z", "link_parent", "Link"),
        Binding("d", "delete", "Delete"),
        Binding("shift+up", "reorder_up", "Move up", group=Binding.Group("Order")),
        Binding(
            "shift+down",
            "reorder_down",
            "Move down",
            key_display="↓",
            group=Binding.Group("Order"),
        ),
        Binding("y", "yank_view", "Copy view"),
        Binding("f5", "sync", "Sync"),
        Binding("f2", "toggle_companion", "AI"),
        Binding("f1", "toggle_help", "Help", show=False),
    ]

    def __init__(self, vault_path: Path = DEFAULT_VAULT_PATH):
        super().__init__()
        self.vault_path = vault_path
        self.graph = load_vault(vault_path)
        self.current_node_id: Optional[str] = None
        self.history: List[Optional[str]] = []
        self._last_view: list[ViewRow] = []

    @property
    def _sync_enabled(self) -> bool:
        return is_git_repo(self.vault_path) and has_remote(self.vault_path)

    def _header_text(self, sync_status: Optional[str] = None) -> str:
        base = f"[bold reverse] p f q [/]  vault: {self.vault_path.name}/"
        if not is_git_repo(self.vault_path):
            return base + "  [dim]local only[/]"
        remote = get_remote_name(self.vault_path)
        if remote is None:
            git_part = "  [dim]↯ no remote[/]"
        else:
            dot = "  [yellow]●[/]" if has_uncommitted_changes(self.vault_path) else ""
            git_part = f"  [dim]⟳ {remote}[/]{dot}"
        if sync_status == "ok":
            status_part = "  [green]✓[/]"
        elif sync_status == "fail":
            status_part = "  [red]![/]"
        else:
            status_part = ""
        return base + git_part + status_part

    def _update_header(self, sync_status: Optional[str] = None) -> None:
        self.query_one("#app-header", Static).update(self._header_text(sync_status))

    def compose(self) -> ComposeResult:
        yield Static("", id="app-header")
        table = DataTable(cursor_type="cell", show_header=True)
        table.add_column("pulse", key="pulse", width=13)
        table.add_column("description", key="desc", width=43)
        table.add_column("when", key="target", width=18)
        table.add_column("mood", key="comment", width=22)
        yield table
        yield Static("  ⬆ why  ·  ⬇ how", id="axis-label")
        yield CompanionPanel(id="companion")
        yield Footer()

    def on_mount(self) -> None:
        self._show_home()
        self._update_header()
        if not self.graph.nodes:
            self.push_screen(HelpModal())
        if self._sync_enabled:
            result = pull(self.vault_path)
            if result.ok:
                if "Pulled" in result.message:
                    self.graph = load_vault(self.vault_path)
                    self._show_home()
                    self.notify("Pulled latest changes")
                self._update_header("ok")
            else:
                self.notify(f"Sync: {result.message}", severity="warning")
                self._update_header("fail")

    def _table(self) -> DataTable:
        return self.query_one(DataTable)

    # ── Views ──────────────────────────────────────────────────────────────────

    def _show_home(self, *, cursor_row: Optional[int] = None) -> None:
        self.current_node_id = None
        col = self._table().cursor_coordinate.column
        rows = build_home_view(self.graph)
        self._last_view = rows
        render_to_table(rows, self._table())
        if cursor_row is not None:
            self._table().move_cursor(row=min(cursor_row, len(rows) - 1), column=col)

    def _show_node(
        self,
        node_id: str,
        *,
        cursor_row: Optional[int] = None,
        cursor_node_id: Optional[str] = None,
    ) -> None:
        self.current_node_id = node_id
        col = self._table().cursor_coordinate.column
        rows = build_node_view(self.graph, node_id)
        self._last_view = rows
        render_to_table(rows, self._table())
        selected_row = next(i for i, r in enumerate(rows) if r.role == "selected")
        if cursor_node_id is not None:
            # try to land on the same node; fall back to previous row position
            found = next(
                (
                    i
                    for i, r in enumerate(rows)
                    if r.node and r.node.node_id == cursor_node_id
                ),
                None,
            )
            target = found if found is not None else min(cursor_row or 0, len(rows) - 1)
        elif cursor_row is not None:
            target = min(cursor_row, len(rows) - 1)
        else:
            target = selected_row
        self._table().move_cursor(row=max(0, target), column=col)

    # ── Navigation ─────────────────────────────────────────────────────────────

    def _navigate_to(self, node_id: str) -> None:
        self.history.append(self.current_node_id)
        self._show_node(node_id)

    _NON_NODE_KEYS = {"__home__"}

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        row_key = str(event.row_key.value)
        if row_key not in self._NON_NODE_KEYS:
            return
        t = self._table()
        row = event.cursor_row
        # skip sentinel (row 0) → go down
        if row == 0:
            t.move_cursor(row=1)

    def on_data_table_cell_selected(self, event: DataTable.CellSelected) -> None:
        if not self._table().has_focus:
            return
        row_key = str(event.cell_key.row_key.value)
        if row_key == "__home__":
            self.action_go_home()
        elif row_key in self.graph.nodes and row_key != self.current_node_id:
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
        if col_key == "pulse":
            self.push_screen(
                UpdateModal(node), lambda r: self._on_update_done(r, row_key, saved_row)
            )
        elif col_key == "target":
            self.push_screen(
                TargetModal(node), lambda r: self._on_target_done(r, row_key, saved_row)
            )
        else:
            self.push_screen(
                EditModal(node, col_key),
                lambda r: self._on_edit_done(r, row_key, saved_row),
            )

    def _on_edit_done(
        self, result: Optional[dict], row_key: str, cursor_row: int
    ) -> None:
        t = self._table()
        if result is None:
            t.move_cursor(row=cursor_row)
            t.focus()
            return
        node = self.graph.get_node(row_key)
        setattr(node, result["attr"], result["value"])
        save_node_fields(node)
        if self.current_node_id is None:
            self._show_home(cursor_row=cursor_row)
        else:
            self._show_node(
                self.current_node_id, cursor_row=cursor_row, cursor_node_id=row_key
            )
        t.focus()

    def _on_target_done(
        self, result: Optional[dict], row_key: str, cursor_row: int
    ) -> None:
        t = self._table()
        if result is None:
            t.focus()
            return
        node = self.graph.get_node(row_key)
        action = result["action"]
        if action == "update_target":
            node.estimated_closing_date = result["estimated_closing_date"]
        elif action == "close":
            node.closed_at = result.get("closed_at") or date.today().isoformat()
            node.close_reason = result.get("reason", "done")
        elif action == "update_closed_at":
            if result.get("closed_at"):
                node.closed_at = result["closed_at"]
        elif action == "reopen":
            node.closed_at = None
            node.close_reason = None
        save_node_fields(node)
        from pfq.model import compute_lifecycle

        compute_lifecycle(self.graph)
        if self.current_node_id is None:
            self._show_home(cursor_row=cursor_row)
        else:
            self._show_node(
                self.current_node_id, cursor_row=cursor_row, cursor_node_id=row_key
            )
        t.focus()

    def _on_update_done(
        self, result: Optional[dict], row_key: str, cursor_row: int
    ) -> None:
        t = self._table()
        if result is None:
            t.focus()
            return
        node = self.graph.get_node(row_key)
        node.opened_at = result["opened_at"]
        node.update_period = result["update_period"]
        save_node_fields(node)
        from pfq.model import compute_lifecycle

        compute_lifecycle(self.graph)
        if self.current_node_id is None:
            self._show_home(cursor_row=cursor_row)
        else:
            self._show_node(
                self.current_node_id, cursor_row=cursor_row, cursor_node_id=row_key
            )
        t.focus()

    # ── Append ─────────────────────────────────────────────────────────────────

    def action_append_node(self) -> None:
        """Append a new node relative to the cursor.

        Home view: create root (no mode choice).
        Any node row: child mode puts new node under cursor; sibling mode puts it
        beside cursor (under cursor's parent, or as a new root if cursor is root).
        Default mode: child for parent/selected rows, sibling for child rows.
        """
        t = self._table()

        if not t.is_valid_coordinate(t.cursor_coordinate):
            self.push_screen(CreateModal("", show_mode=False), self._on_create_root)
            return

        row_key = str(t.coordinate_to_cell_key(t.cursor_coordinate).row_key.value)
        focused_row = next(
            (r for r in self._last_view if r.node and r.node.node_id == row_key), None
        )

        if focused_row is None or row_key not in self.graph.nodes:
            # No real node under cursor (home sentinel, empty vault, …) → create root
            self.push_screen(CreateModal("", show_mode=False), self._on_create_root)
            return

        cursor_node_id = row_key
        cursor_label = focused_row.node.description or row_key

        # For sibling mode: the parent of the cursor node
        if focused_row.role == "child":
            sibling_parent_id = focused_row.visible_parent_id or self.current_node_id
            default_mode = "sibling"
        else:  # parent or selected row
            parents = self.graph.get_parent_ids(cursor_node_id)
            sibling_parent_id = parents[0] if parents else None  # None → cursor is root
            default_mode = "child"

        def _on_done(result, *, _cursor=cursor_node_id, _sib_parent=sibling_parent_id):
            self._on_create_child_with_mode(result, _cursor, _sib_parent)

        self.push_screen(
            CreateModal(cursor_label, mode=default_mode),
            _on_done,
        )

    def _on_create_root(self, result: Optional[dict]) -> None:
        if not result:
            return
        node = create_node(result["description"], self.vault_path)
        self.graph.add_node(node)
        self._show_home()

    def _on_create_child_with_mode(
        self,
        result: Optional[dict],
        cursor_node_id: str,
        sibling_parent_id: Optional[str],
    ) -> None:
        """Create a new node as child of cursor, or sibling of cursor (under sibling_parent_id)."""
        if not result:
            return
        mode = result.get("mode", "child")
        node = create_node(result["description"], self.vault_path)
        self.graph.add_node(node)

        if mode == "child":
            position = len(self.graph.get_children_ids(cursor_node_id))
            self.graph.link_child(cursor_node_id, node.node_id, position)
        else:  # sibling
            if sibling_parent_id is not None:
                siblings = self.graph.get_children_ids(sibling_parent_id)
                position = (
                    siblings.index(cursor_node_id) + 1
                    if cursor_node_id in siblings
                    else len(siblings)
                )
                self.graph.link_child(sibling_parent_id, node.node_id, position)
            # else: cursor is a root → new node is also an unlinked root (no link needed)

        if result.get("close"):
            node.closed_at = date.today().isoformat()
            node.close_reason = "done"
            save_node_fields(node)
            from pfq.model import compute_lifecycle

            compute_lifecycle(self.graph)
        save_vault(self.graph)
        if self.current_node_id is None:
            self._show_home()
        else:
            self._show_node(self.current_node_id)

    # ── Link ───────────────────────────────────────────────────────────────────

    def action_link_parent(self) -> None:
        if self.current_node_id is None:
            return
        t = self._table()
        row_key = str(t.coordinate_to_cell_key(t.cursor_coordinate).row_key.value)
        if row_key not in self.graph.nodes:
            return
        node_label = self.graph.get_node(row_key).description or row_key
        self.push_screen(
            NodePickerModal(
                self.graph,
                allow_create=True,
                exclude_id=row_key,
                show_direction=True,
                node_label=node_label,
            ),
            lambda result: self._on_link_done(result, row_key),
        )

    def _on_link_done(self, result: Optional[dict], node_id: str) -> None:
        if result is None:
            return
        direction = result.get("direction", "parent")
        if result["action"] == "create":
            other = create_node(result["description"], self.vault_path)
            self.graph.add_node(other)
            other_id = other.node_id
        else:
            other_id = result["node_id"]
        if direction == "parent":
            # node_id becomes child of other_id
            self.graph.link_child(
                other_id, node_id, len(self.graph.get_children_ids(other_id))
            )
        else:
            # node_id becomes parent of other_id
            self.graph.link_child(
                node_id, other_id, len(self.graph.get_children_ids(node_id))
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
        parent_id = next(
            (
                r.visible_parent_id
                for r in self._last_view
                if r.node and r.node.node_id == row_key and r.role == "child"
            ),
            None,
        )
        if parent_id is None:
            return
        self.graph.reorder_child(parent_id, row_key, delta)
        save_vault(self.graph)
        rows = build_node_view(self.graph, self.current_node_id)
        new_pos = next(
            (i for i, r in enumerate(rows) if r.node and r.node.node_id == row_key),
            None,
        )
        self._show_node(self.current_node_id, cursor_row=new_pos)

    def action_reorder_up(self) -> None:
        self._action_reorder(-1)

    def action_reorder_down(self) -> None:
        self._action_reorder(1)

    # ── Jump ───────────────────────────────────────────────────────────────────

    def action_jump(self) -> None:
        def _on_jump(result: Optional[dict]) -> None:
            if result:
                self._navigate_to(result["node_id"])

        self.push_screen(NodePickerModal(self.graph), _on_jump)

    # ── Yank ───────────────────────────────────────────────────────────────────

    def action_yank_view(self) -> None:
        try:
            import pyperclip
        except ImportError:
            self.notify(
                "pyperclip not installed — run: pip install pyperclip", severity="error"
            )
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

    def action_toggle_help(self) -> None:
        self.push_screen(HelpModal())

    def action_toggle_companion(self) -> None:
        panel = self.query_one("#companion", CompanionPanel)
        panel.toggle_class("visible")
        if panel.has_class("visible"):
            panel.start_thinking()
        else:
            panel.stop_thinking()

    # ── Delete ─────────────────────────────────────────────────────────────────

    def action_delete(self) -> None:
        t = self._table()
        row_key = str(t.coordinate_to_cell_key(t.cursor_coordinate).row_key.value)
        if row_key == "__home__" or row_key not in self.graph.nodes:
            return

        focused_row = next(
            (r for r in self._last_view if r.node and r.node.node_id == row_key), None
        )
        if focused_row is None:
            return

        if focused_row.role == "sentinel":
            return

        node = self.graph.get_node(row_key)
        node_label = node.description or row_key

        # unlink_pair: (parent_id, child_id) of the link to cut, or None
        if focused_row.role == "child" and focused_row.visible_parent_id:
            unlink_pair = (focused_row.visible_parent_id, row_key)
        elif focused_row.role == "parent" and self.current_node_id:
            unlink_pair = (row_key, self.current_node_id)
        else:
            unlink_pair = None

        saved_cursor_row = self._table().cursor_coordinate.row

        options = self._build_delete_options(row_key, unlink_pair)
        self.push_screen(
            DeleteModal(node_label, options),
            lambda result: self._on_delete_done(
                result, row_key, unlink_pair, saved_cursor_row
            ),
        )

    def _build_delete_options(self, node_id: str, unlink_pair: Optional[tuple]) -> list:
        options = []

        if unlink_pair is not None:
            parent_id, child_id = unlink_pair
            other_id = child_id if child_id != node_id else parent_id
            other_label = self.graph.get_node(other_id).description or other_id
            options.append(
                {
                    "key": "unlink",
                    "label": f'Unlink from "{other_label}"',
                    "detail": "Both nodes stay — only this link is removed.",
                    "nodes": [],
                }
            )

        orphans = [
            self.graph.get_node(nid).description or nid
            for nid in self.graph.get_children_ids(node_id)
            if len(self.graph.get_parent_ids(nid)) == 1
        ]
        orphan_note = (
            f"{len(orphans)} {'child' if len(orphans) == 1 else 'children'} will become unanchored."
            if orphans
            else "No other nodes affected."
        )
        options.append(
            {
                "key": "node",
                "label": "Delete node",
                "detail": orphan_note,
                "nodes": [],
            }
        )

        soft_set = self.graph.deletion_set(node_id, "soft")
        if len(soft_set) > 1:
            soft_nodes = [
                self.graph.get_node(nid).description or nid
                for nid in soft_set
                if nid != node_id
            ]
            options.append(
                {
                    "key": "soft",
                    "label": f"Delete + remove unanchored  ({len(soft_set)} nodes)",
                    "detail": "Also removes nodes that would lose all paths to a root.",
                    "nodes": soft_nodes,
                }
            )

        hard_set = self.graph.deletion_set(node_id, "hard")
        if len(hard_set) > 1:
            hard_nodes = [
                self.graph.get_node(nid).description or nid
                for nid in hard_set
                if nid != node_id
            ]
            options.append(
                {
                    "key": "hard",
                    "label": f"Delete subtree  ({len(hard_set)} nodes)",
                    "detail": "Removes all descendants regardless of other parents.",
                    "nodes": hard_nodes,
                }
            )

        return options

    def _on_delete_done(
        self,
        result: Optional[str],
        node_id: str,
        unlink_pair: Optional[tuple],
        cursor_row: int,
    ) -> None:
        if result is None:
            return

        if result == "unlink":
            if unlink_pair is None:
                return
            parent_id, child_id = unlink_pair
            self.graph.unlink_child(parent_id, child_id)
            save_vault(self.graph)
            # node stays in graph — seek it by id; cursor_row is the fallback
            self._show_node(
                self.current_node_id, cursor_row=cursor_row, cursor_node_id=node_id
            )
            return

        if result == "node":
            self._delete_nodes({node_id}, cursor_row)
            return

        if result in ("soft", "hard"):
            self._delete_nodes(self.graph.deletion_set(node_id, result), cursor_row)
            return

    # ── Sync ───────────────────────────────────────────────────────────────────

    def action_request_quit(self) -> None:
        if not self._sync_enabled:
            self.exit()
            return
        has_changes = has_uncommitted_changes(self.vault_path)
        self.push_screen(SyncModal(has_changes), self._on_sync_quit_done)

    def _on_sync_quit_done(self, result: Optional[str]) -> None:
        if result is None:
            return  # cancelled
        if result == "sync_quit":
            sync_result = commit_and_push(self.vault_path)
            if not sync_result.ok:
                self.notify(f"Sync failed: {sync_result.message}", severity="warning")
                self._update_header("fail")
                return  # stay in app so user sees the error
        self.exit()

    def action_sync(self) -> None:
        if not self._sync_enabled:
            self.notify("No git remote configured for this vault", severity="warning")
            return
        result = commit_and_push(self.vault_path)
        if result.ok:
            self.notify(result.message)
            self._update_header("ok")
        else:
            self.notify(f"Sync failed: {result.message}", severity="warning")
            self._update_header("fail")

    def _delete_nodes(self, node_ids: set, cursor_row: int = 0) -> None:
        navigating_away = self.current_node_id in node_ids
        for nid in node_ids:
            node = self.graph.get_node(nid)
            self.graph.remove_node(nid)
            delete_node_file(node)
        save_vault(self.graph)
        if navigating_away:
            prev = next(
                (
                    p
                    for p in reversed(self.history)
                    if p is not None and p not in node_ids
                ),
                None,
            )
            self.history = [p for p in self.history if p not in node_ids]
            if prev and prev in self.graph.nodes:
                self._show_node(prev)
            else:
                self._show_home()
        elif self.current_node_id is None:
            self._show_home(cursor_row=cursor_row)
        else:
            self._show_node(self.current_node_id, cursor_row=cursor_row)
