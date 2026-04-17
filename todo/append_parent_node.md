# Append parent node — problem & options

## Status: implemented (`z` key)

`z` on any node row opens `LinkModal` — fuzzy search existing nodes or create a new one,
then links it as a parent of the focused node.

## What was implemented

- `z` → `LinkModal(focused_node_id, graph)`
- Fuzzy subsequence search via `NodeGraph.search_nodes(query)` (in `model.py`, no external deps)
- Results update live as you type; ↑↓ to navigate
- Last row always offers `+ Create new: "…"` when query is non-empty
- Enter confirms, Esc cancels
- On confirm: `graph.link_child(parent_id, child_id, ...)` + `save_vault(graph)`

## What was decided

- Multi-parent is allowed (DAG); no cycle detection needed (DFS has a visited set)
- New parent created via the modal becomes a root unless it already exists in the graph
- "Insert between existing parents" (option C from original doc) deferred to a future
  "move / re-link" feature

## Next step

Full link editing (remove links, move nodes) — will supersede the manual workaround
of creating a parent then re-linking.
