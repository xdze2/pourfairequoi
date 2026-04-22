# Daily Planner — Design Notes

## Concept

A scheduled, offline LLM pass over the whole graph. Not reactive — deliberate.
Runs overnight (e.g. 6am via cron), output ready at first `pfq` launch of the day.

Complements the per-node inner voice: where the inner voice is reactive and local,
the daily planner is global and proactive.

---

## Two modes, one tool

| | Inner voice | Daily planner |
|---|---|---|
| Trigger | navigate to a node | scheduled (cron) |
| Scope | local neighborhood (depth 2) | whole graph |
| Output | 2–4 choices | 6–15 actions |
| Backend | Claude CLI (fast, interactive) | Ollama (slow, offline ok) |
| Feel | reactive, conversational | deliberate, morning planning |

---

## What the LLM sees that you don't

Reading the whole graph at once reveals things that are invisible node-by-node:

- nodes stuck for weeks
- roots with no recent activity
- orphan subgraphs (nothing connecting back to a root)
- imbalance — one root has 20 leaves, another has none
- clusters of `todo` that look like a hidden project
- `doing` nodes that haven't moved in a long time

---

## Output format

Three tiers, ordered by effort:

```
=== Daily briefing — 2026-04-20 ===

CLARIFICATIONS (answer these to unblock)
  1. "explore freelance" — still relevant, or archive it?
  2. "talk to 3 freelancers" — who are the 3? Add names as children?

SMALL EDITS (apply directly, low effort)
  3. Mark "finish Python course" as done — doing for 3 weeks
  4. Rename "stuff" → something more specific
  5. Move "buy domain" under "launch side project" instead of root

DAILY ACTIONS (pick 1-2 to work on today)
  6. ○ write first blog post       [todo]
  7. ○ send invoice to client      [todo]
  8. ○ book dentist                [stuck]
```

---

## Backend: Ollama

Slow but offline, no API key, no cost. Acceptable for a nightly batch job.

```bash
ollama run mistral "$(cat briefing_prompt.txt)"
```

Or via Python:

```python
import subprocess

def run_ollama(prompt: str, model: str = "mistral") -> str:
    result = subprocess.run(
        ["ollama", "run", model, prompt],
        capture_output=True, text=True, timeout=300
    )
    return result.stdout.strip()
```

Model choice matters — a larger model (e.g. `llama3`, `mistral`) handles graph reasoning better than small ones.

---

## Scheduling

Cron job, runs once a day before you wake up:

```cron
0 6 * * * cd /path/to/vault && pfq --briefing > .pfq_briefing.txt
```

Or triggered manually: `pfq --briefing` generates on demand.

Output stored in `.pfq_briefing.txt` (gitignored) in the vault.
On first `pfq` launch of the day, if briefing file exists and is from today → show it.

---

## Executability (open question)

Two options:

**Read-only:** briefing is text, you act manually via existing keyboard shortcuts.
Simple to implement. Still useful.

**Executable:** press `3` to apply action 3. Same `ACTION: {...}` parsing as inner voice.
More powerful, same infrastructure — natural v2 once inner voice action parsing exists.

---

## Graph serialization for the prompt

Full graph dump — all nodes with their status, role, and parent/child links:

```python
def build_full_graph_context(graph: NodeGraph) -> str:
    lines = []
    for node_id in graph.get_all_node_ids():
        node = graph.get_node(node_id)
        parents = graph.get_parent_ids(node_id)
        children = graph.get_children_ids(node_id)
        role = "root" if not parents else ("leaf" if not children else "middle")
        lines.append(
            f"{node_id} [{role}] [{node.status}] \"{node.description}\""
            + (f" — children: {', '.join(children)}" if children else "")
        )
    return "\n".join(lines)
```

---

## System prompt (draft)

```
You are reviewing someone's personal knowledge graph at the start of their day.
The graph is a DAG: roots are motivations, leaves are actions, middle nodes are structure.

Your job: produce a daily briefing with 6 to 15 items across three categories.

CLARIFICATIONS: questions the user needs to answer to unblock or clarify the graph.
SMALL EDITS: low-effort structural improvements (rename, move, archive, mark done).
DAILY ACTIONS: 2-4 concrete leaf nodes worth working on today. Prioritize stuck and long-running doing.

Rules:
- Be specific — use actual node descriptions, not generic advice.
- No moralizing. No preamble. Go straight to the list.
- Each item is one line. Numbered. Actionable.

Graph:
{graph_context}
```

---

## Open questions

- **Executable vs read-only:** v1 read-only, v2 executable (reuses inner voice action parsing)
- **Model choice:** `mistral` for speed, `llama3` for quality — make it configurable
- **Briefing freshness:** show only if generated today, else prompt to regenerate
- **Integration point:** shown at startup as a panel, or accessible via a key (e.g. `b` for briefing)?
