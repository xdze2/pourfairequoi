# Refactor internal data structure

## Motivation

The current `NodeGraph` has two sources of truth: YAML files on disk and the
in-memory dicts. Every mutation requires a double-write (in-memory + disk), which
is fragile and has already caused bugs (e.g. `add_child_link` / `graph.link_child`
duplication).

## Proposed architecture

```
NodeGraph (in-memory, single source of truth during a session)
├── nodes: dict[id, Node]         # Node no longer has a `how` field
└── links: set[tuple[src_id, tgt_id]]  # replaces _parents + node.how

load_vault(vault_path) -> NodeGraph   # initial load, reads all YAML files
save_vault(graph, vault_path)         # full sync, rewrites only changed files
```

`node.how` is removed from the `Node` dataclass. All topology lives in `links`.
Disk files are only touched by `load_vault` / `save_vault`, never mid-session.

## What it solves

- Single source of truth: no more double-write pattern
- Link operations are trivial: `graph.links.add((src, tgt))` / `.discard((src, tgt))`
- Queries (`get_parents`, `get_children`, `get_roots`) become simple set lookups
- Foundation for link editing and reparenting features

## What it doesn't solve

- The create-parent UX problem (see `append_parent_node.md`) — that's a graph
  design question independent of storage

## Trade-offs

- It's a refactor: `model.py`, `disk_io.py`, and all call sites in `app.py` need updating
- File format on disk stays the same (YAML with `how` list), so hand-editing still works
- `save_vault` needs a dirty-tracking mechanism or just rewrites all files (acceptable for a small vault)

## Recommendation

Do this before adding more features (link editing, reparenting, filters).
The codebase is small enough that the refactor is cheap now, and expensive later.
