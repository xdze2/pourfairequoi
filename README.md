# PourFaireQuoi (pfq)

PourFaireQuoi is a hierarchical reasoning tool — not just a todo list. Most task managers focus on *what* and *when*. pfq focuses on *why*, *how*, *but*, and *or*: the reasoning structure behind decisions and plans.

The goal is a minimal, simple app for personal use.
The app name is pourfairequoi, abbreviated to "pfq".


## Goals

- Brain dump ideas without friction, then clarify them
- Break down projects into smaller steps
- Identify what is stuck and why
- Keep a decision log with conclusions
- Get a global view without getting lost in detail

Key design principles:
- Local files for privacy
- Terminal-based, minimal UI
- One YAML file per node — git-friendly (readable diffs, version history)
- No required fields — capture first, refine later


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

### Node types

`goal | project | task | event | decision | milestone | constraint`

### Node status

`todo | active | stuck | done | discarded`

### Time

A node can carry:
- `start_date`, `due_date` — actual dates
- `horizon` — broad time scope: `day | week | month | year | vision`

Time scope correlates naturally with DAG depth: roots tend toward long horizons, leaves toward short ones.

### File nodes vs. in-file nodes

A node can be stored in two ways:

**File node** — its own YAML file. Use when the node needs its own sub-structure or may be referenced by multiple parents.

**In-file node** — declared inline inside a parent's `how` list. Use for simple steps, events, or milestones that don't need further decomposition. Promote to a file node when complexity grows.

### Format

```yaml
description: Build a vintage radio       # short title, used in list view
type: project                            # see node types above
status: active                           # see statuses above
start_date: '2026-03-01'
horizon: month                           # optional broad scope
notes: |                                 # working notes, free-form
  Started after watching a restoration video.
conclusion: |                            # for decision nodes: what was decided and why
  Chose to buy a pre-assembled kit — sourcing original capacitors was too slow.

how:
- target_node: KLOP45                    # link to a child file node
- target_node: OAAP11
- type: event                            # in-file node — no separate file needed
  description: Bought the case (12€, leboncoin)
  start_date: '2026-03-14'
  status: done
- type: milestone
  description: First working prototype
  status: todo

constrain:
- target_node: MELP6O                    # link to a constraint file node
- type: but
  description: budget <300 euros         # in-file annotation
- type: alternative_to
  description: Start with a simpler build (alarm clock)
- type: required_for
  description: Do A before B
```

### Link directions

**`how` — stored in the parent, points to children.**
A parent declares what it is made of. Natural direction: a project lists its tasks, like a regular todo list.

**`why` — derived at query time** by reversing `how` links across the store.
"What does this node serve?" is answered by scanning which parents declared it as a child. Never stored — no duplication, no inconsistency.

### Lateral links (`constrain` section)

| Type | Meaning |
|---|---|
| `but` | A blocker that must be resolved |
| `alternative_to` / `or` | An alternative route or option |
| `required_for` / `need` | Ordering dependency — do this first |

Can point to file nodes (`target_node`) or be plain in-file annotations.

### How sub-types via node type

The `how` relationship covers different situations — the child node's `type` carries the distinction:
- **Parts** — parallel sub-components (`task` or `project` nodes)
- **Steps** — sequential actions (`task` or `event` nodes)
- **Decisions** — `decision` nodes with `alternative_to` links

No sub-type field on the link itself needed.


## Architecture

### Files

Each **file node** is a YAML file in the `data/` directory. **In-file nodes** live inline inside a parent's `how` or `constrain` list and have no file of their own.

**Filename format:** `AB12CD_readable_slug.yaml` — a 6-character random ID followed by a slug of the description.

### Config

Fields and valid statuses are defined in `config.py`.


## UI

Terminal-based, two-column layout. All files are loaded into memory at startup.

**Left column — subgraph view / home page:**

At startup shows a home page: all root nodes (no parents) with one level of children.

When a node is open, shows its local neighbourhood as a continuous tree:

```
        ┌── grandparent
    ┌── parent
► current node
├── child 1
│   └── grandchild 1.1
└── child 2
```

Ancestors grow upward, furthest root at the most-indented top line. The current node sits at the leftmost position marked `►`. Descendants branch downward with standard tree connectors. Each line shows type, status, and date chips aligned in columns.

**Right column — task view / link picker:**
- Task view: structured view of the open node, one row selected at a time. Shows `why` (derived backlinks), `how` children, and `constrain` sections.
- Link picker: node list for creating a link (activated with `l`), pre-sorted by word-overlap relevance.

### Keyboard shortcuts

#### Global
| Key | Action |
|---|---|
| `h` | Home page |
| `b` | Go back (navigation history) |
| `Tab` | Switch focus between left and right panel |
| `q` | Quit |

#### Left panel (subgraph / home)
| Key | Action |
|---|---|
| `↑` / `↓` | Navigate |
| `Enter` | Open node in right panel (focus stays left) |
| `Space` | Preview node in right panel (read-only) |
| `n` | New node |
| `d` | Delete node |

#### Right panel (task view)
| Key | Action |
|---|---|
| `↑` / `↓` | Navigate rows |
| `e` | Edit current row |
| `Enter` | Confirm edit / follow link |
| `Esc` | Cancel edit — or return focus to left panel |
| `n` | Insert new row below |
| `d` | Delete selected row |
| `a` | Add a missing field or section |
| `l` | Open link picker |
| `u` | Remove link target (with confirmation) |

#### Link picker
| Key | Action |
|---|---|
| `↑` / `↓` | Navigate |
| `Enter` | Link selected node |
| `Esc` | Cancel |
| `/` | Search / filter |

### CLI

```bash
pfq                                          # open the TUI
pfq new "my project"                         # create a new node and open it
pfq open data/M11AB_vintage_radio_build.yaml # open a specific file
pfq migrate                                  # migrate old format to links format
pfq clean                                    # remove empty fields and links
pfq dedup                                    # remove redundant backlinks from data files
```


## Tech

Built with Python:
- Click
- PyYAML
- Textual (TUI framework, includes Rich)

## Setup

```bash
pip install -e .
pfq new "my first goal"
```

## Roadmap

### v0.1 — done
- Single file view with arrow navigation
- Edit mode, insert, delete, auto-save
- Add missing section (`a`)

### v0.2 — done
- Two-column layout: file list ↔ task view / link picker
- Link creation and removal
- File search, create, delete

### v0.3 — done
- Unified `how`/`constrain` data model (backlinks derived at query time, never stored)
- All files preloaded at startup via `Store` class
- Two-column layout: subgraph view | task view / link picker
- Left panel: inverted tree for ancestors, standard tree for descendants
- Home page: root nodes + one level at startup
- Link picker pre-sorted by word-overlap relevance
- Backlinks (`why`) shown in task view (derived, read-only)
- Chip columns (type, status, date) aligned across all link rows

### Later
- `horizon` field and timeline view (past month, past year)
- `conclusion` field for decision nodes
- `events` — append-only history log with user-declared dates (bi-temporal)
- Computed stuck propagation — derive stuck status from structure
- Next actions view — leaf nodes, no blockers, status todo
- Node health indicator in file list
- Full-text search across `notes`
- AI integration (local, via Ollama)

## Credits

Built with the assistance of [Claude](https://claude.ai) (Anthropic) — used as a coding assistant throughout the design and implementation of this project.
