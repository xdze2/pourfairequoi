from pathlib import Path

import click
from rich.console import Console
from rich.tree import Tree

from pfq.app import PfqApp
from pfq.disk_io import DEFAULT_VAULT_PATH, load_vault


def _export_mermaid(path: Path) -> None:
    graph = load_vault(path)

    def label(node_id: str) -> str:
        node = graph.nodes.get(node_id)
        desc = (node.description or node_id) if node else node_id
        return desc.replace('"', "'")

    lines = ["```mermaid", "graph TD"]
    seen_nodes: set[str] = set()
    for link in sorted(graph.links, key=lambda l: (l.parent_id, l.child_id)):
        lines.append(f'    {link.parent_id}["{label(link.parent_id)}"] --> {link.child_id}["{label(link.child_id)}"]')
        seen_nodes.add(link.parent_id)
        seen_nodes.add(link.child_id)
    for node_id in sorted(graph.nodes):
        if node_id not in seen_nodes:
            lines.append(f'    {node_id}["{label(node_id)}"]')
    lines.append("```")

    out_path = path.parent / f"{path.name}_mermaid_graph.md"
    out_path.write_text("\n".join(lines) + "\n")
    click.echo(f"Mermaid graph written to {out_path}")


def _export_tree(path: Path) -> None:
    graph = load_vault(path)
    visited: set[str] = set()

    def label(node_id: str) -> str:
        node = graph.nodes.get(node_id)
        desc = (node.description or node_id) if node else node_id
        return f"[bold]{node_id}[/bold] {desc}"

    def add_children(tree_node: Tree, node_id: str) -> None:
        for child_id in graph.get_children_ids(node_id):
            if child_id in visited:
                child = graph.nodes.get(child_id)
                desc = (child.description or child_id) if child else child_id
                tree_node.add(f"[dim]↑ {child_id} {desc}[/dim]")
            else:
                visited.add(child_id)
                branch = tree_node.add(label(child_id))
                add_children(branch, child_id)

    console = Console()
    for root_id in graph.get_roots():
        visited.add(root_id)
        root_tree = Tree(label(root_id))
        add_children(root_tree, root_id)
        console.print(root_tree)


EXPORT_FORMATS = click.Choice(["tree", "mermaid"])


@click.command()
@click.argument("vault_path", default=str(DEFAULT_VAULT_PATH), required=False)
@click.option("--export", "export_fmt", type=EXPORT_FORMATS, default=None, help="Export format: tree or mermaid.")
def cli(vault_path: str, export_fmt: str | None) -> None:
    """PourFaireQuoi — a why/how task manager.

    VAULT_PATH is the vault directory to open (default: data/).
    """
    path = Path(vault_path)
    if not path.exists():
        raise click.ClickException(f"Vault not found: {path}\nCreate it first with: mkdir -p {path}")
    if not path.is_dir():
        raise click.ClickException(f"Not a directory: {path}")
    if export_fmt == "mermaid":
        _export_mermaid(path)
    elif export_fmt == "tree":
        _export_tree(path)
    else:
        PfqApp(vault_path=path).run()


if __name__ == "__main__":
    cli()
