from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Label, ListItem, ListView

from pfq.disk_io import DEFAULT_VAULT_PATH
from pfq.model import Node, NodeGraph

INDENT = "   "  # per depth level
TYPE_W = 12
STATUS_W = 10


def _chips(node: Node) -> str:
    type_ = (node.type or "")[:TYPE_W]
    status = (node.status or "")[:STATUS_W]
    return f"{type_:<{TYPE_W}}  {status}"


def _row(margin: str, depth: int, connector: str, node: Node) -> str:
    indent = INDENT * (depth - 1)
    desc = node.description or ""
    return f"{margin}  {indent}{connector} {desc:<36} {_chips(node)}"


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
            text = f"  {desc:<38} {_chips(node)}"
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

        # Parents — farthest first; first shown gets "why" label
        for i, (node, depth) in enumerate(parents):
            margin = "why" if i == 0 else " │ "
            items.append(
                ListItem(Label(_row(margin, depth, "┌─", node)), id=f"n_{node.node_id}")
            )

        # Current node
        current = self.graph.get_node(node_id)
        desc = current.description or ""
        items.append(
            ListItem(Label(f" ▶   {desc:<38} {_chips(current)}"), id=f"n_{node_id}")
        )

        # Children — closest first; last shown gets "how" label
        for i, (node, depth) in enumerate(children):
            margin = "how" if i == len(children) - 1 else " │ "
            items.append(
                ListItem(Label(_row(margin, depth, "└─", node)), id=f"n_{node.node_id}")
            )

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
