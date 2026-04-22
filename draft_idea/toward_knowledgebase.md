# Toward a knowledge base — experiment notes

## What we tried

We built a vault (`internet_research_vault`) from the market analysis corpus — `user_needs.md`, `technical_choices.md`, and `key_concepts.md` — by decomposing everything into atomic claims and connecting them with pfq's parent/child links.

82 nodes, 119 links, 2 root nodes, 27 multi-parent nodes.

The graph was designed around one principle: **the link direction encodes abstraction level**. Moving up always answers "what is the generalisation of this?"; moving down always answers "what is a more specific instance or consequence?". This is the same why/how direction pfq uses for tasks, applied to ideas.

---

## What worked

**The DAG structure exposed something a tree hides.** A claim like *"GTD treats all next actions as equally valid"* ended up with 4 parents: the motivation need, GTD as a method, goal decomposition, and the abstraction ladder. In a tree you would have to duplicate it or pick one home arbitrarily. In the DAG it just lives where it genuinely belongs. That felt right.

**The abstraction-as-navigation idea is sound.** Unlike a wiki, where links are associative and directionless (you never know if you're going broader or narrower), the forced up/down direction gives the reader a spatial sense of position. Zooming out always leads to more general claims; zooming in always leads to more specific ones. It behaves like a map with zoom levels, not a web of undirected associations.

**Multi-parent nodes are meaningful, not accidental.** Every node with multiple parents is a concept that genuinely sits at an intersection — it's evidence that the DAG is capturing real structure, not just taxonomy.

---

## What didn't work

**Titles are both the label and the content.** Because pfq nodes have no body field, the claim had to live in the title. That forced titles to be long ("GTD treats all next actions as equally valid once captured — it has no model of why"), which makes the navigation view unreadable. A navigable knowledge base needs two separate things:

- a **short label** (3–5 words) for navigation — "GTD misses why"
- a **body** for the actual claim, evidence, and tensions

Without this separation, you have to choose between navigability and content. Right now the vault has content but is hard to navigate.

**The extraction phase is the hard part, and it isn't automated.** Building the vault required:
1. Deciding what counts as an atomic claim
2. Deciding the abstraction level of each claim
3. Deciding which parent each claim zooms out to
4. Deciding when a claim has multiple parents vs. when it should be split

None of this can be done mechanically. It requires genuine judgement about what is a generalisation of what. The result is only as good as the decomposition decisions made during that phase.

---

## Thoughts on the data extraction and decomposition phase

This is the intellectually interesting part — and the part that most knowledge tools ignore entirely.

Most tools treat capture and organisation as the hard problem. But the real bottleneck is **atomisation with abstraction awareness**: taking a source (a HN thread, an essay, a conversation) and deciding not just "what are the ideas here" but "at what level of abstraction does each idea live, and what does it generalise to?"

A few observations from doing this manually:

**Claims at the wrong abstraction level are useless.** Too specific and the node is a fact with no connection to anything broader; it floats. Too broad and it's a platitude that nothing specific hangs off of. The sweet spot is a claim that has both — something above it that it instantiates, and something below it that demonstrates it.

**The decomposition reveals gaps.** When you try to place a claim in the DAG and can't find a parent, it usually means either (a) you're missing an intermediate abstraction level, or (b) the claim is actually two claims that need separating. Both are useful discoveries. The structure of the graph acts as a consistency check on the ideas themselves.

**Multi-parent nodes are a quality signal.** If a claim has many parents, it's central. If it has none, it's either a root (a first principle you're not questioning) or an orphan (a claim that doesn't connect to anything, which is suspicious). Orphans usually mean the decomposition work isn't finished.

**The extraction phase is lossy by design.** A 40,000-token HN thread gets compressed into 3–4 nodes. That compression is intentional — the goal is to extract the claim that survives outside of its source context, not to summarise the thread. The test for a good atomic claim: can you read it without knowing what source it came from and still understand what it asserts?

**The goal is not to automate the thinking — it is to remove the tedious part so the thinking actually happens.** The friction in building a knowledge graph is not the intellectual work; it is the bookkeeping: generating IDs, writing valid YAML, keeping links consistent, not losing a half-formed idea before it is placed. If a tool handles that, the person is freed to focus on the only part that matters: deciding whether this claim is really a generalisation of that one, or just a neighbour. The tool encourages thinking by getting out of its way.

---

## The structural gap this exposes in pfq

pfq as a task manager is already well-suited to this use case structurally — the DAG with directional semantics is exactly the right model. What's missing is:

1. **A `notes` field** — freeform text attached to a node, not displayed in the TUI navigation but stored in the YAML file. This decouples the navigable label from the actual content.

2. **Short titles as first-class design** — if nodes are to function as knowledge-base entries, the title should be a concept name (3–5 words), not a sentence. The claim goes in the notes.

These two changes would make the same vault structure usable for both task management (title = action, notes = context) and knowledge organisation (title = concept name, notes = claim + evidence).

---

## The broader idea

pfq is currently shaped as a task manager that happens to use a DAG. The experiment suggests it could equally be a **wiki with forced abstraction structure** — where every link is either a zoom-in or a zoom-out, and navigation is always spatially coherent.

The difference from a conventional wiki: Wikipedia links are associative and flat. You can follow a link and end up somewhere broader, narrower, or just adjacent, with no indication of which. In a DAG knowledge base with directional semantics, every navigation step has a known direction — you always know whether you just went up toward first principles or down toward concrete instances.

This is a different value proposition than any existing tool in the market analysis:
- Not a Zettelkasten (those are flat graphs, no abstraction direction)
- Not an outliner (those are trees, no multi-parent)
- Not a mind map (those are radial, session-based)
- Not GTD (no connection to meaning/why)

The closest analogue is Arcadia's four-layer model — but that's an engineering methodology, not a personal knowledge tool, and it has a fixed number of abstraction layers rather than an open-ended DAG.
