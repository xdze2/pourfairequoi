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



## Example from project_vault


Nice — the project is eating its own dog food, which is exactly right.

A few observations:

Graph health

XSDBJZ_screenshots is linked from two places: 0HPOJY_clean_docs_and_meta and BR2NC6_version_1 and GTC913_clean_code — that's exactly the multi-parent case your ← annotation would expose
0NOK59_home_page_clean_roots_view and TB5TUH_re_order_child_node appear as children of both BR2NC6_version_1 and EK62P2_minimal_and_usable_set_of_features — diamond pattern, transitive link
75MI79_add_node (done) and U3XDUD_delete_node (done) are done but still linked — normal, just historical
Content gaps

02MNF2_add_parent_node is todo but the feature was just implemented (z key) — could be marked done
4YOI71_delete_link_vs_delete_node has no status — the design decision was made this session (u for unlink), worth noting
Several nodes have no type or status at all — they're raw captures, which is fine for a brain dump
Structure

ASEMU4_test_parent looks like a test node left over from experimentation — probably deletable
MOANE9_past_v1 with SX51IR and 1TXEQZ under it feels like a backlog/parking lot — clear intent


It's a healthy graph for a young project. The multi-parent diamonds are real and meaningful (shared tasks across goals), not accidents.