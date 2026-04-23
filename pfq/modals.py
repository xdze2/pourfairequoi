"""Modal screens for pfq."""
from __future__ import annotations

from typing import Optional

from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import DataTable, Input, Label, Select, Static, TextArea

from pfq.config import FIELDS
from pfq.model import Node, NodeGraph

# ── Help ───────────────────────────────────────────────────────────────────────

_HELP_BINDINGS = [
    ("navigate", [
        ("Enter / click", "Open node"),
        ("h",             "Home"),
        ("Escape",        "Back"),
        ("s",             "Search / jump"),
    ]),
    ("edit", [
        ("a",             "Append child (or root)"),
        ("e",             "Edit focused cell"),
        ("z",             "Link to parent"),
        ("d",             "Delete / unlink"),
        ("Shift+↑ / ↓",  "Reorder sibling"),
    ]),
    ("view", [
        ("y",             "Copy view to clipboard"),
        ("f2",            "Toggle AI companion"),
        ("F1",            "Toggle this help"),
    ]),
    ("app", [
        ("f5",            "Sync vault (git push/pull)"),
        ("q",             "Quit"),
    ]),
]


class HelpModal(ModalScreen):
    """Keyboard-shortcut reference. Dismiss with Escape, Enter, or F1."""

    CSS = """
    HelpModal {
        align: center middle;
    }
    HelpModal #dialog {
        background: $background;
        border-left: tall $primary;
        border-right: tall $primary;
        border-bottom: tall $primary;
        padding: 0 0 1 0;
        width: 54;
        height: auto;
    }
    HelpModal #modal-title {
        background: $primary;
        color: $background;
        padding: 0 2;
        width: 1fr;
        height: 1;
        margin-bottom: 1;
    }
    HelpModal #dialog-body {
        padding: 0 2;
        height: auto;
    }
    HelpModal .section-header {
        color: $text-muted;
        margin-top: 1;
        text-style: bold;
    }
    HelpModal .binding-row {
        height: 1;
    }
    HelpModal .key-col {
        width: 20;
        color: $primary;
    }
    HelpModal .desc-col {
        width: 1fr;
    }
    HelpModal #hint {
        color: $text-muted;
        margin-top: 1;
    }
    """
    BINDINGS = [
        Binding("escape", "dismiss", "Close"),
        Binding("enter",  "dismiss", "Close"),
        Binding("f1",     "dismiss", "Close"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("Keyboard shortcuts", id="modal-title")
            with Vertical(id="dialog-body"):
                for section, pairs in _HELP_BINDINGS:
                    yield Label(section, classes="section-header")
                    for key, desc in pairs:
                        with Horizontal(classes="binding-row"):
                            yield Label(key,  classes="key-col")
                            yield Label(desc, classes="desc-col")
                yield Label("F1 to close", id="hint")

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
    """Prompt for a description + optional close-immediately toggle.

    Dismisses with {"description": str, "close": bool}, or None on cancel.
    Tab toggles the close checkbox; Enter confirms.
    """

    CSS = _MODAL_BASE_CSS.format(cls="CreateModal") + """
    CreateModal #dialog { width: 52; }
    CreateModal #close-row {
        height: 1;
        margin-top: 1;
    }
    CreateModal #close-box { width: 3; }
    CreateModal #close-label { width: 1fr; }
    CreateModal #hint { margin-top: 1; }
    """
    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def __init__(self, parent_label: str):
        super().__init__()
        self.parent_label = parent_label
        self._close = False

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label(f"Create  {self._short_label()}", id="modal-title")
            with Vertical(id="dialog-body"):
                yield Input(placeholder="Description…", id="widget")
                with Horizontal(id="close-row"):
                    yield Static("[dim][ ][/]", id="close-box", markup=True)
                    yield Static("[dim] close immediately[/]", id="close-label", markup=True)
                yield Static("[dim]Tab  toggle   Enter  confirm   Esc  cancel[/]", id="hint", markup=True)

    def _short_label(self) -> str:
        label = self.parent_label or ""
        return ("under " + (label[:28] + "…" if len(label) > 28 else label)) if label else ""

    def on_mount(self) -> None:
        self.query_one("#widget").focus()

    def _refresh_toggle(self) -> None:
        if self._close:
            self.query_one("#close-box", Static).update("[bold green][x][/]")
            self.query_one("#close-label", Static).update("[bold] close immediately[/]")
        else:
            self.query_one("#close-box", Static).update("[dim][ ][/]")
            self.query_one("#close-label", Static).update("[dim] close immediately[/]")

    def on_key(self, event) -> None:
        if event.key == "tab":
            event.stop()
            self._close = not self._close
            self._refresh_toggle()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        value = event.value.strip()
        if value:
            self.dismiss({"description": value, "close": self._close})
        else:
            self.dismiss(None)

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

        connector = "╰── " if is_last else "├── "
        row = Text(overflow="ellipsis", no_wrap=True)
        row.append(connector, style="dim")
        row.append(desc[:46])
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


# ── Shared date modal helpers ──────────────────────────────────────────────────


def _parse_date(text: str) -> Optional[str]:
    """Parse a loose date string to ISO format, or None if unparseable."""
    from datetime import date as _date
    from pfq.dates import parse_date
    result = parse_date(text, _date.today())
    return result.isoformat() if result else None


_DATE_MODAL_CSS = """
    {cls} #dialog {{ width: 52; }}
    {cls} .field-label {{ color: $text-muted; margin-top: 1; }}
    {cls} .parsed {{ color: $text-muted; margin-top: 0; height: 1; padding-left: 2; }}
    {cls} .parsed.--ok {{ color: $success; }}
    {cls} .parsed.--err {{ color: $error; }}
    {cls} #hint {{ margin-top: 1; }}
"""


def _set_feedback(modal, widget_id: str, text: str, ok: bool) -> None:
    w = modal.query_one(widget_id, Static)
    w.update(text)
    w.set_class(ok, "--ok")
    w.set_class(not ok and bool(text), "--err")


def _refresh_date_feedback(modal, input_id: str, feedback_id: str) -> None:
    value = modal.query_one(input_id, Input).value.strip()
    if not value:
        _set_feedback(modal, feedback_id, "", True)
        return
    parsed = _parse_date(value)
    if parsed:
        _set_feedback(modal, feedback_id, f"→ {parsed}", True)
    else:
        _set_feedback(modal, feedback_id, "? unrecognised", False)


# ── Target (target date + lifecycle) ──────────────────────────────────────────


class TargetModal(ModalScreen):
    """Combined target date + lifecycle modal.

    Open node:   edit estimated_closing_date or close (reason + optional date).
    Closed node: edit closed_at (backdate) or reopen.

    Dismisses with one of:
      {"action": "update_target",  "estimated_closing_date": str|None}
      {"action": "close",          "reason": str, "closed_at": str|None}
      {"action": "update_closed_at","closed_at": str|None}
      {"action": "reopen"}
    Or None on cancel.
    """

    CSS = _MODAL_BASE_CSS.format(cls="TargetModal") + _DATE_MODAL_CSS.format(cls="TargetModal") + """
    TargetModal #dialog { width: 52; }
    TargetModal #current { color: $text-muted; margin-bottom: 1; }
    TargetModal #reopen-row { height: 1; margin-top: 1; }
    TargetModal #reopen-box { width: 3; }
    TargetModal #reopen-label { width: 1fr; }
    TargetModal #section-close {
        height: auto;
        margin-top: 1;
        border-left: tall $surface;
        padding-left: 1;
    }
    TargetModal #section-close.--active { border-left: tall $primary; }
    TargetModal #reason-row { height: 1; }
    TargetModal .reason-btn {
        width: 1fr;
        padding: 0 1;
        background: $surface;
        color: $text-disabled;
        border: none;
        text-align: center;
    }
    TargetModal .reason-btn.--active {
        background: $surface-lighten-1;
        color: $text;
        text-style: bold;
    }
    """
    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def __init__(self, node: Node):
        super().__init__()
        self.node = node
        self._reason = "done"
        self._close_mode = False
        self._reopen = False

    def compose(self) -> ComposeResult:
        label = (self.node.description or self.node.node_id)[:36]
        with Vertical(id="dialog"):
            yield Label(label, id="modal-title")
            with Vertical(id="dialog-body"):
                if self.node.is_closed:
                    reason = self.node.close_reason or "done"
                    yield Static(f"closed  ·  {reason}", id="current")
                    yield Label("closed date", classes="field-label")
                    yield Input(value=self.node.closed_at or "",
                                placeholder="e.g. yesterday / 2026-04-20", id="inp-closed")
                    yield Static("", id="fb-closed", classes="parsed")
                    with Horizontal(id="reopen-row"):
                        yield Static("[dim][ ][/]", id="reopen-box", markup=True)
                        yield Static("[dim] reopen[/]", id="reopen-label", markup=True)
                    yield Static("[dim]Enter save  Tab reopen  Esc cancel[/]", id="hint", markup=True)
                else:
                    yield Label("target date", classes="field-label")
                    yield Input(value=self.node.estimated_closing_date or "",
                                placeholder="e.g. jun. / in 3 months / thu 30", id="inp-target")
                    yield Static("", id="fb-target", classes="parsed")
                    with Vertical(id="section-close"):
                        yield Label("close as:", classes="field-label")
                        with Horizontal(id="reason-row"):
                            yield Static("done", id="btn-done", classes="reason-btn --active")
                            yield Static("discarded", id="btn-discarded", classes="reason-btn")
                        yield Label("close date  (blank = today)", classes="field-label")
                        yield Input(placeholder="e.g. yesterday / 2d ago", id="inp-closed")
                        yield Static("", id="fb-closed", classes="parsed")
                    yield Static("[dim]Enter confirm  Tab close section  ←→ reason  Esc cancel[/]",
                                 id="hint", markup=True)

    def on_mount(self) -> None:
        if self.node.is_closed:
            self.query_one("#inp-closed", Input).focus()
            _refresh_date_feedback(self, "#inp-closed", "#fb-closed")
        else:
            self.query_one("#inp-target", Input).focus()
            _refresh_date_feedback(self, "#inp-target", "#fb-target")
            self._refresh_reason()

    def _refresh_reason(self) -> None:
        self.query_one("#btn-done").set_class(self._reason == "done", "--active")
        self.query_one("#btn-discarded").set_class(self._reason == "discarded", "--active")

    def _refresh_close_section(self) -> None:
        self.query_one("#section-close").set_class(self._close_mode, "--active")

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "inp-target":
            _refresh_date_feedback(self, "#inp-target", "#fb-target")
        elif event.input.id == "inp-closed":
            _refresh_date_feedback(self, "#inp-closed", "#fb-closed")

    def on_key(self, event) -> None:
        if self.node.is_closed:
            self._handle_key_closed(event)
        else:
            self._handle_key_open(event)

    def _handle_key_open(self, event) -> None:
        if event.key == "tab":
            event.stop()
            self._close_mode = not self._close_mode
            self._refresh_close_section()
            inp = "#inp-closed" if self._close_mode else "#inp-target"
            self.query_one(inp, Input).focus()
        elif event.key in ("left", "right") and self._close_mode:
            event.stop()
            self._reason = "discarded" if self._reason == "done" else "done"
            self._refresh_reason()
        elif event.key == "enter":
            event.stop()
            if self._close_mode:
                raw = self.query_one("#inp-closed", Input).value.strip()
                self.dismiss({"action": "close", "reason": self._reason,
                              "closed_at": _parse_date(raw) if raw else None})
            else:
                raw = self.query_one("#inp-target", Input).value.strip()
                self.dismiss({"action": "update_target",
                              "estimated_closing_date": _parse_date(raw) if raw else None})

    def _refresh_reopen(self) -> None:
        if self._reopen:
            self.query_one("#reopen-box", Static).update("[bold green][x][/]")
            self.query_one("#reopen-label", Static).update("[bold] reopen[/]")
        else:
            self.query_one("#reopen-box", Static).update("[dim][ ][/]")
            self.query_one("#reopen-label", Static).update("[dim] reopen[/]")

    def _handle_key_closed(self, event) -> None:
        if event.key == "tab":
            event.stop()
            self._reopen = not self._reopen
            self._refresh_reopen()
        elif event.key == "enter":
            event.stop()
            if self._reopen:
                self.dismiss({"action": "reopen"})
            else:
                raw = self.query_one("#inp-closed", Input).value.strip()
                self.dismiss({"action": "update_closed_at",
                              "closed_at": _parse_date(raw) if raw else None})

    def action_cancel(self) -> None:
        self.dismiss(None)


# ── Update (opened_at + period) ────────────────────────────────────────────────


class UpdateModal(ModalScreen):
    """Edit opened_at and update_period.

    Dismisses with {"opened_at": str|None, "update_period": int|None}, or None on cancel.
    """

    CSS = _MODAL_BASE_CSS.format(cls="UpdateModal") + _DATE_MODAL_CSS.format(cls="UpdateModal")
    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def __init__(self, node: Node):
        super().__init__()
        self.node = node

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label(f"Update  {(self.node.description or '')[:34]}", id="modal-title")
            with Vertical(id="dialog-body"):
                yield Label("opened", classes="field-label")
                yield Input(value=self.node.opened_at or "",
                            placeholder="e.g. 2026-01-01 / last monday", id="inp-opened")
                yield Static("", id="fb-opened", classes="parsed")

                yield Label("check every (days)", classes="field-label")
                yield Input(value=str(self.node.update_period) if self.node.update_period else "",
                            placeholder="e.g. 7  (leave blank to disable)", id="inp-period")
                yield Static("", id="fb-period", classes="parsed")

                yield Static("[dim]Enter  confirm   Esc  cancel[/]", id="hint", markup=True)

    def on_mount(self) -> None:
        self.query_one("#inp-opened", Input).focus()
        _refresh_date_feedback(self, "#inp-opened", "#fb-opened")
        self._refresh_period()

    def _refresh_period(self) -> None:
        value = self.query_one("#inp-period", Input).value.strip()
        if not value:
            _set_feedback(self, "#fb-period", "", True)
            return
        try:
            days = int(value)
            _set_feedback(self, "#fb-period", f"→ every {days}d", True)
        except ValueError:
            _set_feedback(self, "#fb-period", "? must be a number", False)

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "inp-opened":
            _refresh_date_feedback(self, "#inp-opened", "#fb-opened")
        elif event.input.id == "inp-period":
            self._refresh_period()

    _FIELD_ORDER = ["inp-opened", "inp-period"]

    def on_input_submitted(self, event: Input.Submitted) -> None:
        idx = self._FIELD_ORDER.index(event.input.id)
        if idx < len(self._FIELD_ORDER) - 1:
            self.query_one(f"#{self._FIELD_ORDER[idx + 1]}", Input).focus()
        else:
            self.action_confirm()

    def action_confirm(self) -> None:
        opened = self.query_one("#inp-opened", Input).value.strip()
        period = self.query_one("#inp-period", Input).value.strip()
        result = {"opened_at": _parse_date(opened) if opened else None}
        if period:
            try:
                result["update_period"] = int(period)
            except ValueError:
                result["update_period"] = self.node.update_period
        else:
            result["update_period"] = None
        self.dismiss(result)

    def action_cancel(self) -> None:
        self.dismiss(None)



# ── Sync ───────────────────────────────────────────────────────────────────────


class SyncModal(ModalScreen):
    """Quit confirmation with optional sync.

    Dismisses with:
      "sync_quit"  — run sync then quit
      "quit"       — quit without sync
      None         — cancel (stay in app)
    """

    CSS = """
    SyncModal {
        align: center middle;
    }
    SyncModal #dialog {
        background: $background;
        border-left: tall $primary;
        border-right: tall $primary;
        border-bottom: tall $primary;
        padding: 0 0 1 0;
        width: 52;
        height: auto;
    }
    SyncModal #modal-title {
        background: $primary;
        color: $background;
        padding: 0 2;
        width: 1fr;
        height: 1;
        margin-bottom: 1;
    }
    SyncModal #dialog-body {
        padding: 0 2;
        height: auto;
    }
    .sync-opt {
        border: round $surface-lighten-2;
        padding: 0 1;
        margin-bottom: 1;
        height: auto;
    }
    .sync-opt.--selected {
        border: round $primary;
        background: $surface-lighten-1;
    }
    .sync-opt-label {
        text-style: bold;
    }
    .sync-opt-detail {
        color: $text-muted;
    }
    SyncModal #hint {
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

    _OPTIONS = [
        ("sync_quit", "Sync and quit", "Commit, push, then exit"),
        ("quit",      "Quit without sync", "Exit immediately"),
    ]

    def __init__(self, has_changes: bool):
        super().__init__()
        self._selected = 0
        self.has_changes = has_changes

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("Quit", id="modal-title")
            with Vertical(id="dialog-body"):
                status = "Uncommitted changes detected." if self.has_changes else "No local changes."
                yield Static(status, id="sync-status")
                for i, (_, label, detail) in enumerate(self._OPTIONS):
                    with Vertical(classes="sync-opt", id=f"sopt-{i}"):
                        yield Static(label, classes="sync-opt-label")
                        yield Static(detail, classes="sync-opt-detail")
                yield Static("[dim]↑↓ select   Enter confirm   Esc cancel[/]", id="hint", markup=True)

    def on_mount(self) -> None:
        self._refresh()

    def _refresh(self) -> None:
        for i in range(len(self._OPTIONS)):
            self.query_one(f"#sopt-{i}").set_class(i == self._selected, "--selected")

    def action_move_up(self) -> None:
        self._selected = (self._selected - 1) % len(self._OPTIONS)
        self._refresh()

    def action_move_down(self) -> None:
        self._selected = (self._selected + 1) % len(self._OPTIONS)
        self._refresh()

    def action_confirm(self) -> None:
        self.dismiss(self._OPTIONS[self._selected][0])

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
