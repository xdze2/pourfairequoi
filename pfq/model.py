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
    """Find a YAML file whose stem starts with the given ID (case-insensitive)."""
    if not vault.exists():
        return None
    for p in sorted(vault.iterdir()):
        if p.suffix in (".yaml", ".yml"):
            if p.stem.upper().startswith(task_id.upper()):
                return p
    return None


def find_path_by_id(task_id: str, store: dict[Path, dict]) -> Path | None:
    """Find a path in the store whose stem starts with task_id."""
    task_id_upper = task_id.upper()
    for p in store:
        if p.stem.upper().startswith(task_id_upper):
            return p
    return None


def sort_globally(store: dict[Path, dict]) -> list[tuple[Path, int]]:
    """
    Order all nodes from most abstract (top) to most concrete (bottom).

    Each node declares its own `why → parent` links. We reverse these to get
    parent→children edges, then BFS from roots (nodes with no why targets).

    Roots = nodes with no `why` link pointing to a known node = top-level goals.
    in_degree[A] = number of valid why targets A declares (number of parents).
    Indentation formula: max(0, depth - max(0, in_degree - 1))
    """
    id_to_path: dict[str, Path] = {get_task_id(p): p for p in store}

    # why_children[B] = nodes A that declared `why → B` (A lives below B)
    why_children: dict[Path, list[Path]] = {p: [] for p in store}
    # in_degree[A] = number of valid why targets A has (how many parents)
    in_degree: dict[Path, int] = {p: 0 for p in store}
    has_parent: set[Path] = set()  # nodes with at least one valid why target

    for path, data in store.items():
        for link in get_links(data):
            if link.get("type") != "why":
                continue
            target_id = link.get("target_node")
            if not target_id:
                continue
            target_path = id_to_path.get(target_id.upper())
            if target_path and target_path != path and target_path in store:
                why_children[target_path].append(path)
                in_degree[path] = in_degree.get(path, 0) + 1
                has_parent.add(path)

    # Roots: nodes that declare no why target — top-level goals
    roots = sorted(p for p in store if p not in has_parent)

    # Multi-source BFS from roots through why_children
    visited: dict[Path, int] = {}  # path -> min depth
    queue: list[tuple[Path, int]] = []
    for p in roots:
        visited[p] = 0
        queue.append((p, 0))

    head = 0
    while head < len(queue):
        current_path, current_depth = queue[head]
        head += 1
        for child in why_children.get(current_path, []):
            if child not in visited:
                visited[child] = current_depth + 1
                queue.append((child, current_depth + 1))

    result: list[tuple[Path, int]] = []
    for path, depth in queue:
        deg = in_degree.get(path, 0)
        if deg == 0:
            display_indent = 0  # root
        else:
            display_indent = max(1, depth - max(0, deg - 1))
        result.append((path, display_indent))

    # Append nodes not reached (cycles or disconnected)
    for p in sorted(store):
        if p not in visited:
            result.append((p, 0))

    return result


def traverse_subgraph(
    start_path: Path,
    store: dict[Path, dict],
    direction: str,  # "up" (follow why links) or "down" (follow how links)
) -> list[dict]:
    """
    BFS traversal from start_path following links of a given direction.
    Returns a list of node dicts, each with:
      - path, data, description, status, depth, in_degree, display_indent
    Nodes without target_node (plain annotations) are included at depth 1, in_degree 1.
    """
    link_type = "why" if direction == "up" else "how"

    # Map ID -> path for fast lookup
    id_to_path: dict[str, Path] = {get_task_id(p): p for p in store}

    # BFS: collect (path, depth) for each visited node (first visit = min depth)
    visited: dict[Path, int] = {}  # path -> min depth
    in_degree: dict[Path, int] = {}  # path -> how many nodes in subgraph reference it
    queue: list[tuple[Path, int]] = []

    # Seed from the start node's links of the target type
    start_data = store.get(start_path, {})
    for link in get_links(start_data):
        if link.get("type") != link_type:
            continue
        target_id = link.get("target_node")
        if target_id:
            target_path = id_to_path.get(target_id.upper())
            if target_path and target_path != start_path:
                if target_path not in visited:
                    visited[target_path] = 1
                    queue.append((target_path, 1))
                in_degree[target_path] = in_degree.get(target_path, 0) + 1
        else:
            # Plain annotation — no path, represented as a synthetic entry
            pass

    # Also collect plain annotations (no target_node) separately
    annotations: list[dict] = []
    for link in get_links(start_data):
        if link.get("type") != link_type:
            continue
        if not link.get("target_node"):
            annotations.append({
                "path": None,
                "data": {},
                "description": str(link.get("description", "") or ""),
                "status": "",
                "depth": 1,
                "in_degree": 1,
                "display_indent": 1,
            })

    # BFS expansion
    head = 0
    while head < len(queue):
        current_path, current_depth = queue[head]
        head += 1
        current_data = store.get(current_path, {})
        for link in get_links(current_data):
            if link.get("type") != link_type:
                continue
            target_id = link.get("target_node")
            if not target_id:
                continue
            target_path = id_to_path.get(target_id.upper())
            if not target_path or target_path == start_path:
                continue
            in_degree[target_path] = in_degree.get(target_path, 0) + 1
            if target_path not in visited:
                new_depth = current_depth + 1
                visited[target_path] = new_depth
                queue.append((target_path, new_depth))

    # Build result list, sort by (display_indent, -in_degree, depth)
    result: list[dict] = list(annotations)
    for path, depth in visited.items():
        deg = in_degree.get(path, 1)
        data = store.get(path, {})
        display_indent = max(1, depth - (deg - 1))
        result.append({
            "path": path,
            "data": data,
            "description": str(data.get("description", "") or get_task_id(path)),
            "status": str(data.get("status", "") or ""),
            "depth": depth,
            "in_degree": deg,
            "display_indent": display_indent,
        })

    result.sort(key=lambda n: (n["display_indent"], -n["in_degree"], n["depth"]))
    return result


def get_links(data: dict) -> list[dict]:
    """Return the links list from a task dict, always as a list."""
    links = data.get("links")
    if isinstance(links, list):
        return links
    return []


def migrate_task(data: dict) -> dict:
    """Convert old-format tasks (why/how/need/... list fields) to the new links format."""
    from .config import LINK_TYPE_MAP

    old_fields = {"why", "how", "need", "required_by", "but", "or", "alternative_to"}
    links = list(data.get("links") or [])

    for field in old_fields:
        if field not in data:
            continue
        items = data.get(field)
        if not isinstance(items, list):
            continue
        link_type = field if field in LINK_TYPE_MAP else "but"
        for item in items:
            if not item:
                continue
            text = str(item)
            # extract #ID if present
            m = re.search(r"#(\w+)\s*$", text)
            target = m.group(1) if m else None
            desc = re.sub(r"\s*#\w+\s*$", "", text).strip() if m else text.strip()
            link: dict = {"type": link_type}
            if desc:
                link["description"] = desc
            if target:
                link["target_node"] = target
            links.append(link)
        del data[field]

    if links:
        data["links"] = links
    return data
