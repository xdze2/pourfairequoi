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


def load_all(vault: Path) -> dict[Path, dict]:
    result: dict[Path, dict] = {}
    if not vault.exists():
        return result
    for p in sorted(vault.iterdir()):
        if p.suffix in (".yaml", ".yml"):
            try:
                result[p] = load_task(p)
            except Exception:
                result[p] = {}
    return result


def save_task(path: Path, data: dict) -> None:
    from datetime import date
    data["last_modified"] = date.today().isoformat()
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


def get_task_id(path: Path) -> str:
    """Return the ID prefix of a task filename (e.g. 'M11AB' from 'M11AB_slug.yaml')."""
    return path.stem.split("_")[0]


def add_backlink(target_path: Path, field: str, source_id: str, description: str = "") -> None:
    """Append a backlink entry to target's field if not already present."""
    data = load_task(target_path)
    items = data.setdefault(field, [])
    if not isinstance(items, list):
        items = []
        data[field] = items
    if any(isinstance(i, str) and source_id.upper() in i.upper() for i in items):
        return
    entry = f"{description} #{source_id}".strip() if description else f"#{source_id}"
    items.append(entry)
    save_task(target_path, data)


def remove_backlink(target_path: Path, field: str, source_id: str) -> None:
    """Remove all entries containing source_id from target's field."""
    data = load_task(target_path)
    items = data.get(field)
    if not isinstance(items, list):
        return
    data[field] = [i for i in items if not (isinstance(i, str) and source_id.upper() in i.upper())]
    save_task(target_path, data)


def check_backlinks(vault: Path, store: dict[Path, dict] | None = None) -> list[dict]:
    """Return a list of backlink inconsistencies across all task files."""
    from .config import INVERSE_FIELDS
    data_cache = store if store is not None else load_all(vault)
    issues = []

    for path, data in data_cache.items():
        source_id = get_task_id(path)
        for field, inverse in INVERSE_FIELDS.items():
            for item in data.get(field, []):
                if not isinstance(item, str):
                    continue
                link_id = extract_link(item)
                if not link_id:
                    continue
                target_path = find_file_by_id(link_id, vault)
                if not target_path:
                    issues.append({
                        "type": "broken_link",
                        "file": path.name, "field": field, "link_id": link_id,
                    })
                    continue
                target_data = data_cache.get(target_path, load_task(target_path))
                target_items = target_data.get(inverse, [])
                has_backlink = any(
                    isinstance(i, str) and source_id.upper() in i.upper()
                    for i in (target_items if isinstance(target_items, list) else [])
                )
                if not has_backlink:
                    issues.append({
                        "type": "missing_backlink",
                        "file": path.name, "field": field,
                        "target": target_path.name, "inverse_field": inverse,
                        "source_id": source_id,
                        "description": str(data.get("description", "")),
                    })
    return issues
