# Delete UX redesign

## Status: implemented ✓

## Mental model: "what becomes unanchored?"

Rather than "subtree soft/hard", the guiding question is:
**if this node/link is removed, what loses all paths to a root?**

Like pruning a real tree — a branch either falls to the floor (unanchored) or stays
attached somewhere else. Roots are the perspective anchors; a node that can no longer
reach any root has lost its meaning.

## Four operations, by order of impact

| Action | What is removed |
|---|---|
| **Unlink** | The visible link only. Node stays, may still be anchored elsewhere. |
| **Delete node** | The node and all its links. Children that had no other parent become floating roots. |
| **Delete + unanchored** | The node, plus every node that becomes unreachable from any root after removal. |
| **Delete subtree (hard)** | The node and all descendants, regardless of other parents. |

## Key cases

**Case 1 — leaf, nothing unanchored**
```
@ Goal
  └── Project
        ├── Task A   ← delete
        └── Task B
```
Only Task A removed. Task B stays.

**Case 2 — middle node, children unanchored**
```
@ Goal
  └── Project   ← delete
        ├── Task A
        └── Task B
```
Task A and Task B have no other parents → unanchored → "delete + unanchored" removes all three.

**Case 3 — shared node, soft delete stops at junction**
```
@ Goal A        @ Goal B
  └── Project ──┘          ← delete (from Goal A's view)
        └── Task
```
Unlink Project from Goal A → Project still anchored via Goal B → nothing unanchored.

**Case 4 — partial unanchoring at mid-subtree junction**
```
@ Goal A        @ Goal B
  └── Project          └── Shared Task
        ├── Task A               ↑
        └── Shared Task ─────────┘
```
Delete Project:
- Task A → only parent was Project → **unanchored → removed**
- Shared Task → still has Goal B as ancestor → **stays**

**Case 5 — unlink from a parent row**
```
@ Goal A    @ Goal B
  └── X ────────┘       ← cursor on "Goal A", selected is X
```
Unlink: removes Goal A → X link. X stays anchored via Goal B.

## UI design

Single `d` key, one modal, options shown with consequences.
Options are hidden (not greyed) when not applicable:
- *Unlink* — only when cursor has a visible parent (child row) or is on a parent row
- *Subtree* options — only when node has children

↑↓ navigation + Enter to confirm, consistent with LinkModal.
Second confirmation screen for `soft` and `hard` only (multi-node destructive).

## Applies to

- **child rows**: unlink from visible parent, or delete the child node
- **selected row**: delete only (no unlink — no visible parent in context)
- **parent rows**: unlink the parent from the selected node, or delete the parent node

## Implementation

### `model.py`

- `nodes_unanchored_after_removal(node_ids)` — BFS from remaining roots, returns nodes not reachable
- `deletion_set(node_id, mode)` — returns set of node_ids to delete for "node" / "soft" / "hard"

### `modals.py`

`DeleteModal` — multi-choice, ↑↓/Enter nav, bordered options, selected option highlighted.
Receives precomputed option dicts (no graph logic inside modal).
Returns action key or None on cancel.

### `app.py`

- Single `action_delete` bound to `d` (replaces `action_delete_link` + `action_delete_node`)
- `_build_delete_options(node_id, unlink_pair)` — computes option list
- `_on_delete_done(result, node_id, unlink_pair, cursor_row)` — dispatches result
- `_delete_nodes(node_ids, cursor_row)` — bulk removal + navigation
- `_show_home` and `_show_node` both accept `cursor_row` to restore position after refresh
