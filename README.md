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
start_date: ...
status: stuck
why:
    - fun
    - learn stuff
    - get a nice radio object
    - have a project to show #a1y89
need:
    - time
how:
    - "get elec gear: soldering iron, voltmeter"
    - (opt) find a fablab
    - buy a first old radio #buy_old_radio
    - build the new electronics #radio_elec
but:
    - budget <300 euros #budget300
    - risk stopping midcourse
    - lost time and money
or:
    - Start a less complex build (alarm clock)
```

### Linking

A line ending with `#task_id` links to another file. The ID is resolved by scanning the `data/` directory (supports up to ~500 files). Each line can have at most one link.

### Config

Fields and valid statuses are defined in `config.py`. This allows customising the schema without touching the app code.

## UI

Terminal-based (Unix) with a vertical split screen.

**Left panel:** current task file — parsed view, one line selected at a time.

**Right panel:**
- v0.1: shows the linked file when a line with a `#link` is selected
- v0.2: file list and search panel

**Bottom bar:** inline editor (activated with `i`).

### Keyboard shortcuts

| Key | Action |
|---|---|
| `↑` / `↓` | Navigate lines |
| `i` | Enter edit mode |
| `Enter` | Confirm edit and save to disk |
| `Esc` | Cancel edit (restores original, no save) |
| `n` | Insert new line below |
| `d` | Delete selected line |
| `Enter` | Open linked file in left panel |
| `b` | Go back to previous file |

### Launch

```bash
pfq                                        # open the TUI (file list)
pfq open data/M11AB_vintage_radio_build.yaml  # open a specific file
pfq new "my project"                       # create and open a new task
```

## Tech

Built with Python:
- Click
- Rich and Textual

## Roadmap

### v0.1
- Create and open a single file
- Arrow key navigation
- Edit mode: `i` to enter, `Enter` to save, `Esc` to cancel
- Insert (`n`) and delete (`d`) lines
- Right panel: preview of linked file
- CLI: `pfq <file>`

### v0.2
- File list and search panel
- Navigate between files with back-stack (`b`)

### Later
- AI integration (local, via Ollama)
- Custom fields beyond config.py

## Setup

```bash
pip install -e .
pfq new "my first task"
pfq open data/<filename>.yaml
```

## Credits

Built with the assistance of [Claude](https://claude.ai) (Anthropic) — used as a coding assistant throughout the design and implementation of this project.
