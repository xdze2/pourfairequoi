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

| Status | Meaning |
|---|---|
| `explore` | Not yet defined — tinker, research, think |
| `todo` | Should be done (imperative) |
| `doable` | Could be done, not a priority |
| `active` | In progress |
| `stuck` | Blocked |
| `done` | Complete |
| `discarded` | Dropped |

### Time

A node can carry:
- `start_date`, `due_date` — actual dates (ISO format or loose input: `5d`, `2w`, `1m`, `6m ago`, `1y`)
- `horizon` — broad time scope: `day | week | month | year | vision`

Time scope correlates naturally with DAG depth: roots tend toward long horizons, leaves toward short ones.

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
- target_node: KLOP45_get_the_case       # link to a child file node (full stem)
- target_node: OAAP11_repair_capacitors

constrain:
- target_node: MELP6O_budget_constraint  # link to a constraint file node
- type: but
  description: budget <300 euros         # in-file annotation (constrain only)
- type: alternative_to
  description: Start with a simpler build (alarm clock)
```

Every `how` entry must reference a file node via `target_node` — there are no inline how sub-nodes. This keeps the graph consistent: every how-child is navigable.

`constrain` entries may be inline annotations or file node references.

### Link directions

**`how` — stored in the parent, points to children.**
A parent declares what it is made of. Natural direction: a project lists its tasks.

**`why` — derived at query time** by reversing `how` links across the store.
"What does this node serve?" is answered by scanning which parents declared it as a child. Never stored — no duplication, no inconsistency.

### Lateral links (`constrain` section)

| Type | Meaning |
|---|---|
| `but` | A blocker that must be resolved |
| `alternative_to` | An alternative route or option |

### `target_node` format

Stored as the full file stem (e.g. `KLOP45_get_the_case`), not just the short ID. Human-readable in YAML diffs. Short IDs are still accepted for lookup (backward compatible).


## Architecture

### Files

Each node is a YAML file in the `data/` directory.

**Filename format:** `AB12CD_readable_slug.yaml` — a 6-character random ID followed by a slug of the description.

### Config

Fields, statuses, types, and horizons are defined in `config.py`.


## UI

Terminal-based, two-column layout. All files are loaded into memory at startup.

**Left column — subgraph view / home page:**

At startup shows a home page: all root nodes (no parents) with type, status, and date chips.

When a node is open, shows its local neighbourhood with a left margin indicating direction, capped at 3 levels in each direction:

```
     root
why  ┌── …                   ← ancestors beyond depth 3 (cropped)
 │   ┌── grandparent         goal        active    ──────────┃────────────
 │   ┌── parent              project     todo      ──────────┃──▒▒▒▒▒▒▒▒▒
 ▶       current node        task        active    ──────────█████████████
 │   ├── child 1             task        doable    ──────────┃────────────
 │   │   └── …               ← descendants beyond depth 3 (cropped)
 │   └── child 2             task        done      ──────────░░░░░░░░░────
how  └── grandchild          task        todo      ──────────┃─▒▒▒▒▒▒▒▒▒▒
```

- Left margin: `why`/`│`/`▶`/`│`/`how` shows your position in the hierarchy
- `root` line at the top — selectable, Enter navigates to the home page
- Timeline axis shown on the `root` line (log scale, `now` at 1/3 from left)
- Current node description is coloured by status
- Type and status chips aligned in fixed-width columns to the right of descriptions

**Right column — task view / link picker:**
- Task view: structured view of the open node, one row selected at a time. Shows scalar fields, `why` (derived backlinks), `how` children, and `constrain` sections.
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
| `Enter` | Open node (or go home if on `root` line) |
| `Space` | Preview node in right panel |
| `e` | Edit selected node in right panel |
| `n` | New node |
| `d` | Delete node |

#### Right panel (task view)
| Key | Action |
|---|---|
| `↑` / `↓` | Navigate rows |
| `e` | Edit current row |
| `Enter` | Confirm edit / follow link |
| `Esc` | Cancel edit |
| `n` | Insert new how-child (creates a new file node) |
| `d` | Delete selected row |
| `a` | Add a missing field or section |
| `l` | Open link picker |
| `u` | Remove link target (with confirmation) |

#### Right panel — picker fields (type / status / horizon)
Single-select modal — arrow keys + Enter to choose.

#### Link picker
| Key | Action |
|---|---|
| `↑` / `↓` | Navigate |
| `Enter` | Link selected node |
| `Esc` | Cancel |
| `/` | Search / filter |

### Date input

Date fields (`start_date`, `due_date`) accept ISO format or loose relative input:

| Input | Meaning |
|---|---|
| `2026-04-12` | Exact date |
| `5d` | 5 days from today |
| `2w` | 2 weeks from today |
| `1m` | ~1 month from today |
| `1y` | ~1 year from today |
| `3d ago` | 3 days ago |
| `6m ago` | ~6 months ago |

All inputs are normalised and stored as ISO-8601.

### CLI

```bash
pfq                                          # open the TUI
pfq new "my project"                         # create a new node and open it
pfq open data/M11AB_vintage_radio_build.yaml # open a specific file
pfq migrate                                  # migrate old format to current format
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
- Left panel: inverted tree for ancestors, standard tree for descendants
- Home page: root nodes + one level at startup
- Link picker pre-sorted by word-overlap relevance
- Backlinks (`why`) shown in task view (derived, read-only)
- Chip columns (type, status, date) aligned across all link rows
- Log-scale timeline bar per node

### v0.4 — done
- Graph refresh after node edit (left panel updates live)
- Single-select picker for `type`, `status`, `horizon` fields
- All `how` entries are file nodes — no more inline sub-nodes
- `target_node` stored as full file stem (human-readable YAML)
- Left margin in graph view: `why`/`│`/`▶`/`│`/`how` direction indicators
- `root` selectable entry navigates to home page
- Timeline axis on the `root` line
- Type and status chips in graph view, current node coloured by status
- New statuses: `explore` (undefined/tinkering) and `doable` (low priority)
- Loose date input: `5d`, `2w`, `1m ago`, etc.
- Graph depth limit: capped at 3 levels for both ancestors and descendants, `…` shown on cropped branches

### Later
- Search / filter on home page
- `conclusion` field for decision nodes
- Computed stuck propagation — derive stuck status from structure
- Next actions view — leaf nodes, no blockers, status todo
- Full-text search across `notes`
- Git sync for vault (multi-device)
- AI integration (local, via Ollama)

## Credits

Built with the assistance of [Claude](https://claude.ai) (Anthropic) — used as a coding assistant throughout the design and implementation of this project.
