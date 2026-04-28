# TUI App Improvements (v2)

Date: 2026-04-24


- [x] Show secondary link again, see [backlog/improve_2nd_why_display.md]()
- [x] Fix dates parsing/format!!
- [x] shift left-right: move identation (as a regular list)!!
- [x] Fix col wdith: comment full width (auto is not working)
- [x] Sort roots by importance (size of downward tree)
- [x] Fix glyps in home view
- [tbd] nudge to create layers (max 6-8 child nodes, else than logs) 
- [tbd] pulse = -2/+2 days view ----> get back the log time idea (cols: day, week, month, col year) ???
- [hard] Merge home view and regular view: see [text](lenses.md)
- [hard] Full page calendar view
- [cool] When a node is collapsed, pulse is propagated upward (min) (with a glyph)
- [ ] bug in parents + append (--> allow edit only if result is visible in the tree graph)

## 1. Modal Style & UX Unification

- [ ] Audit all modals (`CreateModal`, `DeleteModal`, `LinkModal`, `StatusModal`, `EditModal`)
- [ ] Define unified modal chrome (title, border, footer with action buttons)
- [ ] Standardize dismiss patterns (Esc, Enter, Ctrl+S — currently inconsistent)
- [ ] Consider: do all modals need the same width? Consistent focus/blur behavior?



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

see lenses...

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
