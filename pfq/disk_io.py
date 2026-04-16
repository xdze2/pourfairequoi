from __future__ import annotations

import os
import random
import re
import string
from pathlib import Path

import yaml

DEFAULT_VAULT_PATH = Path("data")


# ── Low-level file I/O (private helpers) ─────────────────────────────────────


def _generate_id(length: int = 6) -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))


def _slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w]+", "_", text)
    return text.strip("_")[:40]


def _new_filepath(description: str, vault: Path) -> Path:
    vault.mkdir(parents=True, exist_ok=True)
    return vault / f"{_generate_id()}_{_slugify(description)}.yaml"


def create_node(description: str, vault: Path) -> "Node":
    """Create a new YAML file and return the Node (not yet linked to anything)."""
    from pfq.model import Node, filename_to_node_id  # local import to avoid circular

    path = _new_filepath(description, vault)
    node_id = filename_to_node_id(path.stem)
    raw = {"description": description}
    path.write_text(yaml.dump(raw, allow_unicode=True, default_flow_style=False))
    return Node(node_id=node_id, description=description, filepath=str(path))


def add_child_link(parent_node: "Node", child_id: str, position: int) -> None:
    """Insert child_id into parent's how list at position and save."""
    path = Path(parent_node.filepath)
    raw = yaml.safe_load(path.read_text()) or {}
    how = raw.get("how") or []
    how.insert(position, {"target_node": child_id})
    raw["how"] = how
    path.write_text(yaml.dump(raw, allow_unicode=True, default_flow_style=False))


def remove_child_link(parent_node: "Node", child_id: str) -> None:
    """Remove all how entries pointing to child_id from parent and save."""
    path = Path(parent_node.filepath)
    raw = yaml.safe_load(path.read_text()) or {}
    how = raw.get("how") or []
    raw["how"] = [e for e in how if e.get("target_node") != child_id]
    path.write_text(yaml.dump(raw, allow_unicode=True, default_flow_style=False))


def delete_node_file(node: "Node") -> None:
    """Delete the node's YAML file from disk."""
    Path(node.filepath).unlink(missing_ok=True)


def save_node_fields(node: "Node") -> None:
    """Persist description, type, status back to the node's YAML file.
    The 'how' links and any unknown fields are preserved as-is."""
    from pfq.model import Node  # local import to avoid circular

    path = Path(node.filepath)
    raw = yaml.safe_load(path.read_text()) or {}
    for field in ("description", "type", "status"):
        value = getattr(node, field)
        if value:
            raw[field] = value
        else:
            raw.pop(field, None)
    path.write_text(yaml.dump(raw, allow_unicode=True, default_flow_style=False))
