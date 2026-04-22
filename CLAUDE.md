# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Commands

```bash
pip install -e .          # install in editable mode (do this once)
pfq                       # launch the TUI (default vault: data/)
pfq /path/to/vault        # open vault at given path (must exist)
venv/bin/pytest           # run tests
venv/bin/python screenshot.py   # regenerate screenshots/ SVGs (uses tests/test_vault)
```

## Architecture

Nodes form a DAG. `how:` links are stored in the parent; `why` is always derived by
reversing `how` links at load time — never stored.

Three-layer separation: **model → view → render**.

| File | Role |
|---|---|
| `pfq/model.py` | `Node` dataclass + `NodeGraph` (graph traversal) |
| `pfq/disk_io.py` | File I/O: `create_node`, `delete_node_file`, `save_node_fields`, `save_vault` |
| `pfq/config.py` | `FIELDS`, `STATUS_STYLES`, `STATUS_GLYPHS`, status vocabularies |
| `pfq/view.py` | `ViewRow` dataclass + `build_node_view()` + `build_home_view()` |
| `pfq/render.py` | `render_to_table()`, `render_to_text()`, Rich text helpers |
| `pfq/modals.py` | All modal screens: `CreateModal`, `DeleteModal`, `LinkModal`, `StatusModal`, `EditModal` |
| `pfq/companion.py` | `CompanionPanel` — HAL-style inner voice widget |
| `pfq/app.py` | `PfqApp` — navigation, actions, lifecycle only |
| `pfq/__main__.py` | Click CLI entry point |

## Key API

```python
graph = load_vault(path)                               # from pfq.disk_io
graph.get_node(node_id)                        # -> Node  (node_id is the 6-char prefix, e.g. "AB0002")
graph.get_parent_ids(node_id)                  # -> List[str]
graph.get_children_ids(node_id)                # -> List[str], insertion order
graph.get_roots()                              # -> List[str]
graph.get_parents_tree(node_id, max_depth=2)   # -> List[(Node, int)]
graph.get_childrens_tree(node_id, max_depth=2) # -> List[(Node, int)]
```

Topology lives in `graph.links: set[Link]` (NamedTuple with `parent_id`, `child_id`).
Call `save_vault(graph)` from `disk_io` after any structural mutation (link/unlink/delete).

`node_id` is the 6-char prefix extracted from the filename stem (e.g. `AB0002` from `AB0002_practice_chords.yaml`).
`target_node` in YAML always stores the full stem (`AB0002_practice_chords`) — the slug is cosmetic and may go stale on rename.

Tree methods return `(node, depth)` pairs, DFS pre-order: each node appears immediately before its subtree.
`get_parents_tree` result must be reversed before display (farthest ancestor on top).

## View model (`view.py`)

`build_node_view(graph, node_id)` and `build_home_view(graph)` return `list[ViewRow]`.

Each `ViewRow` carries everything the renderer needs — no graph access required in `render.py`:

| Field | Content |
|---|---|
| `role` | `"sentinel"` / `"parent"` / `"selected"` / `"child"` / `"home_root"` |
| `node` | `Node` object (None for sentinel) |
| `depth` | tree depth |
| `is_leaf`, `is_root` | precomputed from graph |
| `bullet` | `"@"`, `"○"`, `"<"`, or `""` |
| `index`, `items` | position + peer list for connector calculation |
| `visible_parent_id` | graph parent shown in the current rendering |
| `also_labels` | descriptions of other parents (for "also" column) |

`PfqApp` stores `self._last_view: list[ViewRow]` — the rows currently on screen.
Actions use it to look up visible parents without re-querying the graph:

```python
# find the visible parent of the focused child row
parent_id = next(
    (r.visible_parent_id for r in self._last_view
     if r.node and r.node.node_id == row_key and r.role == "child"),
    None,
)
```

## Rendering (`render.py`)

`render_to_table(rows, table)` — populates a `DataTable`, clears it first.
`render_to_text(rows)` — returns the plain-text tree representation (used by yank).

Neither function takes a `NodeGraph` argument — all graph-derived data is in `ViewRow`.

`PALETTE` dict is defined in `render.py` and imported by `app.py` for the CSS f-string.

## Editing (`modals.py` + `config.py`)

`e` on a cell opens `StatusModal` (for the status column) or `EditModal(node, col_key)` (for others).

`EditModal` looks up `FIELDS[col_key]` and renders one widget:
- `kind: "text"` → `Input`, dismissed on `Enter`
- `kind: "select"` → `Select`, auto-dismissed on change

After dismiss, `_on_edit_done` calls `setattr(node, attr, value)` then `save_node_fields(node)`.

To add a new editable field: add one entry to `FIELDS` in `config.py`. No changes needed elsewhere.

## Linking (`z` key — `LinkModal`)

`z` opens `LinkModal(focused_node_id, graph)`. Fuzzy search via `graph.search_nodes(query)`.
On confirm, `_on_link_parent_done` calls `graph.link_child(parent_id, child_id, position)` + `save_vault(graph)`.

## Tests

```
tests/
├── test_vault/        # 9-node synthetic vault used by all tests
├── test_model.py      # NodeGraph loading + traversal
└── test_app.py        # TUI navigation (async, pytest-asyncio)
```

**Important Textual gotcha:** `ListView.clear()` and `ListView.extend()` return awaitables — must be awaited or DOM updates are silently deferred (was the first UI bug).
