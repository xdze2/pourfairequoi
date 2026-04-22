# IA Inner Voice — Design Notes

## Concept

A companion integrated into pfq that speaks when you open a node view. Not a chatbot, not a separate agent — an **inner voice**: a part of you that notices things you're too close to see.

It starts the conversation. You can engage or simply navigate away (implicit discard — no "ignore" button needed).

---

## Philosophy

- **The graph is the memory.** No session memory, no history. Each node view = a fresh encounter. The companion reads the local neighborhood and reacts to *that*. Every edit you make *is* your response — the structure remembers, not the companion.
- **Mirror, not character.** The companion has no fixed persona or name. Its tone emerges from what it sees in the graph.
- **Action over chat.** The goal is always to move: edit a node, change a status, restructure a link. The companion nudges toward that.

---

## Tone — driven by graph state

| Signal | Tone |
|---|---|
| Node is `stuck` | warm, encouraging — "what's blocking this?" |
| Node is `doing` with no recent change | gentle itch — "still in progress?" |
| Leaf with no clear parent purpose | curious — "what's this for?" |
| Root with no actionable leaves | generative — "how do we make this concrete?" |
| Node appears under two roots pulling in opposite directions | playful tension — "you put this in two worlds" |
| Graph looks healthy | light, expansive — wild ideas, reframings |

---

## Interaction pattern

1. Companion speaks first: one **observation** + one **open question**
2. User sees 2–4 choices (short, actionable)
3. User picks one → companion responds, possibly with a concrete action proposal
4. User navigates away at any point = implicit discard

```
┌─────────────────────────────────────────────┐
│  @ My career transition              active  │
│    ├── retrain as developer                  │
│    │   ├──○ finish Python course      doing  │
│    │   ╰──○ build a portfolio         todo   │
│    ╰── explore freelance                     │
│        ╰──○ talk to 3 freelancers    todo    │
│                                              │
├─────────────────────────────────────────────┤
│ "retrain" and "freelance" are both alive     │
│ under the same root. Intentional tension,    │
│ or unresolved choice?                        │
│                                              │
│  A) I'm keeping options open                 │
│  B) Tell me more about the tension           │
│  C) Help me pick one                         │
└─────────────────────────────────────────────┘
```

---

## Caching

Input is deterministic: `node_id + local graph snapshot → cache key`.
Same node + same neighborhood = same companion response.
Invalidate when the node or any neighbor is edited.

This avoids recomputing on every navigation and keeps latency low.

---

## Demo Prompt

### How to generate the graph view to inject

Use the existing `NodeGraph` API to build the context string:

```python
from pfq.disk_io import load_vault
from pfq.model import NodeGraph

def build_companion_context(graph: NodeGraph, node_id: str) -> str:
    node = graph.get_node(node_id)
    parents = list(reversed(graph.get_parents_tree(node_id, max_depth=2)))
    children = graph.get_childrens_tree(node_id, max_depth=2)

    lines = []

    for n, depth in parents:
        indent = "  " * depth
        lines.append(f"{indent}{'@ ' if not graph.get_parent_ids(n.node_id) else ''}{n.description}  [{n.status}]")

    lines.append(f"▶ {node.description}  [{node.status}]")

    for n, depth in children:
        indent = "  " * (depth + 1)
        role = "○" if not graph.get_children_ids(n.node_id) else "<"
        lines.append(f"{indent}──{role} {n.description}  [{n.status}]")

    return "\n".join(lines)
```

### System prompt

```
You are the inner voice of someone navigating their personal knowledge graph.
The graph is a DAG of nodes: roots are motivations, leaves are actions, middle nodes are structure.

Your role: notice what the user might be too close to see, and gently surface it.

Rules:
- Read the node view carefully: structure, statuses, positions.
- Write ONE short observation (1-2 sentences max). Be specific — refer to actual node names.
- Ask ONE open question that invites reflection or action.
- Propose 2 to 4 short choices (A, B, C...). At least one should lead toward a concrete edit.
- Never moralize. Never lecture. Stay curious, not critical.
- Tone adapts to graph state (see below).

Tone guide:
- stuck node → warm, "what's in the way?"
- long-running doing → gentle nudge
- leaf with no apparent purpose → curious, "what's this for?"
- root with no leaves → generative, "how do we make this concrete?"
- node under two contradictory roots → playful, "two worlds"
- healthy graph → expansive, offer a wild reframe

Output format (strict):
[observation]
[question]

A) ...
B) ...
C) ...

Current node view:
{graph_view}
```

### Tool integration — letting the companion propose concrete actions

To let the companion do more than talk, expose graph operations as tools (Claude tool use / function calling):

```python
tools = [
    {
        "name": "edit_node",
        "description": "Edit the description or status of a node",
        "input_schema": {
            "type": "object",
            "properties": {
                "node_id": {"type": "string"},
                "field": {"type": "string", "enum": ["description", "status"]},
                "value": {"type": "string"}
            },
            "required": ["node_id", "field", "value"]
        }
    },
    {
        "name": "unlink_nodes",
        "description": "Remove the link between a parent and a child node",
        "input_schema": {
            "type": "object",
            "properties": {
                "parent_id": {"type": "string"},
                "child_id": {"type": "string"}
            },
            "required": ["parent_id", "child_id"]
        }
    },
    {
        "name": "create_child_node",
        "description": "Create a new child node under an existing node",
        "input_schema": {
            "type": "object",
            "properties": {
                "parent_id": {"type": "string"},
                "description": {"type": "string"},
                "status": {"type": "string"}
            },
            "required": ["parent_id", "description"]
        }
    },
    {
        "name": "delete_node",
        "description": "Delete a node (only if it has no children)",
        "input_schema": {
            "type": "object",
            "properties": {
                "node_id": {"type": "string"}
            },
            "required": ["node_id"]
        }
    }
]
```

These map directly to the existing `disk_io.py` API:
- `edit_node` → `save_node_fields(node)`
- `unlink_nodes` → `graph.unlink_child(parent_id, child_id)` + `save_vault(graph)`
- `create_child_node` → `create_node(description, status)` + `graph.link_child(parent_id, child_id)` + `save_vault(graph)`
- `delete_node` → `delete_node_file(node)` + `save_vault(graph)`

The companion can include a tool call in its response. The TUI intercepts it, shows it as a choice ("→ do this"), and executes on confirmation.

---

## Testing workflow (fast path — no code needed)

1. Open a real node in pfq, copy the tree view from the terminal
2. Paste it here with: *"respond as the inner voice"*
3. Evaluate: too aggressive? too soft? wrong focus?
4. Adjust the system prompt, repeat

No integration needed to validate the voice. Build the prompt first, wire it up later.

---

## Implementation

### Backend: Claude CLI first, SDK later

Target audience is developers — they likely have `claude` CLI installed and authenticated already. Zero setup friction vs. asking for an API key and env var.

**v1 — Claude CLI via subprocess:**

```python
import subprocess

def call_companion(prompt: str) -> str:
    result = subprocess.run(
        ["claude", "-p", prompt],
        capture_output=True, text=True, timeout=30
    )
    return result.stdout.strip()
```

**v2 opt-in — Anthropic SDK:**

If `ANTHROPIC_API_KEY` is detected in the environment, switch automatically. This unlocks structured tool use (companion proposing concrete edits via function calling).

```python
import os

def call_companion(prompt: str) -> str:
    if os.environ.get("ANTHROPIC_API_KEY"):
        return _call_via_sdk(prompt)
    return _call_via_cli(prompt)
```

Gracefully disable the companion if neither `claude` CLI nor API key is available.

### Async — never block the TUI

Textual supports background workers. The companion call must be non-blocking:

```python
# in app.py
@work(exclusive=True)
async def fetch_companion(self, node_id: str) -> None:
    context = build_companion_context(self.graph, node_id)
    prompt = SYSTEM_PROMPT.format(graph_view=context)
    response = await asyncio.to_thread(call_companion, prompt)
    self.companion_panel.update(response)
```

Show a subtle `"..."` indicator while waiting. Replace with response on completion.

### Tool use in v1 (CLI path)

The CLI doesn't support structured function calling. Workaround: ask Claude to append a JSON action block when proposing a concrete edit.

Add to the system prompt:
```
If you want to propose a concrete action, append exactly one line at the end:
ACTION: {"op": "edit_node", "node_id": "...", "field": "status", "value": "..."}
```

Parse with a simple regex. Show the action as a labeled choice in the UI ("→ mark as done"). Execute on confirmation — no action taken without user approval.

Supported ops for v1: `edit_node`, `unlink_nodes`, `create_child_node`, `delete_node` (maps to existing `disk_io.py` API).

---

## Open questions

- **Trigger:** automatic on node open, or on keypress (e.g. `?`)? Auto is more NPC-like; keypress is less intrusive.
- **Persona config:** could be a field in `config.py` — e.g. `companion_tone: "direct" | "gentle" | "socratic"`
- **Cache backend:** simple dict in memory per session, or persist to disk (e.g. `.pfq_cache/` in the vault)?
- **CLI availability check:** gracefully disable the companion if `claude` is not found in PATH.
