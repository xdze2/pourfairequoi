from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from rich.text import Text
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

from .config import CONSTRAIN_TYPE_MAP, CONSTRAIN_TYPES, FIELDS, STATUSES, TYPES
from .model import Store, find_path_by_id, get_constrain, get_how, get_task_id, is_inline, load_task


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
    kind: str  # "simple" | "text" | "spacer"
    # | "how_header" | "how_item" | "how_inline" | "how_add"
    # | "constrain_header" | "constrain_item" | "constrain_add"
    # | "why_header" | "why_item"
    field: str  # field name for simple/text; constrain type for constrain rows; "" otherwise
    idx: int | None  # index into how or constrain list; None for headers/add
    backlink_path: "Path | None" = None
    backlink_desc: str = ""

    @property
    def editable(self) -> bool:
        return self.kind in (
            "simple",
            "text",
            "how_item",
            "how_inline",
            "constrain_item",
        )


def build_rows(data: dict) -> list[Row]:
    rows: list[Row] = []

    # scalar / text fields — description always first
    rows.append(Row("simple", "description", None))
    for key, ftype in FIELDS.items():
        if key == "description" or key not in data:
            continue
        rows.append(Row("text" if ftype == "text" else "simple", key, None))

    # how section
    how = get_how(data)
    if how:
        rows.append(Row("how_header", "", None))
        for i, entry in enumerate(how):
            if is_inline(entry):
                rows.append(Row("how_inline", "", i))
            else:
                rows.append(Row("how_item", "", i))
        rows.append(Row("how_add", "", None))

    # constrain section — grouped by type
    constrain = get_constrain(data)
    if constrain:
        for ct in CONSTRAIN_TYPES:
            type_entries = [
                (i, e) for i, e in enumerate(constrain) if e.get("type") == ct.name
            ]
            if type_entries:
                rows.append(Row("constrain_header", ct.name, None))
                for i, _ in type_entries:
                    rows.append(Row("constrain_item", ct.name, i))
                rows.append(Row("constrain_add", ct.name, None))

    return rows


def build_backlink_rows(path: "Path", store: dict) -> list[Row]:
    """Derive 'why' rows by scanning for nodes that declare path as a how child."""
    current_id = get_task_id(path).upper()
    parents: list[tuple[Path, str]] = []
    for src_path, src_data in store.items():
        if src_path == path:
            continue
        for entry in get_how(src_data):
            if (entry.get("target_node") or "").upper() == current_id:
                desc = str(src_data.get("description", "") or get_task_id(src_path))
                parents.append((src_path, desc))
                break

    if not parents:
        return []

    rows: list[Row] = [Row("why_header", "", None)]
    for src_path, src_desc in parents:
        rows.append(
            Row("why_item", "", None, backlink_path=src_path, backlink_desc=src_desc)
        )
    return rows


def _resolve_entry_desc(entry: dict, store: dict) -> str:
    """Return description for a how or constrain entry, falling back to target node's description."""
    desc = str(entry.get("description", "") or "")
    if desc:
        return desc
    target_id = str(entry.get("target_node", "") or "")
    if target_id and store:
        target_path = find_path_by_id(target_id, store)
        if target_path:
            return str(store[target_path].get("description", "") or "")
    return ""


def get_row_text(row: Row, data: dict, store: dict | None = None) -> str:
    if row.kind in ("simple", "text"):
        return str(data.get(row.field) or "")
    _store = store or {}
    if row.kind in ("how_item", "how_inline") and row.idx is not None:
        how = get_how(data)
        if row.idx < len(how):
            return _resolve_entry_desc(how[row.idx], _store)
    if row.kind == "constrain_item" and row.idx is not None:
        constrain = get_constrain(data)
        if row.idx < len(constrain):
            return _resolve_entry_desc(constrain[row.idx], _store)
    return ""


def set_row_text(row: Row, data: dict, value: str) -> None:
    if row.kind in ("simple", "text"):
        data[row.field] = value
    elif row.kind in ("how_item", "how_inline") and row.idx is not None:
        how = get_how(data)
        if row.idx < len(how):
            how[row.idx]["description"] = value
    elif row.kind == "constrain_item" and row.idx is not None:
        constrain = get_constrain(data)
        if row.idx < len(constrain):
            constrain[row.idx]["description"] = value


_SPACER = Row("spacer", "", None)


# ── Style maps ────────────────────────────────────────────────────────────────

STATUS_STYLES: dict[str, str] = {k: v[1] for k, v in STATUSES.items()}
TYPE_STYLES: dict[str, str] = {k: v[1] for k, v in TYPES.items()}

# Fixed column widths for chip alignment (derived from config so they stay in sync)
_TYPE_COL = max(len(k) for k in TYPES)  # "constraint" = 10
_STATUS_COL = max(len(k) for k in STATUSES)  # "discarded"  = 9
_DATE_COL = 10  # ISO-8601 date: yyyy-mm-dd


def _pad(t: Text, text: str, width: int) -> None:
    """Append trailing spaces to reach `width` characters (no-op if text is already wider)."""
    gap = width - len(text)
    if gap > 0:
        t.append(" " * gap)


def _append_chips(t: Text, data: dict) -> None:
    """Append type / status / date in fixed-width columns for table alignment."""
    task_type = str(data.get("type", "") or "")
    status = str(data.get("status", "") or "")
    date = str(data.get("due_date", "") or data.get("start_date", "") or "")

    t.append("  ")
    if task_type:
        t.append(task_type.ljust(_TYPE_COL), style=TYPE_STYLES.get(task_type, "dim"))
    else:
        t.append(" " * _TYPE_COL)

    t.append("  ")
    if status:
        t.append(status.ljust(_STATUS_COL), style=STATUS_STYLES.get(status, "dim"))
    else:
        t.append(" " * _STATUS_COL)

    t.append("  ")
    if date:
        t.append(date, style="dim")
    else:
        t.append(" " * _DATE_COL)


class _AppHeader(Static):
    DEFAULT_CSS = "_AppHeader { height: 3; }"


class SubgraphPane(Widget, can_focus=True):
    """Left panel in node state: ancestors → ► current → descendants."""

    BINDINGS = [
        Binding("up", "cursor_up", show=False),
        Binding("down", "cursor_down", show=False),
        Binding("enter", "select_node", "Select", show=True),
        Binding("space", "preview_node", "Preview", show=False),
        Binding("n", "new_task", "New", show=True),
        Binding("d", "delete_task", "Delete", show=True),
    ]

    cursor: reactive[int] = reactive(0)

    def __init__(self, store, **kwargs):
        super().__init__(**kwargs)
        self.store = store
        self._center: Path | None = None
        self._entries: list[dict] = []
        self._scroll = 0

    def center_on(self, path: Path) -> None:
        self._center = path
        self._build_entries()
        self.refresh()

    def _build_entries(self) -> None:
        path = self._center
        if not path:
            self._entries = []
            return

        up_nodes = self.store.traverse(path, "up")
        down_nodes = self.store.traverse(path, "down")

        max_up = max((n["depth"] for n in up_nodes), default=0)
        up_sorted = sorted(up_nodes, key=lambda n: -n["depth"])

        entries: list[dict] = []
        for node in up_sorted:
            entries.append({
                "path": node["path"],
                "indent": max_up - node["depth"],
                "is_current": False,
                "description": node["description"],
                "status": node["status"],
            })

        data = self.store.get(path, {})
        entries.append({
            "path": path,
            "indent": max_up,
            "is_current": True,
            "description": str(data.get("description", "") or get_task_id(path)),
            "status": str(data.get("status", "") or ""),
        })

        down_sorted = sorted(down_nodes, key=lambda n: (n["display_indent"], n["depth"]))
        for node in down_sorted:
            entries.append({
                "path": node["path"],
                "indent": max_up + node["display_indent"],
                "is_current": False,
                "description": node["description"],
                "status": node["status"],
            })

        self._entries = entries
        for i, e in enumerate(entries):
            if e["is_current"]:
                self.cursor = i
                break

    def current_path(self) -> Path | None:
        if 0 <= self.cursor < len(self._entries):
            return self._entries[self.cursor]["path"]
        return None

    def render(self) -> Text:
        height = max(self.size.height - 1, 3)
        if self.cursor < self._scroll:
            self._scroll = self.cursor
        elif self._entries and self.cursor >= self._scroll + height:
            self._scroll = self.cursor - height + 1

        t = Text(no_wrap=True, overflow="ellipsis")
        for i, entry in enumerate(self._entries[self._scroll : self._scroll + height]):
            abs_i = i + self._scroll
            selected = abs_i == self.cursor
            indent = "  " * entry["indent"]
            marker = "► " if entry["is_current"] else "  "
            desc = entry["description"] or "—"
            status = entry["status"]
            line = Text(no_wrap=True, overflow="ellipsis")
            style = "bold" if entry["is_current"] else ""
            line.append(f"{indent}{marker}{desc}", style=style)
            if status:
                line.append(f"  {status}", style=STATUS_STYLES.get(status, "dim"))
            if selected:
                line.stylize("reverse")
            t.append_text(line)
            t.append("\n")
        return t

    def watch_cursor(self, _: int) -> None:
        self.refresh()

    def action_cursor_up(self) -> None:
        if self.cursor > 0:
            self.cursor -= 1

    def action_cursor_down(self) -> None:
        if self.cursor < len(self._entries) - 1:
            self.cursor += 1

    def action_select_node(self) -> None:
        path = self.current_path()
        if path:
            self.app._open_node(path)  # type: ignore[attr-defined]

    def action_preview_node(self) -> None:
        path = self.current_path()
        if path:
            self.app._preview_node(path)  # type: ignore[attr-defined]

    def action_new_task(self) -> None:
        self.app.push_screen(NewTaskModal(), self._on_new_task)  # type: ignore[attr-defined]

    def _on_new_task(self, description: str | None) -> None:
        if not description:
            return
        from datetime import date
        path, data = self.store.new_node(description)
        data.update({
            "description": description,
            "type": "task",
            "status": "todo",
            "start_date": date.today().isoformat(),
        })
        self.store.save(path, data)
        self.app._open_node(path)  # type: ignore[attr-defined]

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
        self.store.remove(path)
        if path == self._center:
            self.app.action_go_home()  # type: ignore[attr-defined]
        else:
            self._build_entries()
            self.refresh()


class HomePage(Widget, can_focus=True):
    """Startup view: root nodes + one level of children."""

    BINDINGS = [
        Binding("up", "cursor_up", show=False),
        Binding("down", "cursor_down", show=False),
        Binding("enter", "open_node", "Open", show=True),
        Binding("n", "new_task", "New", show=True),
    ]

    cursor: reactive[int] = reactive(0)

    def __init__(self, store, **kwargs):
        super().__init__(**kwargs)
        self.store = store
        self._entries: list[dict] = []
        self._scroll = 0

    def on_mount(self) -> None:
        self.refresh_entries()

    def refresh_entries(self) -> None:
        has_parent: set[Path] = set()
        for data in self.store._data.values():
            for entry in get_how(data):
                tid = (entry.get("target_node") or "").upper()
                if tid:
                    tp = self.store.find(tid)
                    if tp:
                        has_parent.add(tp)

        sorted_nodes = self.store.sort()
        entries: list[dict] = []
        seen: set[Path] = set()

        for path, _ in sorted_nodes:
            if path in has_parent:
                continue
            if path in seen:
                continue
            seen.add(path)
            data = self.store.get(path, {})
            entries.append({
                "path": path,
                "indent": 0,
                "description": str(data.get("description", "") or get_task_id(path)),
                "status": str(data.get("status", "") or ""),
                "type": str(data.get("type", "") or ""),
            })
            for entry in get_how(data):
                tid = (entry.get("target_node") or "").upper()
                if tid:
                    child_path = self.store.find(tid)
                    if child_path and child_path not in seen:
                        seen.add(child_path)
                        cd = self.store.get(child_path, {})
                        entries.append({
                            "path": child_path,
                            "indent": 1,
                            "description": str(cd.get("description", "") or get_task_id(child_path)),
                            "status": str(cd.get("status", "") or ""),
                            "type": str(cd.get("type", "") or ""),
                        })
                elif is_inline(entry):
                    entries.append({
                        "path": None,
                        "indent": 1,
                        "description": str(entry.get("description", "") or "(inline)"),
                        "status": str(entry.get("status", "") or ""),
                        "type": str(entry.get("type", "") or ""),
                    })

        self._entries = entries
        self.cursor = max(0, min(self.cursor, len(entries) - 1))
        self.refresh()

    def render(self) -> Text:
        height = max(self.size.height - 1, 3)
        if self.cursor < self._scroll:
            self._scroll = self.cursor
        elif self._entries and self.cursor >= self._scroll + height:
            self._scroll = self.cursor - height + 1

        t = Text(no_wrap=True, overflow="ellipsis")
        for i, entry in enumerate(self._entries[self._scroll : self._scroll + height]):
            abs_i = i + self._scroll
            selected = abs_i == self.cursor
            indent = "  " * entry["indent"]
            desc = entry["description"] or "—"
            status = entry["status"]
            task_type = entry["type"]
            line = Text(no_wrap=True, overflow="ellipsis")
            line.append(f"{indent} {desc}")
            if task_type:
                line.append(f"  {task_type}", style=TYPE_STYLES.get(task_type, "dim"))
            if status:
                line.append(f"  {status}", style=STATUS_STYLES.get(status, "dim"))
            if selected:
                line.stylize("reverse")
            t.append_text(line)
            t.append("\n")

        t.append(f" {len(self._entries)} node{'s' if len(self._entries) != 1 else ''}", style="dim")
        return t

    def watch_cursor(self, _: int) -> None:
        self.refresh()

    def action_cursor_up(self) -> None:
        if self.cursor > 0:
            self.cursor -= 1

    def action_cursor_down(self) -> None:
        if self.cursor < len(self._entries) - 1:
            self.cursor += 1

    def action_open_node(self) -> None:
        if 0 <= self.cursor < len(self._entries):
            path = self._entries[self.cursor]["path"]
            if path:
                self.app._open_node(path)  # type: ignore[attr-defined]

    def action_new_task(self) -> None:
        self.app.push_screen(NewTaskModal(), self._on_new_task)  # type: ignore[attr-defined]

    def _on_new_task(self, description: str | None) -> None:
        if not description:
            return
        from datetime import date
        path, data = self.store.new_node(description)
        data.update({
            "description": description,
            "type": "task",
            "status": "todo",
            "start_date": date.today().isoformat(),
        })
        self.store.save(path, data)
        self.app._open_node(path)  # type: ignore[attr-defined]


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
        self._scores: dict[Path, float] = {}
        self._searching = False
        self._query = ""
        self._scroll = 0

    def refresh_files(self, scores: dict[Path, float] | None = None) -> None:
        if scores is not None:
            self._scores = scores
        else:
            self._scores = {}
        self._apply_filter()

    def _apply_filter(self) -> None:
        q = self._query.lower()
        all_files = sorted(self.store.keys(), key=lambda p: -self._scores.get(p, 0.0))
        self._files = [
            p
            for p in all_files
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

    def __init__(
        self,
        row: Row,
        data: dict,
        store: dict | None = None,
        link_desc_width: int = 0,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._row = row
        self._data = data
        self._store = store or {}
        self._link_desc_width = link_desc_width

    def compose(self) -> ComposeResult:
        yield Label(self._make_renderable(), id="row-label")

    def on_mount(self) -> None:
        if self._row.kind == "text":
            self.add_class("--text")

    def watch_selected(self, _value: bool) -> None:
        self.refresh_label()

    def _make_renderable(self) -> Text:
        kind = self._row.kind

        if kind == "spacer":
            return Text("")

        if kind == "text":
            text = get_row_text(self._row, self._data)
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
            text = get_row_text(self._row, self._data)
            t.append(f" {self._row.field:<14}", style="dim")
            t.append(text)

        elif kind == "how_header":
            t.append(" ── how ", style="bold cyan")

        elif kind == "how_add":
            t.append("    +", style="dim")

        elif kind in ("how_item", "how_inline"):
            how = get_how(self._data)
            entry = (
                how[self._row.idx]
                if self._row.idx is not None and self._row.idx < len(how)
                else {}
            )
            desc = _resolve_entry_desc(entry, self._store)
            target = str(entry.get("target_node", "") or "")
            own_desc = str(entry.get("description", "") or "")
            t.append("    • ")
            t.append(desc, style="" if own_desc else "dim")
            _pad(t, desc, self._link_desc_width)
            if kind == "how_item" and target:
                target_path = find_path_by_id(target, self._store)
                if target_path:
                    _append_chips(t, self._store.get(target_path, {}))
                t.append(f"  #{target}", style="color(8)")
            else:
                _append_chips(t, entry)

        elif kind == "constrain_header":
            ct = CONSTRAIN_TYPE_MAP.get(self._row.field)
            label = ct.label if ct else self._row.field
            t.append(f" ── {label} ", style="bold magenta")

        elif kind == "constrain_add":
            t.append("    +", style="dim")

        elif kind == "constrain_item":
            constrain = get_constrain(self._data)
            entry = (
                constrain[self._row.idx]
                if self._row.idx is not None and self._row.idx < len(constrain)
                else {}
            )
            desc = _resolve_entry_desc(entry, self._store)
            target = str(entry.get("target_node", "") or "")
            own_desc = str(entry.get("description", "") or "")
            t.append("    • ")
            t.append(desc, style="" if own_desc else "dim")
            _pad(t, desc, self._link_desc_width)
            if target:
                target_path = find_path_by_id(target, self._store)
                if target_path:
                    _append_chips(t, self._store.get(target_path, {}))
                t.append(f"  #{target}", style="color(8)")
            else:
                _append_chips(t, entry)

        elif kind == "why_header":
            t.append(" ── why ", style="bold magenta")

        elif kind == "why_item":
            desc = self._row.backlink_desc or "—"
            t.append("    ← ", style="magenta")
            t.append(desc)
            _pad(t, desc, self._link_desc_width)
            if self._row.backlink_path:
                _append_chips(t, self._store.get(self._row.backlink_path, {}))

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

    DEFAULT_CSS = "_TaskTitle { height: 2; }"

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
        self._all_rows: list[Row] = list(self.rows)
        self._cursor_idx: int = 0
        self._items: list[TaskRowItem] = []
        self._editing: bool = False
        self._edit_original: str = ""
        self._edit_is_new: bool = False
        # pending link operation
        self._link_pending_section: str | None = None  # "how" | "constrain"
        self._link_pending_type: str | None = None  # constrain type name
        self._link_pending_idx: int = -1  # index in list, or -1 for new
        # why rows count (set by _rebuild, used for cursor conversion)
        self._n_why_rows: int = 0

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
        """Rebuild the displayed row list with blank-line spacers between sections.

        Display order:
            description
            [spacer]
            other scalar fields
            [spacer]
            why section
            [spacer]
            how section
            [spacer]
            each constrain group

        keep_cursor is an index into self.rows; we locate the target row by
        object identity in all_rows (spacers are new objects, so they are skipped).
        """
        lv = self._lv()
        lv.clear()
        self._items = []

        scalar_rows = [r for r in self.rows if r.kind in ("simple", "text")]
        section_rows = [r for r in self.rows if r.kind not in ("simple", "text")]

        why_rows: list[Row] = []
        if self.path:
            try:
                why_rows = build_backlink_rows(self.path, self.app.store)
            except Exception:
                pass
        self._n_why_rows = len(why_rows)

        # Split scalar_rows into description + metadata
        desc_rows = scalar_rows[:1]
        meta_rows = scalar_rows[1:]

        # Split section_rows into how group + per-type constrain groups
        how_group = [r for r in section_rows if r.kind.startswith("how_")]
        constrain_groups: list[list[Row]] = []
        cur: list[Row] = []
        for r in section_rows:
            if r.kind == "constrain_header":
                if cur:
                    constrain_groups.append(cur)
                cur = [r]
            elif r.kind in ("constrain_item", "constrain_add"):
                cur.append(r)
        if cur:
            constrain_groups.append(cur)

        # Assemble with spacers between non-empty sections
        def _join(*groups: list[Row]) -> list[Row]:
            result: list[Row] = []
            for g in groups:
                if not g:
                    continue
                if result:
                    result.append(Row("spacer", "", None))
                result.extend(g)
            return result

        all_rows = _join(
            desc_rows,
            meta_rows,
            why_rows,
            how_group,
            *constrain_groups,
        )

        # Locate keep_cursor target by object identity (skips spacers naturally)
        target = self.rows[keep_cursor] if 0 <= keep_cursor < len(self.rows) else None
        new_cursor = 0
        if target is not None:
            for i, r in enumerate(all_rows):
                if r is target:
                    new_cursor = i
                    break

        self._all_rows = all_rows
        self._cursor_idx = new_cursor

        # Compute max description width for column alignment
        _link_kinds = {"how_item", "how_inline", "constrain_item"}
        link_desc_width = 0
        for row in all_rows:
            if row.kind in _link_kinds:
                d = get_row_text(row, self.data, store=self.app.store)
                link_desc_width = max(link_desc_width, len(d))
            elif row.kind == "why_item":
                link_desc_width = max(link_desc_width, len(row.backlink_desc or ""))

        for i, row in enumerate(all_rows):
            item = TaskRowItem(
                row, self.data, store=self.app.store, link_desc_width=link_desc_width
            )
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
        rows = getattr(self, "_all_rows", self.rows)
        if 0 <= idx < len(rows):
            return rows[idx]
        return None

    def _current_item(self) -> TaskRowItem | None:
        idx = self._cursor_idx
        return self._items[idx] if 0 <= idx < len(self._items) else None

    def action_cursor_up(self) -> None:
        idx = self._cursor_idx - 1
        while idx >= 0 and self._all_rows[idx].kind == "spacer":
            idx -= 1
        if idx >= 0:
            self._set_cursor(idx)

    def action_cursor_down(self) -> None:
        rows = self._all_rows
        idx = self._cursor_idx + 1
        while idx < len(rows) and rows[idx].kind == "spacer":
            idx += 1
        if idx < len(rows):
            self._set_cursor(idx)

    def action_follow_link(self) -> None:
        if self._editing:
            return
        row = self.current_row()
        if row is None:
            return
        if row.kind in ("how_add", "constrain_add"):
            self.action_insert()
            return
        if row.kind == "how_item" and row.idx is not None:
            how = get_how(self.data)
            if row.idx < len(how):
                target_id = how[row.idx].get("target_node")
                if target_id:
                    self.app.navigate_to_id(target_id)  # type: ignore[attr-defined]
        elif row.kind == "how_inline" and row.idx is not None and self.path:
            # Promote inline node to file node, then navigate
            store = self.app.store
            new_path = store.promote_inline(self.path, row.idx)
            self.data = store[self.path]
            self.rows = build_rows(self.data)
            self._rebuild(keep_cursor=self._cursor_idx)
            self.app.navigate_to_id(get_task_id(new_path))  # type: ignore[attr-defined]
        elif row.kind == "why_item" and row.backlink_path:
            self.app._open_file(row.backlink_path)  # type: ignore[attr-defined]

    # ── Edit ──────────────────────────────────────────────────────────────────

    def action_edit(self) -> None:
        if not self.path or self._editing:
            return
        row = self.current_row()
        item = self._current_item()
        if row and row.editable and item:
            self._editing = True
            if row.kind in ("how_item", "how_inline") and row.idx is not None:
                how = get_how(self.data)
                edit_text = (
                    str(how[row.idx].get("description", "") or "")
                    if row.idx < len(how)
                    else ""
                )
            elif row.kind == "constrain_item" and row.idx is not None:
                constrain = get_constrain(self.data)
                edit_text = (
                    str(constrain[row.idx].get("description", "") or "")
                    if row.idx < len(constrain)
                    else ""
                )
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
                self.app.store.save(self.path, self.data)
            item.end_edit()
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

        if row.kind in ("how_header", "how_item", "how_inline", "how_add"):
            how = self.data.setdefault("how", [])
            if row.kind in ("how_item", "how_inline") and row.idx is not None:
                insert_at = row.idx + 1
            else:
                insert_at = len(how)
            how.insert(insert_at, {"description": ""})
            self.app.store.save(self.path, self.data)
            self.rows = build_rows(self.data)
            cursor_pos = 0
            for i, r in enumerate(self.rows):
                if r.kind == "how_inline" and r.idx == insert_at:
                    cursor_pos = i
                    break
            self._rebuild(keep_cursor=cursor_pos)
            self._edit_is_new = True
            self.action_edit()

        elif row.kind in ("constrain_header", "constrain_item", "constrain_add"):
            ct_name = row.field
            constrain = self.data.setdefault("constrain", [])
            if row.kind == "constrain_item" and row.idx is not None:
                insert_at = row.idx + 1
            else:
                positions = [
                    i for i, e in enumerate(constrain) if e.get("type") == ct_name
                ]
                insert_at = (positions[-1] + 1) if positions else len(constrain)
            constrain.insert(insert_at, {"type": ct_name, "description": ""})
            self.app.store.save(self.path, self.data)
            self.rows = build_rows(self.data)
            cursor_pos = 0
            for i, r in enumerate(self.rows):
                if (
                    r.kind == "constrain_item"
                    and r.field == ct_name
                    and r.idx == insert_at
                ):
                    cursor_pos = i
                    break
            self._rebuild(keep_cursor=cursor_pos)
            self._edit_is_new = True
            self.action_edit()

    def action_delete(self) -> None:
        row = self.current_row()
        if row is None or not self.path:
            return

        if row.kind in ("how_item", "how_inline") and row.idx is not None:
            how = get_how(self.data)
            if row.idx < len(how):
                how.pop(row.idx)
            self.data["how"] = how
        elif row.kind == "constrain_item" and row.idx is not None:
            constrain = get_constrain(self.data)
            if row.idx < len(constrain):
                constrain.pop(row.idx)
            self.data["constrain"] = constrain
        elif row.kind == "simple" and row.field != "description":
            self.data.pop(row.field, None)
        elif row.kind == "text":
            self.data.pop(row.field, None)
        else:
            return

        self.app.store.save(self.path, self.data)
        self.rows = build_rows(self.data)
        self._rebuild(keep_cursor=max(0, min(self._cursor_idx, len(self.rows) - 1)))

    # ── Add field ─────────────────────────────────────────────────────────────

    def action_add_field(self) -> None:
        missing = []
        for key, ftype in FIELDS.items():
            if key == "description":
                continue
            val = self.data.get(key)
            if not val or not str(val).strip():
                missing.append(key)
        if not get_how(self.data):
            missing.append("how")
        constrain = get_constrain(self.data)
        present_ct = {e.get("type") for e in constrain}
        for ct in CONSTRAIN_TYPES:
            if ct.name not in present_ct:
                missing.append(ct.name)
        if missing:
            self.app.push_screen(  # type: ignore[attr-defined]
                AddSectionModal(missing), self._on_field_chosen
            )

    def _on_field_chosen(self, field: str | None) -> None:
        if not field or not self.path:
            return
        if field == "how":
            how = self.data.setdefault("how", [])
            how.append({"description": ""})
            self.app.store.save(self.path, self.data)
            self.rows = build_rows(self.data)
            cursor_pos = 0
            for i, r in enumerate(self.rows):
                if r.kind == "how_inline" and r.idx == len(how) - 1:
                    cursor_pos = i
                    break
            self._rebuild(keep_cursor=cursor_pos)
            self._edit_is_new = True
            self.action_edit()
        elif field in CONSTRAIN_TYPE_MAP:
            constrain = self.data.setdefault("constrain", [])
            constrain.append({"type": field, "description": ""})
            self.app.store.save(self.path, self.data)
            self.rows = build_rows(self.data)
            cursor_pos = 0
            for i, r in enumerate(self.rows):
                if r.kind == "constrain_item" and r.field == field:
                    cursor_pos = i
                    break
            self._rebuild(keep_cursor=cursor_pos)
            self._edit_is_new = True
            self.action_edit()
        else:
            self.data[field] = ""
            self.app.store.save(self.path, self.data)
            self.rows = build_rows(self.data)
            cursor_pos = 0
            for i, r in enumerate(self.rows):
                if r.field == field and r.kind in ("simple", "text"):
                    cursor_pos = i
                    break
            self._rebuild(keep_cursor=cursor_pos)
            self._edit_is_new = True
            self.action_edit()

    # ── Linking ───────────────────────────────────────────────────────────────

    def action_back_to_nav(self) -> None:
        if not self._editing:
            try:
                self.app.query_one("#subgraph", SubgraphPane).focus()  # type: ignore[attr-defined]
            except Exception:
                pass

    def action_link(self) -> None:
        """Open link picker for the current section."""
        if self._editing or not self.path:
            return
        row = self.current_row()
        if row and row.kind in ("how_header", "how_item", "how_inline", "how_add"):
            pending_idx = row.idx if row.kind in ("how_item", "how_inline") else -1
            self.app._start_linking("how", None, pending_idx)  # type: ignore[attr-defined]
        elif row and row.kind in (
            "constrain_header",
            "constrain_item",
            "constrain_add",
        ):
            pending_idx = row.idx if row.kind == "constrain_item" else -1
            self.app._start_linking("constrain", row.field, pending_idx)  # type: ignore[attr-defined]
        else:
            available = ["how"] + [ct.name for ct in CONSTRAIN_TYPES]
            self.app.push_screen(  # type: ignore[attr-defined]
                AddSectionModal(available, title="Link as:"),
                self._on_link_type_chosen,
            )

    def _on_link_type_chosen(self, section: str | None) -> None:
        if not section or not self.path:
            return
        if section == "how":
            self.app._start_linking("how", None, -1)  # type: ignore[attr-defined]
        elif section in CONSTRAIN_TYPE_MAP:
            self.app._start_linking("constrain", section, -1)  # type: ignore[attr-defined]

    def action_unlink(self) -> None:
        """Clear target_node from the current link entry."""
        if self._editing:
            return
        row = self.current_row()
        if row is None or not self.path:
            return
        if row.kind == "how_item" and row.idx is not None:
            how = get_how(self.data)
            if row.idx < len(how) and how[row.idx].get("target_node"):
                self.app.push_screen(  # type: ignore[attr-defined]
                    ConfirmModal("Remove target from this link?"),
                    lambda ok: self._on_unlink_confirmed(ok, "how", row.idx),
                )
        elif row.kind == "constrain_item" and row.idx is not None:
            constrain = get_constrain(self.data)
            if row.idx < len(constrain) and constrain[row.idx].get("target_node"):
                self.app.push_screen(  # type: ignore[attr-defined]
                    ConfirmModal("Remove target from this link?"),
                    lambda ok: self._on_unlink_confirmed(ok, "constrain", row.idx),
                )

    def _on_unlink_confirmed(self, ok: bool, section: str, idx: int) -> None:
        if not ok or not self.path:
            return
        if section == "how":
            how = get_how(self.data)
            if idx < len(how):
                how[idx].pop("target_node", None)
        elif section == "constrain":
            constrain = get_constrain(self.data)
            if idx < len(constrain):
                constrain[idx].pop("target_node", None)
        self.app.store.save(self.path, self.data)
        self.rows = build_rows(self.data)
        self._rebuild(keep_cursor=self._cursor_idx)


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

#left-switcher {
    width: 1fr;
    height: 1fr;
}

#right-switcher {
    width: 2fr;
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

SubgraphPane, HomePage, TaskPane, LinkPickerPane {
    width: 1fr;
    height: 1fr;
    border: solid $surface-lighten-2;
    padding: 0 1;
    layout: vertical;
}

SubgraphPane:focus, HomePage:focus, TaskPane:focus, LinkPickerPane:focus {
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
        Binding("h", "go_home", "Home", show=True),
        Binding("b", "go_back", "Back", show=True),
        Binding("tab", "switch_focus", "Switch", show=True),
        Binding("q", "quit", "Quit", show=True),
    ]

    def __init__(self, path: Path | None = None) -> None:
        super().__init__()
        self._initial_path = path
        self._history: list[Path] = []
        vault = path.parent if path else Path("data")
        self.store = Store(vault)

    def compose(self) -> ComposeResult:
        vault = self._initial_path.parent if self._initial_path else Path("data")
        yield Horizontal(
            ContentSwitcher(
                HomePage(self.store, id="home-page"),
                SubgraphPane(self.store, id="subgraph"),
                initial="home-page",
                id="left-switcher",
            ),
            ContentSwitcher(
                TaskPane(self._initial_path, id="task-pane"),
                LinkPickerPane(vault, self.store, id="link-picker"),
                initial="task-pane",
                id="right-switcher",
            ),
            id="panes",
        )
        yield Footer()

    def on_mount(self) -> None:
        if self._initial_path:
            self._open_node(self._initial_path)
        else:
            self.query_one("#home-page", HomePage).focus()

    # ── Navigation ────────────────────────────────────────────────────────────

    def action_go_home(self) -> None:
        self._cancel_link()
        left = self.query_one("#left-switcher", ContentSwitcher)
        left.current = "home-page"
        home = self.query_one("#home-page", HomePage)
        home.refresh_entries()
        home.focus()

    def action_go_back(self) -> None:
        if self._history:
            path = self._history.pop()
            self._open_node(path, push_history=False)

    def action_switch_focus(self) -> None:
        left = self.query_one("#left-switcher", ContentSwitcher)
        right = self.query_one("#right-switcher", ContentSwitcher)
        # Determine which side is currently focused
        focused = self.focused
        left_ids = {"home-page", "subgraph"}
        right_ids = {"task-pane", "link-picker"}
        fid = focused.id if focused else None
        if fid in left_ids:
            # Move to right
            if right.current == "task-pane":
                self.query_one("#task-pane", TaskPane).focus()
            else:
                self.query_one("#link-picker", LinkPickerPane).focus()
        else:
            # Move to left
            if left.current == "home-page":
                self.query_one("#home-page", HomePage).focus()
            else:
                self.query_one("#subgraph", SubgraphPane).focus()

    def _open_node(self, path: Path, push_history: bool = True) -> None:
        """Switch to node state, center subgraph on path, open in task pane."""
        pane = self.query_one("#task-pane", TaskPane)
        if push_history and pane.path and pane.path != path:
            self._history.append(pane.path)

        # Update task pane
        data = self.store.get(path) or load_task(path)
        self.store[path] = data
        pane.path = path
        pane.data = data
        pane.rows = build_rows(data)
        pane._refresh_title()
        pane._rebuild()

        # Switch left to subgraph, center on path
        left = self.query_one("#left-switcher", ContentSwitcher)
        left.current = "subgraph"
        subgraph = self.query_one("#subgraph", SubgraphPane)
        subgraph.center_on(path)

        # Cancel any pending link picker
        self._cancel_link()

        # Focus task pane
        pane.focus()

    def _preview_node(self, path: Path) -> None:
        """Load node in task pane read-only; left panel stays centered."""
        data = self.store.get(path) or {}
        pane = self.query_one("#task-pane", TaskPane)
        pane.path = path
        pane.data = data
        pane.rows = build_rows(data)
        pane._refresh_title()
        pane._rebuild()
        # Do NOT focus task pane — left panel keeps focus

    def navigate_to_id(self, link_id: str) -> None:
        target = self.store.find(link_id)
        if target:
            self._open_node(target)

    # ── Linking ───────────────────────────────────────────────────────────────

    def _start_linking(
        self, section: str, constrain_type: str | None, link_idx: int
    ) -> None:
        pane = self.query_one("#task-pane", TaskPane)
        pane._link_pending_section = section
        pane._link_pending_type = constrain_type
        pane._link_pending_idx = link_idx
        query = ""
        if link_idx >= 0:
            if section == "how":
                how = get_how(pane.data)
                if link_idx < len(how):
                    query = str(how[link_idx].get("description", "") or "")
            elif section == "constrain":
                constrain = get_constrain(pane.data)
                if link_idx < len(constrain):
                    query = str(constrain[link_idx].get("description", "") or "")
        scores = self.store.score(query) if query else {}
        picker = self.query_one("#link-picker", LinkPickerPane)
        picker.refresh_files(scores=scores or None)
        picker.cursor = 0
        picker._searching = False
        picker._query = ""
        picker.refresh()
        self.query_one("#right-switcher", ContentSwitcher).current = "link-picker"
        picker.focus()

    def _apply_link(self, path: Path) -> None:
        pane = self.query_one("#task-pane", TaskPane)
        if not pane.path or pane._link_pending_section is None:
            self._cancel_link()
            return
        target_id = get_task_id(path)
        section = pane._link_pending_section
        constrain_type = pane._link_pending_type
        link_idx = pane._link_pending_idx

        if section == "how":
            how = pane.data.setdefault("how", [])
            if 0 <= link_idx < len(how):
                how[link_idx]["target_node"] = target_id
            else:
                how.append({"target_node": target_id})
        elif section == "constrain":
            constrain = pane.data.setdefault("constrain", [])
            if 0 <= link_idx < len(constrain):
                constrain[link_idx]["target_node"] = target_id
            else:
                constrain.append({"type": constrain_type, "target_node": target_id})

        self.store.save(pane.path, pane.data)
        pane.rows = build_rows(pane.data)
        pane._rebuild(keep_cursor=pane._cursor_idx)
        pane._link_pending_section = None
        pane._link_pending_type = None
        pane._link_pending_idx = -1
        self._cancel_link()

    def _cancel_link(self) -> None:
        right = self.query_one("#right-switcher", ContentSwitcher)
        if right.current == "link-picker":
            right.current = "task-pane"
            self.query_one("#task-pane", TaskPane).focus()

    def _create_and_link(self) -> None:
        pane = self.query_one("#task-pane", TaskPane)
        default = ""
        section = pane._link_pending_section
        link_idx = pane._link_pending_idx
        if link_idx >= 0 and section:
            if section == "how":
                how = get_how(pane.data)
                if link_idx < len(how):
                    default = str(how[link_idx].get("description", "") or "")
            elif section == "constrain":
                constrain = get_constrain(pane.data)
                if link_idx < len(constrain):
                    default = str(constrain[link_idx].get("description", "") or "")
        self.push_screen(NewTaskModal(default), self._on_new_task_for_link)

    def _on_new_task_for_link(self, description: str | None) -> None:
        if not description:
            return
        from datetime import date
        path, data = self.store.new_node(description)
        data.update({
            "description": description,
            "type": "task",
            "status": "todo",
            "start_date": date.today().isoformat(),
        })
        self.store.save(path, data)
        self._apply_link(path)
