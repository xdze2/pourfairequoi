# Technical Choices — Atomic Analysis

Each entry is a design decision axis. For each axis: what the options are, what tradeoffs were observed in the sources, and where pfq stands.

---

## 1. Graph topology: list → tree → DAG → general graph

The most fundamental structural choice.

| Model | What it can express | Limitation |
|---|---|---|
| Flat list | Tasks | No hierarchy, no context |
| Tree | Hierarchy, decomposition | Each node has exactly one parent — no sharing |
| DAG | Hierarchy + multi-parent | Acyclic constraint, harder to reason about |
| General graph | Anything | Cycles possible, no inherent direction |

**Observed tensions:**
- Most outliners (WorkFlowy, Dynalist, SMOS, org-mode) are trees. Simple and intuitive.
- The "cycling to work" argument: one action serves health, income, and fun simultaneously — trees can't represent this without duplication.
- The HN Intention thread debated whether their app was really a DAG or a tree (it was a DAG but demo'd as a tree).
- SMOS explicitly refused cross-file links because it couldn't guarantee semantic correctness (broken links).
- Cyclic graphs were raised but dismissed: cycles in goal structures indicate confused thinking, not a feature to support.

**pfq:** DAG. Deliberately chosen as the minimum structure needed — not a general graph (no cycles, no arbitrary edges), not a tree (multi-parent enabled).

---

## 2. Link semantics: untyped vs. typed/directional

In most tools, a link is just a connection. No meaning is attached to its direction.

**Options:**
- **Untyped:** parent/child with no name (Intention, outliners, SMOS)
- **Typed edges:** links carry a label ("blocks", "depends on", "relates to") — used in Jira, Bugzilla
- **Directional semantics:** the direction itself carries meaning regardless of label

**Observed tensions:**
- Intention's links mean "contributes to" implicitly, but this is never named
- Arcadia formalizes this explicitly: Operational Analysis (why) → System Need (what) → Logical Architecture (how) — four named layers with defined directional semantics
- Task dependency tools (Jira, MS Project) use typed "blocks/blocked-by" edges but don't capture goal motivation
- No personal productivity tool in the sources names the edge direction as *why* vs *how*

**pfq:** Directional semantics without labels. Up = generalization/why, down = decomposition/how. Simple binary — no label vocabulary to maintain.

---

## 3. Storage model: database vs. files vs. single file

| Model | Examples | Properties |
|---|---|---|
| Server database | Todoist, Notion, Motion | Sync, collaboration, account required, vendor lock-in |
| Single local file | org-mode (.org), SMOS (.smos) | Simple, one file = one project, hard to cross-reference |
| One file per node | pfq | Git-friendly, grep-able, merge-friendly, cross-ref by ID |
| Local folder of markdown | Obsidian, Logseq | Flexible, bidirectional links via `[[wikilinks]]` |

**Observed tensions:**
- Org-mode's single-file format: praised for simplicity and future-proofness, criticized for being hard to sync and machine-unfriendly
- SMOS chose YAML over org-mode format specifically for machine-readability, but kept a single-file-per-"project" model
- The most upvoted criticism of cloud tools (Intention, Masterplan) was the account requirement
- "I want my data to live on my computer" — a recurring strong sentiment
- Obsidian succeeded largely by committing to local markdown files

**pfq:** One YAML file per node. Unique in the space: enables per-node git history, merge without conflicts, and the vault is just a directory.

---

## 4. File format: proprietary vs. plain text vs. structured text

| Format | Examples | Human-readable | Machine-friendly | Future-proof |
|---|---|---|---|---|
| Proprietary binary | OmniFocus | ✗ | ✗ | ✗ |
| Plain text / org | org-mode | ✅ | ⚠️ (syntax fragile) | ✅ |
| YAML | SMOS, pfq | ✅ | ✅ | ✅ |
| JSON | many | ⚠️ verbose | ✅ | ✅ |
| Markdown + frontmatter | Obsidian, Logseq | ✅ | ✅ | ✅ |

**Observed tensions:**
- Org-mode Reddit thread: YAML criticized as "whitespace sensitive, less human-friendly" — but this conflates YAML-as-hierarchy (SMOS's use, where indentation is structural) with YAML-as-flat-record (pfq's use, where the file is a simple key-value object)
- SMOS chose YAML precisely because it's more machine-readable than org syntax, enabling better tooling
- pfq's YAML is minimal: each file is a small flat record (description, status, how: list). No deep nesting → the whitespace-sensitivity complaint doesn't apply

**pfq:** YAML, but used as a flat record, not as a hierarchy. The graph structure lives in the links, not in indentation.

---

## 5. UI paradigm: GUI / web / TUI / CLI

| Paradigm | Examples | Target user | Strengths |
|---|---|---|---|
| Web/mobile GUI | Intention, Todoist, Notion | General public | Accessible, rich interaction |
| Desktop GUI | OmniFocus, Things | Mac power users | Polish, offline |
| TUI (terminal) | SMOS, pfq, Taskwarrior | Developer / CLI user | Keyboard-native, scriptable, no Electron |
| CLI only | Taskwarrior | Developer | Composable with shell |
| Outliner (browser) | WorkFlowy, Dynalist, Roam | Knowledge workers | Frictionless capture, rich text |

**Observed tensions:**
- Intention was mobile-first (webview) and paid for it: Google OAuth broken, Safari cookie issues, no iOS app possible under App Store rules
- SMOS: "Web interface is just TUI in a browser" — acceptable to its target audience
- WorkFlowy: minimalism as a feature, but HN commenters immediately asked for dates, tags, cross-links — feature pressure over time
- The TUI niche is small but loyal: these users are already comfortable in the terminal, don't want Electron, and appreciate keyboard-first design

**pfq:** TUI via Textual (Python). Aligns with the local-first, developer-audience positioning. The constraint is also a feature: keeps scope narrow.

---

## 6. Data topology display: graph view vs. tree/outline view vs. neighbourhood view

Even if the underlying model is a DAG, the *display* is a separate choice.

| Display | Examples | Properties |
|---|---|---|
| Force-directed graph | TaskGraph, Obsidian graph view | Good for overview, bad for navigation |
| Full tree (outliner) | WorkFlowy, Dynalist, SMOS | Linear, scrollable, familiar |
| Focused neighbourhood | pfq | Shows local context only (depth 2 up + down) |
| Flat list with filters | Todoist, Taskwarrior | Hides structure entirely |

**Observed tensions:**
- Force-directed graph views look impressive but are hard to navigate and don't scale beyond ~50 nodes
- Full tree views work well but can become overwhelming (the WorkFlowy "expanded vs. collapsed" insight)
- SMOS shows the full file as an outline — no cross-file view
- pfq's neighbourhood view is unusual: you're always "inside" a node looking at its immediate context. This matches the *why/how* mental model — you're asking "what does this serve?" and "how do I achieve it?" not "show me everything"

**pfq:** Neighbourhood view, depth-capped. Deliberate trade-off: no global graph view, but always locally coherent.

---

## 7. Identity model: node ID vs. title/slug vs. position

How is a node uniquely referenced?

| Model | Examples | Properties |
|---|---|---|
| Title-based | org-mode, WorkFlowy | Human-readable, breaks on rename |
| Position-based | outliners (indent level) | Implicit, fragile |
| Stable ID + cosmetic slug | pfq (`AB0002_practice_chords`) | Rename-safe, grep-able |
| UUID | many databases | Stable but opaque |

**Observed tensions:**
- Org-mode cross-links break when headings are renamed — a well-known pain point
- SMOS refused cross-file links precisely because it couldn't guarantee stable references
- pfq uses a 6-char random prefix as the stable identity; the slug is cosmetic and can go stale

**pfq:** Stable 6-char ID + cosmetic slug. Enables links that survive renames — the prerequisite for a real DAG.

---

## 8. Scope: all-in-one vs. single-purpose

**The feature creep trap:** every outliner tool eventually gets asked for dates, recurring tasks, collaboration, calendar sync, mobile, tags, search… WorkFlowy, SMOS, and Intention all faced this pressure immediately on launch.

| Approach | Examples | Risk |
|---|---|---|
| All-in-one | Notion, Motion, TickTick | Complexity, loses focus |
| Single-purpose | pfq, Taskwarrior | Users ask for missing features |
| Composable | org-mode (via Emacs ecosystem) | Power, but steep learning curve |

**Observed tensions:**
- SMOS author: "Smos is not for capturing. For that, use intray.eu." — explicit scope decision, composability via separate tools
- org-mode praised for extensibility (Emacs lisp); criticized for requiring Haskell/recompilation for SMOS
- Arcadia/Capella: hyper-focused on one methodology — power tool for one job

**pfq:** Single-purpose. Explicitly no dates, no reminders, no calendar, no collaboration. The vault is just files — composable with git, grep, and other tools.

---

## 9. Extensibility model: configuration vs. plugins vs. code

| Model | Examples | Properties |
|---|---|---|
| None / opinionated | Todoist, SMOS | Easy to start, hard to customize |
| YAML config | pfq (FIELDS in config.py) | Low friction, safe |
| Plugin system | Obsidian, Logseq | Powerful, ecosystem risk |
| Language as config | org-mode (Emacs Lisp), SMOS (Haskell) | Maximum power, steep entry |

**Observed tensions:**
- SMOS Reddit: "You can't redefine TodoState — there's no way to redefine types or functions" — the Haskell-as-config model is praised by Haskellers, alienating to others
- Org-mode's extensibility is its core value proposition for power users
- pfq's `FIELDS` dict in `config.py`: adding a field to the whole app requires one line — minimal but sufficient for its scope

**pfq:** Config-as-code (Python dict). Not a plugin system, but the architecture makes extension trivial for the target user (developer).

---

## Summary: pfq's technical profile

| Axis | pfq choice | Rarity in the space |
|---|---|---|
| Graph topology | DAG | Uncommon (most are trees) |
| Link semantics | Directional why/how | **Unique** |
| Storage | One YAML file per node | **Unique** |
| File format | YAML flat record | Uncommon (org-mode dominates plain-text) |
| UI | TUI (Textual) | Niche |
| Display | Neighbourhood view | **Unique** |
| Node identity | Stable ID + slug | Uncommon |
| Scope | Single-purpose | Common in CLI tools |
| Extensibility | Config dict | Simple, sufficient |
