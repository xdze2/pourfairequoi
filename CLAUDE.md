# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Commands

```bash
pip install -e .          # install in editable mode (do this once)
pfq                       # launch the TUI
pfq --vault /path/to/dir  # use a custom vault directory
venv/bin/pytest           # run tests
```

## Architecture

Nodes form a DAG. `how:` links are stored in the parent; `why` is always derived by
reversing `how` links at load time — never stored.

| File | Role |
|---|---|
| `pfq/model.py` | `Node` dataclass + `NodeGraph` (load, traversal) |
| `pfq/disk_io.py` | File I/O helpers, `DEFAULT_VAULT_PATH` |
| `pfq/app.py` | Textual TUI — view only for now |
| `pfq/__main__.py` | Click CLI entry point |

## Key API

```python
graph = NodeGraph.load_from_disk(path)
graph.get_node(node_id)               # -> Node  (node_id is the 6-char prefix, e.g. "AB0002")
graph.get_node_parents(node_id)       # -> List[str]
graph.get_node_childrens(node_id)     # -> List[str]
graph.get_roots()                     # -> List[str]
graph.get_parents_tree(node_id, max_depth=2)   # -> List[(Node, int)]
graph.get_childrens_tree(node_id, max_depth=2) # -> List[(Node, int)]
```

`node_id` is the 6-char prefix extracted from the filename stem (e.g. `AB0002` from `AB0002_practice_chords.yaml`).
`target_node` in YAML always stores the full stem (`AB0002_practice_chords`) — the slug is cosmetic and may go stale on rename.

Tree methods return `(node, depth)` pairs, BFS order, closest-first.
`get_parents_tree` result must be reversed before display (farthest ancestor on top).

## Tests

```
tests/
├── test_vault/        # 9-node synthetic vault used by all tests
├── test_model.py      # NodeGraph loading + traversal
└── test_app.py        # TUI navigation (async, pytest-asyncio)
```

`ListView.clear()` and `ListView.extend()` are async — always `await` them.
