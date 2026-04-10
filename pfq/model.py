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


def get_task_id(path: Path) -> str:
    """Return the ID prefix of a task filename (e.g. 'M11AB' from 'M11AB_slug.yaml')."""
    return path.stem.split("_")[0]


def find_file_by_id(task_id: str, vault: Path) -> Path | None:
    if not vault.exists():
        return None
    for p in sorted(vault.iterdir()):
        if p.suffix in (".yaml", ".yml"):
            if p.stem.upper().startswith(task_id.upper()):
                return p
    return None


def find_path_by_id(task_id: str, store: dict[Path, dict]) -> Path | None:
    task_id_upper = task_id.upper()
    for p in store:
        if p.stem.upper().startswith(task_id_upper):
            return p
    return None


# ── Section accessors ─────────────────────────────────────────────────────────

def get_how(data: dict) -> list[dict]:
    """Return the how list. Each entry is either:
      {"target_node": ID}                 — file node reference
      {"type": ..., "description": ...}   — in-file node (inline)
    """
    how = data.get("how")
    if isinstance(how, list):
        return how
    return []


def get_constrain(data: dict) -> list[dict]:
    """Return the constrain list."""
    constrain = data.get("constrain")
    if isinstance(constrain, list):
        return constrain
    return []


def is_inline(entry: dict) -> bool:
    """True if this how entry is an in-file node (not a file node reference)."""
    return "target_node" not in entry


def promote_inline(
    parent_path: Path,
    how_index: int,
    store: dict[Path, dict],
) -> Path:
    """
    Promote an inline how entry to a file node.
    Replaces the inline dict in the parent with {"target_node": new_id}.
    Saves the parent and adds the new file to the store.
    Returns the new file path.
    """
    parent_data = store[parent_path]
    how = get_how(parent_data)
    inline = how[how_index]

    description = str(inline.get("description", "") or "untitled")
    new_path = new_filepath(description, parent_path.parent)

    # Build the new file node data
    new_data: dict = {}
    for key in ("type", "description", "status", "start_date", "due_date", "horizon", "notes", "conclusion"):
        if key in inline:
            new_data[key] = inline[key]
    if "description" not in new_data:
        new_data["description"] = description

    save_task(new_path, new_data)
    store[new_path] = new_data

    # Replace inline entry with file reference in parent
    how[how_index] = {"target_node": get_task_id(new_path)}
    save_task(parent_path, parent_data)

    return new_path


# ── Graph algorithms ──────────────────────────────────────────────────────────

def sort_globally(store: dict[Path, dict]) -> list[tuple[Path, int]]:
    """
    Order all file nodes from most abstract (top) to most concrete (bottom).

    Each node declares its children via how: entries with target_node.
    Roots = nodes not referenced as a child by any other node.
    Indentation formula: max(0, depth - max(0, in_degree - 1))
    """
    id_to_path: dict[str, Path] = {get_task_id(p): p for p in store}

    # how_children[A] = file nodes that A declares as how children
    how_children: dict[Path, list[Path]] = {p: [] for p in store}
    # in_degree[B] = number of file nodes that declare B as a how child
    in_degree: dict[Path, int] = {p: 0 for p in store}
    has_parent: set[Path] = set()

    for path, data in store.items():
        for entry in get_how(data):
            target_id = (entry.get("target_node") or "").upper()
            if not target_id:
                continue
            target_path = id_to_path.get(target_id)
            if target_path and target_path != path:
                how_children[path].append(target_path)
                in_degree[target_path] = in_degree.get(target_path, 0) + 1
                has_parent.add(target_path)

    roots = sorted(p for p in store if p not in has_parent)

    visited: dict[Path, int] = {}
    queue: list[tuple[Path, int]] = []
    for p in roots:
        visited[p] = 0
        queue.append((p, 0))

    head = 0
    while head < len(queue):
        current_path, current_depth = queue[head]
        head += 1
        for child in how_children.get(current_path, []):
            if child not in visited:
                visited[child] = current_depth + 1
                queue.append((child, current_depth + 1))

    result: list[tuple[Path, int]] = []
    for path, depth in queue:
        deg = in_degree.get(path, 0)
        display_indent = 0 if deg == 0 else max(1, depth - max(0, deg - 1))
        result.append((path, display_indent))

    for p in sorted(store):
        if p not in visited:
            result.append((p, 0))

    return result


def traverse_subgraph(
    start_path: Path,
    store: dict[Path, dict],
    direction: str,  # "down" (how children) or "up" (parents that declare us)
) -> list[dict]:
    """
    BFS traversal from start_path.

    "down": follow how → target_node entries declared in each node.
    "up":   scan the store for nodes that declare start_path as a how child.

    Returns a list of node dicts:
      path, data, description, status, depth, in_degree, display_indent
    Inline how entries are included in "down" at depth 1 (no further traversal).
    """
    id_to_path: dict[str, Path] = {get_task_id(p): p for p in store}
    start_id = get_task_id(start_path).upper()

    def how_file_children(path: Path) -> list[Path]:
        result = []
        for entry in get_how(store.get(path, {})):
            tid = (entry.get("target_node") or "").upper()
            if tid:
                tp = id_to_path.get(tid)
                if tp and tp != path:
                    result.append(tp)
        return result

    def how_parents(path: Path) -> list[Path]:
        path_id = get_task_id(path).upper()
        result = []
        for p, data in store.items():
            if p == path:
                continue
            for entry in get_how(data):
                if (entry.get("target_node") or "").upper() == path_id:
                    result.append(p)
                    break
        return result

    neighbors = how_file_children if direction == "down" else how_parents

    visited: dict[Path, int] = {}
    in_degree: dict[Path, int] = {}
    queue: list[tuple[Path, int]] = []

    for neighbor in neighbors(start_path):
        if neighbor == start_path:
            continue
        in_degree[neighbor] = in_degree.get(neighbor, 0) + 1
        if neighbor not in visited:
            visited[neighbor] = 1
            queue.append((neighbor, 1))

    head = 0
    while head < len(queue):
        current_path, current_depth = queue[head]
        head += 1
        for neighbor in neighbors(current_path):
            if neighbor == start_path:
                continue
            in_degree[neighbor] = in_degree.get(neighbor, 0) + 1
            if neighbor not in visited:
                visited[neighbor] = current_depth + 1
                queue.append((neighbor, current_depth + 1))

    # Inline how entries (down only, depth 1, no further traversal)
    inline_nodes: list[dict] = []
    if direction == "down":
        for entry in get_how(store.get(start_path, {})):
            if is_inline(entry):
                inline_nodes.append({
                    "path": None, "data": entry,
                    "description": str(entry.get("description", "") or ""),
                    "status": str(entry.get("status", "") or ""),
                    "depth": 1, "in_degree": 1, "display_indent": 1,
                })

    result: list[dict] = list(inline_nodes)
    for path, depth in visited.items():
        deg = in_degree.get(path, 1)
        data = store.get(path, {})
        display_indent = max(1, depth - (deg - 1))
        result.append({
            "path": path, "data": data,
            "description": str(data.get("description", "") or get_task_id(path)),
            "status": str(data.get("status", "") or ""),
            "depth": depth, "in_degree": deg, "display_indent": display_indent,
        })

    result.sort(key=lambda n: (n["display_indent"], -n["in_degree"], n["depth"]))
    return result


def score_tasks(query: str, store: dict[Path, dict]) -> dict[Path, float]:
    """Score each task by word overlap with query (Jaccard similarity)."""
    _STOP = {"a", "an", "the", "to", "of", "and", "or", "in", "for", "is", "it"}

    def tokenize(text: str) -> set[str]:
        words = re.sub(r"[^\w]+", " ", text.lower()).split()
        return {w for w in words if w not in _STOP and len(w) > 1}

    query_words = tokenize(query)
    if not query_words:
        return {p: 0.0 for p in store}

    scores: dict[Path, float] = {}
    for path, data in store.items():
        desc = str(data.get("description", "") or "")
        task_words = tokenize(desc)
        overlap = len(query_words & task_words)
        union = len(query_words | task_words)
        scores[path] = overlap / union if union else 0.0
    return scores


def migrate_task(data: dict) -> dict:
    """Convert old-format tasks (links: list) to new how:/constrain: format."""
    from .config import CONSTRAIN_TYPE_MAP

    old_links = data.pop("links", None)
    if not isinstance(old_links, list):
        return data

    how: list[dict] = list(data.get("how") or [])
    constrain: list[dict] = list(data.get("constrain") or [])

    for link in old_links:
        ltype = link.get("type", "")
        desc = link.get("description", "")
        target = link.get("target_node")

        if ltype == "how":
            entry: dict = {}
            if target:
                entry["target_node"] = target
            if desc:
                entry["description"] = desc
            if entry:
                how.append(entry)
        elif ltype == "why":
            # old why links become nothing — parents will now declare how
            pass
        elif ltype in CONSTRAIN_TYPE_MAP or ltype in ("need", "required_by", "or"):
            mapped = "alternative_to" if ltype == "or" else ltype
            entry = {"type": mapped}
            if desc:
                entry["description"] = desc
            if target:
                entry["target_node"] = target
            constrain.append(entry)

    if how:
        data["how"] = how
    if constrain:
        data["constrain"] = constrain
    return data
