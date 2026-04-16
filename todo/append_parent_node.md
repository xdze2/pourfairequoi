# Append parent node — problem & options

## Current state

`a` creates a child of the selected node (or a root if on home view).
It is intentionally a no-op on parent rows, because creating a parent is
structurally different from creating a child:

- Creating a child: write a new file + insert a `how` link in the current node. Simple.
- Creating a parent: write a new file + insert the current node as a `how` child of the new node.
  But then who is the parent of the new parent? It becomes a root unless we also re-link.

## The real difficulty

Adding a parent node to an existing node can silently restructure the graph:
- If the current node is a root, the new parent becomes a root and the current node
  loses its root status — fine.
- If the current node already has parents, the new node needs to be inserted *between*
  them and the current node, which means modifying multiple existing nodes' `how` lists.
  That is closer to "move / re-link" than "append".

## Options considered

### A. Separate key (e.g. `A` / shift-a) — "add parent"
- Creates a new node and adds current node to its `how` list.
- The new parent becomes a root (no grandparent assigned).
- Simple to implement, but leaves the user to manually re-link if needed.

### B. Navigate first, then `a`
- The user navigates to the intended future parent, presses `a`, and types the
  description. The new node becomes a child of *that* parent.
- Then the user links the original node under the new one manually (once link-editing exists).
- No new key needed, but the workflow is indirect.

### C. Dedicated "reparent" flow (later, with link editing)
- Wait until "modify links / move node" is implemented.
- At that point, creating a parent and re-linking become the same operation.
- Cleanest long-term solution.

## Recommendation

Short term: implement option A (`A` key = add parent, becomes a root).
Long term: supersede with option C once link editing exists.
