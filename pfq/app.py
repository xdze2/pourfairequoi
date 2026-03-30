from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widget import Widget
from textual.widgets import Footer, Input, ListView, ListItem, Label, Static

from .config import FIELDS
from .model import extract_link, find_file_by_id, load_task, save_task


# ── Row model ─────────────────────────────────────────────────────────────────

@dataclass
class Row:
    kind: str        # "header" | "simple" | "item"
    field: str
    idx: int | None  # list index (items only)

    @property
    def editable(self) -> bool:
        return self.kind in ("simple", "item")


def build_rows(data: dict) -> list[Row]:
    rows: list[Row] = []
    for key, ftype in FIELDS.items():
        if key not in data:
            continue
        if ftype == "list":
            rows.append(Row("header", key, None))
            val = data[key]
            if isinstance(val, list):
                for i in range(len(val)):
                    rows.append(Row("item", key, i))
        else:
            rows.append(Row("simple", key, None))
    return rows


def get_row_text(row: Row, data: dict) -> str:
    if row.kind == "header":
        return f"{row.field}:"
    if row.kind == "simple":
        return str(data.get(row.field) or "")
    items = data.get(row.field, [])
    if isinstance(items, list) and row.idx is not None and row.idx < len(items):
        return str(items[row.idx] or "")
    return ""


def set_row_text(row: Row, data: dict, value: str) -> None:
    if row.kind == "simple":
        data[row.field] = value
    elif row.kind == "item":
        items = data.get(row.field)
        if isinstance(items, list) and row.idx is not None and row.idx < len(items):
            items[row.idx] = value


# ── Task pane ─────────────────────────────────────────────────────────────────

class TaskPane(Widget, can_focus=True):
    BINDINGS = [
        Binding("up",    "cursor_up",   "Up",     show=False),
        Binding("down",  "cursor_down", "Down",   show=False),
        Binding("i",     "edit",        "Edit",   show=True),
        Binding("n",     "insert",      "New",    show=True),
        Binding("d",     "delete",      "Delete", show=True),
        Binding("enter", "open_link",   "Open",   show=True),
        Binding("a",     "add_section", "Add section", show=True),
    ]

    cursor: reactive[int] = reactive(0)

    def __init__(self, path: Path, **kwargs):
        super().__init__(**kwargs)
        self.path = path
        self.data: dict = load_task(path)
        self.rows: list[Row] = build_rows(self.data)
        self._scroll: int = 0

    def watch_cursor(self, _value: int) -> None:
        self.refresh()
        try:
            self.app._sync_preview()  # type: ignore[attr-defined]
        except Exception:
            pass

    # ── Render ────────────────────────────────────────────────────────────────

    def render(self) -> Text:
        height = max(self.size.height, 5)
        if self.cursor < self._scroll:
            self._scroll = self.cursor
        elif self.cursor >= self._scroll + height:
            self._scroll = self.cursor - height + 1

        t = Text(no_wrap=True, overflow="ellipsis")
        visible = self.rows[self._scroll: self._scroll + height]
        for i, row in enumerate(visible):
            abs_i = i + self._scroll
            text = get_row_text(row, self.data)
            line = self._render_row(row, text, selected=(abs_i == self.cursor))
            t.append_text(line)
            t.append("\n")
        return t

    def _render_row(self, row: Row, text: str, selected: bool) -> Text:
        t = Text(no_wrap=True, overflow="ellipsis")
        if row.kind == "header":
            t.append(f" ── {text} ", style="bold cyan")
        elif row.kind == "simple":
            t.append(f" {row.field:<14}", style="dim")
            _append_with_link(t, text)
        else:
            t.append("    • ")
            _append_with_link(t, text)
        if selected:
            t.stylize("reverse")
        return t

    # ── Cursor ────────────────────────────────────────────────────────────────

    def _clamp(self) -> None:
        if self.rows:
            self.cursor = max(0, min(self.cursor, len(self.rows) - 1))

    def action_cursor_up(self) -> None:
        if self.cursor > 0:
            self.cursor -= 1

    def action_cursor_down(self) -> None:
        if self.cursor < len(self.rows) - 1:
            self.cursor += 1

    # ── Edit ─────────────────────────────────────────────────────────────────

    def current_row(self) -> Row | None:
        if 0 <= self.cursor < len(self.rows):
            return self.rows[self.cursor]
        return None

    def action_edit(self) -> None:
        row = self.current_row()
        if row and row.editable:
            self.app.begin_edit(row, get_row_text(row, self.data))  # type: ignore[attr-defined]

    def apply_value(self, row: Row, value: str) -> None:
        set_row_text(row, self.data, value)
        save_task(self.path, self.data)
        self.refresh()

    def restore_value(self, row: Row, original: str) -> None:
        set_row_text(row, self.data, original)
        save_task(self.path, self.data)
        self.refresh()

    # ── Insert / Delete ───────────────────────────────────────────────────────

    def action_insert(self) -> None:
        row = self.current_row()
        if row is None:
            return
        if row.kind == "header":
            field, after = row.field, -1
        elif row.kind == "item":
            field, after = row.field, row.idx  # type: ignore[assignment]
        else:
            return
        items = self.data.setdefault(field, [])
        if not isinstance(items, list):
            return
        insert_at = after + 1
        items.insert(insert_at, "")
        save_task(self.path, self.data)
        self.rows = build_rows(self.data)
        for i, r in enumerate(self.rows):
            if r.kind == "item" and r.field == field and r.idx == insert_at:
                self.cursor = i
                break
        self.refresh()
        new_row = self.current_row()
        if new_row:
            self.app.begin_edit(new_row, "")  # type: ignore[attr-defined]

    def action_delete(self) -> None:
        row = self.current_row()
        if row is None or row.kind != "item":
            return
        items = self.data.get(row.field)
        if isinstance(items, list) and row.idx is not None:
            items.pop(row.idx)
        save_task(self.path, self.data)
        self.rows = build_rows(self.data)
        self._clamp()
        self.refresh()

    def action_add_section(self) -> None:
        missing = [key for key in FIELDS if key not in self.data]
        if missing:
            self.app.push_screen(AddSectionModal(missing), self._on_section_chosen)  # type: ignore[attr-defined]

    def _on_section_chosen(self, section: str | None) -> None:
        if not section:
            return
        self.data[section] = [] if FIELDS[section] == "list" else ""
        save_task(self.path, self.data)
        self.rows = build_rows(self.data)
        # Move cursor to the new section header
        for i, r in enumerate(self.rows):
            if r.kind == "header" and r.field == section:
                self.cursor = i
                break
        self.refresh()

    # ── Link navigation ───────────────────────────────────────────────────────

    def action_open_link(self) -> None:
        row = self.current_row()
        if row is None:
            return
        link_id = extract_link(get_row_text(row, self.data))
        if link_id:
            self.app.navigate_to_id(link_id)  # type: ignore[attr-defined]

    def linked_path(self) -> Path | None:
        row = self.current_row()
        if row is None:
            return None
        link_id = extract_link(get_row_text(row, self.data))
        return find_file_by_id(link_id, self.path.parent) if link_id else None


# ── Preview pane ──────────────────────────────────────────────────────────────

class PreviewPane(Static):
    def show_file(self, path: Path | None) -> None:
        if path is None:
            self.update("")
            return
        try:
            data = load_task(path)
            t = Text()
            t.append(path.name + "\n", style="bold")
            t.append("─" * 32 + "\n", style="dim")
            for key, ftype in FIELDS.items():
                val = data.get(key)
                if val is None:
                    continue
                if ftype == "list" and isinstance(val, list):
                    t.append(f"{key}:\n", style="bold cyan")
                    for item in val:
                        t.append(f"  • {item}\n")
                else:
                    t.append(f"{key:<14}", style="dim")
                    t.append(f"{val}\n")
            self.update(t)
        except Exception as exc:
            self.update(f"[red]{exc}[/]")


# ── Add-section modal ─────────────────────────────────────────────────────────

class AddSectionModal(ModalScreen[str | None]):
    """Pick a section to add to the current task."""

    CSS = """\
    AddSectionModal {
        align: center middle;
    }
    #modal-box {
        width: 40;
        height: auto;
        max-height: 20;
        border: solid $primary;
        background: $surface;
        padding: 1 2;
    }
    #modal-box > Label { margin-bottom: 1; }
    """

    BINDINGS = [Binding("escape", "dismiss", "Cancel", show=False)]

    def __init__(self, available: list[str]) -> None:
        super().__init__()
        self._available = available

    def compose(self) -> ComposeResult:
        with Vertical(id="modal-box"):
            yield Label("Add section:")
            with ListView():
                for name in self._available:
                    yield ListItem(Label(name), id=f"section-{name}")

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        section = event.item.id.removeprefix("section-")
        self.dismiss(section)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _append_with_link(t: Text, text: str) -> None:
    m = re.search(r"(\s*#\w+)\s*$", text)
    if m:
        t.append(text[: m.start()])
        t.append(m.group(1).strip(), style="bold yellow")
    else:
        t.append(text)


# ── App ───────────────────────────────────────────────────────────────────────

APP_CSS = """\
Screen { layout: vertical; }

#panes { height: 1fr; }

TaskPane {
    width: 1fr;
    border: solid $primary;
    padding: 0 1;
}

PreviewPane {
    width: 1fr;
    border: solid $surface;
    padding: 0 1;
    overflow-y: auto;
}

#edit-bar {
    height: 3;
    display: none;
}

#edit-bar.active { display: block; }
"""


class PfqApp(App):
    CSS = APP_CSS

    BINDINGS = [
        Binding("b",      "go_back", "Back", show=True),
        Binding("ctrl+q", "quit",    "Quit", show=True),
    ]

    def __init__(self, path: Path) -> None:
        super().__init__()
        self._initial_path = path
        self._history: list[Path] = []
        self._editing_row: Row | None = None
        self._edit_original: str = ""

    def compose(self) -> ComposeResult:
        yield Horizontal(
            TaskPane(self._initial_path, id="task-pane"),
            PreviewPane(id="preview-pane"),
            id="panes",
        )
        yield Input(placeholder="edit — Esc to cancel", id="edit-bar")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#task-pane", TaskPane).focus()

    # ── Preview ───────────────────────────────────────────────────────────────

    def _sync_preview(self) -> None:
        pane = self.query_one("#task-pane", TaskPane)
        self.query_one("#preview-pane", PreviewPane).show_file(pane.linked_path())

    # ── Edit lifecycle ────────────────────────────────────────────────────────

    def begin_edit(self, row: Row, current: str) -> None:
        self._editing_row = row
        self._edit_original = current
        bar = self.query_one("#edit-bar", Input)
        bar.add_class("active")
        bar.value = current
        bar.focus()
        bar.cursor_position = len(current)

    def on_input_changed(self, event: Input.Changed) -> None:
        if self._editing_row is None:
            return
        self.query_one("#task-pane", TaskPane).apply_value(self._editing_row, event.value)
        self._sync_preview()

    def on_input_submitted(self, _event: Input.Submitted) -> None:
        self._end_edit(save=True)

    def on_key(self, event) -> None:
        if event.key == "escape" and self._editing_row is not None:
            self._end_edit(save=False)
            event.prevent_default()
            event.stop()

    def _end_edit(self, save: bool) -> None:
        if not save and self._editing_row is not None:
            self.query_one("#task-pane", TaskPane).restore_value(
                self._editing_row, self._edit_original
            )
        self._editing_row = None
        self._edit_original = ""
        bar = self.query_one("#edit-bar", Input)
        bar.remove_class("active")
        bar.value = ""
        self.query_one("#task-pane", TaskPane).focus()
        self._sync_preview()

    # ── File navigation ───────────────────────────────────────────────────────

    def navigate_to_id(self, link_id: str) -> None:
        pane = self.query_one("#task-pane", TaskPane)
        target = find_file_by_id(link_id, pane.path.parent)
        if target:
            self._history.append(pane.path)
            self._open_file(target)

    def action_go_back(self) -> None:
        if self._history:
            self._open_file(self._history.pop())

    def _open_file(self, path: Path) -> None:
        pane = self.query_one("#task-pane", TaskPane)
        pane.path = path
        pane.data = load_task(path)
        pane.rows = build_rows(pane.data)
        pane.cursor = 0
        pane._scroll = 0
        pane.refresh()
        self._sync_preview()
