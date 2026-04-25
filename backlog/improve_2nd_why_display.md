# Improve secondary-parent display

## Problem

When a node has multiple parents, the current tree view only shows one — the one
that placed it in the spanning tree. The other parents are invisible unless the user
navigates to the node directly. This hides meaningful structure (shared concepts,
cross-cutting concerns) and makes the graph feel like a tree when it isn't.

## Strategies


### Other parent → inline text

- dimmed text, in the description cell, with other parent's name
- Use comma separator to join multiple parents
- limit parent description to 10char (append ".")

```
     ├──○ Find a language partner <-- Have fun      every 2w   ⚠ overdue 
```
- no additional line
- no complex render
- Option: only if parents are not visible in the current view 

### `⑂` icon only

When the tree is too dense or the parent is far away, just show a `⑂` icon on the
node row. The detail is visible on selection anyway.

- as a fallback for to long tree: TBD

### Other parent already visible → left-side connector

Same case as strategy 1, but the connector column is inserted to the left of the
tree, keeping the status/state columns uncluttered on the right.

The leftmost columns are: `[secondary link] [tree + description] [next update] [state]`

```
# Home view example
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


## In-tree solo up-link 
```

   @ Have fun                                           ◉ active
     ╰─  Electronics                                    ⚠ slowing
         ├──○ Build the vintage radio        due: june  ? "What's missing?"
         |    ╭--@ Learn soldering
         ╰──○ Fix the oscilloscope                      ⊘ discarded
```

- Only when there is a single additional parent to a node
- Cost one more line
- render complexity and interaction mess: an extra line disrupts row-to-node-id alignment, which is how DataTable key-based navigation works



## Relation to existing work

inline "also_labels" where implemented, and later partialy removed, to free column space

See `done/ui_graph_display.md` — the `←` inline annotation was an earlier approach
to the same problem. The right-side connector is a complementary idea for the case
where both parents are visible simultaneously.

also_labels already exists — view.py:149 already computes also_labels (other parent descriptions), and render.py documents it but doesn't use it. Strategy 1 ("inline text") is essentially already half-implemented.