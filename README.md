# PourFaireQuoi (pfq)

PourFaireQuoi is a hierarchical todo list, yet another, but:
Most task managers focus on *what* and *when*. pfq focuses on *why* and *how*.


## Goals

- Break down projects into smaller steps
- Identify what is stuck and why
- Brain dump ideas without friction, then clarify them

## Key design principles:
- Local files for privacy
- Terminal-based, minimal UI
- No required fields — capture first, refine later
- One YAML file per node — git-friendly (readable diffs, version history)
- Each node is a YAML file in the `data/` directory.
- Filename format: `{node_id}_{readable_slug}.yaml`
- `node_id` is the 6-character random prefix (e.g. `AB0002`). The slug is cosmetic — human-readable in file explorers, never used for resolution.


## Data model

### What a node encodes


A node is a single unit of thought. It can represent any of:
- a **goal** — long-horizon aspiration, no clear end condition
- a **project** — bounded effort with a deliverable
- a **task** — concrete, completable action
- an **event** — something that happened (past-dated, status done)
- a **question / decision** — a node whose output is a conclusion, not an artifact
- a **milestone** — a marker in time, signals progress
- a **constraint** — a fact that shapes decisions, not something you do

All are the same data structure. The difference is semantic, carried by `type` and context.


### Node status

- free text

### Yaml file format

```yaml
description: Build a vintage radio       # short title, used in list view
type: project                            # see node types above
status: active                           # see statuses above

how:
- target_node: KLOP45_get_the_case       # {node_id}_{slug} — slug is informational only
- target_node: OAAP11_repair_capacitors

```

Every `how` entry references a node via `target_node: {node_id}_{slug}`. The model resolves links using only the `node_id` prefix — the slug can go stale if a node is renamed without updating its incoming links, which is acceptable (use a linter to re-sync slugs).


### Link directions

**`how` — stored in the parent, points to children.**
A parent declares what it is made of. Natural direction: a project lists its tasks.

**`why` — derived at load time** by reversing `how` links across the store.
"What does this node serve?" is answered by scanning which parents declared it as a child. Never stored — no duplication, no inconsistency.



## Architecture

Terminal-based, using Textual. All files are loaded into memory at startup.

```
Disk <──> Model <──api──> UI
```

The model exposes two tree queries, both returning `[(Node, depth), ...]`:
- `get_parents_tree(node_id, max_depth=2)` — BFS upward; depth 1 = immediate parent
- `get_childrens_tree(node_id, max_depth=2)` — BFS downward; depth 1 = immediate child

BFS with a visited set handles DAGs: a shared node appears once, at its shallowest depth. The UI reverses the parents list to display the most distant ancestor at the top.


## UI: Subgraph views

At startup shows a home page: all root nodes (no parents) with type and status chips.

When a node is selected, shows its local neighbourhood capped at `max_depth=2` in each direction:

```
     - root
why     ┌─ grandparent 2       goal        active
 │      ┌─ grandparent         goal        active
 │   ┌─ parent                 project     todo
 ▶   current node              task        active
 │   ├─ child 1                task        doable
 │   └─ child 2                task        done
how     └─ grandchild          task        todo
```

- Left margin: `why`/`│`/`▶`/`│`/`how` shows position in the hierarchy
- `root` line at the top — selectable, Enter navigates home
- Type and status chips aligned in fixed-width columns to the right


### Keyboard shortcuts

#### Global
| Key | Action |
|---|---|
| `h` | Home page |
| `esc` | Go back to previously selected node (navigation history) |
| `q` | Quit |
| `↑` / `↓` | Navigate between node|
| `Enter` | Select one node (or go home if on `root` line) |

### CLI

```bash
pfq                                          # open the TUI
```


## Tech

Built with Python:
- Click
- PyYAML
- Textual (TUI framework, includes Rich)

## Status

- [x] Data model + graph traversal (`model.py`)
- [x] TUI — view only: home page, subgraph view, keyboard navigation
- [ ] Node editing (create, update fields, add/remove links)
- [ ] Search / filter on home page

## Setup

```bash
pip install -e .
pfq
```


## Credits

Built with the assistance of [Claude](https://claude.ai) (Anthropic) — used as a coding assistant throughout the design and implementation of this project.
