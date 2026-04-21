# Time axis — design notes

## Motivations

- "What was I working on a month ago?" → chronological activity timeline
- "This project is stuck... why?" → per-node history, diagnose stagnation
- "How much time did I spend?" → journal entries with optional duration

---

## What we ruled out

- **OR / NOT / REQUIRE link types** — OR dissolves into an intermediate decision node; NOT is usually a reframing problem; REQUIRE can wait.
- **Central events.log** — redundant given all YAMLs are loaded at startup; per-node is simpler and coherent with the existing model.

---

## Data model

Events are owned by nodes — a list in each YAML file. Not a first-class graph object.

```yaml
events:
  - date: 2026-04-21
    type: status_change
    from: todo
    to: doing
  - date: 2026-04-21
    type: journal
    text: "spent 2h debugging the parser"
```

### Event types

| Type | Trigger |
|------|---------|
| `created` | node first created |
| `status_change` | status edited, records `from`/`to` |
| `renamed` | description changed |
| `linked` | node gained a parent (recorded on the child) |
| `unlinked` | node lost a parent (recorded on the child) |
| `journal` | manual entry, free text + optional duration |

Structural events involving two nodes (linked/unlinked) are recorded on the **child** — that's where you'd look when asking "why is this here?".

Events are **declarative and editable** — you can correct dates, add past entries, delete mistakes. Not an audit trail, a personal record.

---

## UI surfaces

### 1. `last event` column — home page

Passive staleness signal. Shows date of most recent event on any node in the branch.

```
@ Build the radio         active      2026-04-21
@ Learn Portuguese        on hold     2026-03-02
@ Fix the bike            someday     2026-01-14
```

### 2. History view — dedicated page

Chronological list of events, two entry points:
- `L` from **home** → global timeline across all nodes
- `L` from **node view** → scoped to current node and its descendants

```
── Activity ─────────────────────────────────────
2026-04-21  [KLOP45 repair capacitors]  status → doing
2026-04-20  [KLOP45]  "spent 2h debugging the parser"
2026-03-15  [OAAP11 get the case]  status → todo
```

Editing in history view: cursor on event, `e` to edit, `a` to add, `D` to delete. Same keys as everywhere else.

---

## Implementation order

1. Add `events` to YAML schema + `Node` dataclass
2. Auto-record `created` and `status_change` events
3. `last event` column on home page
4. History view (global + node-scoped)
