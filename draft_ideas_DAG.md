# Core model

## What a node encodes

A node is a single unit of thought. It can represent any of:
- a **goal** — long-horizon aspiration, no clear end condition
- a **project** — bounded effort with a deliverable
- a **task** — concrete, completable action
- an **event** — something that happened (past-dated node, status done)
- a **question / decision** — a node whose output is a conclusion, not an artifact
- a **milestone** — a marker in time, signals progress
- a **specification or constraint** — a fact that shapes decisions, not something you do

All are the same data structure. The difference is semantic, carried by `type` and context.

### Time

A node can carry:
- a **time scope** — broad horizon: `day | week | month | year | vision`
- an **actual date or range** — `start_date`, `due_date`
- a **history** — append-only `events` list with valid time (user-declared date, not save date)

Time scope correlates naturally with DAG depth: roots tend toward long horizons, leaves toward short ones. Default = derived from structure, override with explicit field.

### Status and history

- `status` — current state: `todo | active | stuck | done | discarded`
- `events` — append-only log of status changes and notes, each with a user-declared date
- `conclusion` — final word on a decision node: what was decided and why (written once, after the fact)

`notes` = working space during. `conclusion` = the "therefore", readable six months later.

---

## How nodes are linked

### Vertical (hierarchy)
- `why` → parent motivation / goal (declared by the child)
- `how` → sub-task / implementation step (derived by reversing `why` in the store — no backlink stored)

### Lateral
- `but` / constraint — a blocker or precondition that must be resolved
- `or` / `alternative_to` — an alternative route or option
- `need` / `required_by` — strict ordering dependency (do this first)

### How links encode different subpart types

The `how` relationship covers three structurally different situations:
- **Parts** — parallel, independent sub-components (A and B and C)
- **Steps** — sequential, ordered sub-actions (1 then 2 then 3)
- **Reflection / alternatives** — thinking nodes (should we do A or B? but C is a risk)

Currently all encoded as `how`. Could eventually be distinguished by a sub-type or ordering field — but not yet needed.

---

# DAG — mathematical properties & methods

## Properties you can compute

**Topological sort** — already done (your `sort_globally`). The canonical DAG operation: linear order consistent with the hierarchy.

**Longest path from a node** — the "depth" of a subgraph. Tells you how complex a goal is. A goal with longest path = 5 has a deeply nested plan.

**Reachability** — can A reach B? Useful for: detecting if a cycle would be introduced before allowing a link, or finding "what does this node ultimately serve?"

**Transitive closure** — for every node, the full set of ancestors (all whys, recursively) and descendants (all hows). Useful for: showing the complete motivation chain, or finding everything blocked by a stuck node.

---

## Metrics per node

**In-degree** (how many nodes point to this as a `how`) = **how shared is this sub-task?** A node with in-degree 3 is a leverage point — completing it unblocks many things.

**Out-degree** (how many `how` children) = **complexity**. High out-degree = needs decomposition.

**Betweenness centrality** — how often does a node lie on shortest paths between others? High betweenness = structural bottleneck. In your graph, `Something to show` and `Meet more people` would score very high — removing them disconnects the graph.

**PageRank / authority score** — nodes referenced by many important nodes score higher. This would surface your *real* priorities, regardless of how you labeled them.

---

## Useful derived views

**Critical path** — longest chain from a root to a leaf. Tells you the minimum sequence of steps to reach a goal, assuming no parallelism. Directly maps to "what do I do first?"

**Connected components** — which goals are completely isolated from each other? Useful to spot orphans (like `a new app4`) or detect when the graph is fragmenting.

**Dominator tree** — node A *dominates* node B if every path from roots to B passes through A. In your graph: if `Something to show` dominates `PourFaireQuoi`, then PourFaireQuoi is only meaningful *through* Something to show. Dominators are your single points of failure.

**Minimum spanning DAG** — remove redundant edges that are already implied by transitivity. If A→B→C and also A→C directly, the A→C link is redundant. Could help clean up the graph.

---

## Status propagation

This is probably the most immediately useful:

- **Blocked propagation**: if a node has any `but` without a resolved `how`, it's stuck. If a parent's child is stuck, the parent is implicitly stuck. You could surface this automatically.
- **Done propagation**: a node is *candidate for done* when all its `how` children are done and all its `but` nodes are resolved.
- **Progress score**: `done_children / total_children` gives a completion percentage per node, aggregatable upward.

---

## What's unique to your model vs a generic DAG

The `but` nodes are interesting — they're not part of the standard DAG structure. A `but` is more like a **precondition that must be falsified** rather than a sub-task to complete. Mathematically, it's a blocking edge with inverted semantics. This maps to **AND/OR graphs**: a node is achievable when all `how` children are achievable AND all `but` blockers are resolved.

The `or` link type makes this explicit: it's an OR-branch in the plan. This is closer to **AND-OR trees** (used in AI planning) than a plain DAG.

---

## Most actionable for the app

In priority order:
1. **Stuck propagation** — automatically flag a node if any descendant is stuck with no resolution
2. **Critical path** — highlight the one sequence of actions that gets you to a goal fastest
3. **Completion score** — `%done` per node, rolled up the tree
4. **Betweenness / leverage score** — surface the few nodes where effort has the highest payoff
