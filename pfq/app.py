from pathlib import Path
from typing import Literal

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Label, ListItem, ListView

from pfq.disk_io import DEFAULT_VAULT_PATH
from pfq.model import Node, NodeGraph

INDENT = "   "  # per depth level
TYPE_W = 12
STATUS_W = 10

NodeRole = Literal["parent", "selected", "child"]

_ROLE_CONNECTOR     = {"parent": "┌─", "child": "└─"}
_ROLE_BOUNDARY_LABEL = {"parent": "why", "child": "how"}


def _chips(node: Node) -> str:
    type_ = (node.type or "")[:TYPE_W]
    status = (node.status or "")[:STATUS_W]
    return f"{type_:<{TYPE_W}}  {status}"


def _depth_markup(text: str, depth: int) -> str:
    """Wrap text in Rich markup for the given depth: 0 → bold, 2 → dim, else plain."""
    if depth == 0:
        return f"[bold]{text}[/bold]"
    if depth == 2:
        return f"[dim]{text}[/dim]"
    return text


def _styled_desc(desc: str, width: int, depth: int) -> str:
    """Pad description to width, then apply depth markup.

    Padding is applied before markup so tag characters don't skew alignment.
    """
    return _depth_markup(f"{desc:<{width}}", depth)


def _format_tree_row(role: NodeRole, depth: int, node: Node, *, boundary: bool = False) -> str:
    """Format a tree node as a display row from its semantic role and depth.

    role     │ connector │ depth meaning
    ─────────┼───────────┼──────────────────────────────
    parent   │ ┌─        │ distance to current node (dim at 2)
    selected │ —         │ always 0 → bold
    child    │ └─        │ distance from current node (dim at 2)

    boundary=True shows "why" (parent) or "how" (child) in the margin instead of " │ ".
    """
    desc = node.description or ""

    if role == "selected":
        return f" ▶   {_styled_desc(desc, 38, 0)} {_chips(node)}"

    margin = _ROLE_BOUNDARY_LABEL[role] if boundary else " │ "
    indent = INDENT * (depth - 1)
    connector = _depth_markup(_ROLE_CONNECTOR[role], depth)
    return f"{margin}  {indent}{connector} {_styled_desc(desc, 36, depth)} {_chips(node)}"


class PfqApp(App):
    TITLE = "pfq"
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("h", "go_home", "Home"),
        Binding("escape", "go_back", "Back"),
    ]

    def __init__(self, vault_path: Path = DEFAULT_VAULT_PATH):
        super().__init__()
        self.graph = NodeGraph.load_from_disk(vault_path)
        self.current_node_id: str | None = None
        self.history: list[str | None] = []

    def compose(self) -> ComposeResult:
        yield ListView()
        yield Footer()

    async def on_mount(self) -> None:
        await self._show_home()

    # ── Views ──────────────────────────────────────────────────────────────────

    async def _show_home(self) -> None:
        self.current_node_id = None
        lv = self.query_one(ListView)
        await lv.clear()
        items = []
        for node_id in sorted(self.graph.get_roots()):
            node = self.graph.get_node(node_id)
            desc = node.description or ""
            text = f"  {_styled_desc(desc, 38, 0)} {_chips(node)}"
            items.append(ListItem(Label(text), id=f"n_{node_id}"))
        await lv.extend(items)

    async def _show_node(self, node_id: str) -> None:
        self.current_node_id = node_id
        lv = self.query_one(ListView)
        await lv.clear()

        parents = list(reversed(self.graph.get_parents_tree(node_id)))
        children = self.graph.get_childrens_tree(node_id)

        items = []

        # Root line
        items.append(ListItem(Label("    ─ root"), id="go_home"))

        # Parents — farthest first; farthest gets "why" boundary label
        for i, (node, depth) in enumerate(parents):
            items.append(ListItem(Label(_format_tree_row("parent", depth, node, boundary=(i == 0))), id=f"n_{node.node_id}"))

        # Current node
        current = self.graph.get_node(node_id)
        items.append(ListItem(Label(_format_tree_row("selected", 0, current)), id=f"n_{node_id}"))

        # Children — closest first; last gets "how" boundary label
        for i, (node, depth) in enumerate(children):
            items.append(ListItem(Label(_format_tree_row("child", depth, node, boundary=(i == len(children) - 1))), id=f"n_{node.node_id}"))

        await lv.extend(items)
        lv.index = 1 + len(parents)

    # ── Navigation ─────────────────────────────────────────────────────────────

    async def _navigate_to(self, node_id: str) -> None:
        self.history.append(self.current_node_id)
        await self._show_node(node_id)

    async def on_list_view_selected(self, event: ListView.Selected) -> None:
        item_id = event.item.id
        if item_id == "go_home":
            await self.action_go_home()
        elif item_id and item_id.startswith("n_"):
            node_id = item_id[2:]
            if node_id != self.current_node_id:
                await self._navigate_to(node_id)

    async def action_go_home(self) -> None:
        if self.current_node_id is not None:
            self.history.append(self.current_node_id)
            await self._show_home()

    async def action_go_back(self) -> None:
        if self.history:
            prev = self.history.pop()
            if prev is None:
                await self._show_home()
            else:
                await self._show_node(prev)
