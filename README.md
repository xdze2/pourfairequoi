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
- Filename format: `{random_6_char}_{readable_slug}.yaml` 
- `node_id` is the entire file stem.


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
- target_node: KLOP45_get_the_case       # link to a child file node (full stem)
- target_node: OAAP11_repair_capacitors

```

Every `how` entry must reference a file node via `target_node`.


### Link directions

**`how` — stored in the parent, points to children.**
A parent declares what it is made of. Natural direction: a project lists its tasks.

**`why` — derived at load time** by reversing `how` links across the store.
"What does this node serve?" is answered by scanning which parents declared it as a child. Never stored — no duplication, no inconsistency.



## Architecture
Terminal-based, using textual.
All files are loaded into memory at startup.

```
Disk <---> Model <--api--> UI
```

## UI: Subgraph views

At startup shows a home page: all root nodes (no parents) with type, status, and date chips.

When a node is open, shows its local neighbourhood with a left margin indicating direction, capped at 3 levels in each direction:

```
     - root
why     ┌─ grandparent 2 
 │      ┌─ grandparent         goal        active  
 │   ┌─ parent                 project     todo     
 ▶   current node              task        active    
 │   ├─ child 1                task        doable   
 │   └─ child 2                task        done     
how     └─ grandchild          task        todo     
```

- Left margin: `why`/`│`/`▶`/`│`/`how` shows your position in the hierarchy
- `root` line at the top — selectable, Enter navigates to the home page
- Type and status chips aligned in fixed-width columns to the right of descriptions


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

## Setup

```bash
pip install -e .
pfq
```


## Credits

Built with the assistance of [Claude](https://claude.ai) (Anthropic) — used as a coding assistant throughout the design and implementation of this project.
