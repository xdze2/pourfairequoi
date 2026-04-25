"""Generate web_demo/data.json from a vault."""

import json
import sys
from datetime import date
from pathlib import Path

import click

repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

from pfq.disk_io import load_vault
from pfq.view import build_home_view, build_node_view, ViewRow


def row_to_dict(row: ViewRow) -> dict:
    d: dict = {"role": row.role}
    if row.node is None:
        return d
    n = row.node
    d["node_id"] = n.node_id
    d["description"] = n.description or ""
    d["is_leaf"] = row.is_leaf
    d["is_root"] = row.is_root
    d["bullet"] = row.bullet
    d["depth"] = row.depth
    d["index"] = row.index
    d["items_depths"] = [dep for (_, dep) in row.items]
    d["also_labels"] = row.also_labels
    d["when_label"] = row.when_label
    d["pulse_label"] = row.pulse_label
    d["close_reason"] = n.close_reason
    d["is_closed"] = n.is_closed
    d["comment"] = (n.comment or "").splitlines()[0] if n.comment else ""
    return d


def build_data(vault_path: Path) -> dict:
    today = date.today()
    graph = load_vault(vault_path, today=today)

    home_rows = [row_to_dict(r) for r in build_home_view(graph, today=today)]

    node_views = {}
    for node_id in graph.nodes:
        rows = build_node_view(graph, node_id, today=today)
        node_views[node_id] = [row_to_dict(r) for r in rows]

    # minimal node list for search
    nodes_list = [
        {"node_id": n.node_id, "description": n.description or ""}
        for n in graph.nodes.values()
    ]

    return {
        "home": home_rows,
        "views": node_views,
        "nodes": nodes_list,
    }


@click.command()
@click.argument("vault", default=None, required=False,
                type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--out", default=None, type=click.Path(dir_okay=False, path_type=Path),
              help="Output JSON path (default: web_demo/data.json)")
def main(vault: Path, out: Path):
    """Generate data.json for the web demo from VAULT (default: data/)."""
    if vault is None:
        vault = repo_root / "data"
        if not vault.exists():
            vault = repo_root / "tests" / "test_vault"
            click.echo(f"data/ not found, using {vault}", err=True)

    out_path = out or Path(__file__).parent / "data.json"
    data = build_data(vault)
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    click.echo(f"wrote {out_path}  ({len(data['views'])} nodes)")


if __name__ == "__main__":
    main()
