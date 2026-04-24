# Inferred state — design notes

## Core idea

Status is not declared by the user — it is derived from evidence.
The user logs what happened; the system infers what is true.

The only exceptions are terminal declarations: **done** and **discarded**.
These are events on the timeline, not a status field.

---

## Event tiers

**Activity events** — feed the inference engine:

| Type | Meaning |
|------|---------|
| `created` | node was created |
| `journal` | something happened, free text |
| `due_date` | a scheduled moment in the future |
| `linked` / `unlinked` | structural change |

**Declaration events** — override inference:

| Type | Meaning |
|------|---------|
| `done` | user asserts this is finished |
| `discarded` | user intentionally drops this |

The user can declare `done` or `discarded`. They cannot declare `active` —
that has to be earned through activity.

---

## Inferred states

Computed fresh at render time, never stored.

| State | Condition |
|-------|-----------|
| `done` | last declaration event is `done` |
| `discarded` | last declaration event is `discarded` |
| `overdue` | a `due_date` has passed, no `done` declaration |
| `active` | journal activity within the last ~2 weeks |
| `slowing` | last activity 2–4 weeks ago |
| `forgotten` | no activity for 4+ weeks, no declaration |
| `new` | created recently, no activity yet |

Thresholds are configurable. Declaration events take priority over inferred
states — but the inner voice can still flag tension (see below).

---

## The status field

The explicit `status:` YAML field becomes **legacy / escape hatch**.
- Existing vaults keep working — old status values are shown as-is.
- New nodes don't need it.
- Gradually replaced by inference as users add timeline events.

---

## Inner voice

The inner voice is not a status display. It is a thinking aid —
it asks questions and surfaces tensions to help the user reason.

It operates on `(inferred_state, timeline, due_dates, declarations)` and
produces a short prompt or observation, not a verdict.

### Example outputs

```
"No activity in 3 weeks — still relevant?"
"Due in 5 days, nothing logged since last month."
"Marked done, but you've been adding notes. Reopening?"
"Started 2 months ago, never touched. Discard or commit?"
"Slowing down — what's blocking this?"
```

### Design principles

- **Questions, not labels.** The inner voice asks, it doesn't judge.
- **One thought at a time.** Not a list of warnings — a single nudge.
- **Reactive.** Shown as you navigate to a node, not in a dashboard.
- **Perishable.** The nudge is for right now, in this context. Not stored.

### Rule sketch

Rules are priority-ordered. First match wins.

```
if overdue                              → "Due {date} — still happening?"
if done but recent activity             → "Marked done, but still active?"
if discarded but recent activity        → "You dropped this — reconsidering?"
if forgotten and was_active             → "Nothing for {n}w — forgotten?"
if slowing and due_date approaching     → "Slowing down, due in {n}d."
if new and no activity after 2w         → "Just created — what's the first step?"
if active                               → (silent, things are fine)
```

Rules are heuristics, not truth. The user is always right.

---

## What this removes

- The `status` field as a user-facing input (becomes derived/legacy).
- The `StatusModal` — replaced by `done` / `discarded` declaration events
  on the timeline.
- The mental overhead of keeping status in sync with reality.

---

## Open questions

- What is the refresh threshold — global config, per-node, or per-branch?
- Should `done` propagate upward? (all children done → parent nudged toward done)
- How does the inner voice handle nodes with no timeline at all (legacy nodes)?
