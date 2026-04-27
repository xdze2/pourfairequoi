# Lenses — Generalized Home View

Date: 2026-04-27

## Idea

The current home view hardcodes one perspective: roots ordered by subtree size.
Generalize it: a **lens** is a named point-of-view that selects a set of focal nodes
and displays each with depth 1 (node + immediate children). No row filtering —
the local tree structure is preserved for each focal node.

Navigation stays the same: selecting a node enters its full local view.
The lens is a *launcher*, not a mode — a curated entry point into the graph.

Two zoom levels:
- **Local view** (current) — one node selected, full depth, short focus
- **Lens view** (new) — a broad perspective, multiple focal nodes at depth 1

## Predefined lenses

| Key | Name | Focal nodes | Signal |
|---|---|---|---|
| `g` | Goals | roots | subtree size (current home view) |
| `n` | Next actions | `-->` nodes + active leaves | pulse (recent activity) |
| `s` | Stuck | `!!` nodes + status=stuck + stale activity | age of last edit |
| `f` | Focus | `*` nodes | explicit user choice |
| `w` | Waiting | `<--` nodes | age since marked waiting |

Lenses map naturally onto the node type vocabulary from `node_type_inference.md`.
The inner voice could also use the active lens as context ("user is in stuck review mode").

## Hard parts

### 1. Scoring formula

Ranking focal nodes within a lens requires mixing heterogeneous signals:
- **Type signal** — explicit marker (`!!` > `*` > `-->` > `<--`)
- **Pulse** — recency of last edit on the node itself
- **Subtree pulse** — recency propagated upward from children (a parent with a recently
  edited child is not stale, even if the parent itself wasn't touched)
- **Depth** — a stuck leaf close to a root is more urgent than a stuck leaf in a deep subtree

A weighted formula is fragile and hard to tune. A simpler approach: sort by a single
dominant signal per lens (age for `stuck`, recency for `next actions`, explicit for `focus`),
and only introduce mixing if the single signal proves insufficient in practice.

### 2. Grouping sibling nodes

Two sibling nodes could both rank high in the same lens (e.g. two stuck leaves under the
same parent). Displaying them as separate stacked groups is redundant and noisy — their
shared parent tells the real story.

Options:
- **Collapse siblings**: if 2+ focal nodes share a parent, show the parent once at depth 2
  instead of each child at depth 1
- **Deduplicate by ancestor**: walk up from each focal node, find the highest ancestor that
  covers all of them, use that as the focal node
- **Show focal node + badge**: show the parent at depth 1, but mark which children triggered
  the lens (small indicator on the child row)

The third option is probably the most informative — you see the context (parent) and the
signal (which children are stuck/active) in one glance.

### 3. Lens vs. current view state

The app currently has one view state: a selected node + its local tree.
Lenses need a second state: no selected node, lens active.
Switching between lenses should be instant (single keypress).
Entering a local view from a lens should preserve the lens so `Esc` returns to it.

## Relationship to other backlog items

- **node_type_inference.md** — lens focal node selection relies on inferred types
  (`-->`, `*`, `<--`, `!!`). The two features are complementary: types make lenses precise.
- **inner_voice_local.md** — the active lens gives the inner voice session context.
  "User is reviewing stuck nodes" changes which questions are appropriate.
- **ideas.md (prioritization / opportunity cost)** — the `next actions` and `stuck` lenses
  are a lightweight answer to "what should I work on now?" without a scoring system.

## Open questions

- Should lenses be user-definable (custom focal set + depth), or just the 5 predefined ones?
- How to handle a lens with zero focal nodes? ("Nothing stuck" is good news — show it explicitly.)
- Should the lens name be visible in the UI header, so the user always knows which
  point-of-view they're in?
- Depth 1 per focal node — or let the user toggle depth 1/2 within a lens?
