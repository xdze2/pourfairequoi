# User Needs — Atomic Analysis

Extracted from the sources in `raw_data_src/`. Each need is stated independently of any tool that tries to address it.

---

## 1. Capture — "Get it out of my head"

The most primal need: remove something from working memory before it's lost. Low friction is essential — any barrier (login, format, typing speed) causes abandonment. Users reach for pen & paper when tools fail here.

*Seen in:* Todoist ("capture instantly"), WorkFlowy ("type like in a text editor"), org-mode, every app with a quick-entry feature.

---

## 2. Not forgetting — "Make sure it comes back"

The captured thing must resurface at the right moment, not just sit in a list forever. This includes due dates, reminders, recurring tasks, and spaced repetition (LearnObit). Different from capture: it's about time-based reliability.

Taskwarrior surfaces a revealing failure mode here: its recurring-task system is architecturally broken — "do first Monday of every month" is impossible to express. Multiple users cite this as the single reason they abandoned an otherwise excellent tool. Recurrence correctness is non-negotiable.

*Seen in:* Todoist (today/upcoming views), TickTick (reminders), SMOS (schedule-aware queries), Anki/LearnObit (SRS), Taskwarrior (limitation: broken recurrence cited as dealbreaker).

---

## 3. Overview — "See the whole picture without drowning"

As volume grows, flat lists become chaotic. Users need to collapse and expand detail on demand — to zoom out to goals, zoom in to tasks. WorkFlowy's core insight: *the same list expanded vs. collapsed looks completely different*. This was the "aha" moment that made people sign up.

*Seen in:* WorkFlowy ("organize your brain"), Dynalist, outliners in general, SMOS, org-mode.

---

## 4. Structure / decomposition — "Break big things into smaller things"

Users naturally think in hierarchies: a goal has sub-goals has tasks. Tools need to support this decomposition without fighting it. The outliner format (infinite nesting) is the mainstream answer. DAG tools go further by allowing shared sub-tasks.

*Seen in:* WorkFlowy, Dynalist, Taskade, Intention, SMOS, org-mode, OmniFocus.

---

## 5. Motivation / "why am I doing this?" — "Connect actions to purpose"

A recurring but **underserved** need: knowing *why* a task exists keeps motivation alive and helps prioritize. Several HN commenters described losing the thread between daily tasks and larger goals. One user literally described building their DAG up to Maslow's hierarchy. The Snakemake comment captures it perfectly: *"if a task is not linked to an end goal, it doesn't get executed."*

GTD gestures at this with "Projects" and "Someday/Maybe" lists, but the methodology deliberately avoids modelling the direction of meaning — it treats all next actions as equally actionable once captured. The question "why am I doing this project at all?" is left to the user. Taskwarrior's urgency system answers "what first?" but not "why at all."

*Seen explicitly in:* Intention (partially), the Maslow-DAG commenter, Arcadia ("Operational Analysis = the Why"), pfq (the whole point), GTD (absent — notable gap in the canonical methodology).

**This need is almost entirely unaddressed by mainstream tools.** Todoist, TickTick, Notion, WorkFlowy, GTD — none model the direction of meaning.

---

## 6. Scheduling / time realism — "Know what is actually doable today"

Tasks without time context create a false sense of control. Users need to know if their list fits in the available hours. The AI-scheduling tools (Motion, Morgen) specifically target this: *"if you have 5h of meetings and 6h of tasks, you'll understand why you're always running."* SMOS addresses this with context-aware queries (`smos-query work office`).

*Seen in:* Motion (auto-schedule), Morgen, Sunsama (intentional daily planning), SMOS.

---

## 7. Prioritization — "What should I do first?"

Different from scheduling: not *when* to do something, but *which* thing matters most. Expressed as priority flags, urgency scores, impact/effort grids. Often conflated with scheduling but is a separate cognitive act.

*Seen in:* Todoist (priority levels), OmniFocus (flags), Aha!/Jira Product Discovery (impact scoring), Akiflow (triage inbox).

---

## 8. Focus / noise reduction — "Show me only what's relevant right now"

The flip side of overview: the ability to zoom in and hide everything else. WorkFlowy's "zoom into a node" is the canonical solution. Also: context filtering (SMOS: "don't show me 'water plants at home' when I'm at the office"), tag-based filtering.

*Seen in:* WorkFlowy (zoom), SMOS (context queries), OmniFocus (available filter), Dynalist (tags + filter).

---

## 9. Cross-referencing — "This task belongs to several things at once"

A single action can serve multiple goals. Trees can't express this; DAGs can. Cycling to work contributes to health, fun, and income simultaneously. This is the structural argument for DAGs over trees — and it comes up repeatedly in HN discussions.

*Seen in:* Intention (DAG, multi-parent), the Maslow-DAG commenter, org-mode (cross-links, though clunky), Roam/Logseq (bidirectional links for notes).

---

## 10. Data ownership / longevity — "My data is mine, forever"

A strong need in the technical community: no account required, local files, plain text, no vendor lock-in. The most upvoted criticism of Intention was the login requirement. The most praised aspect of org-mode is that it's plain text files on your own disk. SMOS gained credibility by being local YAML. Obsidian was born from this need.

The Ink & Switch "local-first software" essay formalises this as seven ideals (fast, multi-device, offline, collaborative, longevity, privacy, user control) and proposes CRDTs as the enabling technology. Roam's ToS ("perpetual license to create derivative works, terminate without notice") crystallised the risk of cloud-only tools for the HN community — a single thread drove significant migration away from Roam. Obsidian's manifesto commits to this explicitly as a company stance, not just a feature.

*Seen in:* org-mode users, SMOS (local YAML), WorkFlowy criticisms, Obsidian (local folder + company manifesto), Roam (ToS backlash), Ink & Switch essay, pfq (local vault, plain YAML).

---

## 13. Typed structure — "Give nodes meaning beyond position"

A need that emerges at scale: when a graph or list grows large, users need nodes to carry semantic type information — not just where they sit in the hierarchy, but *what they are*. A meeting note, a contact, a project, a task — these are different kinds of things and should behave differently.

Zettelkasten (atomic notes + unique IDs) is the minimal version: each note has an identifier and a type implied by its content. Tana's supertags are the most explicit formalisation: a supertag is an ontological declaration ("is a meeting") that inherits fields, not a descriptive label ("has property #meeting"). Org-Supertag brings this model to Org-mode via a SQLite backing layer.

The tension: typed structure adds expressive power but at the cost of setup overhead and rigidity. Most users resist defining schemas upfront — they want to capture first, classify later. Tana's marketing copy targets this exactly: "dump a fleeting idea and let it categorize itself." Tools that require classification before capture lose users at the inbox stage.

*Seen in:* Tana (supertags), Zettelkasten (atomic notes), Org-Supertag (typed fields on Org nodes), Smos (typed state history), Arcadia (four typed analysis layers).

---

## 11. Collaboration — "Share and delegate with others"

The need to share structure with teammates, assign tasks, and see others' progress. Almost entirely absent in tools targeting individuals; central to team tools (Masterplan, Linear, Motion). Personal tools add it late and it's often awkward (WorkFlowy shared lists, Notion databases).

*Seen in:* Masterplan/graph task manager, WorkFlowy (requested early), Linear, Motion.

---

## 12. Traceability — "Know why a decision was made"

A professional/engineering need: given a technical choice, trace it back to the requirement it satisfies, and from there back to the user goal. Arcadia's core value proposition. Not relevant for personal GTD, but critical for complex system design.

*Seen in:* Arcadia/Capella, Jama Connect, IBM DOORS, Aha!, Jira Product Discovery.

---

## Summary map

| Need | Mainstream coverage | pfq coverage |
|---|---|---|
| Capture | ✅ Well-served | Partial (keyboard-first TUI) |
| Not forgetting | ✅ Well-served (recurrence quality varies) | ✗ No dates/reminders |
| Overview | ✅ Outliners | ✅ Depth-2 neighbourhood view |
| Decomposition | ✅ Outliners/trees | ✅ DAG |
| **Motivation / why** | ❌ Almost absent (GTD ignores it) | ✅ **Core differentiator** |
| Scheduling / time realism | ✅ Motion, SMOS | ✗ Out of scope |
| Prioritization | ✅ Most tools | Partial (status field) |
| Focus / noise reduction | ✅ Filters, zoom | ✅ Local view, depth cap |
| Cross-referencing | ⚠️ Only DAG tools | ✅ Multi-parent DAG |
| Data ownership | ⚠️ Niche (Obsidian, org-mode) — growing | ✅ Local YAML vault |
| Typed structure | ⚠️ Advanced tools only (Tana, Arcadia) | Partial (fields, no supertags) |
| Collaboration | ✅ Team tools | ✗ Single-user |
| Traceability | ✅ Pro tools (Arcadia) | Partial (implicit via DAG) |
