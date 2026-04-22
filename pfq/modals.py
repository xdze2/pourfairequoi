"""Modal screens for pfq."""
from __future__ import annotations

from typing import Optional

from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import DataTable, Input, Label, Select, Static

from pfq.config import FIELDS, LEAF_STATUSES, NODE_STATUSES, STATUS_GLYPHS, STATUS_STYLES
from pfq.model import Node, NodeGraph

# ── Create ─────────────────────────────────────────────────────────────────────


class CreateModal(ModalScreen):
    """Prompt for a description, then dismiss with the string (or None on cancel)."""

    CSS = """
    CreateModal {
        align: center middle;
    }
    #dialog {
        background: #1e1a00;
        border: round #7a6000;
        padding: 1 2;
        width: 52;
        height: auto;
    }
    #dialog Label {
        color: $text-muted;
        margin-bottom: 1;
    }
    #widget {
        border: tall #7a6000;
    }
    #widget:focus {
        border: tall #c8a000;
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


# ── Delete ─────────────────────────────────────────────────────────────────────


class DeleteModal(ModalScreen):
    """Multi-choice delete/unlink modal.

    options: list of dicts with keys:
        key       str   action identifier returned on confirm
        label     str   short title
        detail    str   consequence description
        nodes     list[str]  node descriptions affected (shown for soft/hard)

    Navigated with ↑↓, confirmed with Enter. soft/hard ask a second confirmation.
    Dismisses with the chosen option key, or None on cancel.
    """

    CSS = """
    DeleteModal {
        align: center middle;
    }
    #dialog {
        background: $background;
        border: round $error;
        padding: 1 2;
        width: 62;
        height: auto;
    }
    #title {
        color: $error;
        text-style: bold;
        margin-bottom: 1;
    }
    .option {
        border: round $surface-lighten-2;
        padding: 0 1;
        margin-bottom: 1;
        height: auto;
    }
    .option.--selected {
        border: round $error;
        background: $surface-lighten-1;
    }
    .option-label {
        color: $text;
        text-style: bold;
        margin-top: 0;
    }
    .option-detail {
        color: $text-muted;
        padding-left: 1;
    }
    .option-nodes {
        color: $text-disabled;
        padding-left: 1;
    }
    #hint {
        color: $text-muted;
        margin-top: 1;
    }
    #confirm-dialog {
        background: $background;
        border: round $error;
        padding: 1 2;
        width: 60;
        height: auto;
    }
    #confirm-title {
        margin-bottom: 1;
    }
    #confirm-hint {
        color: $text-muted;
        margin-top: 1;
    }
    """
    BINDINGS = [
        Binding("up", "move_up", "Up", show=False),
        Binding("down", "move_down", "Down", show=False),
        Binding("enter", "confirm", "Confirm"),
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(self, node_label: str, options: list[dict]):
        super().__init__()
        self.node_label = node_label
        self.options = options
        self._selected = 0
        self._confirming = False

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label(f"Delete  {self.node_label}", id="title")
            for i, opt in enumerate(self.options):
                with Vertical(classes="option", id=f"opt-{i}"):
                    yield Static(opt["label"], id=f"opt-label-{i}", classes="option-label")
                    yield Static(opt["detail"], classes="option-detail")
                    if opt.get("nodes"):
                        preview = opt["nodes"][:5]
                        extra = len(opt["nodes"]) - len(preview)
                        lines = "\n".join(f"  ○ {n}" for n in preview)
                        if extra:
                            lines += f"\n  … and {extra} more"
                        yield Static(lines, classes="option-nodes")
            yield Static("[dim]↑↓ select   Enter confirm   Esc cancel[/]", id="hint", markup=True)

    def on_mount(self) -> None:
        self._refresh()

    def _refresh(self) -> None:
        for i in range(len(self.options)):
            container = self.query_one(f"#opt-{i}", Vertical)
            if i == self._selected:
                container.add_class("--selected")
            else:
                container.remove_class("--selected")

    def action_move_up(self) -> None:
        self._selected = (self._selected - 1) % len(self.options)
        self._refresh()

    def action_move_down(self) -> None:
        self._selected = (self._selected + 1) % len(self.options)
        self._refresh()

    def action_confirm(self) -> None:
        opt = self.options[self._selected]
        if opt["key"] in ("soft", "hard") and not self._confirming:
            self._confirming = True
            self._show_confirmation(opt)
        else:
            self.dismiss(opt["key"])

    def _show_confirmation(self, opt: dict) -> None:
        n = len(opt.get("nodes", []))
        msg = f"Delete {n} node{'s' if n != 1 else ''}? This cannot be undone."

        class ConfirmScreen(ModalScreen):
            BINDINGS = [
                Binding("enter", "yes", "Yes"),
                Binding("escape", "no", "Cancel"),
            ]

            def compose(self_inner) -> ComposeResult:
                with Vertical(id="confirm-dialog"):
                    yield Label(f"[bold red]{opt['label']}[/]  —  {msg}", id="confirm-title", markup=True)
                    yield Static("[dim]Enter confirm   Esc cancel[/]", id="confirm-hint", markup=True)

            def action_yes(self_inner) -> None:
                self_inner.dismiss(True)

            def action_no(self_inner) -> None:
                self_inner.dismiss(False)

        def _on_confirm(result: bool) -> None:
            self._confirming = False
            if result:
                self.dismiss(opt["key"])

        self.app.push_screen(ConfirmScreen(), _on_confirm)

    def action_cancel(self) -> None:
        self.dismiss(None)


# ── NodePickerModal ─────────────────────────────────────────────────────────────


class NodePickerModal(ModalScreen):
    """Fuzzy node search with grouped results.

    Dismisses with:
      {"action": "pick",   "node_id": str}   — a node was selected
      {"action": "create", "description": str} — only when allow_create=True
      None                                    — cancelled
    """

    CSS = """
    NodePickerModal {
        align: center middle;
    }
    #dialog {
        background: $background;
        border: round $primary;
        padding: 1 2;
        width: 68;
        height: 24;
    }
    #results {
        height: 1fr;
        overflow-y: auto;
        overflow-x: hidden;
        margin-top: 1;
        background: $background;
    }
    #results > .datatable--cursor {
        background: #2e2600;
        color: #f0ead0;
    }
    #hint {
        color: $text-muted;
        height: 1;
        margin-top: 1;
    }
    #widget {
        border: tall $primary-darken-2;
        background: $panel;
    }
    #widget:focus {
        border: tall $primary;
    }
    """
    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("up", "move_up", "Up", show=False),
        Binding("down", "move_down", "Down", show=False),
    ]

    def __init__(
        self,
        graph: NodeGraph,
        *,
        placeholder: str = "› search nodes…",
        allow_create: bool = False,
        exclude_id: Optional[str] = None,
    ):
        super().__init__()
        self.graph = graph
        self.placeholder = placeholder
        self.allow_create = allow_create
        self.exclude_id = exclude_id
        self._matches: list[str] = []   # selectable node_ids in order
        self._create_shown: bool = False
        self._selected: int = 0         # index into _matches, or len(_matches) = "create"

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Input(placeholder=self.placeholder, id="widget")
            yield DataTable(cursor_type="row", show_header=False, id="results")
            yield Label("↑↓ select  Enter confirm  Esc cancel", id="hint")

    def on_mount(self) -> None:
        t = self.query_one("#results", DataTable)
        t.add_column("row", width=62)
        self.query_one("#widget", Input).focus()
        self._update_results("")

    def _build_row_text(self, node_id: str, *, is_last: bool) -> Text:
        node = self.graph.get_node(node_id)
        desc = node.description or node_id
        status = node.status or ""
        glyph = STATUS_GLYPHS.get(status, "")
        status_color = STATUS_STYLES.get(status, "#888888")

        connector = "╰── " if is_last else "├── "
        row = Text(overflow="ellipsis", no_wrap=True)
        row.append(connector, style="dim")
        max_desc = 44
        row.append(desc[:max_desc])
        if glyph or status:
            pad = max(1, max_desc - len(desc[:max_desc]) + 2)
            row.append(" " * pad)
            row.append(f"{glyph} {status}".rstrip() if glyph else status, style=status_color)
        return row

    def _update_results(self, query: str) -> None:
        t = self.query_one("#results", DataTable)
        t.clear()
        self._matches = []
        self._create_shown = False
        self._selected = 0

        if query.strip():
            nodes = [
                n for n in self.graph.search_nodes(query)
                if n.node_id != self.exclude_id
            ][:16]
        else:
            nodes = [
                self.graph.get_node(nid)
                for nid in self.graph.get_roots()
                if nid != self.exclude_id
            ]

        # Group by first parent (None = roots)
        groups: dict[Optional[str], list[str]] = {}
        for node in nodes:
            parent_ids = self.graph.get_parent_ids(node.node_id)
            key = parent_ids[0] if parent_ids else None
            groups.setdefault(key, []).append(node.node_id)

        if self.allow_create and query.strip():
            create_text = Text(overflow="ellipsis", no_wrap=True)
            create_text.append(f'+ Create "{query.strip()}"', style="italic green")
            t.add_row(create_text, key="__create__")
            self._create_shown = True
            if not self._matches:
                self._selected = len(self._matches)  # point at create row

        sep_counter = 0
        for parent_id, node_ids in groups.items():
            if parent_id is None:
                header = Text("@ roots", style="dim")
            else:
                p = self.graph.get_node(parent_id)
                label = (p.description or parent_id)[:54]
                header = Text(label, style="dim")
            t.add_row(header, key=f"__sep__{sep_counter}")
            sep_counter += 1

            for i, node_id in enumerate(node_ids):
                self._matches.append(node_id)
                t.add_row(self._build_row_text(node_id, is_last=(i == len(node_ids) - 1)), key=node_id)

        self._highlight()

    def _total(self) -> int:
        return len(self._matches) + (1 if self._create_shown else 0)

    def _row_key_for_selected(self) -> str:
        if self._selected == len(self._matches) and self._create_shown:
            return "__create__"
        return self._matches[self._selected]

    def _selectable_row_index(self, key: str) -> int:
        t = self.query_one("#results", DataTable)
        try:
            return t.get_row_index(key)
        except Exception:
            return 0

    def _highlight(self) -> None:
        t = self.query_one("#results", DataTable)
        if self._total() == 0 or t.row_count == 0:
            return
        key = self._row_key_for_selected()
        t.move_cursor(row=self._selectable_row_index(key))

    def on_input_changed(self, event: Input.Changed) -> None:
        self._update_results(event.value)

    def on_input_submitted(self, _: Input.Submitted) -> None:
        self.action_confirm()

    def action_move_up(self) -> None:
        if self._total() == 0:
            return
        self._selected = (self._selected - 1) % self._total()
        self._highlight()

    def action_move_down(self) -> None:
        if self._total() == 0:
            return
        self._selected = (self._selected + 1) % self._total()
        self._highlight()

    def action_confirm(self) -> None:
        if self._total() == 0:
            self.dismiss(None)
            return
        if self._selected == len(self._matches) and self._create_shown:
            query = self.query_one("#widget", Input).value.strip()
            self.dismiss({"action": "create", "description": query})
        else:
            self.dismiss({"action": "pick", "node_id": self._matches[self._selected]})

    def action_cancel(self) -> None:
        self.dismiss(None)


# ── Status ─────────────────────────────────────────────────────────────────────

_ROOT_STATUSES = sorted(NODE_STATUSES)
_NODE_STATUSES = sorted(NODE_STATUSES)
_LEAF_STATUSES = sorted(LEAF_STATUSES)

_COLUMNS = [
    ("@ root", _ROOT_STATUSES),
    ("< node", _NODE_STATUSES),
    ("○ leaf", _LEAF_STATUSES),
]


class StatusModal(ModalScreen):
    """Status editor: three role columns with filter input and free-text entry."""

    CSS = """
    StatusModal {
        align: center middle;
    }
    #dialog {
        background: #1e1a00;
        border: round #7a6000;
        padding: 1 2;
        width: 62;
        height: auto;
    }
    #modal-title {
        color: $text-muted;
        margin-bottom: 1;
    }
    #node-desc {
        margin-bottom: 1;
    }
    #widget {
        border: tall #7a6000;
        background: $panel;
        margin-bottom: 1;
    }
    #widget:focus {
        border: tall #c8a000;
    }
    #columns {
        height: auto;
        margin-bottom: 1;
    }
    .col-header {
        color: $text-disabled;
        text-style: dim;
        width: 1fr;
    }
    .col-body {
        width: 1fr;
        height: auto;
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

    def __init__(self, node: Node, graph: NodeGraph):
        super().__init__()
        self.node = node
        self.graph = graph

    def compose(self) -> ComposeResult:
        is_root = len(self.graph.get_parent_ids(self.node.node_id)) == 0
        is_leaf = len(self.graph.get_children_ids(self.node.node_id)) == 0
        bullet = "@" if is_root else ("○" if is_leaf else "<")
        with Vertical(id="dialog"):
            yield Label("Edit status", id="modal-title")
            yield Label(f"{bullet}  {self.node.description or ''}", id="node-desc")
            yield Input(value=self.node.status or "", placeholder="filter…", id="widget")
            with Horizontal(id="columns"):
                for i, (header, statuses) in enumerate(_COLUMNS):
                    with Vertical(classes="col-body"):
                        yield Label(header, classes="col-header")
                        yield Static(id=f"col-{i}")
            yield Static(
                "[dim]\\[enter] confirm  [/][dim]\\[tab] pick  [/][dim]\\[esc] cancel[/]",
                id="hint", markup=True,
            )

    def on_mount(self) -> None:
        self._matches: list[str] = []
        self._selected: Optional[str] = None
        inp = self.query_one("#widget", Input)
        inp.focus()
        self._refresh_columns(inp.value)

    def _refresh_columns(self, query: str) -> None:
        q = query.lower().strip()
        matches = {s for s in STATUS_STYLES if not q or q in s}
        self._matches = [s for s in STATUS_STYLES if s in matches]
        if q and self._matches:
            if self._selected not in self._matches:
                self._selected = self._matches[0]
        else:
            self._selected = None
        for i, (_, statuses) in enumerate(_COLUMNS):
            col_text = Text()
            for s in statuses:
                color = STATUS_STYLES.get(s, "")
                active = s in matches
                if active:
                    prefix = "→ " if s == self._selected else "  "
                    col_text.append(prefix + s, style=color)
                else:
                    col_text.append("  " + s, style=f"{color} strike dim")
                col_text.append("\n")
            self.query_one(f"#col-{i}", Static).update(col_text)

    def on_input_changed(self, event: Input.Changed) -> None:
        self._refresh_columns(event.value)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        value = self._selected or event.value.strip() or None
        self.dismiss({"attr": "status", "value": value})

    def action_pick_suggestion(self) -> None:
        if not self._matches:
            return
        inp = self.query_one("#widget", Input)
        inp.value = self._selected or self._matches[0]
        inp.action_end()

    def action_cancel(self) -> None:
        self.dismiss(None)


# ── Edit ───────────────────────────────────────────────────────────────────────


class EditModal(ModalScreen):
    """Single-field editor. Driven by FIELDS config — no hardcoded field logic."""

    CSS = """
    EditModal {
        align: center middle;
    }
    #dialog {
        background: #1e1a00;
        border: round #7a6000;
        padding: 1 2;
        width: 52;
        height: auto;
    }
    #dialog Label {
        color: $text-muted;
        margin-bottom: 1;
    }
    #hint {
        color: $text-muted;
        margin-top: 1;
    }
    #widget {
        border: tall #7a6000;
    }
    #widget:focus {
        border: tall #c8a000;
    }
    """
    BINDINGS = [Binding("escape", "cancel", "Cancel")]

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
                yield Select([(o, o) for o in options], allow_blank=True, id="widget", **extra)
            else:
                yield Input(value=current, id="widget")
                yield Static("[dim]\\[enter] confirm  [/][dim]\\[esc] cancel[/]", id="hint", markup=True)

    def on_mount(self) -> None:
        self.query_one("#widget").focus()

    def _dismiss_with_value(self, value: Optional[str]) -> None:
        self.dismiss({"attr": self.field["attr"], "value": value or None})

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self._dismiss_with_value(event.value.strip())

    def on_select_changed(self, event: Select.Changed) -> None:
        options = self.field.get("options", [])
        value = event.value if event.value in options else None
        self._dismiss_with_value(value)

    def action_cancel(self) -> None:
        self.dismiss(None)
