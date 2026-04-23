# Node lifecycle — design notes

## How we got here

The starting point was a simple `status` field on each node — a user-declared label
(`todo`, `doing`, `done`, `stuck`...). The user maintains it manually.

**Problem:** status goes stale. The user forgets to update it. The list becomes
a source of guilt, not clarity.

**First attempt: a separate timeline per node.** Each node gets a `timeline:` list
in its YAML — a sequence of typed events. Status becomes derived from events rather
than declared.

**Problem:** a parallel data structure alongside the graph adds complexity — two
things to render, two things to edit, two things to keep consistent.

**Second attempt: events as nodes.** Events become child nodes with a `type` field
(`journal`, `due`, `done`, `discarded`). One data structure, but a new node type
leaks everywhere: traversal, search, completion ratio, display all need to filter
events out. The graph is "the only data structure" but nodes are no longer uniform.

**The insight:** nodes already have a lifecycle — they are opened and closed.
Activity is not a special event type; it is closing something. A journal entry is
just creating a child node and closing it immediately. No new concept needed.

---

## Core idea

Nodes have a lifecycle: `open` or `closed`. Closing a node is the only form of
activity. Everything else — inferred state, staleness, inner voice cadence — is
computed from close timestamps propagating bottom-up through the DAG.

---

## Node schema

```yaml
description: Build the vintage radio
opened_at: 2026-04-01          # user-set: when this work began or will begin
closed_at: null                # set on closing
close_reason: null              # done | discarded | null (null = still open)
estimated_closing_date: null    # date | null  (null = no feedback)
update_period: null             # period | null  (null = no feedback)
comment: null                   # free text hint: "needs deep focus", "waiting for Marc"
how:
  - target_node: ...
```

No `status`, no `type`, no `date` field on nodes. State is carried by
`opened_at` / `closed_at` / `close_reason`.

`opened_at` is user-set and can differ from the actual file creation date:
a node created today may have `opened_at` two weeks in the past ("I started
this a while ago") or in the future ("this begins next month").

---

## The journal pattern

A journal entry = create a child node + close it immediately:

```yaml
description: spent 2h on the chassis
opened_at: 2026-04-20
closed_at: 2026-04-20
close_reason: done
```

This is not a special node type — it is just a node whose lifecycle lasted zero
seconds. Creating a child and completing a subtask are the same operation;
both advance `_last_active` up the tree identically.

**Implication:** opening a node does not count as activity. Intentions don't
register — only completed things do.

---

## Example

```
○ Build the vintage radio
   ├──○ Source the NOS capacitors
   ├──● 2026-04-20  spent 2h on the chassis
   ╰──● 2026-04-22  done
```

`●` = closed node. No special connector, no separate timeline column.
Closed children are dimmed in the UI.

---

## Computed fields

All computed at load time (topological order, leaves → roots). Never stored.

| Field | Definition |
|-------|-----------|
| `_last_active` | `max(close_timestamp)` across all closed descendants; `null` if none |
| `_is_overdue` | `now > estimated_closing_date`; `null` if no `estimated_closing_date` |
| `_last_update` | start of current period window (see below); `null` if no `update_period` |
| `_is_active` | `_last_active >= _last_update`; `null` if no `update_period` or still in first period |

### `_last_update` — period window floor

Computed at load time (not stored), snapped to the period grid:

```
elapsed = today - opened_at
periods = elapsed // update_period
_last_update = opened_at + periods * update_period
```

If `opened_at` is in the future, the node is dormant — `_is_active` stays `null`.

**First period grace:** if `periods == 0` (today is still within the first
`update_period` window), `_is_active` is `null` regardless of activity. No
check-in is due yet, so "forgotten" would be a false alarm.

`_last_update + update_period` is the next check-in deadline.
`_is_active` is true when a descendant was closed at or after `_last_update`.

### `_last_active` propagation

`_last_active` on a parent = `max(_last_active)` across all children (both open
and closed children contribute their own `_last_active`). Structural edits
(description, `estimated_closing_date`, etc.) do not advance it.

### Closed nodes

A closed node's `_is_active` is always `null` — no point tracking cadence.
`_is_overdue` can remain true on a closed node (informative: closed late vs. on time).

### State space

No third state is needed. `open | closed` combined with `update_period` and
`opened_at` covers all cases:

| state | update_period | opened_at | reading |
|-------|--------------|-----------|---------|
| open | set | past / today | actively tracked |
| open | null | any | parked, no feedback |
| open | set (long) | future | scheduled — dormant until that date |
| closed | — | — | done / discarded |

"Scheduled" is not a separate state — it is an open node with a future `opened_at`
and a long enough `update_period` that the inner voice stays quiet until then.

---

## Inferred state

Assembled in priority order, for open nodes only:

```
state == closed                    → done / discarded  (from close_reason)
_is_overdue                        → overdue
_is_active == true                 → active
_is_active == false                → forgotten
_is_active == null                 → (no badge)  — no period set, or still in first period
```

---

## UI

### Table layout

```
[ tree + description ] [ when ] [ state ]
```

- **when** — for open nodes: `estimated_closing_date` (relative) or `update_period` cadence
- **state** — inferred state badge

Closed children are rendered dimmed, with their `close_timestamp` in the **when**
column. No separate connector style needed — dimming is enough.

### Creating a journal entry

Shortcut (e.g. `j`) opens a quick-entry modal: description only. The node is
created and immediately closed (`close_reason: done`, timestamps = now).

### Editing

`e` on a closed child opens a minimal edit modal: description and close_timestamp.
`e` on an open node: description, estimated_closing_date, update_period, comment.

---

## What this replaces

| Old | New |
|-----|-----|
| `status` field | `state` (open/closed) + `close_reason` |
| `type` on event nodes | removed — no event node type |
| separate `timeline` | closed child nodes |
| `is_closed` derived from children | `closed_at != null` directly on the node |
| `last_activity` from journal children | `_last_active` from any closed descendant |
| `note` + `work_type` | `comment` |
| `_creation_date` | `opened_at` (user-editable, can be past or future) |

---

## Roadmap

Each step leaves the app working.

**Step 1 — node lifecycle fields**
- add `open_timestamp`, `close_timestamp`, `close_reason` to `Node` and YAML schema
- `open_timestamp` set automatically at creation
- closing a node: `s` or dedicated shortcut → sets `close_timestamp` + `close_reason`
- closed nodes rendered dimmed; `status` field kept as legacy display fallback

**Step 2 — journal shortcut**
- `j` opens quick-entry modal (description only)
- creates child node + immediately closes it
- no new node type — purely a UX shortcut over existing operations

**Step 3 — computed fields (leaf level)**
- compute `_last_active`, `_is_overdue` from direct children
- show in home view columns
- no propagation yet

**Step 4 — bottom-up propagation**
- topological sort at load time
- propagate `_last_active` leaves → roots
- compute `_last_update`, `_is_active` for nodes with `update_period`
- inferred state replaces `status` display; `status` field becomes legacy/ignored

**Step 5 — inner voice**
- add `estimated_closing_date`, `update_period`, `comment` to node schema
- plug computed fields into the prompt
- one question, 3-4 choices mapping to concrete app actions

---

## Open questions

- Should closing a node require navigating to it, or can it be done from any view (e.g. inline in the table)?
- Filtering: hide closed children older than N days?
- `completion_ratio` — still useful? Would be: `closed children / total children` (no event filtering needed).
- Legacy `status` migration: nodes with `status: done` — auto-set `close_reason: done` on first load?
