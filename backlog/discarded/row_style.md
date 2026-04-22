# Row highlight — exploration notes

## Goal

In the DataTable (cursor_type="cell"), highlight:
- **entire selected row** with a dark background
- **cursor cell** with a brighter background

## What we tried

### 1. Pure CSS via `datatable--highlight` — did not work

Assumed `datatable--highlight` was applied to the cursor row. It is not.
Textual's `_should_highlight()` for `cursor_type="cell"` returns True only for the
exact cursor cell. `datatable--highlight` is mouse hover only. No built-in
"cursor row" CSS class exists for keyboard navigation in cell mode.

### 2. `update_cell` with `t.style = "on <color>"` — partially works

We store base cell content in `_base_cells` and listen to `on_data_table_cell_highlighted`.
On each cursor move, non-cursor cells in the current row are updated via `update_cell`
with `_with_bg(cell, row_bg)` which sets `t.style = "on #..."`.

**Result**: background appears, but only behind the text characters, not the full cell width.
The padding area (empty space filling the column width) stays uncolored.

## Root cause of remaining issue

Rich `Text.style` sets the base style for rendered characters.
The DataTable renders each cell as a fixed-width segment — but the *padding* is added by
Textual's cell rendering pipeline, not by the Rich Text object. The padding inherits
from the DataTable's own background, not from the Text's style.

## Possible paths forward

- **Override `_render_cell`** in a DataTable subclass to inject row-level background
  at the Textual rendering level (before padding is applied). Fragile, touches internals.

- **Override `render_line`** similarly — even more internal.

- **Use `cursor_type="row"`** for row highlight, track cursor column manually,
  update the cursor cell separately. Loses native left/right column navigation.

- **Set background on the DataTable widget itself** when a row is selected and
  clip/mask per-row — probably not feasible in Textual's layout model.

- **Wait for Textual upstream**: a future version may expose a proper "cursor row"
  component class for cell cursor mode.

## Current state of the code

`_with_bg`, `_base_cells`, `on_data_table_cell_highlighted`, `_update_row_cells` are
all in place and wired up correctly. The partial highlight (text-only) is visible.
Only the padding fill is missing.

Reverting the highlight code is straightforward — remove `_with_bg`, `_base_cells`,
`_prev_coord`, `on_data_table_cell_highlighted`, and `_update_row_cells`.
