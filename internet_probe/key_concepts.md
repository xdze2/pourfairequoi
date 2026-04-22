# Key Concepts — Thinking Methods

This file catalogues the foundational thinking methods that underlie the tools in this space. The focus is on the *method* — the mental model or organisational practice — independently of any software that implements it.

---

## 1. Getting Things Done (GTD)

**Origin:** David Allen, *Getting Things Done* (2001).

**Core idea:** Offload everything from your head into a trusted external system. The brain is unreliable at remembering; it is not "dumb" — it just doesn't handle open loops well. A fully externalised system gives you *mind like water*: calm, ready to respond to whatever is most important.

**Structure:**
- **Capture** — write everything down into an "In" inbox, immediately
- **Clarify** — is it actionable? If yes: what's the *next physical action*?
- **Organise** — put it in one of five lists:
  - *Next Actions* — specific physical steps, doable now
  - *Projects* — anything requiring 2+ actions
  - *Waiting For* — delegated or blocked items
  - *Someday/Maybe* — aspirations with no commitment
  - *Calendar* — time-specific or day-specific actions
- **Review** — weekly sweep to keep the system trusted
- **Engage** — choose what to do based on context, energy, time, priority

**Key practices:**
- 2-minute rule: if it takes under 2 minutes, do it now
- Contexts (@home, @phone, @computer) — filter by situation
- Weekly review — the practice that keeps the system alive
- Tickler file (43 folders) — physical reminder system

**What GTD does well:** Zero-friction capture, clarifying "what is the literal next step," and reducing anxiety by making all open loops explicit.

**What GTD does not address:** Why a project exists. GTD treats all projects as equally valid once captured. There is no model for connecting a next action to a long-term goal or value. Motivation is the user's problem.

**Seen in:** OmniFocus (the canonical GTD tool), Todoist, Things, Akiflow, Sunsama — all built around the GTD vocabulary.

---

## 2. Mind Mapping

**Origin:** Popularised by Tony Buzan (1974, *Use Your Head*), though radial diagrams trace to Porphyry's *Isagoge* (3rd century) and Ramon Llull's medieval concept maps.

**Core idea:** Externalise thought radially from a central concept. Unlike linear notes, a mind map mirrors how associative thinking actually works — not sequentially, but by branching and linking.

**Structure:**
- One central node (the topic)
- Branches radiate outward by association
- Each branch can itself branch further (tree structure)
- Visual encoding: colours, icons, spatial position carry meaning
- No inherent ordering within branches

**Variants:**
- **Concept map** (Novak, 1970s): like a mind map but edges are labelled ("causes", "is a", "requires") — directed, typed relationships. More rigorous, less free-form.
- **Argument map**: tracks reasoning and counter-reasoning (claim → reason → objection)
- **Spider diagram**: a simplified mind map with less structure
- **Hierarchical mind map (JumpRoot-style)**: removes the visual/spatial dimension, retains the tree; essentially an outliner with mind-map framing

**Effectiveness:** Research shows 10-15% improvement in learning over conventional note-taking. Effect is discipline-dependent (stronger for arts/design than CS students). Benefits larger for lower-ability learners.

**What mind mapping does well:** Brainstorming, initial decomposition, making associations visible, reducing the blank-page problem. Natural fit for early-stage exploration.

**What mind mapping does not address:** Task management, sequencing, priority, or time. Mind maps are snapshots of structure, not operational systems. They answer "what is related?" not "what should I do next?"

**Tension in the corpus:** "Hackers mind map" HN threads repeatedly debate whether a text-based hierarchical tool *is* a mind map — or just an outliner with a different name. The visual dimension (spatial layout, colour, icons) is what Buzan considered essential; the HN/developer community often wants the structure without the visuals.

**Software:** FreeMind, XMind, MindMeister, Freeplane, Coggle, iThoughts, OmniGraffle (concept maps). Most are radial-tree tools; few support multi-parent graphs.

---

## 3. Outliners

**Origin:** RAND Corporation's PROMIS (1960s), then NLS/Augment (Doug Engelbart, 1968), then ThinkTank/MORE for early Macs (1980s). Modernised by WorkFlowy (2010).

**Core idea:** All information is organised as a nested list of items. Every item can have children. Collapse and expand nodes to manage complexity. The viewport — what you see — is a zoom level, not a separate document.

**Structure:**
- Infinite nesting (items → children → grandchildren)
- Zoom into any node → it becomes the root of your current view
- Collapse subtrees to reduce cognitive load
- Linear within each level (ordered siblings)

**Key insight (WorkFlowy):** The "aha" moment that drove signups was realising that *the same list, expanded vs. collapsed, looks completely different*. Outliners don't just organise — they let you *choose how much reality to see at once*.

**Constraints:**
- Each node has exactly one parent (tree, not DAG)
- Sharing a task across two projects requires duplication or external references
- Order within siblings is manual

**Variants:**
- **Block-based outliners** (Roam, LogSeq, Notion): every paragraph/block has a unique ID and can be referenced/transclused elsewhere — adds graph properties to the outliner model
- **Power outliners** (Dynalist, OmniOutliner): tags, filters, cross-references while keeping the tree as primary structure
- **Smos**: YAML-native outliner with state history on each node ("forest of entries")

**What outliners do well:** Natural decomposition ("break big things into smaller things"), overview at adjustable granularity, fast keyboard-driven input.

**What outliners do not address:** Multi-parent relationships (a task that contributes to two goals), non-hierarchical connections.

---

## 4. Zettelkasten

**Origin:** Niklas Luhmann, sociologist (1950s–2000s). Physical card system of ~90,000 notes that supported decades of prolific academic output. Popularised to software communities in the 2010s.

**Core idea:** A collection of *atomic* notes (one idea per note), each with a unique identifier, connected by explicit links. The value is not in any individual note but in the emergent network of connections — ideas that would never meet in a linear document find each other through linking.

**Structure:**
- Each note: unique ID, atomic content (one concept), explicit links to other notes
- No fixed hierarchy (unlike outliners) — the graph is flat, structure emerges from links
- Notes often have a "parent" only as a starting point; over time they acquire connections in all directions

**Key distinction from mind maps:** Mind maps are tree-shaped, top-down, created in one session. Zettelkasten is a growing graph, bottom-up, accumulated over years. Mind maps externalise a current mental model; Zettelkasten *builds* a new one over time.

**Tension in the corpus:** "Zettelkasten is just a note-taking technique for one researcher, not a universal truth" (HN). The community debate is whether Zettelkasten is a system (portable to everyone) or a personal practice (worked for Luhmann because of how *he* worked). Also: almost all "Zettelkasten apps" (Obsidian, Roam, LogSeq) add hierarchy back in (folder-based vaults, namespaces, tags) because pure flat graphs become unnavigable at scale.

**What Zettelkasten does well:** Building a personal knowledge base over time, making unexpected connections, resisting premature categorisation.

**What Zettelkasten does not address:** Task management, prioritisation, time, or motivation. Zettelkasten is a *knowledge* method, not a *doing* method.

**Software:** Obsidian, Roam, LogSeq, Org-Roam, Zettlr, The Archive.

---

## 5. Kanban

**Origin:** Toyota Production System (Taiichi Ohno, 1950s). Software adaptation by David Anderson (2010). Personal Kanban by Jim Benson.

**Core idea:** Visualise work as cards moving through stages (columns). Limit work-in-progress (WIP) at each stage. The constraint creates flow: you can only pull new work when a downstream stage has capacity.

**Structure:**
- Columns represent stages (To Do → In Progress → Done, or more granular)
- Cards represent work items
- WIP limits: each column has a maximum — forces finishing over starting
- Pull system: work is pulled forward by demand, not pushed by scheduling

**Personal Kanban (simplified):**
- Three columns only: Backlog, Doing, Done
- Visualise everything in flight
- Limit "Doing" to 3-5 items
- No WIP limits are the most common reason personal Kanban fails

**What Kanban does well:** Making work-in-progress visible, exposing bottlenecks, preventing overcommitment, creating a satisfying "done" ritual.

**What Kanban does not address:** Why any of the work exists (no goal hierarchy), decomposition (a card is a card), prioritisation across columns (the backlog remains unsorted), or long-horizon planning.

**Software:** Trello (canonical), Linear (engineering-focused), Notion (embedded), Jira (enterprise). The Ink & Switch Trellis prototype was a local-first Kanban.

---

## 6. Work Breakdown Structure (WBS)

**Origin:** US Department of Defense / NASA (1960s). Formalised in project management standards (PMI, PMBoK).

**Core idea:** Decompose a project deliverable (the "what") into progressively smaller components until each piece is estimable, assignable, and verifiable. Every leaf node is a *work package* — a unit of work that can be scheduled, costed, and owned.

**Structure:**
- Tree (not DAG) — each work package has exactly one parent
- Top node = project deliverable
- Each decomposition level = a more granular "what"
- Leaf nodes = work packages (smallest unit)
- 100% rule: a WBS must cover 100% of the project scope — no overlap, no gap

**Key distinction from outliners:** A WBS is scope-driven ("what must be produced"), not action-driven ("what must be done"). A task list answers "what do I do?"; a WBS answers "what do I deliver?"

**What WBS does well:** Scope clarity, estimability, team assignment, completeness verification.

**What WBS does not address:** Sequencing (that's the network diagram / CPM), motivation (why the project exists — that's requirements), or the "how" at implementation level.

**Seen in:** Professional PM tools (MS Project, Aha!, Jira), and implicitly in how technical teams decompose epics → stories → tasks.

---

## 7. Hierarchical Goal Decomposition (why → how)

**Origin:** Various: management by objectives (Drucker, 1950s), IDEF0 functional decomposition (1970s USAF), Arcadia/Capella systems engineering method (2000s Thales/Airbus).

**Core idea:** Goals are arranged in a directed acyclic graph (or tree) where each node answers "why" by pointing to its parent and "how" by pointing to its children. The top of the structure is a value or purpose; the bottom is an action.

**Structure (Arcadia model — most formal version):**
1. **Operational Analysis** — why: stakeholder goals, context, motivations
2. **System Need Analysis** — what: system capabilities required to satisfy operational goals
3. **Logical Architecture** — how (conceptual): functions and their relationships
4. **Physical Architecture** — how (concrete): components and their allocation

**Simpler personal version:**
- Value → Goal → Sub-goal → Project → Task → Action
- Each level answers "how do I achieve the level above?"
- Traversing upward always gives the "why"

**Key property:** A task with no upward connection to a goal is orphaned — doing it is hard to justify. A goal with no downward connection to actions is inert — it will never be achieved. The structure enforces coherence between meaning and action.

**What this method does well:** Keeping motivation visible, supporting principled prioritisation ("which task contributes most to which goals?"), exposing orphaned tasks and empty goals.

**What it does not address:** Scheduling, time, recurrence. It is a *structure*, not a *process*.

**Seen in:** Arcadia/Capella (professional, rigorous), pfq (personal, lightweight), the "Maslow DAG" HN commenter, the Intention app (implicitly).

---

## 8. GTD vs. Goal Decomposition — the structural gap

These two methods are complementary but are almost never combined in a single tool.

| | GTD | Goal decomposition |
|---|---|---|
| Primary question | What is the next action? | Why am I doing this? |
| Structure | Flat lists by context/project | DAG by meaning |
| Time horizon | This week / today | Years / life |
| Captures | Actions + projects | Goals + values |
| Weakness | No "why" | No operational flow |

GTD practitioners regularly report that their system is efficient but feels empty — they know what to do but lose sight of why. Goal decomposition systems (OKRs, Arcadia, pfq) address this but often lack the operational granularity to manage day-to-day work. The gap between these two modes is where pfq lives.

---

## 9. Summary — method comparison

| Method | Primary organising unit | Topology | Time horizon | Best for |
|---|---|---|---|---|
| GTD | Next action / project | Flat lists | Days–weeks | Operational flow, reducing anxiety |
| Mind mapping | Concept / association | Radial tree | Session | Brainstorming, initial decomposition |
| Outliners | Item (any granularity) | Tree | Flexible | Hierarchical organisation, notes |
| Zettelkasten | Atomic note | Graph | Years | Knowledge accumulation |
| Kanban | Work item (card) | Stages (columns) | Days–weeks | Flow visualisation, WIP control |
| WBS | Deliverable / work package | Tree | Project duration | Scope definition, estimation |
| Goal decomposition | Goal / action | DAG | Years + days | Connecting meaning to action |
