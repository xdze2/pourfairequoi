# Interface

<!-- The interface is a user-facing contract: any correct implementation must
     reproduce this behavior and appearance to feel like the same tool.
     The user loop is: observe → act → observe. Layout, states, and transitions
     are documented together because they are two sides of the same thing. -->

## Principles

<!-- Core rules governing both appearance and interaction.
     E.g: keyboard-only, information density, no mouse required. -->

- ...

## Layout

<!-- Overall screen structure: what regions exist, where, how they relate.
     ASCII diagram is enough. -->

```
+----------------------------------+
|                                  |
|                                  |
+----------------------------------+
```

## States

<!-- The app is always in exactly one state.
     Each state has a specific screen appearance.
     Describe what the user sees in each state. -->

### State: ...

<!-- What is visible, what is focused, what is the main element. -->

#### Columns / elements

| Element | Content | Notes |
|---|---|---|
| ... | ... | ... |

#### Row / item appearance

| Role | Visual treatment |
|---|---|
| ... | ... |

### State: ...

## Transitions

<!-- Key → action → new state.
     The full observe→act→observe loop, per state.
     Be explicit about edge cases. -->

### From state: ...

| Key | Action | New state | Edge cases |
|---|---|---|---|
| ... | ... | ... | ... |

### From state: ...

## Modals

<!-- Overlays that interrupt the main state machine.
     Entry, appearance, input handling, confirm vs cancel outcome. -->

### Modal: ...

**Opened by:** ...  
**Appearance:** ...  
**On confirm:** ...  
**On cancel:** ...  

## Glyphs & symbols

| Symbol | Meaning |
|---|---|
| ... | ... |

## Color roles

<!-- Named by role, not hex — implementation decides exact shades. -->

| Role | Used for |
|---|---|
| ... | ... |
