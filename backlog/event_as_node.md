# Events as nodes — design notes

## How we got here

The starting point was a simple `status` field on each node — a user-declared label
(`todo`, `doing`, `done`, `stuck`...). Two vocabularies, one for leaves, one for
roots/middle nodes. The user maintains it manually.

**Problem:** status goes stale. The user forgets to update it. The list becomes
a source of guilt, not clarity. And status can't tell you *why* a node is stuck,
or *how long* it has been.

**First attempt: a separate timeline per node.** Each node gets a `timeline:` list
in its YAML — a sequence of typed events (`created`, `journal`, `due_date`,
`status_change`...). Status becomes derived from events rather than declared.
The inner voice reads the timeline to generate nudges.

**Problem:** a parallel data structure alongside the graph adds complexity — two
things to render, two things to edit, two things to keep consistent. And events
have no graph relationships of their own.

**The insight:** events are just nodes with a date. The graph is already the right
structure. A journal entry, a deadline, a closure declaration — all become child
nodes, created and linked like anything else. No new concept needed.

**Result:** one data structure, four event types, computed state propagating
bottom-up through the DAG. The inner voice reads the graph and asks one
actionable question per node.

---

## Core idea

No separate timeline structure. Events are just child nodes with a `date` field.
The graph is the only data structure.

---

## Node schema

```yaml
description: Build the vintage radio
comment: need the fablab to be open, waiting for the visit
next_due_date: ("periodic", "2w")   # or ("date", date) or null (inner voice off)
_creation_date: 2026-04-01          # meta, set once at creation, could be editable
how:
  - target_node: ...
```

Regular nodes have no `type`, no `status`, no `date`.

---

## Event nodes

A node becomes an event when it has a `date` field. Event nodes are regular children,
created and linked like any other node. The `type` field is only present on event nodes.

```yaml
description: spent 2h on the chassis
date: 2026-04-20
type: journal
```

### Event type vocabulary

| Type | Role | Counts as |
|------|------|-----------|
| `journal` | activity log, free text | `last_activity` |
| `due` | deadline or scheduled moment | `next_due` |
| `done` | terminal declaration | `is_closed` |
| `discarded` | terminal declaration | `is_closed` |

Four types, four distinct roles, no overlap.

A `due` node is a future anchor — it does not count as activity. "Overdue" is derived
at read time (`next_due < today and not is_closed`), never stored.

---

## Example

```
○ Build the vintage radio
   ├──○ Source the NOS capacitors
   ├──○ 2026-04-20  spent 2h on the chassis     [journal]
   ├──○ 2026-06-01  fablab visit                [due]
   ╰──○ 2026-04-22  done                        [done]
```

---

## Computed fields (read time, never stored)

| Field | Definition |
|-------|-----------|
| `is_closed` | any child with type `done` or `discarded` |
| `last_activity` | most recent `date` among `journal` children |
| `next_due` | nearest future `date` among `due` children |
| `overdue` | `next_due < today and not is_closed` |
| `completion_ratio` | closed children / total non-event children |

`is_closed` is checked first — a closed node skips all other computation.

---

## Bottom-up propagation

Computed fields propagate level by level, leaves first (topological order).
Each node aggregates only its **direct children** — but since children have already
aggregated their own, the signal naturally reaches the roots.

**Aggregation rules:**

| Field | Rule |
|-------|------|
| `is_closed` | all non-event children are closed |
| `last_activity` | max(`last_activity`) across children |
| `next_due` | min(`next_due`) across open children |
| `overdue` | any open child is overdue |
| `completion_ratio` | closed children / total non-event children |

**Computed once at load time, in topological order (leaves → roots).**
Invalidated and recomputed when any node in the subtree is edited.

A closed parent mutes its children — they are visually dimmed and the inner voice
stays silent for them, even if individually they would trigger a nudge.

---

## Inferred state

Assembled from the four computed fields, in priority order:

```
is_closed                         → done / discarded
overdue                           → overdue
last_activity > 4w ago (or none)  → forgotten
last_activity > 2w ago            → slowing
else                              → active
```

---

## Inner voice

`next_due_date` controls the nudge cadence:

```
null                  → inner voice off for this node
(date, date)          → check between these dates
("periodic", "2w")    → check every 2 weeks
```

The inner voice receives as context:
- `description`
- `comment`  ← free text hint from the user ("needs deep focus", "waiting for Marc")
- `inferred_state`
- `last_activity`
- `next_due`
- previous journal entries (last 2-3)

It produces one question and 3-4 choices, each mapping to a concrete action
(add a child node, mark done, add a due date, etc.).

---

## What this replaces

- `status` field — replaced by `is_closed` + inferred state from event children
- `type` field on regular nodes — removed, position in graph carries the meaning
- separate `timeline` structure — replaced by dated child nodes
- `note` + `work_type` fields — merged into `comment`

---

## Roadmap

Incremental steps, each leaving the app working. The current `status` field survives
as legacy data until step 4, then gets quietly retired.

**Step 1 — add `date` field to nodes**
- add `date` to `Node` dataclass and YAML schema
- render event nodes in the tree: `2026-04-20  spent 2h on the chassis`
- editable via `e` like any other field
- no type, no propagation yet — just data

**Step 2 — event type vocabulary**
- add `type` field (only meaningful when `date` is set): `journal`, `due`, `done`, `discarded`
- render event nodes differently (dimmed, date prefix, type glyph)
- filter toggle: hide/show event children in the tree

**Step 3 — computed fields (leaf level)**
- compute `is_closed`, `last_activity`, `next_due` from direct event children
- show `last_activity` and `next_due` columns in home view
- no propagation yet

**Step 4 — bottom-up propagation**
- topological sort at load time
- propagate level by level, leaves → roots
- inferred state replaces the current `status` display
- `status` field becomes legacy/ignored

**Step 5 — inner voice**
- add `next_due_date` and `comment` fields to node schema
- plug computed fields into the prompt
- one question, 3-4 choices mapping to concrete app actions

---

## Open questions

- Should `_creation_date` auto-generate a `journal` child, or stay as a bare meta field?
- Filtering: hide event nodes older than N days? hide `done`/`discarded` subtrees?
- Remove the existing `timeline` field now or keep as legacy alongside event nodes?
