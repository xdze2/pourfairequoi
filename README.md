# PourFaireQuoi (pfq)

PourFaireQuoi is yet another todo list app, but while most task managers focus on *what* and *when*, this app focuses on *how*, *why*, *but*, *or*, and other reasoning dimensions. It allows you to build a reasoning engine for complex projects, tracking decisions, alternatives, and history.

The goal is a minimal, simple app for prototyping and personal use.
The app name is pourfairequoi, abbreviated to "pfq".


## Goals

- Brainstorm ideas
- Plan projects
- Brain dump / mind mapping
- Identify real motivations and alternative routes
- Keep a decision log
- Identify project blockers
  - Why is it stuck?
  - Break it down into smaller steps

It is more a personal tool than a professional/enterprise task manager.
Key design principles:
- Local files for privacy
- Simplicity: terminal-based
- One YAML file per task — git-friendly (readable diffs, version history, branching)

Could eventually be paired with AI, but:
- Should work without AI
- Prefer local AI (e.g. Ollama)

## Data model

### Node types
- goal — aspirational, no clear end condition ("be healthier")
- task — concrete, completable ("buy running shoes")
- constraint — a fact that shapes decisions, not something you do ("budget < 300€")


### Node status

statuses as pure lifecycle

- todo, active, stuck, done, discarded


## Architecture

### Files

Each task (or project) is a YAML file stored in the `data/` directory.

**Filename format:** `AB12CD_readable_slug.yaml` — a random 6-character ID followed by a human-readable slug of the description.

Example: `data/M11AB_vintage_radio_build.yaml`

```yaml
description: Build a vintage radio   # short title, used in list view
type: goal                            # goal | task | constraint
status: stuck                         # todo | active | stuck | done | discarded
start_date: '2026-03-01'
due_date: '2026-06-01'               # deadline or scheduled date (optional)
notes: |                              # free-form multiline text
  Started this after watching a restoration video.
  Main challenge is sourcing the original capacitors.
links:
- type: why
  description: fun
- type: why
  description: learn stuff
- type: how
  description: get elec gear
- type: how
  description: build the new electronics
  target_node: R4DIO1               # optional: 6-char ID of the linked node
- type: but
  description: budget <300 euros
- type: or
  description: Start a less complex build (alarm clock)
```

### Linking

Links are stored in a unified `links` list. Each entry has:
- `type` — the link kind: `why`, `how`, `but`, `or`, etc.
- `description` — free-form text label
- `target_node` — (optional) the 6-character ID of another node in `data/`

A link without `target_node` is a plain annotation (no file reference).

### Backlinks

Some link types have a defined inverse. When a link is created or removed via the TUI, the corresponding backlink in the target file is automatically maintained:

| Type | Inverse |
|---|---|
| `how` | `why` |
| `why` | `how` |
| `need` | `required_by` |
| `required_by` | `need` |

`but` and `or` are one-directional (no inverse).

### Config

Fields and valid statuses are defined in `config.py`. This allows customising the schema without touching the app code.

## UI

Terminal-based (Unix), three-column layout.

All files are loaded into memory at startup for fast search and graph traversal.

**Left column (1fr):**
- **App header** — app title
- **File list** — browse and search all tasks, showing description, type and status

**Middle column (2fr)** — switches between:
- **Task view** — parsed view of the open task, one line selected at a time
- **Link picker** — file list for creating a link (activated with `l`)

**Right column (1fr) — context pane (read-only, auto-updated):**
- **Why subgraph** — all nodes reachable upward via `why` links (BFS, flattened)
- **Current node** — description, type, status
- **How subgraph** — all nodes reachable downward via `how` links (BFS, flattened)
- **Statistics** — node counts by status across both subgraphs

Indentation in the subgraphs reflects depth from the current node, reduced for nodes cited multiple times (shared sub-goals or shared steps). A `×N` marker indicates a node referenced by N parents in the subgraph.

**Bottom bar:** key bindings reference (Textual footer).

### Keyboard shortcuts

#### File list
| Key | Action |
|---|---|
| `↑` / `↓` | Navigate files |
| `Enter` | Open file in task view |
| `n` | Create new task (prompts for description) |
| `d` | Delete task (with confirmation) |
| `/` | Search / filter by description |
| `Esc` | Clear search |

#### Task view
| Key | Action |
|---|---|
| `↑` / `↓` | Navigate lines |
| `e` | Enter edit mode |
| `Enter` | Confirm edit and save |
| `Esc` | Cancel edit — or return to file list |
| `n` | Insert new line below |
| `d` | Delete selected line |
| `a` | Add a missing section |
| `l` | Create a link on the selected line |
| `u` | Remove the link on the selected line (with confirmation) |
| `Enter` | Follow link — open linked file |
| `b` | Go back (link navigation history) |

#### Link picker (right panel)
| Key | Action |
|---|---|
| `↑` / `↓` | Navigate files |
| `Enter` | Link selected file (auto-creates backlink) |
| `Esc` | Cancel |
| `/` | Search / filter |

### CLI

```bash
pfq                                          # open the TUI
pfq new "my project"                         # create a new task and open it
pfq open data/M11AB_vintage_radio_build.yaml # open a specific file
pfq check                                    # report missing or broken backlinks
pfq fix                                      # auto-fix missing backlinks
pfq fix --dry-run                            # preview fixes without writing
```

## Tech

Built with Python:
- Click
- PyYAML
- Textual (TUI framework, includes Rich)

## Setup

```bash
pip install -e .
pfq new "my first task"
```

## Roadmap

### v0.1 — done
- Single file view with arrow navigation
- Edit mode (`e` / `Enter` / `Esc`), insert (`n`), delete (`d`)
- Auto-save on confirm, cancel restores original
- Right panel: preview of linked file
- Add missing section (`a`)

### v0.2 — done
- Two-column layout (file list ↔ task view, preview ↔ link picker)
- File list with search (`/`), create (`n`), delete (`d`)
- Link creation (`l`) and removal (`u`) with automatic backlink management
- `pfq check` / `pfq fix` for backlink consistency

### v0.3 — in progress
- New data model: `type` (goal / task / constraint), `due_date`, `notes`
- Preload all files into memory at startup for fast search and graph traversal
- Three-column layout: file list | task view / link picker | context pane
- Context pane: local why/how subgraph with BFS traversal, indentation by depth, statistics

### Later
- Show type and due date in file list
- Full-text search across `notes`
- AI integration (local, via Ollama)
- Custom fields via config.py

## Credits

Built with the assistance of [Claude](https://claude.ai) (Anthropic) — used as a coding assistant throughout the design and implementation of this project.
