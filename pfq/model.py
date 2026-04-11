from __future__ import annotations

import os
import random
import re
import string
from pathlib import Path

import yaml

_VAULT = Path("data")


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


def load_task(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


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


def find_path_by_id(task_id: str, store) -> Path | None:
    """Return the path whose filename starts with task_id (works with Store or dict)."""
    task_id_upper = task_id.upper()
    for p in store:
        if p.stem.upper().startswith(task_id_upper):
            return p
    return None


# ── Section accessors (pure, work on plain dicts) ─────────────────────────────


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


# ── Store ─────────────────────────────────────────────────────────────────────


class Store:
    """In-memory cache of all YAML nodes in a vault, with graph query methods.

    Supports dict-like read access so widgets can use store[path], store.get(),
    store.items(), etc. without needing to know about the class.
    """

    def __init__(self, vault: Path = _VAULT) -> None:
        self.vault = vault
        self._data: dict[Path, dict] = {}
        if vault.exists():
            for p in sorted(vault.iterdir()):
                if p.suffix in (".yaml", ".yml"):
                    try:
                        self._data[p] = load_task(p)
                    except Exception:
                        self._data[p] = {}

    # ── Dict-like interface ───────────────────────────────────────────────────

    def __getitem__(self, path: Path) -> dict:
        return self._data[path]

    def __setitem__(self, path: Path, data: dict) -> None:
        self._data[path] = data

    def __contains__(self, path: object) -> bool:
        return path in self._data

    def __iter__(self):
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def get(self, path: Path, default: dict | None = None) -> dict | None:
        return self._data.get(path, default)

    def keys(self):
        return self._data.keys()

    def items(self):
        return self._data.items()

    # ── Node lifecycle ────────────────────────────────────────────────────────

    def new_node(self, description: str) -> tuple[Path, dict]:
        """Create a new YAML file, register it in the store, return (path, data)."""
        path = _new_filepath(description, self.vault)
        data: dict = {}
        self._data[path] = data
        return path, data

    def save(self, path: Path, data: dict) -> None:
        """Persist data to disk and keep the store in sync."""
        save_task(path, data)
        self._data[path] = data

    def remove(self, path: Path) -> None:
        """Delete the file from disk and from the store."""
        path.unlink(missing_ok=True)
        self._data.pop(path, None)

    # ── Graph queries ─────────────────────────────────────────────────────────

    def find(self, task_id: str) -> Path | None:
        """Return the path whose filename starts with task_id (case-insensitive)."""
        task_id_upper = task_id.upper()
        for p in self._data:
            if p.stem.upper().startswith(task_id_upper):
                return p
        return None

    def sort(self) -> list[tuple[Path, int]]:
        """Order all nodes from most abstract (roots) to most concrete (leaves).

        Returns list of (path, display_indent).
        Roots = nodes not referenced as a how child by any other node.
        Indentation formula: 0 if root, else max(1, depth - max(0, in_degree - 1))
        """
        id_to_path: dict[str, Path] = {get_task_id(p): p for p in self._data}

        how_children: dict[Path, list[Path]] = {p: [] for p in self._data}
        in_degree: dict[Path, int] = {p: 0 for p in self._data}
        has_parent: set[Path] = set()

        for path, data in self._data.items():
            for entry in get_how(data):
                target_id = (entry.get("target_node") or "").upper()
                if not target_id:
                    continue
                target_path = id_to_path.get(target_id)
                if target_path and target_path != path:
                    how_children[path].append(target_path)
                    in_degree[target_path] = in_degree.get(target_path, 0) + 1
                    has_parent.add(target_path)

        roots = sorted(p for p in self._data if p not in has_parent)

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

        for p in sorted(self._data):
            if p not in visited:
                result.append((p, 0))

        return result

    def traverse(self, start_path: Path, direction: str) -> list[dict]:
        """BFS traversal from start_path.

        direction="down": follow how → target_node entries declared in each node.
        direction="up":   find nodes that declare start_path as a how child.

        Returns list of node dicts: path, data, description, status, depth,
        in_degree, display_indent.
        Inline how entries are included in "down" at depth 1.
        """
        id_to_path: dict[str, Path] = {get_task_id(p): p for p in self._data}

        def how_file_children(path: Path) -> list[Path]:
            result = []
            for entry in get_how(self._data.get(path, {})):
                tid = (entry.get("target_node") or "").upper()
                if tid:
                    tp = id_to_path.get(tid)
                    if tp and tp != path:
                        result.append(tp)
            return result

        def how_parents(path: Path) -> list[Path]:
            path_id = get_task_id(path).upper()
            result = []
            for p, data in self._data.items():
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

        inline_nodes: list[dict] = []
        if direction == "down":
            for entry in get_how(self._data.get(start_path, {})):
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
            data = self._data.get(path, {})
            display_indent = max(1, depth - (deg - 1))
            result.append({
                "path": path, "data": data,
                "description": str(data.get("description", "") or get_task_id(path)),
                "status": str(data.get("status", "") or ""),
                "depth": depth, "in_degree": deg, "display_indent": display_indent,
            })

        result.sort(key=lambda n: (n["display_indent"], -n["in_degree"], n["depth"]))
        return result

    def score(self, query: str) -> dict[Path, float]:
        """Score each node by word overlap with query (Jaccard similarity)."""
        _STOP = {"a", "an", "the", "to", "of", "and", "or", "in", "for", "is", "it"}

        def tokenize(text: str) -> set[str]:
            words = re.sub(r"[^\w]+", " ", text.lower()).split()
            return {w for w in words if w not in _STOP and len(w) > 1}

        query_words = tokenize(query)
        if not query_words:
            return {p: 0.0 for p in self._data}

        scores: dict[Path, float] = {}
        for path, data in self._data.items():
            desc = str(data.get("description", "") or "")
            task_words = tokenize(desc)
            overlap = len(query_words & task_words)
            union = len(query_words | task_words)
            scores[path] = overlap / union if union else 0.0
        return scores

    def promote_inline(self, parent_path: Path, how_index: int) -> Path:
        """Promote an inline how entry to a file node.

        Replaces the inline dict in the parent with {"target_node": new_id},
        saves both files, updates the store.
        Returns the new file path.
        """
        parent_data = self._data[parent_path]
        how = get_how(parent_data)
        inline = how[how_index]

        description = str(inline.get("description", "") or "untitled")
        new_path = _new_filepath(description, parent_path.parent)

        new_data: dict = {}
        for key in ("type", "description", "status", "start_date", "due_date",
                    "horizon", "notes", "conclusion"):
            if key in inline:
                new_data[key] = inline[key]
        if "description" not in new_data:
            new_data["description"] = description

        save_task(new_path, new_data)
        self._data[new_path] = new_data

        how[how_index] = {"target_node": get_task_id(new_path)}
        save_task(parent_path, parent_data)

        return new_path


# ── Migration utility ─────────────────────────────────────────────────────────


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
