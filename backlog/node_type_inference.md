# Node Type Inference from Description Typography

Date: 2026-04-27

## Idea

Infer the semantic type of a node from lightweight typography markers in its description.
No new field, no friction — the description itself carries the type signal.
The UI gives instant visual feedback (chip or color) as the user types, nudging toward
consistent conventions. The LLM (inner voice) receives a clean, reliable type without guessing.

## Marker vocabulary

| Marker | Type | Posture | Example |
|---|---|---|---|
| ends `?` | question | open, needs an answer | `go no go ?` |
| ends `...` | thought | vague, not yet formed | `think...` |
| `!` prefix or suffix | constraint | boundary, rule, to avoid | `! no cloud sync` |
| `!!` | blocker | hard stop, urgent | `!! waiting for client approval` |
| `*` prefix | focus | deliberately chosen as current | `* finish radio build` |
| `-->` prefix | next action | explicit outward push | `--> call the fablab` |
| `<--` prefix | waiting | inbound, blocked on external event | `<-- delivery matos` |
| `+` prefix | idea / candidate | proposed, not committed | `+ try oil on wood panel` |
| `#tag` | label | cross-cutting, filter only | (no inner voice routing) |
| verb-first, no marker | doable | default task | `Buy good paint` |
| noun-first, no marker | area | goal / container node | `Wood working` |

Verb detection: first word in a known list (Buy, Make, Find, Get, Go, Build, Ask, Learn,
Test, Fix, Try, Use, Start, Continue, Do, Look, Run, Setup, Create, Draw, ...).
Verb/noun detection is a fallback — explicit markers take precedence.

- `$` to buy/budget
- `%`, `))`, `((`, `& desc`, `| pipe`, `/>  <]  <= )<  `, `(<  >] -] desc   ::    ::: `

## UI feedback

- Chip or subtle color change appears inline as the user types in `EditModal`
- No confirmation needed — purely informational nudge
- If the inferred type looks wrong, the user adjusts the description naturally
- Encourages maintaining clean, meaningful descriptions as a side effect

## Value for inner voice

Node type routes `select_question()` directly instead of guessing from structure:

- `question` → "is this answered or quietly abandoned?"
- `thought` → "is this worth keeping? where does it belong?"
- `waiting` (`<--`) → "how long? is there a follow-up action to unstick this?"
- `blocker` (`!!`) → immediate attention, not a gentle nudge
- `focus` (`*`) → "is this still the priority?"
- `doable` → decomposition questions (can you finish this in one session?)
- `area` → "can you name one concrete action under this?"

See `backlog/inner_voice_local.md` for the full question bank and selector architecture.

## Related ideas (from backlog/ideas.md and discussion)

**Prioritization / opportunity cost** — surfacing "what should I work on now?" including
background tasks (not abandoned, just not active) and A-vs-B binary comparisons.
Node type (`*` focus, `-->` next action) is part of this answer.

**Alternative / horizontal links** — a new `alt_links.yaml` for lateral relationships
between nodes at the same level. Subtypes: `or` (pick one satisfies the goal),
`nor` / exclusive (must pick exactly one, they're incompatible), `and` (default, both).
Start with a single `alt` link type and let the description carry the subtype semantics.
A node with 2+ `alt` links could auto-infer `type: decision` without any marker.

**Work mode** (`high focus`, `physical`, `people`) — session-level context, set once
when sitting down. Used to filter which nodes the inner voice surfaces, not as a
per-node field. Orthogonal to node type, easy to add later.

**Inner voice local retry** — now that node type is explicit and clean, the
rule-based `select_question()` selector becomes more precise. The small local model
only needs to elaborate warmly (~50 tokens of context), never sees the graph.
Worth retrying with a better 3B+ model. See `backlog/inner_voice_local.md`.

## Open questions

- Which description field does the chip appear in — just the description cell, or also
  the `EditModal` live as you type?
- Should `verb-first` detection use a hardcoded list or a small POS tagger?
- Double markers (`!!`, `**`) — keep `!!` for blocker, drop `**` (no clear semantic gap)?
- `-->` next action vs `*` focus: collapse into one marker, or keep the
  intentional/structural distinction?
