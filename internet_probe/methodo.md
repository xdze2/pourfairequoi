# Market Analysis — Methodology

This document explains what this `internet_probe/` directory is, how it was built, and how to continue the work in a new session.

---

## Purpose

A market analysis of the **personal task/goal management** tool space — covering graph-based tools, outliners, plain-text systems, and professional goal-decomposition methods.

The goal is not a feature comparison. It is to understand:
1. What **user needs** exist in this space, and which are underserved
2. What **technical choices** tools make, and what tradeoffs each implies

A specific competitive positioning analysis (comparing a target tool against this landscape) is a separate step, to be done after the field analysis is complete.

---

## Directory structure

```
internet_probe/
├── methodology.md          ← this file
├── raw_data_index.md       ← index of all sources with quality/relevance notes
├── user_needs.md           ← 12 atomic user needs extracted from sources
├── technical_choices.md    ← 9 technical decision axes with tradeoffs
└── raw_data_src/           ← raw source documents (HTML→markdown exports)
    ├── *.md                ← one file per source
```

---

## How sources are collected

Pages are saved manually as markdown files into `raw_data_src/`. The filename is the page title as copied from the browser tab, with the site name appended.

**Collection method used so far:**
- Browser "Save as markdown" or copy-paste into a `.md` file
- File naming convention: `{page title}  {site name}.md` (two spaces before site name)

**Sources collected:**
- Hacker News "Show HN" threads for similar apps
- Reddit threads (r/orgmode, r/productivity)
- App feature/marketing pages
- Wikipedia articles
- AI-generated overviews (Gemini) for taxonomy

**Note on AI-generated sources:** Files like `app_analyse_fonc.md`, `project_scoping_pro.md`, `arcadia.md`, and the Gemini outliner list are AI summaries, not primary community discussion. They are useful for taxonomy but carry no user sentiment. Treat them as structured overviews only.

---

## How the analysis files are generated

All three analysis files (`user_needs.md`, `technical_choices.md`, `raw_data_index.md`) were written by Claude Code after reading all source files in `raw_data_src/`.

**Process followed:**
1. Read all source files (some large files required grep or offset/limit reads)
2. Identify recurring patterns across sources
3. Abstract each pattern into an "atomic" unit — a need or a design choice that stands independently of any specific tool
4. Write each unit with: definition, observed tensions from sources, notes on coverage across the field
5. Produce a summary table at the end of each file

**Framing principle:** Features are evidence, not the point. A recurring feature request signals an underlying need. A design choice signals a value trade-off. The analysis always asks *why* a tool made a choice, not just *what* it chose.

---

## Current state of the analysis (April 2026)

### Done
- [x] `user_needs.md` — 12 atomic needs, coverage map across tools
- [x] `technical_choices.md` — 9 decision axes with tradeoffs
- [x] `raw_data_index.md` — source quality/relevance ratings + gap suggestions

### Not yet done
- [ ] Additional sources from `raw_data_index.md` gap list (Taskwarrior, Tana, Obsidian launch, local-first essay)
- [ ] Deep read of the two large org-mode HN files (currently underexplored — 40–46k tokens each)
- [ ] Target user profile — who uses these tools? what is their workflow before/after?
- [ ] Competitive positioning (separate step, requires a specific tool to compare against)

---

## How to resume a work session

### Context to give Claude at the start

> "We are doing a market analysis for a personal task manager.
> Read `internet_probe/methodology.md` for context, `internet_probe/raw_data_index.md` for the source inventory, and the two analysis files `user_needs.md` and `technical_choices.md` for what has already been extracted."

### Suggested next tasks (in order)

1. **Add new sources** — fetch the gap sources listed in `raw_data_index.md` (Taskwarrior HN thread, Tana HN thread, Obsidian launch, Ink & Switch local-first essay). Save to `raw_data_src/`, update `raw_data_index.md`.

2. **Exploit underexplored sources** — the two large org-mode HN files. Use grep with targeted queries:
   - `grep -i "plain text\|sync\|future.proof\|why\|goal\|motivation" "raw_data_src/Org Mode for Emacs..."`

3. **Write `target_user.md`** — who uses these tools? What is their workflow before adopting a structured tool? What pain are they describing? Draw from user need patterns in `user_needs.md`.

4. **Competitive positioning** — once the field analysis is solid, a separate session can compare a specific tool against this landscape using `technical_choices.md` and `user_needs.md` as the framework.

---

## Design principles for this analysis

- **Primary sources over AI summaries.** HN threads and Reddit give real opinions; AI overviews give taxonomy. Both are useful but not equally weighted.
- **Atomic units over feature lists.** Each need/choice should be irreducible — it cannot be split further without losing meaning.
- **Tensions over conclusions.** The interesting insight is always in the trade-off, not the answer. Document what each choice costs as well as what it gains.
- **No home-team bias.** The field analysis must be done independently of any specific tool being evaluated. Conclusions about what is underserved should emerge from the sources, not be reverse-engineered from a desired outcome. The comparison step comes later, and uses this analysis as neutral ground.
