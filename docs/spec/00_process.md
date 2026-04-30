# Spec Process

<!-- How this spec directory works: conventions, workflow, and guidelines
     for both human contributors and AI tools working with these documents. -->

## Purpose of this directory

<!-- What these documents are for, who reads them, what decisions they drive. -->

## Document map

<!-- How the four files relate to each other.
     Reading order, dependency order (vision → stories → requirements → constraints). -->

| File | Question answered | Audience |
|---|---|---|
| `vision.md` | Why does this exist? | Anyone |
| `user-stories.md` | What does a user want to do? | Designer, implementer |
| `requirements.md` | What must the system do? | Implementer, tester |
| `constraints.md` | What must never change? | Implementer, porter |

## Writing style

<!-- Style choices made and why. -->

### General rules

- ...

### Per-document style

| File | Style |
|---|---|
| `vision.md` | Prose narrative |
| `user-stories.md` | ... |
| `requirements.md` | ... |
| `constraints.md` | ... |

### Vocabulary

<!-- Canonical terms used across all documents. Using the wrong word is a spec bug. -->

| Term | Meaning | Do not use |
|---|---|---|
| ... | ... | ... |

## Workflow

### Adding a feature

<!-- Step-by-step: where to write first, how changes propagate across files. -->

1. Start with a user story in `user-stories.md`
2. ...

### Changing or removing a feature

<!-- How to update consistently, what to check for conflicts. -->

### Resolving conflicts between documents

<!-- What to do when requirements and constraints contradict each other,
     or when a story has no matching requirement. -->

## Definition of done

<!-- What "complete" looks like for a spec section.
     Prevents half-written sections from being treated as final. -->

A spec section is done when:
- [ ] ...
- [ ] ...

## Instructions for AI tools

<!-- Explicit guidance so an AI assistant interprets and extends
     these documents consistently without inventing conventions. -->

- Always follow the writing style defined above — do not switch styles between sections
- When filling a section, derive content from higher-level documents (vision → stories → requirements)
- Flag ambiguity explicitly rather than resolving it silently
- Never add requirements that contradict `constraints.md`
- When in doubt about vocabulary, refer to the terms table above
- ...
