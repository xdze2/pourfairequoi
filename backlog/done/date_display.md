# Date display — design notes

## The three date fields

| Field | Set by | Meaning |
|-------|--------|---------|
| `estimated_closing_date` | user, while open | the plan — "I expect to finish this by jun." |
| `closed_at` | user on close (can be backdated) | the fact — "I actually finished this on apr. 20" |
| `opened_at` | user | when the work started (or will start) |

`estimated_closing_date` is a planning signal. `closed_at` is a historical record.
They are independent — a node can be closed late, early, or without any estimate at all.

**Current bug:** `_due_label` in `view.py` switches what it displays based on `is_closed`,
so closing a node makes the estimated date disappear and `closed_at` (today) appears in its
place — looks like the due date moved.

---

## What does the user want to see?

### While a node is open:
- **Am I on track?** → `estimated_closing_date` vs today (`_is_overdue`)
- **When do I need to check in?** → next `update` date
- **Is this node alive?** → `pulse` (active / forgotten)

### After a node is closed:
- **When did I finish it?** → `closed_at` (+ duration from `opened_at`)
- **Was it on time?** → `closed_at` vs `estimated_closing_date` (late / early / on time)
- **How long did it take?** → `closed_at - opened_at`

---

## Open questions

**1. Should `estimated_closing_date` remain visible after closing?**

Option A: Yes, always — lets you see planned vs actual at a glance.
Option B: No — once closed it's noise; `closed_at` is what matters.
Option C: Show both — `✓ apr. 20  (was jun.)` — but risks clutter.

**2. Column split**

Current: `pulse | update | description | state | target`

The `target` column conflates two things depending on state:
- Open: estimated close date (a plan)
- Closed: actual close date (a fact)

Alternatives:
- Two columns: `planned` + `closed` — sparse but unambiguous
- One column with smart display: show `closed_at` for closed, `estimated_closing_date`
  for open, and on closed nodes add a dim suffix if they differ
- Drop `estimated_closing_date` from the table entirely for closed nodes — it lives
  in the YAML and can be seen on edit

**3. `closed_at` editability**

Currently `closed_at` is set to `date.today()` on close with no way to backdate from
the UI. The `StateModal` should allow the user to set a custom close date
(e.g. "I finished this yesterday").

**4. Duration — from what to what?**

`opened_at → closed_at` is the most meaningful duration.
But `opened_at` is optional — fallback to file creation date? Or just omit duration.

---

## Proposed direction (to validate)

- `estimated_closing_date` always shows in `target` for open nodes (the plan)
- On close: `target` shows `✓ closed_at  (duration)`, with `estimated_closing_date`
  as a dim suffix only if it differs significantly — e.g. `✓ apr. 20  · was jun.`
- `StateModal` gains an optional date input for backdating `closed_at`
- `pulse` stays read-only, `update` stays editable, `state` becomes the close action
