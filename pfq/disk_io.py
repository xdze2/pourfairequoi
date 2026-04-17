from __future__ import annotations

import os
import random
import re
import string
from pathlib import Path

import yaml

DEFAULT_VAULT_PATH = Path("data")


# ── Low-level helpers ─────────────────────────────────────────────────────────


def _generate_id(length: int = 6) -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))


def _slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w]+", "_", text)
    return text.strip("_")[:40]


def _new_filepath(description: str, vault: Path) -> Path:
    vault.mkdir(parents=True, exist_ok=True)
    return vault / f"{_generate_id()}_{_slugify(description)}.yaml"


# ── Node file operations ──────────────────────────────────────────────────────


def create_node(description: str, vault: Path) -> "Node":
    """Create a new YAML file and return the Node (not yet linked to anything)."""
    from pfq.model import Node, filename_to_node_id

    path = _new_filepath(description, vault)
    node_id = filename_to_node_id(path.stem)
    raw = {"description": description}
    path.write_text(yaml.dump(raw, allow_unicode=True, default_flow_style=False))
    return Node(node_id=node_id, description=description, filepath=str(path))


def delete_node_file(node: "Node") -> None:
    """Delete the node's YAML file from disk."""
    Path(node.filepath).unlink(missing_ok=True)


def save_node_fields(node: "Node") -> None:
    """Persist description, type, status back to the node's YAML file.
    The 'how' links and any unknown fields are preserved as-is."""
    path = Path(node.filepath)
    raw = yaml.safe_load(path.read_text()) or {}
    for field in ("description", "type", "status"):
        value = getattr(node, field)
        if value:
            raw[field] = value
        else:
            raw.pop(field, None)
    path.write_text(yaml.dump(raw, allow_unicode=True, default_flow_style=False))


# ── Vault-level I/O ───────────────────────────────────────────────────────────


def save_vault(graph: "NodeGraph") -> None:
    """Sync the full graph topology to disk.

    For each node, rewrites its YAML file's 'how' list to match the current
    in-memory links. All other fields (description, type, status, unknown keys)
    are preserved unchanged.
    """
    from pfq.model import filename_to_node_id

    for node in graph.nodes.values():
        path = Path(node.filepath)
        raw = yaml.safe_load(path.read_text()) or {}

        children = graph.get_children_ids(node.node_id)
        if children:
            # Use the filename stem as the target_node value (matches load format)
            child_stems = {}
            for other in graph.nodes.values():
                stem = Path(other.filepath).stem
                child_stems[other.node_id] = stem

            raw["how"] = [{"target_node": child_stems[cid]} for cid in children]
        else:
            raw.pop("how", None)

        path.write_text(yaml.dump(raw, allow_unicode=True, default_flow_style=False))
