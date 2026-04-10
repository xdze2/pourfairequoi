from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from rich.text import Text
from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widget import Widget
from textual.widgets import (
    ContentSwitcher,
    Footer,
    Input,
    Label,
    ListItem,
    ListView,
    Static,
)

from .config import FIELDS, LINK_TYPES, LINK_TYPE_MAP, STATUSES, TYPES
from .model import (
    find_path_by_id,
    get_links,
    get_task_id,
    load_all,
    load_task,
    new_filepath,
    save_task,
    sort_globally,
    traverse_subgraph,
)


# ── Modals ────────────────────────────────────────────────────────────────────

_MODAL_CSS = """\
    {name} {{ align: center middle; }}
    #modal-box {{
        width: 50; height: auto; max-height: 20;
        border: solid $primary; background: $surface; padding: 1 2;
    }}
    #modal-box > Label {{ margin-bottom: 1; }}
"""


class NewTaskModal(ModalScreen[Optional[str]]):
    CSS = _MODAL_CSS.format(name="NewTaskModal")
    BINDINGS = [Binding("escape", "dismiss", show=False)]

    def __init__(self, default: str = "") -> None:
        super().__init__()
        self._default = default

    def compose(self) -> ComposeResult:
        with Vertical(id="modal-box"):
            yield Label("New task description:")
            yield Input(
                value=self._default, placeholder="description…", id="desc-input"
            )

    def on_mount(self) -> None:
        inp = self.query_one("#desc-input", Input)
        inp.cursor_position = len(self._default)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.dismiss(event.value.strip() or None)


class ConfirmModal(ModalScreen[bool]):
    CSS = _MODAL_CSS.format(name="ConfirmModal")
    BINDINGS = [
        Binding("y", "yes", "Yes", show=True),
        Binding("n", "no", "No", show=True),
        Binding("escape", "no", show=False),
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
    kind: str  # "simple" | "text" | "link_header" | "link_item" | "link_add"
    field: str  # field name for simple/text; link type name for link rows
    idx: int | None  # index in data["links"] for link_item, else None

    @property
    def editable(self) -> bool:
        return self.kind in ("simple", "text", "link_item")


def build_rows(data: dict) -> list[Row]:
    rows: list[Row] = []
    # scalar / text fields — description always first
    rows.append(Row("simple", "description", None))
    for key, ftype in FIELDS.items():
        if key == "description" or key not in data:
            continue
        rows.append(Row("text" if ftype == "text" else "simple", key, None))

    # links — grouped by type, sorted by sort_order
    links = get_links(data)
    present_types = []
    seen = set()
    for lt in sorted(LINK_TYPES, key=lambda x: x.sort_order):
        type_links = [(i, l) for i, l in enumerate(links) if l.get("type") == lt.name]
        if type_links:
            if lt.name not in seen:
                present_types.append(lt.name)
                seen.add(lt.name)
            rows.append(Row("link_header", lt.name, None))
            for i, _ in type_links:
                rows.append(Row("link_item", lt.name, i))
            rows.append(Row("link_add", lt.name, None))
    return rows


def _resolve_link_desc(link: dict, store: dict) -> str:
    """Return link description, falling back to the target node's description."""
    desc = str(link.get("description", "") or "")
    if desc:
        return desc
    target_id = str(link.get("target_node", "") or "")
    if target_id and store:
        target_path = find_path_by_id(target_id, store)
        if target_path:
            return str(store[target_path].get("description", "") or "")
    return ""


def get_row_text(row: Row, data: dict, store: dict | None = None) -> str:
    if row.kind in ("simple", "text"):
        return str(data.get(row.field) or "")
    if row.kind == "link_item" and row.idx is not None:
        links = get_links(data)
        if row.idx < len(links):
            link = links[row.idx]
            desc = _resolve_link_desc(link, store or {})
            target = str(link.get("target_node", "") or "")
            if desc and target:
                return f"{desc} #{target}"
            return target and f"#{target}" or desc
    return ""


def set_row_text(row: Row, data: dict, value: str) -> None:
    if row.kind in ("simple", "text"):
        data[row.field] = value
    elif row.kind == "link_item" and row.idx is not None:
        links = get_links(data)
        if row.idx < len(links):
            links[row.idx]["description"] = value


# ── File nav pane ─────────────────────────────────────────────────────────────

STATUS_STYLES: dict[str, str] = {k: v[1] for k, v in STATUSES.items()}
TYPE_STYLES: dict[str, str] = {k: v[1] for k, v in TYPES.items()}


class _AppHeader(Static):
    DEFAULT_CSS = "_AppHeader { height: 3; }"


class FileNavPane(Widget, can_focus=True):
    BINDINGS = [
        Binding("up", "cursor_up", show=False),
        Binding("down", "cursor_down", show=False),
        Binding("enter", "open_file", "Open", show=True),
        Binding("n", "new_task", "New", show=True),
        Binding("d", "delete_task", "Delete", show=True),
    ]

    cursor: reactive[int] = reactive(0)

    def __init__(self, vault: Path, store: dict[Path, dict], **kwargs):
        super().__init__(**kwargs)
        self.vault = vault
        self.store = store
        self._files: list[Path] = []
        self._indent: dict[Path, int] = {}
        self._searching = False
        self._query = ""
        self._scroll = 0

    def on_mount(self) -> None:
        self._apply_filter()

    def _apply_filter(self) -> None:
        q = self._query.lower()
        sorted_nodes = sort_globally(self.store)
        self._indent = {p: indent for p, indent in sorted_nodes}
        if q:
            self._files = [
                p for p, _ in sorted_nodes
                if q in str(self.store[p].get("description", "") or p.stem).lower()
                or q in p.stem.lower()
            ]
        else:
            self._files = [p for p, _ in sorted_nodes]
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
        for i, path in enumerate(self._files[self._scroll : self._scroll + height]):
            abs_i = i + self._scroll
            selected = abs_i == self.cursor
            data = self.store.get(path, {})
            desc = str(data.get("description", "") or path.stem)
            status = str(data.get("status", "") or "")
            task_type = str(data.get("type", "") or "")
            indent = self._indent.get(path, 0)
            line = Text(no_wrap=True, overflow="ellipsis")
            line.append("  " * indent + " ")
            line.append(desc)
            if task_type:
                line.append(f" {task_type}", style=TYPE_STYLES.get(task_type, "dim"))
            if status:
                line.append(f" {status}", style=STATUS_STYLES.get(status, "dim"))
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
            "type": "task",
            "status": "todo",
            "start_date": date.today().isoformat(),
        }
        for key, ftype in FIELDS.items():
            if ftype == "list" and key not in data:
                data[key] = []
        save_task(path, data)
        self.notify_file_added(path, data)
        self.app._open_in_task_pane(path)  # type: ignore[attr-defined]

    def action_delete_task(self) -> None:
        path = self.current_path()
        if path is None:
            return
        desc = str(self.store.get(path, {}).get("description", "") or path.stem)
        self.app.push_screen(  # type: ignore[attr-defined]
            ConfirmModal(f"Delete '{desc}' ?"),
            lambda ok: self._on_delete_confirmed(ok, path),
        )

    def _on_delete_confirmed(self, ok: bool, path: Path) -> None:
        if not ok:
            return
        path.unlink(missing_ok=True)
        self.store.pop(path, None)
        self._apply_filter()
        pane = self.app.query_one("#task-pane", TaskPane)  # type: ignore[attr-defined]
        if pane.path == path:
            pane.path = None
            pane.data = {}
            pane.rows = []
            pane._rebuild()

    def notify_file_added(self, path: Path, data: dict) -> None:
        self.store[path] = data
        self._apply_filter()
        if path in self._files:
            self.cursor = self._files.index(path)


# ── Link picker pane ──────────────────────────────────────────────────────────

_CREATE_NEW = "✦  Create new task…"


class LinkPickerPane(Widget, can_focus=True):
    BINDINGS = [
        Binding("up", "cursor_up", show=False),
        Binding("down", "cursor_down", show=False),
        Binding("enter", "select", "Link", show=True),
        Binding("escape", "cancel", "Cancel", show=True),
    ]

    cursor: reactive[int] = reactive(0)

    def __init__(self, vault: Path, store: dict[Path, dict], **kwargs):
        super().__init__(**kwargs)
        self.vault = vault
        self.store = store
        self._files: list[Path] = []
        self._searching = False
        self._query = ""
        self._scroll = 0

    def refresh_files(self) -> None:
        self._apply_filter()

    def _apply_filter(self) -> None:
        q = self._query.lower()
        all_files = sorted(self.store.keys())
        self._files = [
            p for p in all_files
            if not q
            or q in str(self.store[p].get("description", "") or p.stem).lower()
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
        height = max(self.size.height - 1, 3)
        if self.cursor < self._scroll:
            self._scroll = self.cursor
        elif self.cursor >= self._scroll + height:
            self._scroll = self.cursor - height + 1

        entries: list[Path | None] = [None] + self._files
        t = Text(no_wrap=True, overflow="ellipsis")
        for i, entry in enumerate(entries[self._scroll : self._scroll + height]):
            abs_i = i + self._scroll
            selected = abs_i == self.cursor
            line = Text(no_wrap=True, overflow="ellipsis")
            if entry is None:
                line.append(f" {_CREATE_NEW}", style="bold green")
            else:
                data = self.store.get(entry, {})
                desc = str(data.get("description", "") or entry.stem)
                status = str(data.get("status", "") or "")
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
        if self.cursor < len(self._files):
            self.cursor += 1

    def action_select(self) -> None:
        if self.cursor == 0:
            self.app._create_and_link()  # type: ignore[attr-defined]
        else:
            self.app._apply_link(self._files[self.cursor - 1])  # type: ignore[attr-defined]

    def action_cancel(self) -> None:
        self.app._cancel_link()  # type: ignore[attr-defined]


# ── Inline input & non-focusable list ────────────────────────────────────────


class _InlineInput(Input):
    """Inline editor — Escape is not consumed so it bubbles to TaskPane.on_key."""

    def _on_key(self, event) -> None:
        if event.key != "escape":
            super()._on_key(event)


class _TaskList(ListView, can_focus=False):
    """ListView that never steals focus — TaskPane owns all keyboard handling."""


# ── Task row item ─────────────────────────────────────────────────────────────


class TaskRowItem(ListItem):
    """A single row in the task view."""

    selected: reactive[bool] = reactive(False)

    def __init__(self, row: Row, data: dict, store: dict | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self._row = row
        self._data = data
        self._store = store or {}

    def compose(self) -> ComposeResult:
        yield Label(self._make_renderable(), id="row-label")

    def on_mount(self) -> None:
        if self._row.kind == "text":
            self.add_class("--text")

    def watch_selected(self, _value: bool) -> None:
        self.refresh_label()

    def _make_renderable(self) -> Text:
        text = get_row_text(self._row, self._data)
        kind = self._row.kind

        if kind == "text":
            t = Text(overflow="fold")
            t.append(f" ── {self._row.field} \n", style="bold cyan")
            if text:
                for line in text.splitlines():
                    t.append(f"   {line}\n", style="dim")
            else:
                t.append("   (empty)\n", style="dim")
            if self.selected:
                t.stylize("reverse")
            return t

        t = Text(no_wrap=True, overflow="ellipsis")

        if kind == "simple":
            t.append(f" {self._row.field:<14}", style="dim")
            t.append(text)
        elif kind == "link_header":
            lt = LINK_TYPE_MAP.get(self._row.field)
            label = lt.label if lt else self._row.field
            t.append(f" ── {label} ", style="bold cyan")
        elif kind == "link_add":
            t.append("    +", style="dim")
        elif kind == "link_item":
            links = get_links(self._data)
            link = links[self._row.idx] if self._row.idx is not None and self._row.idx < len(links) else {}
            desc = _resolve_link_desc(link, self._store)
            target = str(link.get("target_node", "") or "")
            t.append("    • ")
            if desc:
                own_desc = str(link.get("description", "") or "")
                t.append(desc, style="" if own_desc else "dim")
            if target:
                t.append(f" #{target}", style="color(8)")

        if self.selected:
            t.stylize("reverse")
        return t

    def refresh_label(self) -> None:
        try:
            self.query_one("#row-label", Label).update(self._make_renderable())
        except Exception:
            pass

    def begin_edit(self, value: str) -> None:
        try:
            self.query_one("#row-label", Label).display = False
        except Exception:
            pass
        inp = _InlineInput(value=value, id="inline-input")
        self.mount(inp)
        inp.focus()
        inp.cursor_position = len(value)

    def end_edit(self) -> None:
        """Remove inline input and restore label from current data."""
        try:
            self.query_one("#inline-input", Input).remove()
        except Exception:
            pass
        try:
            lbl = self.query_one("#row-label", Label)
            lbl.update(self._make_renderable())
            lbl.display = True
        except Exception:
            pass


# ── Task header (title + metadata) ───────────────────────────────────────────


class _TaskTitle(Static):
    """Context bar: type + status."""

    DEFAULT_CSS = "_TaskTitle { height: 1; }"

    def update_task(self, data: dict) -> None:
        task_type = str(data.get("type", "") or "")
        status = str(data.get("status", "") or "")
        t = Text(no_wrap=True, overflow="ellipsis")
        t.append("  ")
        if task_type:
            t.append(task_type, style=TYPE_STYLES.get(task_type, "dim"))
            t.append("  ")
        if status:
            t.append(status, style=STATUS_STYLES.get(status, "dim"))
        else:
            t.append("—", style="dim")
        self.update(t)


# ── Task pane ─────────────────────────────────────────────────────────────────


class TaskPane(Widget, can_focus=True):
    BINDINGS = [
        Binding("up", "cursor_up", show=False),
        Binding("down", "cursor_down", show=False),
        Binding("enter", "follow_link", "Follow", show=True),
        Binding("e", "edit", "Edit", show=True),
        Binding("n", "insert", "New", show=True),
        Binding("d", "delete", "Delete", show=True),
        Binding("a", "add_field", "Add field", show=True),
        Binding("l", "link", "Link", show=True),
        Binding("u", "unlink", "Unlink", show=True),
        Binding("escape", "back_to_nav", "Files", show=True),
    ]

    def __init__(self, path: Path | None = None, **kwargs):
        super().__init__(**kwargs)
        self.path = path
        self.data: dict = load_task(path) if path else {}
        self.rows: list[Row] = build_rows(self.data)
        self._cursor_idx: int = 0
        self._items: list[TaskRowItem] = []
        self._editing: bool = False
        self._edit_original: str = ""
        self._edit_is_new: bool = False
        # pending link operation: type name + index in links list (-1 = new)
        self._link_pending_type: str | None = None
        self._link_pending_idx: int = -1

    def compose(self) -> ComposeResult:
        yield _TaskTitle(id="task-title")
        yield _TaskList(id="task-list")

    def on_mount(self) -> None:
        if self.path:
            self._refresh_title()
            self._rebuild()

    def _refresh_title(self) -> None:
        try:
            self.query_one("#task-title", _TaskTitle).update_task(self.data)
        except Exception:
            pass

    def _lv(self) -> _TaskList:
        return self.query_one("#task-list", _TaskList)

    def _rebuild(self, keep_cursor: int = 0) -> None:
        lv = self._lv()
        lv.clear()
        self._items = []
        self._cursor_idx = min(keep_cursor, len(self.rows) - 1) if self.rows else 0
        for i, row in enumerate(self.rows):
            item = TaskRowItem(row, self.data, store=self.app.store)
            item.selected = i == self._cursor_idx
            self._items.append(item)
            lv.append(item)

    def _set_cursor(self, new_idx: int) -> None:
        if 0 <= self._cursor_idx < len(self._items):
            self._items[self._cursor_idx].selected = False
        self._cursor_idx = new_idx
        if 0 <= new_idx < len(self._items):
            self._items[new_idx].selected = True
            self._lv().scroll_to_widget(self._items[new_idx])

    def current_row(self) -> Row | None:
        idx = self._cursor_idx
        if 0 <= idx < len(self.rows):
            return self.rows[idx]
        return None

    def _current_item(self) -> TaskRowItem | None:
        idx = self._cursor_idx
        return self._items[idx] if 0 <= idx < len(self._items) else None

    def action_cursor_up(self) -> None:
        if self._cursor_idx > 0:
            self._set_cursor(self._cursor_idx - 1)

    def action_cursor_down(self) -> None:
        if self._cursor_idx < len(self.rows) - 1:
            self._set_cursor(self._cursor_idx + 1)

    def action_follow_link(self) -> None:
        if self._editing:
            return
        row = self.current_row()
        if row is None:
            return
        if row.kind == "link_add":
            self.action_insert()
            return
        if row.kind == "link_item" and row.idx is not None:
            links = get_links(self.data)
            if row.idx < len(links):
                target_id = links[row.idx].get("target_node")
                if target_id:
                    self.app.navigate_to_id(target_id)  # type: ignore[attr-defined]

    # ── Edit ──────────────────────────────────────────────────────────────────

    def action_edit(self) -> None:
        if not self.path or self._editing:
            return
        row = self.current_row()
        item = self._current_item()
        if row and row.editable and item:
            self._editing = True
            if row.kind == "link_item" and row.idx is not None:
                links = get_links(self.data)
                edit_text = str(links[row.idx].get("description", "") or "") if row.idx < len(links) else ""
            else:
                edit_text = get_row_text(row, self.data)
            self._edit_original = edit_text
            item.begin_edit(edit_text)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if not self._editing:
            return
        row = self.current_row()
        item = self._current_item()
        if row and item:
            set_row_text(row, self.data, event.value)
            if self.path:
                save_task(self.path, self.data)
            item.end_edit()
            # if description changed, refresh title bar
            if row.field == "description":
                self._refresh_title()
        self._editing = False
        self._edit_original = ""
        self._edit_is_new = False
        self.focus()
        event.stop()

    def on_key(self, event) -> None:
        if self._editing and event.key == "escape":
            row = self.current_row()
            item = self._current_item()
            if self._edit_is_new:
                if item:
                    item.end_edit()
                self._editing = False
                self._edit_original = ""
                self._edit_is_new = False
                self.action_delete()
            else:
                if row:
                    set_row_text(row, self.data, self._edit_original)
                if item:
                    item.end_edit()
                self._editing = False
                self._edit_original = ""
            self.focus()
            event.stop()

    # ── Insert / Delete ───────────────────────────────────────────────────────

    def action_insert(self) -> None:
        row = self.current_row()
        if row is None or not self.path:
            return
        if row.kind not in ("link_header", "link_item", "link_add"):
            return
        link_type = row.field
        links = self.data.setdefault("links", [])
        # insert after current item, or at end of this type's group
        if row.kind == "link_item" and row.idx is not None:
            insert_at = row.idx + 1
        else:
            # after last link of this type
            positions = [i for i, l in enumerate(links) if l.get("type") == link_type]
            insert_at = (positions[-1] + 1) if positions else len(links)
        links.insert(insert_at, {"type": link_type, "description": ""})
        save_task(self.path, self.data)
        self.rows = build_rows(self.data)
        cursor_pos = 0
        for i, r in enumerate(self.rows):
            if r.kind == "link_item" and r.field == link_type and r.idx == insert_at:
                cursor_pos = i
                break
        self._rebuild(keep_cursor=cursor_pos)
        self._edit_is_new = True
        self.action_edit()

    def action_delete(self) -> None:
        row = self.current_row()
        if row is None or not self.path:
            return
        if row.kind == "link_item" and row.idx is not None:
            links = get_links(self.data)
            if row.idx < len(links):
                links.pop(row.idx)
            self.data["links"] = links
        elif row.kind == "simple" and row.field != "description":
            self.data.pop(row.field, None)
        elif row.kind == "text":
            self.data.pop(row.field, None)
        else:
            return
        save_task(self.path, self.data)
        self.rows = build_rows(self.data)
        self._rebuild(keep_cursor=max(0, min(self._cursor_idx, len(self.rows) - 1)))

    # ── Add field ─────────────────────────────────────────────────────────────

    def action_add_field(self) -> None:
        missing = []
        # scalar/text fields not yet present or empty
        for key, ftype in FIELDS.items():
            if key == "description":
                continue
            val = self.data.get(key)
            if not val or not str(val).strip():
                missing.append(key)
        # link types not yet used
        present_link_types = {l.get("type") for l in get_links(self.data)}
        for lt in LINK_TYPES:
            if lt.name not in present_link_types:
                missing.append(lt.name)
        if missing:
            self.app.push_screen(  # type: ignore[attr-defined]
                AddSectionModal(missing), self._on_field_chosen
            )

    def _on_field_chosen(self, field: str | None) -> None:
        if not field or not self.path:
            return
        if field in LINK_TYPE_MAP:
            # adding a link type section — create first empty link, open edit
            links = self.data.setdefault("links", [])
            insert_at = len(links)
            links.append({"type": field, "description": ""})
        else:
            self.data[field] = ""
        save_task(self.path, self.data)
        self.rows = build_rows(self.data)
        cursor_pos = 0
        for i, r in enumerate(self.rows):
            if r.field == field and r.kind not in ("link_header",):
                cursor_pos = i
                break
        self._rebuild(keep_cursor=cursor_pos)
        self._edit_is_new = True
        self.action_edit()

    # ── Linking ───────────────────────────────────────────────────────────────

    def action_back_to_nav(self) -> None:
        if not self._editing:
            self.app._show_file_nav()  # type: ignore[attr-defined]

    def action_link(self) -> None:
        """Open link picker. If on a link row, use that type; else ask for type first."""
        if self._editing or not self.path:
            return
        row = self.current_row()
        if row and row.kind in ("link_header", "link_item", "link_add"):
            link_type = row.field
            pending_idx = row.idx if row.kind == "link_item" else -1
            self.app._start_linking(link_type, pending_idx)  # type: ignore[attr-defined]
        else:
            # ask for link type first
            available = [lt.name for lt in LINK_TYPES]
            self.app.push_screen(  # type: ignore[attr-defined]
                AddSectionModal(available, title="Link type:"),
                self._on_link_type_chosen,
            )

    def _on_link_type_chosen(self, link_type: str | None) -> None:
        if link_type and self.path:
            self.app._start_linking(link_type, -1)  # type: ignore[attr-defined]

    def action_unlink(self) -> None:
        """Clear target_node from the current link_item."""
        if self._editing:
            return
        row = self.current_row()
        if row is None or row.kind != "link_item" or row.idx is None or not self.path:
            return
        links = get_links(self.data)
        if row.idx < len(links) and links[row.idx].get("target_node"):
            self.app.push_screen(  # type: ignore[attr-defined]
                ConfirmModal("Remove target from this link?"),
                lambda ok: self._on_unlink_confirmed(ok, row.idx),
            )

    def _on_unlink_confirmed(self, ok: bool, idx: int) -> None:
        if not ok or not self.path:
            return
        links = get_links(self.data)
        if idx < len(links):
            links[idx].pop("target_node", None)
        save_task(self.path, self.data)
        item = self._current_item()
        if item:
            item.refresh_label()


# ── Context pane ──────────────────────────────────────────────────────────────

STATUS_SYMBOLS: dict[str, str] = {
    "todo":      "·",
    "active":    "▶",
    "stuck":     "!",
    "done":      "✓",
    "discarded": "×",
}


class ContextPane(Widget):
    """Read-only right panel showing the local why/how subgraph."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._path: Path | None = None
        self._store: dict[Path, dict] = {}

    def compose(self) -> ComposeResult:
        yield Static("", id="context-content")

    def update_context(self, path: Path | None, store: dict[Path, dict]) -> None:
        self._path = path
        self._store = store
        self._rebuild()

    def _rebuild(self) -> None:
        try:
            widget = self.query_one("#context-content", Static)
        except Exception:
            return
        if not self._path:
            widget.update("")
            return

        data = self._store.get(self._path, {})
        desc = str(data.get("description", "") or "")
        status = str(data.get("status", "") or "")
        node_type = str(data.get("type", "") or "")

        why_nodes = traverse_subgraph(self._path, self._store, "up")
        how_nodes = traverse_subgraph(self._path, self._store, "down")

        t = Text(overflow="fold")

        # ── why subgraph ──────────────────────────────────────────────────────
        t.append("── why ", style="bold cyan")
        t.append("─" * 20 + "\n", style="dim")
        if why_nodes:
            for node in why_nodes:
                self._append_node(t, node)
        else:
            t.append("  (none)\n", style="dim")

        # ── current node ──────────────────────────────────────────────────────
        t.append("\n")
        sym = STATUS_SYMBOLS.get(status, "·")
        t.append(f" {sym} ", style=STATUS_STYLES.get(status, "dim"))
        t.append(desc or "—", style="bold")
        if node_type:
            t.append(f"  {node_type}", style=TYPE_STYLES.get(node_type, "dim"))
        t.append("\n\n")

        # ── how subgraph ──────────────────────────────────────────────────────
        t.append("── how ", style="bold cyan")
        t.append("─" * 20 + "\n", style="dim")
        if how_nodes:
            for node in how_nodes:
                self._append_node(t, node)
        else:
            t.append("  (none)\n", style="dim")

        # ── statistics ───────────────────────────────────────────────────────
        all_nodes = why_nodes + how_nodes
        if all_nodes:
            counts: dict[str, int] = {}
            for node in all_nodes:
                s = node["status"] or "?"
                counts[s] = counts.get(s, 0) + 1
            t.append("\n")
            t.append("─" * 27 + "\n", style="dim")
            total = len(all_nodes)
            t.append(f" {total} node{'s' if total != 1 else ''}  ", style="dim")
            parts = []
            for s, sym in STATUS_SYMBOLS.items():
                if s in counts:
                    parts.append((f"{sym}{counts[s]}", STATUS_STYLES.get(s, "dim")))
            for i, (part_text, part_style) in enumerate(parts):
                if i:
                    t.append("  ")
                t.append(part_text, style=part_style)
            t.append("\n")

        widget.update(t)

    def _append_node(self, t: Text, node: dict) -> None:
        indent = "  " * node["display_indent"]
        sym = STATUS_SYMBOLS.get(node["status"], " ") if node["status"] else " "
        style = STATUS_STYLES.get(node["status"], "dim") if node["status"] else "dim"
        t.append(f"{indent}{sym} ", style=style)
        t.append(node["description"] or "—")
        if node["in_degree"] > 1:
            t.append(f"  ×{node['in_degree']}", style="dim")
        t.append("\n")


# ── Add-section modal ─────────────────────────────────────────────────────────


class AddSectionModal(ModalScreen[Optional[str]]):
    CSS = """\
    AddSectionModal { align: center middle; }
    #modal-box {
        width: 40; height: auto; max-height: 20;
        border: solid $primary; background: $surface; padding: 1 2;
    }
    #modal-box > Label { margin-bottom: 1; }
    """
    BINDINGS = [Binding("escape", "dismiss", show=False)]

    def __init__(self, available: list[str], title: str = "Add field:") -> None:
        super().__init__()
        self._available = available
        self._title = title

    def compose(self) -> ComposeResult:
        with Vertical(id="modal-box"):
            yield Label(self._title)
            with ListView():
                for name in self._available:
                    yield ListItem(Label(name), id=f"section-{name}")

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        self.dismiss(event.item.id.removeprefix("section-"))


# ── App ───────────────────────────────────────────────────────────────────────

APP_CSS = """\
Screen { layout: vertical; }

#panes { height: 1fr; }

#left-col {
    width: 1fr;
    height: 1fr;
}

#mid-col {
    width: 2fr;
    height: 1fr;
}

#right-switcher {
    width: 2fr;
    height: 1fr;
}

ContextPane {
    width: 1fr;
    height: 1fr;
    border: solid $surface-lighten-2;
    padding: 0 1;
    layout: vertical;
}

ContextPane > Static {
    height: 1fr;
}

_AppHeader {
    height: 3;
    width: 1fr;
    padding: 0 2;
    background: $boost;
    border: solid $surface-lighten-2;
    text-style: bold;
    content-align: left middle;
}

FileNavPane, TaskPane, LinkPickerPane {
    width: 1fr;
    height: 1fr;
    border: solid $surface-lighten-2;
    padding: 0 1;
    layout: vertical;
}

FileNavPane:focus, TaskPane:focus, LinkPickerPane:focus {
    border: solid $primary;
}

LinkPickerPane {
    border: solid $accent;
}

#task-title {
    height: 1;
    width: 1fr;
    padding: 0 1;
    background: $boost;
}


_TaskList {
    height: 1fr;
    background: transparent;
    padding: 1 1 0 1;
}

TaskRowItem {
    height: 1;
    padding: 0 0;
    background: transparent;
}

TaskRowItem.--text {
    height: auto;
}

TaskRowItem > Label {
    width: 1fr;
    padding: 0;
    background: transparent;
}

TaskRowItem.--text > Label {
    height: auto;
}

TaskRowItem > Input {
    height: 1;
    border: none;
    padding: 0 1;
    background: $surface;
}

/* Disable ListView's default highlight — we use Rich `reverse` on the label text instead */
TaskRowItem.--highlight {
    background: transparent;
}
"""


class PfqApp(App):
    CSS = APP_CSS
    ENABLE_COMMAND_PALETTE = False

    BINDINGS = [
        Binding("b", "go_back", "Back", show=True),
        Binding("q", "quit", "Quit", show=True),
    ]

    def __init__(self, path: Path | None = None) -> None:
        super().__init__()
        self._initial_path = path
        self._history: list[Path] = []
        vault = path.parent if path else Path("data")
        self.store: dict[Path, dict] = load_all(vault)

    def compose(self) -> ComposeResult:
        vault = self._initial_path.parent if self._initial_path else Path("data")
        yield Horizontal(
            Vertical(
                _AppHeader(" pourquoifaire", id="app-header"),
                FileNavPane(vault, self.store, id="file-nav"),
                id="left-col",
            ),
            Vertical(
                ContentSwitcher(
                    TaskPane(self._initial_path, id="task-pane"),
                    LinkPickerPane(vault, self.store, id="link-picker"),
                    initial="task-pane",
                    id="right-switcher",
                ),
                id="mid-col",
            ),
            ContextPane(id="context-pane"),
            id="panes",
        )
        yield Footer()

    def on_mount(self) -> None:
        if self._initial_path:
            self.query_one("#task-pane", TaskPane).focus()
        else:
            self.query_one("#file-nav", FileNavPane).focus()

    # ── Panel switching ───────────────────────────────────────────────────────

    def _show_file_nav(self) -> None:
        self._cancel_link()
        self.query_one("#file-nav", FileNavPane).focus()

    def _show_task_pane(self) -> None:
        self.query_one("#task-pane", TaskPane).focus()

    # ── Linking ───────────────────────────────────────────────────────────────

    def _start_linking(self, link_type: str, link_idx: int) -> None:
        pane = self.query_one("#task-pane", TaskPane)
        pane._link_pending_type = link_type
        pane._link_pending_idx = link_idx
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
        if not pane.path or pane._link_pending_type is None:
            self._cancel_link()
            return
        target_id = get_task_id(path)
        link_type = pane._link_pending_type
        link_idx = pane._link_pending_idx
        links = pane.data.setdefault("links", [])
        if link_idx >= 0 and link_idx < len(links):
            links[link_idx]["target_node"] = target_id
        else:
            links.append({"type": link_type, "target_node": target_id})
        save_task(pane.path, pane.data)
        pane.rows = build_rows(pane.data)
        pane._rebuild(keep_cursor=pane._cursor_idx)
        pane._link_pending_type = None
        pane._link_pending_idx = -1
        self._cancel_link()
        self._refresh_context()

    def _cancel_link(self) -> None:
        right = self.query_one("#right-switcher", ContentSwitcher)
        if right.current == "link-picker":
            right.current = "task-pane"
            self.query_one("#task-pane", TaskPane).focus()

    def _create_and_link(self) -> None:
        pane = self.query_one("#task-pane", TaskPane)
        default = ""
        if pane._link_pending_idx >= 0:
            links = get_links(pane.data)
            if pane._link_pending_idx < len(links):
                default = str(links[pane._link_pending_idx].get("description", "") or "")
        self.push_screen(NewTaskModal(default), self._on_new_task_for_link)

    def _on_new_task_for_link(self, description: str | None) -> None:
        if not description:
            return
        from datetime import date
        vault = self.query_one("#file-nav", FileNavPane).vault
        path = new_filepath(description, vault)
        data: dict = {
            "description": description,
            "type": "task",
            "status": "todo",
            "start_date": date.today().isoformat(),
        }
        save_task(path, data)
        self.store[path] = data
        self.query_one("#file-nav", FileNavPane).notify_file_added(path, data)
        self._apply_link(path)

    # ── File navigation ───────────────────────────────────────────────────────

    def _open_in_task_pane(self, path: Path) -> None:
        self._open_file(path)
        self._show_task_pane()

    def navigate_to_id(self, link_id: str) -> None:
        pane = self.query_one("#task-pane", TaskPane)
        if not pane.path:
            return
        target = find_path_by_id(link_id, self.store)
        if target:
            self._history.append(pane.path)
            self._open_file(target)

    def action_go_back(self) -> None:
        if self._history:
            self._open_file(self._history.pop())

    def _refresh_context(self) -> None:
        pane = self.query_one("#task-pane", TaskPane)
        self.query_one("#context-pane", ContextPane).update_context(pane.path, self.store)

    def _open_file(self, path: Path) -> None:
        pane = self.query_one("#task-pane", TaskPane)
        pane.path = path
        data = self.store.get(path) or load_task(path)
        self.store[path] = data  # ensure store holds the live dict
        pane.data = data
        pane.rows = build_rows(pane.data)
        pane._refresh_title()
        pane._rebuild()
        nav = self.query_one("#file-nav", FileNavPane)
        if path in nav._files:
            nav.cursor = nav._files.index(path)
        self._refresh_context()
