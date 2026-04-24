"""NotePanel — floating post-it display for the cursor node's note."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.widgets import Static


NOTE_BORDER = "#3a3a44"
NOTE_TEXT = "#c8c8d4"


class NotePanel(Static):
    """Display-only floating post-it docked top-right. Hidden when no note."""

    DEFAULT_CSS = f"""
    NotePanel {{
        layer: overlay;
        dock: right;
        margin: 2 2 2 0;
        width: 32;
        height: 18;
        background: transparent;
        border: round {NOTE_BORDER};
        padding: 1 2;
        color: {NOTE_TEXT};
        display: none;
    }}
    NotePanel.visible {{
        display: block;
    }}
    """

    def compose(self) -> ComposeResult:
        yield Static("", id="note-content")

    def load_node(self, node_id: str | None, note: str | None) -> None:
        if note:
            self.query_one("#note-content", Static).update(note)
            self.add_class("visible")
        else:
            self.remove_class("visible")
