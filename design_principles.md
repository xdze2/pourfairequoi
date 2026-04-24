# Design principles

Four values that guide pfq's UI/UX decisions. Each one vetoes a class of bad ideas.

---

## Reversibility

Every action can be undone or corrected. Destructive operations ask for confirmation. Structural changes (link, unlink) are always reversible — the graph never traps you.

*Vetoes: silent deletes, irreversible bulk operations.*

---

## Consistency

Same key, same effect, everywhere. Same structure, same visual output. Muscle memory is the UX — a key that behaves differently depending on context is a bug.

*Vetoes: context-dependent key rebinding, special cases per view.*

---

## Signal / noise

Every pixel earns its place. No decorative chrome. Information density follows Tufte: if it's visible, it's meaningful.

The Footer is the complete action contract — every available action appears there, nothing more. This resolves discoverability without adding noise: no hidden actions, no help page needed.

*Vetoes: decorative UI, tooltips for things already in the Footer, hidden power-user shortcuts.*

---

## Locality

Actions operate on what's visible, at cursor. The context is the view — you never navigate away to a settings panel or fill a form disconnected from the node you're acting on.

*Vetoes: modal wizards, multi-step flows, settings screens.*

---

## Low friction, high reward

The table is cell-based: `e` edits whatever cell the cursor is on. Every editable concept maps to a column — even computed ones like `state`. This keeps the interaction model uniform (no special keys per field) and makes closing a node feel like a first-class action, not a side-effect of a status dropdown.

Closing is the rewarding part of a task manager. It should be: one keypress to reach, one keypress to confirm, optional note on the way out. Never a form.

*Vetoes: dedicated shortcut keys per field, close buried inside an edit form, required fields on close.*
