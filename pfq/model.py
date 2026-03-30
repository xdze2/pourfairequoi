from __future__ import annotations

import os
import random
import re
import string
from pathlib import Path

import yaml

VAULT = Path("data")


def generate_id(length: int = 6) -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w]+", "_", text)
    return text.strip("_")[:40]


def new_filepath(description: str, vault: Path = VAULT) -> Path:
    vault.mkdir(parents=True, exist_ok=True)
    return vault / f"{generate_id()}_{slugify(description)}.yaml"


def load_task(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def save_task(path: Path, data: dict) -> None:
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
    os.replace(tmp, path)


def find_file_by_id(task_id: str, vault: Path) -> Path | None:
    """Find a YAML file whose stem starts with the given ID (case-insensitive)."""
    if not vault.exists():
        return None
    for p in sorted(vault.iterdir()):
        if p.suffix in (".yaml", ".yml"):
            if p.stem.upper().startswith(task_id.upper()):
                return p
    return None


def extract_link(line: str) -> str | None:
    """Return the task_id from a trailing #tag, or None."""
    m = re.search(r"#(\w+)\s*$", line)
    return m.group(1) if m else None
