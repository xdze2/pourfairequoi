# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Commands

```bash
pip install -e .          # install in editable mode (do this once)
pfq                       # launch the TUI (default vault: data/)
pfq /path/to/vault        # open vault at given path (must exist)
venv/bin/pytest           # run tests
```

## Architecture

Nodes form a DAG. `how:` links are stored in the parent; `why` is always derived by
reversing `how` links at load time — never stored.

| File | Role |
|---|---|
| `pfq/model.py` | `Node` dataclass + `NodeGraph` (load, traversal) |
| `pfq/disk_io.py` | File I/O: `create_node`, `delete_node_file`, `save_node_fields`, `save_vault` |
| `pfq/config.py` | `FIELDS` dict — editable column definitions (label, kind, attr, options) |
| `pfq/app.py` | Textual TUI — navigation + field editing via `EditModal` |
| `pfq/__main__.py` | Click CLI entry point |

## Key API

```python
graph = NodeGraph.load_from_disk(path)
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

Tree methods return `(node, depth)` pairs, DFS pre-order: each node appears immediately before its subtree (correct for tree views).
`get_parents_tree` result must be reversed before display (farthest ancestor on top).

## Editing (`app.py` + `config.py`)

`e` on a cell opens `EditModal(node, col_key)`. The modal looks up `FIELDS[col_key]` and renders one widget:
- `kind: "text"` → `Input`, dismissed on `Enter` via `on_input_submitted`
- `kind: "select"` → `Select`, auto-dismissed on `on_select_changed` (membership check, not `Select.BLANK`)

After dismiss, `_on_edit_done` calls `setattr(node, attr, value)` then `save_node_fields(node)`.

`save_node_fields` in `disk_io.py` reads the raw YAML, patches only the three text fields, and writes back — `how` links are preserved untouched.
`save_vault(graph)` rewrites the `how` list of every node file to match the in-memory `graph.links`. Call it after any structural mutation.

To add a new editable field: add one entry to `FIELDS` in `config.py`. No changes needed elsewhere.

## TUI row notation (`app.py`)

Tree rows use three semantic roles: `"parent"`, `"selected"`, `"child"`.
Do **not** use `"why"` or `"how"` as role values — those are UX labels, not roles.
The boundary label ("why" / "how") is controlled by the `boundary=True` kwarg on `_format_tree_row`.

```python
# correct
_format_tree_row("parent", depth, node, boundary=True)   # shows "why" margin
_format_tree_row("child",  depth, node, boundary=False)  # shows " │ " margin

# wrong — "why" and "how" are not valid roles
_format_tree_row("why",  depth, node)
_format_tree_row("how",  depth, node)
```

## Tests

```
tests/
├── test_vault/        # 9-node synthetic vault used by all tests
├── test_model.py      # NodeGraph loading + traversal
└── test_app.py        # TUI navigation (async, pytest-asyncio)
```

`ListView.clear()` and `ListView.extend()` are async — always `await` them.



**Important Textual gotcha:** `ListView.clear()` and `ListView.extend()` return awaitables — must be awaited or DOM updates are silently deferred (was the first UI bug).