"""Modal screens for pfq."""
from __future__ import annotations

from typing import Optional

from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import DataTable, Input, Label, Select, Static, TextArea

from pfq.config import FIELDS, LEAF_STATUSES, NODE_STATUSES, STATUS_GLYPHS, STATUS_STYLES
from pfq.model import Event, Node, NodeGraph

# Shared CSS for the title-bar modal pattern
_MODAL_BASE_CSS = """
    {cls} {{
        align: center middle;
    }}
    {cls} #dialog {{
        background: $background;
        border-left: tall $primary;
        border-right: tall $primary;
        border-bottom: tall $primary;
        padding: 0 0 1 0;
        height: auto;
    }}
    {cls} #modal-title {{
        background: $primary;
        color: $background;
        padding: 0 2;
        width: 1fr;
        height: 1;
        margin-bottom: 1;
    }}
    {cls} #dialog-body {{
        padding: 0 2;
        height: auto;
    }}
    {cls} #widget {{
        border: tall $primary-darken-2;
        background: $panel;
    }}
    {cls} #widget:focus {{
        border: tall $primary;
    }}
    {cls} #hint {{
        color: $text-muted;
        margin-top: 1;
    }}
"""

# ── Create ─────────────────────────────────────────────────────────────────────


class CreateModal(ModalScreen):
    """Prompt for a description, then dismiss with the string (or None on cancel)."""

    CSS = _MODAL_BASE_CSS.format(cls="CreateModal") + """
    CreateModal #dialog {
        width: 52;
    }
    """
    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def __init__(self, parent_label: str):
        super().__init__()
        self.parent_label = parent_label

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label(f"Create  {self._short_label()}", id="modal-title")
            with Vertical(id="dialog-body"):
                yield Input(placeholder="Description…", id="widget")

    def _short_label(self) -> str:
        label = self.parent_label or ""
        return ("under " + (label[:28] + "…" if len(label) > 28 else label)) if label else ""

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
    DeleteModal #dialog {
        background: $background;
        border-left: tall $error;
        border-right: tall $error;
        border-bottom: tall $error;
        padding: 0 0 1 0;
        width: 62;
        height: auto;
    }

    DeleteModal #modal-title {
        background: $error;
        color: $background;
        padding: 0 2;
        width: 1fr;
        height: 1;
        margin-bottom: 1;
    }
    DeleteModal #dialog-body {
        padding: 0 2;
        height: auto;
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
    DeleteModal #hint {
        color: $text-muted;
        margin-top: 1;
    }
    #confirm-dialog {
        background: $background;
        border-left: tall $error;
        border-right: tall $error;
        border-bottom: tall $error;
        padding: 0 0 1 0;
        width: 60;
        height: auto;
    }
    #confirm-modal-title {
        background: $error;
        color: $background;
        padding: 0 2;
        width: 1fr;
        height: 1;
        margin-bottom: 1;
    }
    #confirm-body {
        padding: 0 2;
        height: auto;
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
            yield Label(f"Delete  {self.node_label}", id="modal-title")
            with Vertical(id="dialog-body"):
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
                    yield Label(f"Confirm  {opt['label']}", id="confirm-modal-title")
                    with Vertical(id="confirm-body"):
                        yield Label(msg, id="confirm-title")
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
    """Fuzzy node search with grouped results and optional direction toggle.

    Dismisses with:
      {"action": "pick",   "node_id": str,      "direction": "parent"|"child"}
      {"action": "create", "description": str,  "direction": "parent"|"child"}
        — create only when allow_create=True
      None — cancelled
    """

    CSS = _MODAL_BASE_CSS.format(cls="NodePickerModal") + """
    NodePickerModal #dialog {
        width: 68;
        height: 24;
    }
    NodePickerModal #dialog-body {
        height: 1fr !important;
    }
    NodePickerModal #dir-label {
        color: $text-disabled;
        margin-top: 1;
    }
    NodePickerModal #direction {
        height: 1;
        margin-top: 0;
        margin-bottom: 1;
    }
    NodePickerModal #dir-parent, NodePickerModal #dir-child {
        width: 1fr;
        padding: 0 1;
        background: $surface;
        color: $text-disabled;
        border: none;
    }
    NodePickerModal #dir-parent.--active, NodePickerModal #dir-child.--active {
        background: $surface-lighten-1;
        color: $text;
        text-style: bold;
    }
    NodePickerModal #results {
        height: 1fr;
        overflow-y: auto;
        overflow-x: hidden;
        margin-top: 1;
        background: $background;
    }
    NodePickerModal #results > .datatable--cursor {
        background: #2e2600;
        color: #f0ead0;
    }
    NodePickerModal #hint {
        height: 1;
    }
    """
    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("up", "move_up", "Up", show=False),
        Binding("down", "move_down", "Down", show=False),
        Binding("tab", "toggle_direction", "Toggle direction", show=False),
    ]

    def __init__(
        self,
        graph: NodeGraph,
        *,
        allow_create: bool = False,
        exclude_id: Optional[str] = None,
        show_direction: bool = False,
        initial_direction: str = "parent",
        node_label: str = "",
    ):
        super().__init__()
        self.graph = graph
        self.allow_create = allow_create
        self.exclude_id = exclude_id
        self.show_direction = show_direction
        self._direction: str = initial_direction
        self.node_label = node_label
        self._matches: list[str] = []
        self._create_shown: bool = False
        self._selected: int = 0

    def _short_label(self) -> str:
        label = self.node_label or self.exclude_id or "node"
        return label[:28] + "…" if len(label) > 28 else label

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label(f"Link  {self._short_label()}", id="modal-title")
            with Vertical(id="dialog-body"):
                if self.show_direction:
                    yield Label("direction  [Tab]", id="dir-label")
                    with Horizontal(id="direction"):
                        yield Static(id="dir-parent")
                        yield Static(id="dir-child")
                yield Input(placeholder="› search nodes…", id="widget")
                yield DataTable(cursor_type="row", show_header=False, id="results")
                yield Label("↑↓ select  Enter confirm  Esc cancel", id="hint")

    def on_mount(self) -> None:
        t = self.query_one("#results", DataTable)
        t.add_column("row", width=62)
        self.query_one("#widget", Input).focus()
        self._refresh_direction()
        self._update_results("")

    def _refresh_direction(self) -> None:
        if not self.show_direction:
            return
        name = self._short_label()
        self.query_one("#dir-parent", Static).update(f"↑ ___  →  {name}")
        self.query_one("#dir-child",  Static).update(f"↓ {name}  →  ___")
        self.query_one("#dir-parent").set_class(self._direction == "parent", "--active")
        self.query_one("#dir-child").set_class(self._direction == "child",  "--active")

    def action_toggle_direction(self) -> None:
        if not self.show_direction:
            return
        self._direction = "child" if self._direction == "parent" else "parent"
        self._refresh_direction()

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
            self.dismiss({"action": "create", "description": query, "direction": self._direction})
        else:
            self.dismiss({"action": "pick", "node_id": self._matches[self._selected], "direction": self._direction})

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

    CSS = _MODAL_BASE_CSS.format(cls="StatusModal") + """
    StatusModal #dialog {
        width: 62;
    }
    StatusModal #node-desc {
        margin-bottom: 1;
    }
    StatusModal #widget {
        margin-bottom: 1;
    }
    StatusModal #columns {
        height: auto;
        margin-bottom: 1;
    }
    StatusModal .col-header {
        color: $text-disabled;
        text-style: dim;
        width: 1fr;
    }
    StatusModal .col-body {
        width: 1fr;
        height: auto;
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
            yield Label("Set status", id="modal-title")
            with Vertical(id="dialog-body"):
                yield Label(f"{bullet}  {self.node.description or ''}", id="node-desc")
                yield Input(value=self.node.status or "", placeholder="filter…", id="widget")
                with Horizontal(id="columns"):
                    for i, (header, _) in enumerate(_COLUMNS):
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

    CSS = _MODAL_BASE_CSS.format(cls="EditModal") + """
    EditModal #dialog {
        width: 52;
    }
    EditModal TextArea {
        height: 8;
        border: tall $primary-darken-2;
        background: $panel;
    }
    EditModal TextArea:focus {
        border: tall $primary;
    }
    """
    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("ctrl+s", "submit_textarea", "Save", show=False),
    ]

    def __init__(self, node: Node, col_key: str):
        super().__init__()
        self.node = node
        self.col_key = col_key
        self.field = FIELDS[col_key]

    def compose(self) -> ComposeResult:
        current = getattr(self.node, self.field["attr"]) or ""
        with Vertical(id="dialog"):
            yield Label(f"Edit  {self.field['label']}", id="modal-title")
            with Vertical(id="dialog-body"):
                if self.field["kind"] == "select":
                    options = self.field["options"]
                    extra = {"value": current} if current in options else {}
                    yield Select([(o, o) for o in options], allow_blank=True, id="widget", **extra)
                elif self.field["kind"] == "textarea":
                    yield TextArea(current, id="widget")
                    yield Static("[dim]ctrl+s  save  [/][dim]esc  cancel[/]", id="hint", markup=True)
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

    def action_submit_textarea(self) -> None:
        if self.field["kind"] == "textarea":
            value = self.query_one("#widget", TextArea).text.strip()
            self._dismiss_with_value(value)

    def action_cancel(self) -> None:
        self.dismiss(None)


# ── Timeline ───────────────────────────────────────────────────────────────────


class EventEditModal(ModalScreen):
    """Edit or create a single Event (date, type, text)."""

    CSS = _MODAL_BASE_CSS.format(cls="EventEditModal") + """
    EventEditModal #dialog { width: 56; }
    EventEditModal Input { margin-bottom: 1; }
    """
    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def __init__(self, event: Optional[Event] = None):
        super().__init__()
        self._event = event

    def compose(self) -> ComposeResult:
        e = self._event
        title = "Edit event" if e else "Add event"
        with Vertical(id="dialog"):
            yield Label(title, id="modal-title")
            with Vertical(id="dialog-body"):
                yield Input(value=e.date or "" if e else "", placeholder="date  e.g. 2026-04-21 / april 2027", id="inp-date")
                yield Input(value=e.type or "" if e else "", placeholder="type  e.g. journal / due_date", id="inp-type")
                yield Input(value=e.text or "" if e else "", placeholder="description (optional)", id="inp-text")
                yield Static("[dim]Enter  save   Esc  cancel[/]", id="hint", markup=True)

    def on_mount(self) -> None:
        self.query_one("#inp-date", Input).focus()

    def on_input_submitted(self, _: Input.Submitted) -> None:
        raw = self.query_one("#inp-date", Input).value.strip() or None
        type_val = self.query_one("#inp-type", Input).value.strip() or "journal"
        text_val = self.query_one("#inp-text", Input).value.strip() or None
        date_iso, when = self._resolve_date(raw)
        self.dismiss(Event(type=type_val, date=date_iso, when=when, text=text_val))

    @staticmethod
    def _resolve_date(raw: Optional[str]):
        if not raw:
            return None, None
        from datetime import date as _date
        try:
            _date.fromisoformat(raw)
            return raw, None  # already ISO — no need to store when
        except ValueError:
            pass
        import dateparser
        dt = dateparser.parse(raw, settings={"RETURN_AS_TIMEZONE_AWARE": False, "PREFER_DAY_OF_MONTH": "first"})
        if dt:
            return dt.date().isoformat(), raw
        return None, raw  # unparseable — store as when only

    def action_cancel(self) -> None:
        self.dismiss(None)


class TimelineModal(ModalScreen):
    """Browse and edit the timeline of a node.

    Dismisses with the updated list[Event] (possibly unchanged), or None on cancel.
    """

    CSS = _MODAL_BASE_CSS.format(cls="TimelineModal") + """
    TimelineModal #dialog {
        width: 72;
        height: 24;
    }
    TimelineModal #dialog-body {
        height: 1fr !important;
    }
    TimelineModal #table {
        height: 1fr;
        background: $background;
    }
    TimelineModal #hint { height: 1; }
    """
    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("e", "edit_event", "Edit", show=True),
        Binding("a", "add_event", "Add", show=True),
        Binding("D", "delete_event", "Delete", show=True),
    ]

    def __init__(self, node: Node):
        super().__init__()
        self.node = node
        self._events: list[Event] = list(node.timeline)

    def compose(self) -> ComposeResult:
        label = (self.node.description or self.node.node_id)[:40]
        with Vertical(id="dialog"):
            yield Label(f"Timeline  {label}", id="modal-title")
            with Vertical(id="dialog-body"):
                yield DataTable(cursor_type="row", show_header=True, id="table")
                yield Static("[dim]e edit   a add   D delete   Esc close[/]", id="hint", markup=True)

    def on_mount(self) -> None:
        t = self.query_one("#table", DataTable)
        t.add_column("date", key="date", width=16)
        t.add_column("parsed", key="parsed", width=12)
        t.add_column("type", key="type", width=12)
        t.add_column("description", key="desc", width=28)
        self._rebuild()
        t.focus()

    def _sorted_events(self) -> list[tuple[int, Event]]:
        def sort_key(pair):
            _, e = pair
            return (e.date is None, e.date or "")
        return sorted(enumerate(self._events), key=sort_key)

    def _rebuild(self) -> None:
        t = self.query_one("#table", DataTable)
        t.clear()
        pairs = self._sorted_events()
        for orig_idx, e in pairs:
            display = e.when if e.when else (e.date or "")
            resolved = Text(e.date or "?", style="dim" if e.date else "dim red")
            desc_parts = []
            if e.text:
                desc_parts.append(e.text)
            for k, v in e.extra.items():
                desc_parts.append(f"{k}: {v}")
            desc_text = Text(", ".join(desc_parts) if desc_parts else "")
            t.add_row(Text(display), resolved, Text(e.type), desc_text, key=str(orig_idx))

    def _focused_orig_idx(self) -> Optional[int]:
        t = self.query_one("#table", DataTable)
        if t.row_count == 0:
            return None
        try:
            key = t.coordinate_to_cell_key(t.cursor_coordinate).row_key.value
            return int(key)
        except Exception:
            return None

    def action_edit_event(self) -> None:
        orig_idx = self._focused_orig_idx()
        if orig_idx is None:
            return
        event = self._events[orig_idx]

        def _on_done(result: Optional[Event]) -> None:
            if result is not None:
                self._events[orig_idx] = result
                self._rebuild()
            self.query_one("#table", DataTable).focus()

        self.app.push_screen(EventEditModal(event), _on_done)

    def action_add_event(self) -> None:
        def _on_done(result: Optional[Event]) -> None:
            if result is not None:
                self._events.append(result)
                self._rebuild()
            self.query_one("#table", DataTable).focus()

        self.app.push_screen(EventEditModal(), _on_done)

    def action_delete_event(self) -> None:
        orig_idx = self._focused_orig_idx()
        if orig_idx is None:
            return
        self._events.pop(orig_idx)
        self._rebuild()

    def action_cancel(self) -> None:
        self.dismiss(self._events)
