from __future__ import annotations

import random
import re
import string
from datetime import date
from pathlib import Path

import yaml

DEFAULT_VAULT_PATH = Path("data")

_STORED_FIELDS = (
    "description", "opened_at", "closed_at", "close_reason",
    "estimated_closing_date", "update_period", "comment",
)


# ── Low-level helpers ─────────────────────────────────────────────────────────


def filename_to_node_id(filename: str) -> str:
    return filename.split("_")[0].upper()


def _generate_id(length: int = 6) -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))


def _slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w]+", "_", text)
    return text.strip("_")[:40]


def _new_filepath(description: str, vault: Path) -> Path:
    vault.mkdir(parents=True, exist_ok=True)
    return vault / f"{_generate_id()}_{_slugify(description)}.yaml"


def _today() -> str:
    return date.today().isoformat()


def _iso(value) -> str | None:
    """Coerce a YAML date value (may be datetime.date or str) to ISO string."""
    if value is None:
        return None
    return str(value)


# ── Node file operations ──────────────────────────────────────────────────────


def create_node(description: str, vault: Path) -> "Node":
    """Create a new YAML file and return the Node (not yet linked to anything)."""
    from pfq.model import Node

    path = _new_filepath(description, vault)
    node_id = filename_to_node_id(path.stem)
    today = _today()
    raw = {"description": description, "opened_at": today}
    path.write_text(yaml.dump(raw, allow_unicode=True, default_flow_style=False))
    return Node(node_id=node_id, description=description, opened_at=today, filepath=str(path))


def delete_node_file(node: "Node") -> None:
    Path(node.filepath).unlink(missing_ok=True)


def save_node_fields(node: "Node") -> None:
    """Persist stored fields back to the node's YAML file.
    The 'how' links and any unknown fields are preserved as-is."""
    path = Path(node.filepath)
    raw = yaml.safe_load(path.read_text()) or {}

    for f in _STORED_FIELDS:
        value = getattr(node, f)
        if value is not None:
            raw[f] = value
        else:
            raw.pop(f, None)

    path.write_text(yaml.dump(raw, allow_unicode=True, default_flow_style=False))


# ── Vault-level I/O ───────────────────────────────────────────────────────────


def load_vault(vault_path: Path, today=None) -> "NodeGraph":
    """Load all nodes and links from YAML files in vault_path. Returns a NodeGraph
    with computed lifecycle fields populated."""
    from pfq.model import Link, Node, NodeGraph, compute_lifecycle

    graph = NodeGraph()
    for path in sorted(vault_path.glob("*.yaml")):
        node_id = filename_to_node_id(path.stem)
        raw = yaml.safe_load(path.read_text()) or {}
        graph.nodes[node_id] = Node(
            node_id=node_id,
            description=raw.get("description"),
            opened_at=_iso(raw.get("opened_at")),
            closed_at=_iso(raw.get("closed_at")),
            close_reason=raw.get("close_reason"),
            estimated_closing_date=_iso(raw.get("estimated_closing_date")),
            update_period=raw.get("update_period"),
            comment=raw.get("comment"),
            filepath=str(path),
        )

    for path in sorted(vault_path.glob("*.yaml")):
        parent_id = filename_to_node_id(path.stem)
        raw = yaml.safe_load(path.read_text()) or {}
        for entry in raw.get("how") or []:
            if isinstance(entry, dict) and "target_node" in entry:
                child_id = filename_to_node_id(entry["target_node"])
                if child_id in graph.nodes:
                    graph.links.add(Link(parent_id, child_id))
                    graph._child_order.setdefault(parent_id, []).append(child_id)

    compute_lifecycle(graph, today=today)
    return graph


def save_vault(graph: "NodeGraph") -> None:
    """Sync the full graph topology to disk."""
    for node in graph.nodes.values():
        path = Path(node.filepath)
        raw = yaml.safe_load(path.read_text()) or {}

        children = graph.get_children_ids(node.node_id)
        if children:
            child_stems = {other.node_id: Path(other.filepath).stem for other in graph.nodes.values()}
            raw["how"] = [{"target_node": child_stems[cid]} for cid in children]
        else:
            raw.pop("how", None)

        path.write_text(yaml.dump(raw, allow_unicode=True, default_flow_style=False))
