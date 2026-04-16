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
