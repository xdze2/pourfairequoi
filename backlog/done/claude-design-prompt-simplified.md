# Mobile App Wireframe Prompt for Claude Design

## Product Overview

**PourFaireQuoi (pfq)** is a task manager for on-the-go task capture and hierarchy exploration.

Core idea: Every task decomposes into steps. Navigate downward to see "how to do it."

Users use it to:
- Capture a new task quickly
- See what subtasks/steps a goal breaks down into
- Drill deeper into a step to see its own subtasks
- Update task status (open, done, discarded)

## The Mobile View: Downward Tree Navigation

See attached sketch. The interaction model is simple:

1. **Selected Node** (top): The current task you're looking at
2. **Child Nodes Below**: All direct children (next level down)
3. **Grandchild Nodes** (indented further): One level deeper, shown when a child is expanded

**Interaction:**
- Tap a child node → it becomes the selected node (drill down)
- Visual connection (arrow) shows the hierarchy relationship
- Swipe/back button to go back up (pop to parent)

## Design Requirements

### Visual Hierarchy

The sketch shows the concept:
- **Selected Node** = full width, prominent (at top of screen)
- **Child Nodes** = stacked below, same width
- **Grandchild Nodes** = indented, showing they belong to their parent child

All nodes should be **card-like** or **button-like** — tappable, with clear visual bounds.

### Information Per Node

Each node card should show:
- **Title** (primary)
- **Status indicator** (open / done / discarded) — small icon or color indicator
- due date if set (e.g., "→ 2 weeks" or "✓ done")
- pulse status (forgotten, late, active)




### Tone

- Minimal, clean interface
- Focus on the task title (primary information)
- Status/date are secondary (smaller, muted)
- Clear visual hierarchy (selected node is most prominent)

### Example Scenario

User opens app at "Practice chords" (selected node):

```
  ╭──@ Learn guitar
  ├──@ keep a creative practice
▶ Practice chords
  ├──○ Find tutorials online   (done)
  ├── Learn a first song
  │   ├──○ Pick a simple song
  │   ╰──○ Play it slowly first
  ╰──○ 1h friday morning
```
