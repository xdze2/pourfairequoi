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

## Coverage gaps — suggested additional sources

### High priority

**Taskwarrior** — the canonical CLI task manager with dependencies. Direct technical comparator to pfq. Community is large and opinionated about plain-text, local-first, CLI composability.
- Search: `site:news.ycombinator.com taskwarrior`
- Or fetch: `https://taskwarrior.org/docs/` and a HN "Show HN" thread

**Tana** — most conceptually ambitious recent entrant (2023). "Supertags" turn nodes into typed objects. The HN launch thread likely has the sharpest current discussion of what's missing in the space.
- Search: `site:news.ycombinator.com "Show HN" Tana supertag`

**Obsidian launch thread** — the local-first PKM that succeeded by committing to plain markdown files. The HN thread likely crystallizes the "data ownership" argument better than any other source.
- Search: `site:news.ycombinator.com Obsidian "local" "markdown"`

**OmniFocus** — the GTD gold standard for Apple users. Understanding why power users accept its complexity (and what frustrates them) would sharpen pfq's positioning in the "serious personal productivity" segment.
- Search: `site:news.ycombinator.com omnifocus` or r/omnifocus discussions

### Medium priority

**"Ask HN: How do you manage long-term goals?"** — these threads surface the "motivation / why" need directly in user language.
- Search: `site:news.ycombinator.com "long-term goals" OR "why are you doing" personal productivity`

**SMOS features page** (`https://smos.cs-syd.eu/features.html`) — the actual feature documentation, not just Reddit reactions. Would give a complete picture of what SMOS does and does not do technically.

**Roam Research launch thread** — Roam popularized the "everything is a block" + bidirectional links model. Understanding why it resonated (and why people left) clarifies the PKM vs. task manager distinction.
- Search: `site:news.ycombinator.com "Roam Research" OR "roamresearch"`

**The "local-first software" essay (Ink & Switch)** — the intellectual manifesto behind pfq's storage model. Widely cited in the HN community.
- URL: `https://www.inkandswitch.com/local-first/`

### Lower priority

**Logseq vs. Obsidian comparison threads** — useful for the "networked outliner" space but not directly relevant to pfq's goal/task focus.

**GTD (Getting Things Done) HN discussions** — the methodology that shaped most of these tools. Understanding GTD's limitations from practitioners would surface unmet needs.
- Search: `site:news.ycombinator.com "getting things done" OR "GTD" limitations`

---

## Notes on collection method

- AI-generated summaries (`app_analyse_fonc.md`, `project_scoping_pro.md`, `arcadia.md`, Gemini outliner list) are useful for taxonomy but contain no primary user opinions. They should be treated as structured overviews, not evidence of real user sentiment.
- The two large HN org-mode files were unreadable at full length. They likely contain the richest technical debate in the corpus. **Worth re-reading with targeted grep queries** (e.g. search for "plain text", "sync", "future proof", "why", "goal").
- Reddit sources are good for emotional/attitudinal signal. HN sources are better for technical depth and design debate.
