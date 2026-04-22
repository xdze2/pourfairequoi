# Time axis — design notes

## Motivations

- "What was I working on a month ago?" → chronological activity timeline
- "This project is stuck... why?" → per-node history, diagnose stagnation
- "How much time did I spend?" → journal entries with optional duration
- "What's coming up?" → deadlines, meetings, scheduled dates

---

## What we ruled out

- **OR / NOT / REQUIRE link types** — OR dissolves into an intermediate decision node; NOT is usually a reframing problem; REQUIRE can wait.
- **Central events.log** — redundant given all YAMLs are loaded at startup; per-node is simpler and coherent with the existing model.
- **Separate `date:` field on nodes for deadlines** — a `due_date` event on the timeline covers this; no need for a parallel concept.

---

## Data model

Each node owns a **timeline** — a list of events in its YAML file. Not a first-class graph object.

```yaml
timeline:
  - date: "2026-04-21"
    type: created
  - date: "2026-04-21"
    type: status_change
    from: todo
    to: doing
  - date: "2026-04-25"
    type: due_date
    text: "team sync"
  - date: "march 2027"
    type: due_date
    text: "project review"
  - date: "2026-04-20"
    type: journal
    text: "spent 2h debugging the parser"
```

### Event types

Two categories:

**Meta types** — auto-recorded by the app:

| Type | Trigger |
|------|---------|
| `created` | node first created |
| `status_change` | status edited, records `from`/`to` |
| `linked` | node gained a parent (recorded on the child) |
| `unlinked` | node lost a parent (recorded on the child) |

**User types** — manually added, free text:

| Type | Use |
|------|-----|
| `due_date` | scheduled future event: meeting, deadline, appointment |
| `journal` | activity log entry: "worked on this today", notes, duration |

The type field is a free string — meta types happen to be fixed snake_case, user types can be anything.

Structural events (linked/unlinked) are recorded on the **child** — that's where you'd look when asking "why is this here?".

### Dates

`date` is a **free text string**. Examples: `"2026-04-21"`, `"april 2026"`, `"march 2027"`, `"Q3 2026"`.

Parsing is best-effort, done at display/query time. Events with unparseable or vague dates are shown but excluded from sorted queries (or shown separately). No data is lost.

### A meeting is a node

A scheduled meeting or deadline is just a regular node with `due_date` events on its timeline. It can be linked wherever it belongs in the graph. The node's status (`todo` / `done` / `cancelled`) tracks its lifecycle.

Events are **declarative and editable** — you can correct dates, add past entries, delete mistakes. Not an audit trail, a personal record.

---

## UI surfaces

### 1. `last event` column — home page

Passive staleness signal. Shows date of most recent past event on any node in the branch.

```
@ Build the radio         active      2026-04-21
@ Learn Portuguese        on hold     2026-03-02
@ Fix the bike            someday     2026-01-14
```

### 2. `next event` column — home page

Shows the nearest upcoming `due_date` event across descendants. Displayed as relative time ("in 3 days", "in 2 months"). Vague dates shown as-is. Empty if none.

```
@ Build the radio         active      2026-04-21    in 3 days
@ Learn Portuguese        on hold     2026-03-02    march 2027
@ Fix the bike            someday     2026-01-14
```

### 3. History view — dedicated page

Chronological list of events, two entry points:
- `L` from **home** → global timeline across all nodes
- `L` from **node view** → scoped to current node and its descendants

```
── Activity ─────────────────────────────────────
2026-04-25  [KLOP45 repair capacitors]  due: team sync
2026-04-21  [KLOP45 repair capacitors]  status → doing
2026-04-20  [KLOP45]  "spent 2h debugging the parser"
2026-03-15  [OAAP11 get the case]  status → todo
```

Editing in history view: cursor on event, `e` to edit, `a` to add, `D` to delete. Same keys as everywhere else.

---

## Implementation order

1. Add `timeline` to YAML schema + `Node` dataclass
2. Auto-record `created` and `status_change` events
3. `last event` column on home page
4. `next event` column on home page (requires date parsing utility)
5. History view (global + node-scoped)
