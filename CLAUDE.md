# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
pip install -e .          # install in editable mode (do this once)
pfq                       # launch the TUI
pfq new "description"     # create a node and open it
pfq open data/FILE.yaml   # open a specific file
pfq migrate               # convert old links: format → how:/constrain:
pfq clean                 # strip empty fields and entries from all files
python screenshot.py      # capture SVG screenshots of the TUI
```

No test suite or linter is configured.

## Architecture

### Core concept
Nodes form a DAG. `how:` links are stored in the parent (parent declares its children). `why` is always **derived** by scanning the store — never stored. This eliminates consistency bugs.

### Module roles

| File | Role |
|---|---|
| `pfq/model.py` | `Store` class + pure data helpers |
| `pfq/config.py` | Constants: `FIELDS`, `STATUSES`, `TYPES`, `HORIZONS`, `CONSTRAIN_TYPES` |
| `pfq/app.py` | Full Textual TUI |
| `pfq/__main__.py` | Click CLI (`pfq new`, `pfq open`, `pfq migrate`, `pfq clean`) |

### Data format
Each node is `data/AB12CD_readable_slug.yaml` — a 6-char random uppercase+digit ID followed by a slug. The ID is the node's stable identity.

Two node kinds: **file nodes** (own YAML file) and **inline nodes** (dicts inside a parent's `how:` list, promoted to file nodes on demand via `store.promote_inline()`).

### Store class (`model.py`)
`Store(vault: Path)` loads all YAML files at init into `self._data: dict[Path, dict]` and exposes a dict-like interface. Key methods:
- `store.find(task_id)` → `Path | None`
- `store.sort()` → topological order with display indent
- `store.traverse(path, "up"|"down")` → BFS subgraph
- `store.score(query)` → Jaccard similarity for link picker relevance
- `store.promote_inline(parent_path, how_index)` → `Path`
- `store.save(path, data)` — persists + auto-stamps `last_modified`

Pure helpers (no Store dependency): `get_how(data)`, `get_constrain(data)`, `is_inline(entry)`, `get_task_id(path)`, `load_task(path)`, `save_task(path, data)`.

### TUI layout (`app.py`)
Three application states managed via `ContentSwitcher`:

```
┌─────────────────┬────────────────────────────────┐
│  LEFT (1fr)     │  RIGHT (2fr)                   │
│                 │                                │
│  HomePage       │  TaskPane      ← default       │
│    OR           │    OR                          │
│  SubgraphPane   │  LinkPickerPane                │
└─────────────────┴────────────────────────────────┘
```

- **HomePage**: startup view — root nodes + one level of children, navigable
- **SubgraphPane**: local neighborhood of the current node (ancestors → `► current` → descendants)
- **TaskPane**: node editor with typed rows (`Row` dataclass); builds backlink (why) rows by scanning the store
- **LinkPickerPane**: file selector for creating `how`/`constrain` links

Key app methods: `_open_node(path)` switches to node state and re-centers SubgraphPane; `_preview_node(path)` loads task pane read-only without stealing focus.

### Row model (TaskPane)
`Row(kind, field, idx, ...)` drives all rendering. Kinds: `simple | text | spacer | why_header | why_item | how_header | how_item | how_inline | how_add | constrain_header | constrain_item | constrain_add`. Spacers are skipped by ↑↓ navigation. Link rows display fixed-width type/status/date chip columns (`_TYPE_COL`, `_STATUS_COL`, `_DATE_COL`).

### Key bindings
Global: `h` home, `b` back, `Tab` switch focus, `q` quit.
SubgraphPane: `↑↓` navigate, `Enter` select (re-centers), `Space` preview (read-only, no re-center), `n` new, `d` delete.
TaskPane: `↑↓` rows, `e` edit, `Enter` confirm/follow, `Esc` cancel or focus left, `n` insert, `d` delete, `a` add field, `l` link picker, `u` unlink.
