# Inner Voice — Local Implementation Notes

## What was tested

### Ollama + qwen3.5:0.8b
Attempted to run the inner voice companion locally using a small 8B model via Ollama.

**Result: Failed.**

The model got stuck in analysis paralysis:
- Could not reliably parse the tree ASCII notation
- Looped on "Wait, I see..." instead of producing output
- Confused by the "Output format (strict)" vs "Propose choices" ambiguity in the prompt
- Never committed to a response

**Why it failed:**
1. **Insufficient context window** — the model couldn't hold the nested graph structure in working memory
2. **Weak chain-of-thought** — even with explicit "thinking" instructions, the 8B model couldn't extract meaning from the tree diagram
3. **Format confusion** — the prompt structure (strict format + thinking process + choices) was too ambiguous for a small model to parse reliably
4. **No graceful exit** — the thinking loop had no stopping condition, so the model kept generating reasoning tokens indefinitely

### Prompt revisions tested

**First attempt** (from inner_voice.md):
- Long system prompt with tone guide as a list
- Separate "Output format (strict)" section
- Complex nested instructions
- Result: Model got stuck analyzing, never produced output

**Revised attempt:**
- Simplified language
- Explicit "OUTPUT FORMAT:" section with example
- Moved tone guide down
- Reduced verbosity
- Result: Same failure, just slower

**Conclusion:** Prompt refinement alone cannot fix a fundamental model capability gap.

---

## Key insight: the bottleneck is RAM, not compute

A local Ollama model is limited by **available RAM**, not CPU:
- 8B model (qwen3.5) needs ~10GB RAM
- 7B model (Mistral, Llama2) needs ~14-20GB RAM  
- Larger models (13B+) need 24GB+

Even quantized (`4-bit`) models still demand 6-8GB. Running overnight via cron doesn't solve this — it's the same constraint.

**Implication:** Can't solve the inner voice problem with a local LLM, no matter the scheduling or prompt engineering.

---

## What LLM thinking actually is

An LLM's "thinking" mode is still next-word prediction, just with a dedicated scratch space:

```
Input: "What is 2+2?"
Output: "<thinking>Let me add... 2 + 2 = 4</thinking>\nThe answer is 4."
```

The model doesn't have a separate reasoning engine. It just generates more tokens (the thinking block) before the final answer. Without explicit instruction to stop and produce output, it will loop indefinitely.

**Why Ollama looped:**
- The prompt asked "What is your thinking process?"
- The model interpreted this as: generate reasoning tokens
- It had no explicit stop condition
- It kept generating more reasoning instead of moving to the answer

---

## Recommended approach: hybrid system

**Don't try to do complex LLM reasoning locally.**

Instead, split the work:

| Component | Technology | Why |
|---|---|---|
| **Inner voice** (per-node, interactive) | Claude API (cloud) | Needs reasoning power. Small input (depth-2 neighborhood). Fast response. Low cost. |
| **Daily briefing** (whole-graph, batch) | Rule-based heuristics + embeddings (local) | Deterministic. No hallucinations. Runs in 100ms. Free. |

### Daily briefing: rule-based + embeddings (local)

Replace Ollama with a simple Python script that:

1. **Detects anomalies** (rule-based):
   - Nodes stuck for 2+ weeks (status in `todo`/`stuck`/`doing` + no recent edits)
   - Roots with no leaves (incomplete structure)
   - Orphan subgraphs (disconnected from roots)
   - Status/role mismatch (leaf with root vocabulary, root with leaf vocabulary)

2. **Finds semantic clusters** (embeddings):
   - Use lightweight embedding model (`sentence-transformers`, ~80MB)
   - Find similar descriptions (cosine similarity > 0.7)
   - Suggest grouping or deduplication

3. **Outputs simple briefing:**
   ```
   === Daily insights ===
   
   STUCK OR STALE (waiting 2+ weeks)
   • "finish Python course" — todo for 16 days
   
   INCOMPLETE STRUCTURE (roots with no leaves)
   • "Have fun" — has middle nodes but no actionable tasks
   
   POSSIBLY RELATED (consider grouping)
   • "Build a vintage radio" ↔ "build the new electronics" (0.84 similarity)
   ```

**Advantages:**
- Deterministic (no hallucinations)
- Fast (100ms for a 50-node graph)
- Runs offline, no API key needed
- Easy to tune (adjust thresholds)
- No GPU/high RAM required

**Limitations:**
- More mechanical, less conversational
- Can't detect subtle insights ("you're split between contradictory paths")
- No soft nudges

---

## Refined approach: question selector + small local model

The key insight: **the AI doesn't need to solve the problem — it needs to ask the right question.**

This is a Socratic method approach. The user will figure out the answer themselves. The assistant's job is to surface the right question at the right moment.

### Why this works locally

Instead of asking a small model to reason about complex graph structure, split the work:

1. **Rule-based question selector** (pure Python, no model): detect the node's situation and pick the most relevant question from a fixed list
2. **Small local model** (3-8B): elaborate on that question warmly, in 2-3 sentences

The small model's job is *elaboration*, not *reasoning*. Even qwen3.5:0.8b can do this reliably.

```python
def select_question(node: Node, graph: NodeGraph) -> str:
    """Pick the one most relevant question for this node."""

    if node.status == "stuck":
        return "What's actually blocking this — time, clarity, materials, or motivation?"

    if node.status == "doing" and days_since_edit(node) > 21:
        return "How long has this been in doing? If >3 weeks, something's wrong."

    if is_leaf(node) and not graph.get_parent_ids(node.node_id):
        return "Is this aligned with a root? If not, where does it belong?"

    if len(graph.get_parent_ids(node.node_id)) > 1:
        return "Is this intentional, or are you avoiding a decision?"

    if is_root(node) and not has_leaves(node, graph):
        return "Can you name one concrete action under this goal?"

    # Healthy node — offer reflection
    return "Am I doing this because I want to, or because I think I should?"
```

The small model prompt becomes minimal and focused:

```
You are a thoughtful coach. The user is looking at a node in their project graph.

A key question has been selected for them. Your job: ask it warmly, add 1-2 lines of
context why it matters. Be brief. Be curious, not critical.

Question: {selected_question}
Node: {node_description}
Context: {node_status} for {days} days, under {parent_count} parent(s)

Respond in 2-3 sentences. End with the question.
```

**Example output:**

```
You've had "Build a vintage radio" in todo for 3 weeks, but you already got the old radio
and sourced the parts.

What's actually keeping you from starting — is it that you're not sure how to begin,
waiting for the fablab visit, or something else?
```

### The 15 questions (question bank)

Derived from the motivation/decision checklist:

**Frame (why am I doing this?)**
1. Is this aligned with a root? If not, where does it belong?
2. Which root, specifically — is there a conflict?
3. Am I doing this because I want to, or because I think I should?

**Structure (is this decomposed enough?)**
4. Can I finish this in one session? If not, what's the next smaller step?
5. Do I know what "done" looks like?
6. What's the smallest step that moves this forward?

**Energy (do I have what's needed?)**
7. Am I doing this at the right energy level right now?
8. What's actually blocking this — time, clarity, materials, or motivation?
9. Do I have everything I need, or am I blocked waiting?

**Conflict (what's pulling in two directions?)**
10. Is this node under two roots — intentional tension, or unresolved choice?
11. Which root would I pick if I had to drop one?
12. Is this "keeping options open", or am I avoiding a decision?

**Momentum (am I stuck?)**
13. How long has this been in doing/todo? If >3 weeks, something's wrong.
14. What would it take to move this?
15. Should I abandon this, or commit to it?

### Architecture

```
User opens node
  ↓
Rule selector: "which question applies?" (pure Python, instant)
  ↓
Small local model (3-8B): "elaborate on that question warmly" (2-3 sentences)
  ↓
User sees one focused question, thinks, acts
```

No back-and-forth needed. One question is enough.

---

## Next steps

1. **Build the daily briefing** as a rule-based + embeddings system
2. **Keep inner voice for the cloud** (Claude API, per-node, interactive)
3. **Test the heuristics** on the actual vault to refine thresholds
4. **Integrate into pfq** as a `--briefing` flag (runs nightly via cron, shown at startup)

This keeps you out of the "AI hype" while still getting useful insights — and the cloud API spend is minimal (small prompts, infrequent).

---

## Files referenced

- `inner_voice.md` — original companion design (assumes cloud backend)
- `daily_planner.md` — batch briefing design (tried local Ollama, needs rethinking)
- `inner_voice_local.md` — this file

## Open questions

- Should the daily briefing be automatically shown at startup, or accessible via keypress (`b`)?
- How many days back should "stale" be defined as? (currently assumed 2 weeks, ~14 days)
- Should the briefing be regenerated daily, or cached if already generated today?
