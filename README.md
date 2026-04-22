# PourFaireQuoi (pfq)

Most task managers focus on *what* and *when*. pfq focuses on *why* and *how*.

It is a personal knowledge graph — a DAG of nodes where up-links mean generalization and down-links mean decomposition. Tasks are just leaf nodes. Goals are just roots.

---

## Philosophy

**Goal: clarity. Means: structure.**

A structure is not a permanent truth — it's how you currently think about something. It can and should evolve. The graph is a first-person instrument, not a universal ontology.

A DAG is a superposition of trees, one per root. Each root is a **perspective anchor** — a seed that radiates meaning downward. The structural position of a node already tells you what kind of thing it is:

- `@` **root** — a seed, a motivation, a point of view. Everything below it exists because of it.
- middle node — structure, a category, a "how"
- `○` **leaf** — an atom, an action, something that can be resolved

See [philo.md](philo.md) for the full design thinking.

---

## Data model

### Nodes and links

A node is a single unit of thought — a goal, a project, a task, an idea, a constraint. All are the same data structure. The difference is semantic, carried by position in the graph.

Links are directional: `how` (downward, toward detail/decomposition) and `why` (upward, toward motivation/generalization, derived by reversing `how` links — never stored).

The graph is a DAG: a node can have multiple parents. This allows the same concept to belong to several perspectives simultaneously.

### Node role (derived from structure)

| Symbol | Role | Meaning |
|--------|------|---------|
| `@` | root | no parents — a perspective anchor |
| (none) | middle | has both parents and children — structure |
| `○` | leaf | no children — an actionable atom |

### Node status

Status is free text, but two vocabularies are suggested depending on the node's structural role:

**Leaf statuses** (actions):
- `todo` — should be done
- `doable` — could be done, not urgent
- `doing` — work in progress
- `done` — completed
- `stuck` — blocked, unclear why
- `waiting` — can't proceed, external dependency

**Root/middle statuses** (concepts, goals):
- `active` — currently relevant
- `on hold` — paused
- `archived` — no longer relevant
- `someday` — maybe later

Using a leaf status on a root/middle node (or vice versa) is highlighted with a background color — a soft signal, not an error.

### Node fields

| Field | Purpose |
|-------|---------|
| `description` | The node title — what it is |
| `type` | Optional classification (`goal`, `project`, `task`, `event`, …) |
| `status` | Lifecycle state (see vocabularies above) |
| `note` | Free-form elaboration — the depth dimension of *what* |

### YAML format

```yaml
description: Build a vintage radio
type: project                        # optional
status: active
note: |                              # optional
  Started from a 1952 Philips chassis.
  Need to source NOS capacitors.

how:
- target_node: KLOP45_get_the_case
- target_node: OAAP11_repair_capacitors
```

One YAML file per node in the vault directory. Filename: `{node_id}_{slug}.yaml`. The `node_id` is a 6-character random prefix used for link resolution — the slug is cosmetic.

---

## Screenshots

| Home | Node view | Delete modal |
|------|-----------|--------------|
| ![home](screenshots/01_home.svg) | ![node](screenshots/02_node.svg) | ![delete](screenshots/05_delete_modal.svg) |

Regenerate with `venv/bin/python screenshot.py`.

---

## UI

### Home page

Shows all root nodes (`@`) with type and status.

### Node view

Shows the local neighbourhood of the selected node, capped at depth 2 in each direction:

```
─ root
  ╭── grandparent
  ├── parent
▶ Current node
  ├── child 1
  │   ├──< middle grandchild
  │   ╰──○ leaf grandchild
  ╰──○ leaf child
```

The tree connectors are rounded (`╰`, `╭`). Node role symbols are embedded in the connector terminal:
- `@ ` prefix on home screen for roots
- `──<` for middle nodes at depth 2
- `──○` for leaf nodes at depth 2
- depth 1 nodes have no bullet — the connector is enough

### Keyboard shortcuts

#### Navigation
| Key | Action |
|-----|--------|
| `h` | Home page |
| `Esc` | Go back |
| `q` | Quit |
| `↑` / `↓` | Move cursor |
| `Enter` | Open node |

#### Editing
| Key | Action |
|-----|--------|
| `e` | Edit focused cell (description, type, status, note) |
| `a` | Add child node at cursor |
| `z` | Link focused node to a parent (search or create) |
| `d` | Delete / unlink focused node (multi-choice modal) |
| `Shift+↑` / `Shift+↓` | Reorder children |
| `y` | Copy current view to clipboard |

Note editing: move cursor to the `note` column and press `e`. A multiline text editor opens — `ctrl+s` to save, `Esc` to cancel. When a node has a note, a `✎` icon appears in the note column and the note text is shown in a floating card (top-right).

---

## Architecture

```
Disk <──> Model <──> UI
```

All YAML files are loaded into memory at startup into a `NodeGraph`. The UI never touches disk directly — all writes go through `disk_io`.

Key files:
- `pfq/model.py` — `Node` dataclass, `NodeGraph` (BFS/DFS traversal)
- `pfq/disk_io.py` — load/save vault, create/delete nodes
- `pfq/config.py` — status palettes, mismatch vocabularies
- `pfq/app.py` — Textual TUI

---

## Setup

```bash
pip install -e .
pfq                        # open default vault (data/)
pfq /path/to/vault         # open a specific vault
```

---

## Status

- [x] Data model + graph traversal
- [x] Home page + node view with tree connectors
- [x] Node role symbols (`@`, `<`, `○`) integrated into connectors
- [x] Status mismatch highlighting
- [x] Node editing (description, type, status)
- [x] Create child node, link to parent, unlink, delete
- [x] Reorder children
- [x] Root node creation from home page
- [x] Copy view to clipboard (`y`)
- [x] Note field — multiline, per-node, shown in floating card
- [ ] Search / filter on home page

---

## Credits

Built with the assistance of [Claude](https://claude.ai) (Anthropic).
