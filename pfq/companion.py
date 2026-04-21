"""CompanionPanel — HAL-style inner voice, docked at the bottom of the TUI."""
from __future__ import annotations

from rich.text import Text
from textual.widgets import Static

HAL = {
    "bg":          "#1a1a1e",   # near-black, cool gray
    "border":      "#7a3030",   # muted dark red
    "dot":         "#cc3322",   # HAL eye — active
    "dot_dim":     "#663322",   # HAL eye — thinking
    "text":        "#c05050",   # warm red text
    "text_bright": "#e07060",   # brighter red for main message
}

PLACEHOLDER_MESSAGE = (
    ">> I notice this node sits between two active threads with no clear connection.\n"
    "   What holds them together for you?\n\n"
    "  _A_ They share a constraint I haven't named yet\n"
    "  _B_ One is a fallback for the other\n"
    "  _C_ They don't — I should unlink one"
)


# ── Spinner frames ─────────────────────────────────────────────────────────────

def _build_hal_frames() -> list[list[str]]:
    """Build ASCII spinner: dot orbiting a 6×6 box perimeter (20 positions)."""
    W, H = 6, 6
    perimeter: list[tuple[int, int]] = []
    for c in range(W):              perimeter.append((0, c))           # top L→R
    for r in range(1, H):           perimeter.append((r, W - 1))       # right T→B
    for c in range(W - 2, -1, -1):  perimeter.append((H - 1, c))      # bottom R→L
    for r in range(H - 2, 0, -1):   perimeter.append((r, 0))          # left B→T

    def base_grid() -> list[list[str]]:
        g = [["·"] * W for _ in range(H)]
        g[0][0] = "╭"; g[0][W-1] = "╮"
        g[H-1][0] = "╰"; g[H-1][W-1] = "╯"
        for c in range(1, W-1): g[0][c] = "─"; g[H-1][c] = "─"
        for r in range(1, H-1): g[r][0] = "│"; g[r][W-1] = "│"
        for r in range(1, H-1):
            for c in range(1, W-1): g[r][c] = " "
        return g

    frames = []
    for pr, pc in perimeter:
        g = base_grid()
        g[pr][pc] = "●"
        frames.append(["".join(row) for row in g])
    return frames


_HAL_FRAMES = _build_hal_frames()


# ── Panel widget ───────────────────────────────────────────────────────────────

class CompanionPanel(Static):
    """HAL-style inner voice panel, docked at the bottom."""

    DEFAULT_CSS = f"""
    CompanionPanel {{
        layer: overlay;
        dock: bottom;
        margin: 1 4 2 4;
        width: 75%;
        height: auto;
        max-height: 12;
        background: {HAL['bg']};
        border: round {HAL['border']};
        padding: 1 2;
        display: none;
    }}
    CompanionPanel.visible {{
        display: block;
    }}
    """

    _frame_index: int = 0
    _timer = None
    _thinking: bool = False

    def render(self) -> Text:
        spinner_color = HAL["dot"] if not self._thinking else HAL["dot_dim"]
        frame = _HAL_FRAMES[self._frame_index]
        msg_lines = PLACEHOLDER_MESSAGE.split("\n")

        result = Text()
        for i, spin_line in enumerate(frame):
            for ch in spin_line:
                if ch == "●":
                    result.append(ch, style=f"bold {spinner_color}")
                else:
                    result.append(ch, style=HAL["border"])
            result.append("  ")
            if i < len(msg_lines):
                result.append(msg_lines[i], style=HAL["text_bright"])
            result.append("\n")

        result.append("\n")
        result.append("  ✦ response cached", style=f"dim {HAL['text']}")
        result.append("   ")
        result.append("F5", style=f"bold {HAL['text']}")
        result.append(" recompute", style=f"dim {HAL['text']}")
        result.append("   ")
        result.append("F2", style=f"bold {HAL['text']}")
        result.append(" hide", style=f"dim {HAL['text']}")
        return result

    def start_thinking(self) -> None:
        self._thinking = True
        self._frame_index = 0
        self._timer = self.set_interval(0.15, self._tick)
        self.refresh()

    def stop_thinking(self) -> None:
        self._thinking = False
        if self._timer:
            self._timer.stop()
            self._timer = None
        self.refresh()

    def _tick(self) -> None:
        self._frame_index = (self._frame_index + 1) % len(_HAL_FRAMES)
        self.refresh()
