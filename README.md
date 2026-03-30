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

## Architecture

### Files

Each task (or project) is a YAML file stored in the `data/` directory.

**Filename format:** `AB12CD_readable_slug.yaml` — a random 6-character ID followed by a human-readable slug of the description.

Example: `data/M11AB_vintage_radio_build.yaml`

```yaml
description: Build a vintage radio
start_date: '2026-03-01'
status: stuck
why:
    - fun
    - learn stuff
how:
    - get elec gear: soldering iron, voltmeter
    - build the new electronics #R4DIO_elec
but:
    - budget <300 euros
    - risk stopping midcourse
or:
    - Start a less complex build (alarm clock)
required_by:
    - personal projects showcase #A1B2C3
```

### Linking

A line ending with `#task_id` links to another file. The ID is resolved by scanning the `data/` directory (supports up to ~500 files). Each line can have at most one link.

### Backlinks

Some fields have a defined inverse. When a link is created or removed via the TUI, the corresponding backlink in the target file is automatically maintained:

| Field | Inverse |
|---|---|
| `how` | `why` |
| `why` | `how` |
| `need` | `required_by` |
| `required_by` | `need` |

`but` and `or` are one-directional (no inverse).

### Config

Fields and valid statuses are defined in `config.py`. This allows customising the schema without touching the app code.

## UI

Terminal-based (Unix), two-column layout.

**Left panel** — switches between:
- **File list** — browse and search all tasks in `data/`
- **Task view** — parsed view of the open task, one line selected at a time

**Right panel** — switches between:
- **Preview** — shows the file linked on the selected line
- **Link picker** — file list for creating a link (activated with `l`)

**Bottom bar:** inline editor, shown when editing a line.

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

### Later
- AI integration (local, via Ollama)
- Custom fields via config.py

## Credits

Built with the assistance of [Claude](https://claude.ai) (Anthropic) — used as a coding assistant throughout the design and implementation of this project.
