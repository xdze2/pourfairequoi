# Improve secondary-parent display

## Problem

When a node has multiple parents, the current tree view only shows one — the one
that placed it in the spanning tree. The other parents are invisible unless the user
navigates to the node directly. This hides meaningful structure (shared concepts,
cross-cutting concerns) and makes the graph feel like a tree when it isn't.

## Three strategies, by case

### 1. Other parent already visible in the current view → right-side connector

Draw a vertical line on the right margin connecting the two parent rows to the
shared child. No extra lines in the tree, just a visual bridge.

```
  @  Learn Portuguese                        every 3w   ◉ active
     ├─  Oral practice                                  ○ active    │
     │   ├──○ Find a language partner        every 2w   ⚠ overdue   │
     │   ╰──○ Do 10 Pimsleur sessions        every 2w   ○ todo      │
     ╰─  Reading                                        ○ active    │
         ╰──○ Buy a Portuguese novel         someday    ✓ done      │

  @  Have fun                                           ◉ active
     ╰─  Electronics                                    ⚠ slowing   │
         ├──○ Build the vintage radio        due: june  ? "..."     ╯
         ╰──○ Fix the oscilloscope                      ⊘ discarded
```

"Build the vintage radio" is a child of both "Electronics" and "Learn Portuguese" —
the `│ ... ╯` connector on the right links them without touching the tree structure.

**Implementation note:** requires a second rendering pass — row positions of both
parents must be known before the connector can be drawn.

### 2. Other parent not visible in the current view → inline `╎ also:` line

Draw a dimmed line below the node with the other parent's name. Costs one extra row,
only shown when relevant.

```
     ├──○ Find a language partner        every 2w   ⚠ overdue
     │    ╎ also: Have fun
```

The `╎` (dashed vertical) signals a secondary link, not a tree edge.

### 3. Fallback → `⑂` icon only

When the tree is too dense or the parent is far away, just show a `⑂` icon on the
node row. The detail is visible on selection anyway.

### 4. Other parent already visible → left-side connector

Same case as strategy 1, but the connector column is inserted to the left of the
tree, keeping the status/state columns uncluttered on the right.

The leftmost columns are: `[secondary link] [tree + description] [next update] [state]`

```
╭-  @ Learn Portuguese                        every 3w   ◉ active
│     ├─  Oral practice                                  ○ active
│     │   ├──○ Find a language partner        every 2w   ⚠ overdue
│     │   ╰──○ Do 10 Pimsleur sessions        every 2w   ○ todo
│     ╰─  Reading                                        ○ active
│         ╰──○ Buy a Portuguese novel         someday    ✓ done
│
│   @ Have fun                                           ◉ active
│     ╰─  Electronics                                    ⚠ slowing
╰->       ├──○ Build the vintage radio        due: june  ? "What's missing?"
          |    ╭--@ Learn soldering
          ╰──○ Fix the oscilloscope                      ⊘ discarded
```

"Build the vintage radio" is a child of both "Electronics" (current tree parent) and
"Learn Portuguese" — the `│ ... ╰──@` connector on the left links the two roots,
reading top-to-bottom as "this branch also connects down to here".

The `╰──@` terminal on the second root signals the entry point of the secondary link.

**Advantages over right-side:**
- connector stays spatially close to the tree structure it describes
- status/state/question column is never interrupted
- multiple secondary links stack naturally as additional left columns

**Disadvantage:** eats into the left margin — deep trees may run out of space.

## Decision logic

| Condition | Strategy |
|-----------|----------|
| Other parent is visible in current view | Right-side connector |
| Other parent is not visible | `╎ also:` line below |
| Tree is too dense / many parents | `⑂` icon only |

## Relation to existing work

See `done/ui_graph_display.md` — the `←` inline annotation was an earlier approach
to the same problem. The right-side connector is a complementary idea for the case
where both parents are visible simultaneously.

## Open questions

- How to handle 3+ parents? Stack multiple `╎ also:` lines, or cap at one + `⑂`?
- Right-side connectors with multiple shared children in the same view — lines will
  cross. Need a column-assignment strategy.
- Should the `╎ also:` line be shown by default or toggled with a keypress?
- Depth limit: only show secondary-parent info for depth-1 nodes, or grandchildren too?
