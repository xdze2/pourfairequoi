- Use full filename in target linking (instead of just ID): human readable
- Fix bugs UI/UX (it is not usable now)
- Refactor code
  - Defined model API (data - model - UI)
- add tests
- improve Claude workflow
- Improve UI, polish, should be easy as textfile editing
- Constrain is a "negative" task
- add before/after link (next app project after v1)
- git sync for the vault, to work on multi-computer
- manage task order
- better filter search
- spec node: analyse fonctionnel, constraint solver
- budget node: time, money, .... Sum over hows.
- Show alternative link in Graphs (I shape ?)

### Effort & budget tracking
- Append-only effort log on nodes: `date`, `time`, `cost`, `note`
- Budgetizable quantities: `time_spent`, `time_est` (remaining), `cost`, `budget` (cap)
- Scalars aggregate up the graph (Σ children) — branch nodes can override with explicit value
- Key insight: total investment + remaining estimate at goal level = planning superpower
- Architecture: arbitrary quantities, not hardcoded — user defines what to track

### Next actions & insight engine
- **Next actions view** — leaf nodes that are `todo`/`doable`, with at least one `active` ancestor
- **Stuck propagation** — node implicitly stuck if all active children are stuck; surface visually
- **Staleness signal** — `active` node older than its `horizon`; nudge to reassess
- **Orphan detection** — nodes with no parents and no children; prompt to link or discard
- **Blocking path** — trace from a root goal to the first `stuck` leaf; show the path
- **Missing fields highlight** — nodes without `status`, `type`, or `how` children marked incomplete

### Futur
- Easter-eggs, ascii art
- Node insight: stats, LLM
- LLM interfaces
- Online version (web+api)
- wayback machine (also hide old nodes)

### UI friction
- graph view, can't go back/up
  - add root top line
  - "esc" keybinding ?
  - show/manage history navigation (breadcrump...)
- edit in graph view: no, if editing in node view is easy
- grah is not updated on node edit (not refresh)
- search in home page
- Loose date inputs (and horiton): "1m", "5d"...
- limit graph view to 3-4 levels, show crops (...)
