# Raw Data Index

Sources collected in `raw_data_src/`. Quality and relevance assessed relative to pfq's market analysis goals (user needs, technical choices, positioning).

---

## Existing sources

### Direct competitors / DAG tools

| File | Source | Quality | Relevance |
|---|---|---|---|
| `Show HN Intention – DAG Todo App  Hacker News.md` | HN thread, 2020 | ★★★★★ | **Core source.** Real community feedback on the closest concept to pfq. Rich discussion on DAG vs tree, local-first, login friction, semantic gaps. |
| `Show HN we built a graph based task manager  Hacker News.md` | HN thread, 2022 | ★★★ | Useful for "graph as project manager" angle. Shallow thread — only the author's pitch captured, few comments. More team/collab focused, less personal. |

### Outliner ecosystem

| File | Source | Quality | Relevance |
|---|---|---|---|
| `WorkFlowy (YC S10) launches a better way to organize your brain  Hacker News.md` | HN thread, 2010 | ★★★★ | Excellent on user psychology: the "overview" need, capture friction, the value of zoom. Historic but the reactions are timeless. Large file (truncated in analysis). |
| `Features - Dynalist.md` | Dynalist marketing page | ★★ | Feature list only — no opinions, no tradeoffs. Useful as a checklist of "mainstream outliner features" but no depth. |
| `What are the web app for note taking based on the concept everything is a list - Google Gemini.md` | AI-generated overview | ★★★ | Good taxonomy of outliner types (pure / networked / power). Covers WorkFlowy, Dynalist, Roam, Logseq, Tana, Taskade, Checkvist. No primary opinions — AI summary. |

### Org-mode / plain-text ecosystem

| File | Source | Quality | Relevance |
|---|---|---|---|
| `Org Mode for Emacs – Your Life in Plain Text  Hacker News.md` | HN thread | ★★★★ | Very large file (40k tokens, had to grep). Likely rich on plain-text philosophy and data ownership. **Underexplored** — only partial analysis done. |
| `Life is 90_ of my use cases for org-mode  Hacker News.md` | HN thread | ★★★★ | Largest file (46k tokens). Likely covers the "minimal org-mode" angle — what people actually use vs. the full feature set. **Underexplored.** |
| `Smos A comprehensive self-management tool  rorgmode.md` | Reddit r/orgmode | ★★★★ | Good direct comparison: SMOS vs org-mode, YAML vs org format, local-first debate. Author responds. Covers tree-only limitation explicitly. |
| `Smos a replacement for emacs org mode  rorgmode.md` | Reddit r/orgmode | ★★★ | Shorter thread, mostly hostile reactions to the "replace org-mode" claim. Useful for community sentiment, less technical depth. |

### Mainstream task managers

| File | Source | Quality | Relevance |
|---|---|---|---|
| `8 Best To-Do List Apps (2026) Ranked & Reviewed  Efficient App.md` | Review site | ★★★ | Covers Superlist, Motion, Todoist, TickTick, Morgen, Akiflow, Sunsama, Linear. Good for user-need vocabulary (scheduling, daily planning, consolidation). Marketing framing — no critical depth. |
| `Todoist  Une to do list pour organiser vie et travail.md` | Todoist homepage (FR) | ★ | Marketing copy only. Single data point: Todoist's self-description ("clarity", "capture instantly"). No user opinions. |
| `Best All in One Todo List, Note taking, Calendar app that's simple to use  rproductivity.md` | Reddit r/productivity | ★★★ | Real user voices. Captures the "all-in-one" fatigue, Notion setup burden, pen & paper fallback. Confirms that no tool fits everyone. |

### Learning tools

| File | Source | Quality | Relevance |
|---|---|---|---|
| `Show HN A tool for your learning, like Anki and WorkFlowy in one  Hacker News.md` | HN thread, 2020 | ★★ | Adjacent space (learning, not task management). Interesting for tree-as-knowledge-structure angle. Low direct relevance to pfq unless you consider the knowledge graph angle. |

### Professional / systems engineering

| File | Source | Quality | Relevance |
|---|---|---|---|
| `app_analyse_fonc.md` | AI-generated overview | ★★ | Overview of tools for "Analyse Fonctionnelle" (Miro, Notion, Trello, Gleek). Broad and shallow. Confirms Notion's positioning as generic scoping tool. |
| `project_scoping_pro.md` | AI-generated overview | ★★★ | Covers professional ALM tools (Jama, DOORS, Aha!, Jira PD, Capella). Useful for the "traceability" need and professional DAG use. Shows the high end of the why/how market. |
| `arcadia.md` | AI-generated summary | ★★★ | Good explanation of Arcadia's 4-layer model (Operational=why, System=what, Logical=how-conceptual, Physical=how-real). Confirms pfq's why/how framing has deep engineering roots. |
| `Arcadia (engineering) - Wikipedia.md` | Wikipedia | ★★★ | More formal / complete than the AI summary. Confirms Arcadia/Capella is open-source and field-tested. Reinforces the intellectual legitimacy of the why/how decomposition approach. |

---

## New sources (added April 2026)

### Taskwarrior

| File | Source | Quality | Relevance |
|---|---|---|---|
| `Taskwarrior  Hacker News.md` | HN thread | ★★★★ | Rich community discussion. Core themes: urgency scoring, dependency tracking, broken recurrence system, sync pain (mutual TLS), mobile failure. Real frustrations from power users. |
| `Taskwarrior – CLI Task Management  Hacker News.md` | HN thread | ★★★★ | Second HN thread; overlapping themes but distinct comments. ADHD users praise auto-prioritization. TUI (taskwarrior-tui) discussed. Same mobile / sync weaknesses. |
| `Taskwarrior The Command-Line Task Manager for Power Users  by Jose Rodríguez  The Productivity Blog.md` | Blog/marketing | ★★ | Tutorial content, no tensions surfaced. Useful for feature vocabulary (urgency, contexts, named reports). |
| `Taskwarrior - Best Practices - Taskwarrior.md` | Official docs | ★★★ | Best practices around atomic tasks, metadata hygiene, regular review, urgency tuning. Explicit warning against "productivity theater." |

### Supertags / typed nodes

| File | Source | Quality | Relevance |
|---|---|---|---|
| `Supertags.md` | Tana marketing | ★★★ | Explains supertags as ontological types (not labels). Key idea: structured fields inherited by type, not added ad hoc. Flexible workflow restructuring without rebuilding the graph. |
| `Intro to nodes, fields and supertags in Tana.md` | Tana documentation | ★★★★ | Technical walkthrough. Node = unique ID. Field = structured metadata. Supertag = "is a" (type) vs tag = "has a" (property). Clearest explanation of typed-node model in the corpus. |
| `Show HN Org-Supertag  Hacker News.md` | HN thread | ★★★ | Bridges Tana's supertag concept into Emacs/Org-mode via SQLite. Community reaction: interested but confused by abstraction. Documents adoption friction for typed-node models. |
| `yibieorg-supertag Implement a modern note-taking app style in Org-mode..md` | GitHub README | ★★★ | Technical spec. Pure Emacs Lisp, database-backed fields on plain .org files. Comparison table vs. Org-roam / Denote. |

### Knowledge management / Zettelkasten

| File | Source | Quality | Relevance |
|---|---|---|---|
| `Zettelkasten - Wikipedia.md` | Wikipedia | ★★★ | Historical and conceptual foundation. Atomic notes + unique IDs + emergent connections. Graph model (not tree). Effectiveness evidence mixed. |
| `From my perspective, they are all derivatives of org-mode.  Hacker News.md` | HN thread | ★★★ | Argues Obsidian/Roam/LogSeq are Org-mode derivatives. Zettelkasten framing questioned. Good on learning-curve patterns and tool-switching behaviour. |
| `Roam – a graph-based personal knowledgebase  Hacker News.md` | HN thread | ★★ | Only one substantial comment captured (ToS/data-ownership alarm). Roam's licensing terms sparked community backlash — confirms data ownership as non-negotiable for power users. |
| `Obsidian – A knowledge base from a local folder of plain text Markdown files  Hacker News.md` | HN thread (large) | ★★★★ | Very large (~65k tokens). Local-first + plain markdown = strong resonance. Backlinks, community plugins, vault concept. Tensions: plugin ecosystem lock-in, sync pricing. |
| `About - Obsidian.md` | Obsidian manifesto | ★★★ | Seven principles (Yours, Durable, Private, Malleable, Independent). Non-VC, user-funded model. Clearest articulation of the local-first value proposition as a business/product commitment. |

### OmniFocus / GTD gold standard

| File | Source | Quality | Relevance |
|---|---|---|---|
| `OmniFocus – Task Management Software Built for Pros  Hacker News.md` | HN thread | ★★★★ | OmniFocus as GTD canonical. Perspectives system is differentiator; web version inadequate. Apple-only lock-in causes real user regret. Users delay leaving Apple ecosystem solely for OmniFocus. |
| `OmniFocus v Things – Mac  iPad  iPhone  Hacker News.md` | HN thread | ★★★ | OmniFocus vs. Things comparison. Things as simpler/elegant alternative. Manual sync weakness, slower development. Data loss incidents pushing users from OmniFocus. |

### Smos

| File | Source | Quality | Relevance |
|---|---|---|---|
| `Smos Documentation - Features.md` | Official docs | ★★★★ | Complete technical picture. YAML forest structure, state history with timestamps, customisability-first design ("XMonad for task management"). Machine-readable format + sync. Closes the gap in previous Smos analysis. |

### Mind mapping

| File | Source | Quality | Relevance |
|---|---|---|---|
| `Mind map - Wikipedia.md` | Wikipedia | ★★★ | Definition, history (Buzan 1974, roots to Porphyry 3rd century), effectiveness research (10-15% improvement, discipline-dependent). Contextualises mind maps as a thinking method, not just software. |
| `List of concept- and mind-mapping software - Wikipedia.md` | Wikipedia catalog | ★★ | Taxonomy of 50+ tools. Categories: educational, business, web-based, desktop. Useful for landscape overview, no depth per tool. |
| `H-m-m Hackers mind map  Hacker News.md` | HN thread | ★★★ | Terminal mind-map with Vim keybindings. Tensions: Insert-key UX confusion, outliner vs. mind-map semantics. "Why not a nested list if not visual?" debate. |
| `My Mind A new web-based mind map editor  Hacker News.md` | HN thread | ★★ | Early web mind-mapping tool. Same Insert-key UX friction. Use cases: infrastructure docs, system architecture. |
| `Show HN I made a mind map tool meant for large, detailed node hierarchies  Hacker News.md` | HN thread | ★★★ | JumpRoot: hierarchical tool for broad/deep structures. Author argues visual graphs too inefficient for large knowledge bases. "Viewer nodes" concept. Terminology debate: mind-map vs. outliner. |

### GTD methodology

| File | Source | Quality | Relevance |
|---|---|---|---|
| `GTD in 15 minutes – A Pragmatic Guide to Getting Things Done.md` | Tutorial | ★★★★ | Clear exposition of GTD's five lists (In, Next Actions, Waiting For, Projects, Someday/Maybe), 2-minute rule, contexts, weekly review. Good reference for the methodology underlying most tools in this space. |
| `GTD in 15 Minutes – A Pragmatic Guide to Getting Things Done  Hacker News.md` | HN thread | ★★★ | User adaptations of GTD: Markdown journals, GitHub issues, phone alarms. Procrastination reframed as "missing ingredients." |
| `A Beginner´s Guide to Getting Things Done  Hacker News.md` | HN thread (large) | ★★★ | Large thread (~44k tokens, partially read). Multiple GTD interpretation schools. Discipline > tool choice. Calendar/reminder integration essential. |

### Local-first

| File | Source | Quality | Relevance |
|---|---|---|---|
| `Local-first software You own your data, in spite of the cloud.md` | Ink & Switch essay | ★★★★★ | The canonical manifesto. Seven ideals: fast, multi-device, offline, collaboration, longevity, privacy, user control. CRDTs as enabling technology. Three prototypes. **Core intellectual reference for pfq's storage model.** |
| `Show HN Muse 2.0 with local-first sync  Hacker News.md` | HN thread | ★★★ | Practical CRDT implementation (Swift + Go sync server). Transactional/blob/ephemeral data model. Demonstrates local-first is production-viable. |

### Product design philosophy

| File | Source | Quality | Relevance |
|---|---|---|---|
| `Three constraints before I build anything  Hacker News.md` | HN thread, 2025 | ★★★★ | Compact thread on product primitives. Core idea: small number of powerful, composable primitives beats feature sprawl. Tana cited as a cautionary case (two primitives yet overwhelming complexity). Useful vocabulary: "concept count", "nouns and verbs of a product." |

### Side-project psychology

| File | Source | Quality | Relevance |
|---|---|---|---|
| `It's OK to abandon your side-project (2024)  Hacker News.md` | HN thread, 2024 | ★★★ | Compact thread on the emotional lifecycle of side projects. Themes: "end-of-life wrap-up" as closure ritual, weekly justification loop, building for learning over shipping. Tangentially relevant as pfq is itself a side project. |

### AI and thinking

| File | Source | Quality | Relevance |
|---|---|---|---|
| `AI should elevate your thinking, not replace it  Hacker News.md` | HN thread, 2025 | ★★★ | Large thread (~210k chars). Central debate: does AI-assisted coding atrophy engineering judgment? Key quote: "there is no compression algorithm for experience." Peripherally relevant — surfaces the broader question of tools vs. thinking that underpins pfq's philosophy. **Underexplored** — only partial read. |

---

## Coverage gaps — suggested additional sources

### High priority

**"Ask HN: How do you manage long-term goals?"** — these threads surface the "motivation / why" need directly in user language. Still uncollected.
- Search: `site:news.ycombinator.com "long-term goals" OR "why are you doing" personal productivity`

**Tana launch HN thread** — Supertags marketing page and docs are now in the corpus (good on concepts) but the HN launch thread would give community reaction and competitive positioning that those docs lack.
- Search: `site:news.ycombinator.com "Show HN" Tana`

**Roam Research full launch thread** — only one comment was captured in the current Roam file (the ToS alarm). The full thread likely has richer discussion on the block-based model and why it resonated.
- Search: `site:news.ycombinator.com "Roam Research" launch`

### Medium priority

**Logseq vs. Obsidian comparison threads** — useful for understanding what drove users from one to the other in the networked-outliner space.

**GTD critique threads** — the methodology's limitations from practitioners. The GTD tutorial is now in the corpus but practitioner frustrations are underrepresented.
- Search: `site:news.ycombinator.com "getting things done" limitations OR frustrations`

**Large org-mode HN files (still underexplored)** — the two existing large org-mode files (40k and 46k tokens) were only partially analysed. Targeted grep queries would extract more.
- `grep -i "plain text\|sync\|future.proof\|why\|goal\|motivation" "raw_data_src/Org Mode for Emacs..."`

---

## Notes on collection method

- AI-generated summaries (`app_analyse_fonc.md`, `project_scoping_pro.md`, `arcadia.md`, Gemini outliner list) are useful for taxonomy but contain no primary user opinions. They should be treated as structured overviews, not evidence of real user sentiment.
- The two large HN org-mode files were unreadable at full length. They likely contain the richest technical debate in the corpus. **Worth re-reading with targeted grep queries** (e.g. search for "plain text", "sync", "future proof", "why", "goal").
- Reddit sources are good for emotional/attitudinal signal. HN sources are better for technical depth and design debate.
