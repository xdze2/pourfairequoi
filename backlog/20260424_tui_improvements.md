# TUI App Improvements (v2)

Date: 2026-04-24


- Show secondary link again, see [backlog/improve_2nd_why_display.md]()
- Fix dates parsing/format!!
- shift left-right: move identation (as a regular list)
- [x] Fix col wdith: comment full width (auto is not working)
- [x] Sort roots by importance (size of downward tree)
- bug in parents + append
- nudge to create layers (max 6-8 child nodes, else than logs) 
- Merge home view and regular view (fix symbols leaf in home view)
- pulse = -2/+2 days view ----> get back the log time idea (cols: day, week, month, col year) ???

scale + position
yQmwd
#
 0
  #
    0
    +3


- Full page calendar view
- When a node is collapsed, pulse is propagated upward (min) (with a glyph)

## 1. Modal Style & UX Unification

**Current state**: Modals have inconsistent styling and interaction patterns.

**Goal**: Make all modals feel like part of the same system.

**Tasks**:
- [ ] Audit all modals (`CreateModal`, `DeleteModal`, `LinkModal`, `StatusModal`, `EditModal`)
- [ ] Define unified modal chrome (title, border, footer with action buttons)
- [ ] Standardize dismiss patterns (Esc, Enter, Ctrl+S — currently inconsistent)
- [ ] Test modal nesting (can you open one modal from another? no...)
- [ ] Consider: do all modals need the same width? Consistent focus/blur behavior?

**Why**: Users should spend mental energy on *what* they're doing, not *how* the modal works.

---

## 2. Exploit "Mood" / Comment → Inner Voice (Companion)

**Current state**: The `CompanionPanel` exists but is underutilized. Comments are just text.

**Idea**: Comments become "notes to self" that the companion can respond to or amplify.

**Possible directions**:
- [ ] Show companion reactions to the current node's comment (encouragement, devil's advocate, breakdown of vague goals)
- [ ] Companion summarizes the "why chain" (parents) in plain language — why are you really doing this?
- [ ] Companion flags inconsistencies (e.g., "this task has been open 6 months with no update, but target date was 2 weeks ago")
- [ ] Companion suggests next action based on comment + status + date
- [ ] Toggle: show companion for nodes with comments only, or always?

**Why**: The companion is pfq's soul — it's what differentiates from a flat task list. Make it pull its weight.

---

## 3. Node View Filtering: Mask Done / Old Tasks

**Current state**: All children/parents visible, regardless of status or age.

**Problem**: For large goal hierarchies, done tasks and very old stale branches clutter the view.

**Filters to add**:
- [ ] Hide done tasks (toggle: show/hide closed nodes)
- [ ] Hide very old tasks (configurable: hide nodes closed >N days ago)
- [ ] Hide forgotten tasks (pulse status = forgotten — hide by default?)
- [ ] Preserve filter across navigation (user's preference)

**Implementation notes**:
- Filters apply to the view layer (`view.py`), not the graph — no data is deleted
- Add visual indicator when filters are active (e.g., "3 hidden")
- Keyboard shortcut to toggle each filter

**Why**: Focus on what's active right now. Archival/history is important but shouldn't dominate the UI.

---

## 4. "Pulse"— Definition & Visibility


- What does "forgotten" actually mean? forgoten since the creation date ? or the last update date ?
- Add also last edit ?
- Add also next target, even if no update set up:  `◇` upcoming
- [ ] Highlight "what closed recently" — activity is as important as age

**Why**: "What is hot now" = "what changed recently" + "what's due soon" + "what's overdue". Multiple signals matter.

---

## 5. Deep Code Review Needed

**Current hot spots for review**:
- [ ] `app.py`: Navigation, modal lifecycle, state management — getting complex?
- [ ] `view.py`: `build_node_view()` — is tree-building logic clear? Room for filters?
- [ ] `model.py`: `compute_lifecycle()` — is the `_is_active`, `_is_overdue` logic bulletproof?
- [ ] `render.py`: Is status glyph logic readable? Room for new statuses?
- [ ] `modals.py`: Can modal code be factored better? Too much duplication?
- [ ] `disk_io.py`: Load/save path — any edge cases with symlinks, special chars, concurrent writes?

**Goal**: Before locking down the information model for mobile, make sure the v1 code is clean and the decisions are documented.

---

## 6. New Views: "What's Next?" / "What's Up Today?"

**Current views**: Home (roots + children), Node (neighborhood).

**New views to explore**:
- [ ] **Today's Agenda**: All open tasks due today or overdue, sorted by urgency. Show parents (why) for context.
- [ ] **What's Hot**: Recently closed tasks (last 7 days) + tasks due soon (next 7 days) + forgotten tasks. Shows momentum + risk.
- [ ] **Inbox / Unlinked**: New tasks that haven't been linked to a parent yet. Quick triage.
- [ ] **Search Results**: Jump-to view after `s` search.

**Implementation**:
- [ ] Add navigation keys: `t` for today, `n` for next (hot), `i` for inbox
- [ ] Reuse `build_node_view()` logic where possible (same ViewRow rendering)
- [ ] Consider: can these be tabs instead of separate views?

**Why**: Different use cases (morning planning, quick check-in, end-of-day review) need different views. The current neighborhood model is exploration-focused; these would be action-focused.

---

## Not In Scope (v2)

- Mobile version (separate effort)
- Sync/cloud (local vault only)
- Recurring tasks / templates
- Analytics / burndown charts
- Undo/redo history

---

## Rough Priority

1. **Code review** (unblock confidence in architecture)
2. **Pulse definition** (clarify what "hot" means — informs all other changes)
3. **Modal unification** (improves perceived quality)
4. **Filters** (unclutter view for heavy users)
5. **New views** (enable different use cases)
6. **Companion expansion** (polish, not essential)

---

## Questions for Discussion

- Should filtering persist in `app.py` state, or be stored per-vault in config?
- What's the default `update_period` for nodes that don't specify one? (Or is "no period" the right answer?)
- Does "forgotten" apply to root nodes? They often don't have frequent check-ins.
- Should "What's Hot" be algorithmic (weighted scoring) or just a filtered view (recency + due date)?
