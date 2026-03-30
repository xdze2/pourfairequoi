from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from rich.text import Text
from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widget import Widget
from textual.widgets import ContentSwitcher, Footer, Input, Label, ListItem, ListView, Static

from .config import FIELDS, INVERSE_FIELDS
from .model import (
    add_backlink, check_backlinks, extract_link, find_file_by_id,
    get_task_id, load_task, new_filepath, remove_backlink, save_task,
)


# ── Edit input ────────────────────────────────────────────────────────────────

class EditInput(Input):
    BINDINGS = [
        Binding("enter",  "submit",      "Save",   show=True),
        Binding("escape", "cancel_edit", "Cancel", show=True),
    ]

    def action_cancel_edit(self) -> None:
        self.app._end_edit(save=False)  # type: ignore[attr-defined]


# ── Modals ────────────────────────────────────────────────────────────────────

_MODAL_CSS = """\
    {name} {{ align: center middle; }}
    #modal-box {{
        width: 50; height: auto; max-height: 20;
        border: solid $primary; background: $surface; padding: 1 2;
    }}
    #modal-box > Label {{ margin-bottom: 1; }}
"""


class NewTaskModal(ModalScreen[str | None]):
    CSS = _MODAL_CSS.format(name="NewTaskModal")
    BINDINGS = [Binding("escape", "dismiss", show=False)]

    def __init__(self, default: str = "") -> None:
        super().__init__()
        self._default = default

    def compose(self) -> ComposeResult:
        with Vertical(id="modal-box"):
            yield Label("New task description:")
            yield Input(value=self._default, placeholder="description…", id="desc-input")

    def on_mount(self) -> None:
        inp = self.query_one("#desc-input", Input)
        inp.cursor_position = len(self._default)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.dismiss(event.value.strip() or None)


class ConfirmModal(ModalScreen[bool]):
    CSS = _MODAL_CSS.format(name="ConfirmModal")
    BINDINGS = [
        Binding("y",      "yes",     "Yes",    show=True),
        Binding("n",      "no",      "No",     show=True),
        Binding("escape", "no",                show=False),
    ]

    def __init__(self, message: str) -> None:
        super().__init__()
        self._message = message

    def compose(self) -> ComposeResult:
        with Vertical(id="modal-box"):
            yield Label(self._message)
            yield Label("[dim]y = confirm   n / Esc = cancel[/dim]")

    def action_yes(self) -> None:
        self.dismiss(True)

    def action_no(self) -> None:
        self.dismiss(False)


# ── Row model ─────────────────────────────────────────────────────────────────

@dataclass
class Row:
    kind: str        # "header" | "simple" | "item"
    field: str
    idx: int | None

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


# ── File nav pane ─────────────────────────────────────────────────────────────

STATUS_STYLES: dict[str, str] = {
    "todo":      "dim",
    "active":    "bold green",
    "stuck":     "yellow",
    "done":      "green",
    "abandoned": "red",
}


class FileNavPane(Widget, can_focus=True):
    BINDINGS = [
        Binding("up",    "cursor_up",    show=False),
        Binding("down",  "cursor_down",  show=False),
        Binding("enter", "open_file",    "Open",   show=True),
        Binding("n",     "new_task",     "New",    show=True),
        Binding("d",     "delete_task",  "Delete", show=True),
    ]

    cursor: reactive[int] = reactive(0)

    def __init__(self, vault: Path, **kwargs):
        super().__init__(**kwargs)
        self.vault = vault
        self._all_files: list[Path] = []
        self._files: list[Path] = []
        self._meta: dict[Path, tuple[str, str]] = {}  # path -> (description, status)
        self._searching = False
        self._query = ""
        self._scroll = 0

    def on_mount(self) -> None:
        self._refresh_files()

    def _refresh_files(self) -> None:
        if self.vault.exists():
            self._all_files = sorted(
                p for p in self.vault.iterdir()
                if p.suffix in (".yaml", ".yml")
            )
        else:
            self._all_files = []
        for p in self._all_files:
            if p not in self._meta:
                try:
                    data = load_task(p)
                    desc = str(data.get("description", "") or p.stem)
                    status = str(data.get("status", "") or "")
                    self._meta[p] = (desc, status)
                except Exception:
                    self._meta[p] = (p.stem, "")
        self._apply_filter()

    def _apply_filter(self) -> None:
        q = self._query.lower()
        if q:
            self._files = [
                p for p in self._all_files
                if q in self._meta.get(p, (p.stem, ""))[0].lower()
                or q in p.stem.lower()
            ]
        else:
            self._files = list(self._all_files)
        self.cursor = max(0, min(self.cursor, len(self._files) - 1))
        self._scroll = 0
        self.refresh()

    def on_key(self, event) -> None:
        if self._searching:
            if event.key == "escape":
                self._searching = False
                self._query = ""
                self._apply_filter()
                event.stop()
            elif event.key == "backspace":
                self._query = self._query[:-1]
                self._apply_filter()
                event.stop()
            elif event.key == "enter":
                self._searching = False
                self.refresh()
                event.stop()
            elif event.character and event.character.isprintable():
                self._query += event.character
                self._apply_filter()
                event.stop()
        else:
            if event.character == "/":
                self._searching = True
                self._query = ""
                self.refresh()
                event.stop()
            elif event.key == "escape":
                try:
                    self.app.query_one("#task-pane", TaskPane).focus()
                except Exception:
                    pass
                event.stop()

    def render(self) -> Text:
        height = max(self.size.height - 1, 3)
        if self.cursor < self._scroll:
            self._scroll = self.cursor
        elif self._files and self.cursor >= self._scroll + height:
            self._scroll = self.cursor - height + 1

        t = Text(no_wrap=True, overflow="ellipsis")
        for i, path in enumerate(self._files[self._scroll: self._scroll + height]):
            abs_i = i + self._scroll
            selected = abs_i == self.cursor
            desc, status = self._meta.get(path, (path.stem, ""))
            line = Text(no_wrap=True, overflow="ellipsis")
            line.append(f" {desc}")
            if status:
                line.append(f" [{status}]", style=STATUS_STYLES.get(status, "dim"))
            if selected:
                line.stylize("reverse")
            t.append_text(line)
            t.append("\n")

        if self._searching:
            t.append(f" /{self._query}▋", style="bold yellow")
        else:
            n = len(self._files)
            t.append(f" {n} file{'s' if n != 1 else ''}  / to search", style="dim")
        return t

    def watch_cursor(self, _value: int) -> None:
        self.refresh()
        if self.has_focus:
            try:
                self.app._sync_preview()  # type: ignore[attr-defined]
            except Exception:
                pass

    def action_cursor_up(self) -> None:
        if self.cursor > 0:
            self.cursor -= 1

    def action_cursor_down(self) -> None:
        if self.cursor < len(self._files) - 1:
            self.cursor += 1

    def action_open_file(self) -> None:
        if 0 <= self.cursor < len(self._files):
            self.app._open_in_task_pane(self._files[self.cursor])  # type: ignore[attr-defined]

    def current_path(self) -> Path | None:
        if 0 <= self.cursor < len(self._files):
            return self._files[self.cursor]
        return None

    def action_new_task(self) -> None:
        self.app.push_screen(NewTaskModal(), self._on_new_task)  # type: ignore[attr-defined]

    def _on_new_task(self, description: str | None) -> None:
        if not description:
            return
        from datetime import date
        path = new_filepath(description, self.vault)
        data: dict = {
            "description": description,
            "status": "todo",
            "start_date": date.today().isoformat(),
        }
        for key, ftype in FIELDS.items():
            if ftype == "list" and key not in data:
                data[key] = []
        save_task(path, data)
        self.notify_file_added(path)
        self.app._open_in_task_pane(path)  # type: ignore[attr-defined]

    def action_delete_task(self) -> None:
        path = self.current_path()
        if path is None:
            return
        desc = self._meta.get(path, (path.stem, ""))[0]
        self.app.push_screen(  # type: ignore[attr-defined]
            ConfirmModal(f"Delete '{desc}' ?"),
            lambda ok: self._on_delete_confirmed(ok, path),
        )

    def _on_delete_confirmed(self, ok: bool, path: Path) -> None:
        if not ok:
            return
        path.unlink(missing_ok=True)
        self._meta.pop(path, None)
        self._refresh_files()
        pane = self.app.query_one("#task-pane", TaskPane)  # type: ignore[attr-defined]
        if pane.path == path:
            pane.path = None
            pane.data = {}
            pane.rows = []
            pane.refresh()

    def notify_file_added(self, path: Path) -> None:
        self._meta.pop(path, None)
        self._refresh_files()
        if path in self._files:
            self.cursor = self._files.index(path)


# ── Link picker pane ──────────────────────────────────────────────────────────

_CREATE_NEW = "✦  Create new task…"


class LinkPickerPane(Widget, can_focus=True):
    BINDINGS = [
        Binding("up",     "cursor_up",  show=False),
        Binding("down",   "cursor_down", show=False),
        Binding("enter",  "select",     "Link",   show=True),
        Binding("escape", "cancel",     "Cancel", show=True),
    ]

    cursor: reactive[int] = reactive(0)

    def __init__(self, vault: Path, **kwargs):
        super().__init__(**kwargs)
        self.vault = vault
        self._all_files: list[Path] = []
        self._files: list[Path] = []
        self._meta: dict[Path, tuple[str, str]] = {}
        self._searching = False
        self._query = ""
        self._scroll = 0

    def refresh_files(self) -> None:
        if self.vault.exists():
            self._all_files = sorted(
                p for p in self.vault.iterdir()
                if p.suffix in (".yaml", ".yml")
            )
        else:
            self._all_files = []
        for p in self._all_files:
            if p not in self._meta:
                try:
                    data = load_task(p)
                    self._meta[p] = (
                        str(data.get("description", "") or p.stem),
                        str(data.get("status", "") or ""),
                    )
                except Exception:
                    self._meta[p] = (p.stem, "")
        self._apply_filter()

    def _apply_filter(self) -> None:
        q = self._query.lower()
        self._files = [
            p for p in self._all_files
            if not q
            or q in self._meta.get(p, (p.stem, ""))[0].lower()
            or q in p.stem.lower()
        ]
        self.cursor = 0
        self._scroll = 0
        self.refresh()

    def on_key(self, event) -> None:
        if self._searching:
            if event.key == "escape":
                self._searching = False
                self._query = ""
                self._apply_filter()
                event.stop()
            elif event.key == "backspace":
                self._query = self._query[:-1]
                self._apply_filter()
                event.stop()
            elif event.key == "enter":
                self._searching = False
                self.refresh()
                event.stop()
            elif event.character and event.character.isprintable():
                self._query += event.character
                self._apply_filter()
                event.stop()
        elif event.character == "/":
            self._searching = True
            self._query = ""
            self.refresh()
            event.stop()

    def render(self) -> Text:
        # Row 0 = "Create new", rows 1..N = files
        total = 1 + len(self._files)
        height = max(self.size.height - 1, 3)
        if self.cursor < self._scroll:
            self._scroll = self.cursor
        elif self.cursor >= self._scroll + height:
            self._scroll = self.cursor - height + 1

        entries: list[Path | None] = [None] + self._files
        t = Text(no_wrap=True, overflow="ellipsis")
        for i, entry in enumerate(entries[self._scroll: self._scroll + height]):
            abs_i = i + self._scroll
            selected = abs_i == self.cursor
            line = Text(no_wrap=True, overflow="ellipsis")
            if entry is None:
                line.append(f" {_CREATE_NEW}", style="bold green")
            else:
                desc, status = self._meta.get(entry, (entry.stem, ""))
                line.append(f" {desc}")
                if status:
                    line.append(f" [{status}]", style=STATUS_STYLES.get(status, "dim"))
            if selected:
                line.stylize("reverse")
            t.append_text(line)
            t.append("\n")

        if self._searching:
            t.append(f" /{self._query}▋", style="bold yellow")
        else:
            t.append(" / to search", style="dim")
        return t

    def watch_cursor(self, _value: int) -> None:
        self.refresh()

    def action_cursor_up(self) -> None:
        if self.cursor > 0:
            self.cursor -= 1

    def action_cursor_down(self) -> None:
        if self.cursor < len(self._files):  # 1 + len - 1
            self.cursor += 1

    def action_select(self) -> None:
        if self.cursor == 0:
            self.app._create_and_link()  # type: ignore[attr-defined]
        else:
            self.app._apply_link(self._files[self.cursor - 1])  # type: ignore[attr-defined]

    def action_cancel(self) -> None:
        self.app._cancel_link()  # type: ignore[attr-defined]


# ── Task pane ─────────────────────────────────────────────────────────────────

class TaskPane(Widget, can_focus=True):
    BINDINGS = [
        Binding("up",    "cursor_up",   show=False),
        Binding("down",  "cursor_down", show=False),
        Binding("e",      "edit",        "Edit",        show=True),
        Binding("n",      "insert",      "New",         show=True),
        Binding("d",      "delete",      "Delete",      show=True),
        Binding("a",      "add_section", "Add section", show=True),
        Binding("enter",  "open_link",   "Open",        show=True),
        Binding("l",      "link",        "Link",        show=True),
        Binding("u",      "unlink",      "Unlink",      show=True),
        Binding("escape", "back_to_nav", "Files",       show=True),
    ]

    cursor: reactive[int] = reactive(0)

    def __init__(self, path: Path | None = None, **kwargs):
        super().__init__(**kwargs)
        self.path = path
        self.data: dict = load_task(path) if path else {}
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
        if not self.path:
            t = Text()
            t.append("\n  No file open\n", style="dim")
            t.append("  Select a file from the list", style="dim")
            return t

        height = max(self.size.height, 5)
        if self.cursor < self._scroll:
            self._scroll = self.cursor
        elif self.cursor >= self._scroll + height:
            self._scroll = self.cursor - height + 1

        t = Text(no_wrap=True, overflow="ellipsis")
        for i, row in enumerate(self.rows[self._scroll: self._scroll + height]):
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
        if not self.path:
            return
        row = self.current_row()
        if row and row.editable:
            self.app.begin_edit(row, get_row_text(row, self.data))  # type: ignore[attr-defined]

    def apply_value(self, row: Row, value: str) -> None:
        """Update in-memory only — caller is responsible for saving."""
        set_row_text(row, self.data, value)
        self.refresh()

    def restore_value(self, row: Row, original: str) -> None:
        """Restore original in-memory value — no save needed."""
        set_row_text(row, self.data, original)
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

    # ── Add section ───────────────────────────────────────────────────────────

    def action_add_section(self) -> None:
        missing = [key for key in FIELDS if key not in self.data]
        if missing:
            self.app.push_screen(  # type: ignore[attr-defined]
                AddSectionModal(missing), self._on_section_chosen
            )

    def _on_section_chosen(self, section: str | None) -> None:
        if not section:
            return
        self.data[section] = [] if FIELDS[section] == "list" else ""
        save_task(self.path, self.data)
        self.rows = build_rows(self.data)
        for i, r in enumerate(self.rows):
            if r.kind == "header" and r.field == section:
                self.cursor = i
                break
        self.refresh()

    # ── Link navigation ───────────────────────────────────────────────────────

    def action_back_to_nav(self) -> None:
        self.app._show_file_nav()  # type: ignore[attr-defined]

    def action_link(self) -> None:
        if self.path and self.current_row() and self.current_row().editable:  # type: ignore[union-attr]
            self.app._start_linking()  # type: ignore[attr-defined]

    def action_unlink(self) -> None:
        row = self.current_row()
        if row is None or not self.path:
            return
        text = get_row_text(row, self.data)
        if not extract_link(text):
            return
        self.app.push_screen(  # type: ignore[attr-defined]
            ConfirmModal("Remove this link?"),
            lambda ok: self._on_unlink_confirmed(ok, row, text),
        )

    def _on_unlink_confirmed(self, ok: bool, row: Row, original: str) -> None:
        if not ok:
            return
        link_id = extract_link(original)
        if link_id and row.field in INVERSE_FIELDS and self.path:
            target = find_file_by_id(link_id, self.path.parent)
            if target:
                remove_backlink(target, INVERSE_FIELDS[row.field], get_task_id(self.path))
        clean = re.sub(r"\s*#\w+\s*$", "", original)
        self.apply_value(row, clean)
        save_task(self.path, self.data)  # type: ignore[arg-type]

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
        self._load(path)

    @work(thread=True, exclusive=True)
    def _load(self, path: Path) -> None:
        """Load and render a task file in a background thread.

        exclusive=True cancels any in-flight load when a new one starts,
        so rapid cursor movement never queues up blocking reads.
        """
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
            self.app.call_from_thread(self.update, t)
        except Exception as exc:
            self.app.call_from_thread(self.update, f"[red]{exc}[/]")


# ── Add-section modal ─────────────────────────────────────────────────────────

class AddSectionModal(ModalScreen[str | None]):
    CSS = """\
    AddSectionModal { align: center middle; }
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

    BINDINGS = [Binding("escape", "dismiss", show=False)]

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
        self.dismiss(event.item.id.removeprefix("section-"))


# ── Helpers ───────────────────────────────────────────────────────────────────

def _append_with_link(t: Text, text: str) -> None:
    m = re.search(r"(\s*#\w+)\s*$", text)
    if m:
        t.append(text[: m.start()])
        t.append(" " + m.group(1).strip(), style="color(8)")
    else:
        t.append(text)


# ── App ───────────────────────────────────────────────────────────────────────

APP_CSS = """\
Screen { layout: vertical; }

#panes { height: 1fr; }

ContentSwitcher {
    width: 1fr;
    height: 1fr;
}

FileNavPane, TaskPane, LinkPickerPane {
    width: 1fr;
    height: 1fr;
    border: solid $primary;
    padding: 0 1;
}

LinkPickerPane {
    border: solid $accent;
}

PreviewPane {
    width: 1fr;
    border: solid $surface;
    padding: 0 1;
    overflow-y: auto;
}

#edit-bar { height: 3; display: none; }
#edit-bar.active { display: block; }
"""


class PfqApp(App):
    CSS = APP_CSS
    ENABLE_COMMAND_PALETTE = False

    BINDINGS = [
        Binding("b",      "go_back", "Back", show=True),
        Binding("ctrl+q", "quit",    "Quit", show=True),
    ]

    def __init__(self, path: Path | None = None) -> None:
        super().__init__()
        self._initial_path = path
        self._history: list[Path] = []
        self._editing_row: Row | None = None
        self._edit_original: str = ""

    def compose(self) -> ComposeResult:
        vault = self._initial_path.parent if self._initial_path else Path("data")
        yield Horizontal(
            ContentSwitcher(
                FileNavPane(vault, id="file-nav"),
                TaskPane(self._initial_path, id="task-pane"),
                initial="file-nav" if not self._initial_path else "task-pane",
                id="left-switcher",
            ),
            ContentSwitcher(
                PreviewPane(id="preview-pane"),
                LinkPickerPane(vault, id="link-picker"),
                initial="preview-pane",
                id="right-switcher",
            ),
            id="panes",
        )
        yield EditInput(placeholder="edit…", id="edit-bar")
        yield Footer()

    def on_mount(self) -> None:
        self._show_file_nav()

    # ── Panel switching ───────────────────────────────────────────────────────

    def _show_file_nav(self) -> None:
        self.query_one("#left-switcher", ContentSwitcher).current = "file-nav"
        self._cancel_link()
        self.query_one("#file-nav", FileNavPane).focus()
        self._sync_preview()

    def _show_task_pane(self) -> None:
        self.query_one("#left-switcher", ContentSwitcher).current = "task-pane"
        self.query_one("#task-pane", TaskPane).focus()
        self._sync_preview()

    # ── Preview sync ─────────────────────────────────────────────────────────

    def _sync_preview(self) -> None:
        right = self.query_one("#right-switcher", ContentSwitcher)
        if right.current == "link-picker":
            return  # link picker manages the right panel itself
        preview = self.query_one("#preview-pane", PreviewPane)
        left = self.query_one("#left-switcher", ContentSwitcher)
        if left.current == "file-nav":
            preview.show_file(self.query_one("#file-nav", FileNavPane).current_path())
        else:
            preview.show_file(self.query_one("#task-pane", TaskPane).linked_path())

    # ── Linking ───────────────────────────────────────────────────────────────

    def _start_linking(self) -> None:
        picker = self.query_one("#link-picker", LinkPickerPane)
        picker.refresh_files()
        picker.cursor = 0
        picker._searching = False
        picker._query = ""
        picker.refresh()
        self.query_one("#right-switcher", ContentSwitcher).current = "link-picker"
        picker.focus()

    def _apply_link(self, path: Path) -> None:
        pane = self.query_one("#task-pane", TaskPane)
        row = pane.current_row()
        if not (row and row.editable and pane.path):
            self._cancel_link()
            return

        target_id = get_task_id(path)
        current = get_row_text(row, pane.data)

        # Remove old backlink if replacing an existing link
        old_id = extract_link(current)
        if old_id and row.field in INVERSE_FIELDS:
            old_target = find_file_by_id(old_id, pane.path.parent)
            if old_target:
                remove_backlink(old_target, INVERSE_FIELDS[row.field], get_task_id(pane.path))

        clean = re.sub(r"\s*#\w+\s*$", "", current)
        pane.apply_value(row, f"{clean} #{target_id}")
        save_task(pane.path, pane.data)

        # Add backlink in target file
        if row.field in INVERSE_FIELDS:
            source_desc = str(pane.data.get("description", ""))
            add_backlink(path, INVERSE_FIELDS[row.field], get_task_id(pane.path), source_desc)

        self._cancel_link()

    def _cancel_link(self) -> None:
        right = self.query_one("#right-switcher", ContentSwitcher)
        if right.current == "link-picker":
            right.current = "preview-pane"
            self.query_one("#task-pane", TaskPane).focus()
            self._sync_preview()

    def _create_and_link(self) -> None:
        pane = self.query_one("#task-pane", TaskPane)
        row = pane.current_row()
        default = ""
        if row and row.editable:
            raw = get_row_text(row, pane.data)
            default = re.sub(r"\s*#\w+\s*$", "", raw).strip()
        self.push_screen(NewTaskModal(default=default), self._on_new_task_for_link)

    def _on_new_task_for_link(self, description: str | None) -> None:
        if not description:
            return
        from datetime import date
        vault = self.query_one("#file-nav", FileNavPane).vault
        path = new_filepath(description, vault)
        data: dict = {
            "description": description,
            "status": "todo",
            "start_date": date.today().isoformat(),
        }
        for key, ftype in FIELDS.items():
            if ftype == "list" and key not in data:
                data[key] = []
        save_task(path, data)
        self.query_one("#file-nav", FileNavPane).notify_file_added(path)
        self._apply_link(path)

    # ── Edit lifecycle ────────────────────────────────────────────────────────

    def begin_edit(self, row: Row, current: str) -> None:
        self._editing_row = row
        self._edit_original = current
        bar = self.query_one("#edit-bar", EditInput)
        bar.add_class("active")
        bar.value = current
        bar.focus()
        bar.cursor_position = len(current)

    def on_input_changed(self, event: Input.Changed) -> None:
        if self._editing_row is None:
            return
        self.query_one("#task-pane", TaskPane).apply_value(self._editing_row, event.value)

    def on_input_submitted(self, _event: EditInput.Submitted) -> None:
        self._end_edit(save=True)

    def _end_edit(self, save: bool) -> None:
        pane = self.query_one("#task-pane", TaskPane)
        if save and self._editing_row is not None:
            save_task(pane.path, pane.data)
        elif not save and self._editing_row is not None:
            pane.restore_value(self._editing_row, self._edit_original)
        self._editing_row = None
        self._edit_original = ""
        bar = self.query_one("#edit-bar", EditInput)
        bar.remove_class("active")
        bar.value = ""
        self._show_task_pane()

    # ── File navigation ───────────────────────────────────────────────────────

    def _open_in_task_pane(self, path: Path) -> None:
        self._open_file(path)
        self._show_task_pane()

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
        # Sync nav selection (watch_cursor won't touch preview since nav isn't focused)
        nav = self.query_one("#file-nav", FileNavPane)
        if path in nav._files:
            nav.cursor = nav._files.index(path)
        self._sync_preview()
