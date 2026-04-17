# UI — Graph display redesign

## Problem

The current view is a spanning tree (DFS, max_depth=2) rooted at the selected node.
This is lossy: shared nodes appear only once (visited set), multi-parent relationships
are hidden, and redundant/transitive links are invisible. As the graph grows the user
cannot make sense of the structure or clean it up.

## Direction

Keep the spanning tree as the backbone (it is the right structure for navigation),
but enrich each row with inline connectivity information so the user gets graph
awareness without leaving the current view.

## Designed display

```
         ┌─ Grandparent
      ┌─ Parent
▶  Current
      └─ Child A1
      └─ Child A2
      └─ Child A3   ← (^) Other context          type    status
             └─ Grandchild
```

### Inline `←` annotation (other parents of a node)

Every node row may show a `←` suffix listing its parents **other than the one
that placed it in the current tree**:

- `← (^) Name` — parent already visible in the current tree (shown above)
- `← Name` — parent outside the current view (hidden context)
- `← (^)` — shorthand when the above-parent has no useful label, or to save space
- No `←` — node has only one parent (the one that placed it here), no hidden context

Multiple other-parents: `← (^) Context A, Context B`

### Reading the annotation

| Annotation | Meaning |
|---|---|
| *(none)* | Clean: single-parent or fully explained by current tree |
| `← (^)` | Shared within this tree (diamond / transitive link visible here) |
| `← Other context` | Node lives elsewhere too — current view is partial |
| `← (^) Other context` | Both: shared inside and outside |

### Transitivity / diamond detection

From node A, with links A→B, B→C, A→C:
- B appears as a child of A (depth 1)
- C appears as a child of B (depth 2, placed via B)
- C's row shows `← (^)` because A is also a parent and A is visible (it's the current node)

The user sees the redundant A→C link without navigating anywhere.

### `←` is read-only

The annotation is a status indicator, not an interactive handle.
To act on the connections, the user selects the node and uses `z` (link) or `u` (unlink).

## Also discussed: `a` key scope

`a` currently only works on the selected node row. Should work on any visible row
(parent or child) — the "new line" mental model from text editors is strong and
working/seeing up to two tree levels makes this natural.

## Also discussed: `u` for unlink

`d` = delete node file (destructive).
`u` = unlink (remove the `how` edge between parent and child, node survives).
Unlink modal should clarify which parent to unlink from if the node has multiple.

## Also discussed: LinkModal UX

Show all nodes (or top N) on open, before any query is typed.
Search is a filter helper, not the primary interaction — the list should be visible
immediately so the intent ("pick from a list") is clear.

## Not yet decided

- Truncation strategy when many other-parents: cap at N names + "…+k"?
- Whether `(^)` should show the parent's description or just the sigil
- Depth of grandchild parent annotation (probably only depth-1 children get it, grandchildren too noisy)
- Nested tree rows for other-parents (rejected in favour of inline annotation — keeps tree clean)

## Next steps (suggested order)

1. `a` on any row (quick fix)
2. LinkModal shows candidates on open (quick fix)
3. `u` unlink action + modal
4. Inline `←` annotation on child rows
