# Timeline widget — brainstorm

## Concept

A logarithmic, "now-centered" time axis rendered as a single row per node in the home view.
Inspired by `btop` (braille/block glyphs for intensity) and GitHub contribution calendar (color heatmap).

```
<-  past    now   future  ->
Y  Q  M  W  D  t  D  W  M  Q  Y
·  ·  ▄  █  █  |               Wood working    (green gradient, | = deadline)
            █                  Grocery store   (single bright cell ≈ now)
·  ·                           Learning Python (dim past, no deadline)
                  |            Next holidays   (deadline only)
```

## Axis definition

Symmetric log scale centered on today (`t`):

| label | future range     | past range       |
|-------|-----------------|-----------------|
| `t`   | today           | today           |
| `D`   | +1d → +3d       | -1d → -3d       |
| `W`   | +4d → +16d      | -4d → -16d      |
| `M`   | +17d → +40d     | -17d → -40d     |
| `Q`   | +41d → +90d     | -41d → -90d     |
| `Y`   | +91d → ∞        | -91d → -∞       |

Boundaries are arbitrary and should be tuned by feel after first implementation.

## What each column encodes

**Past columns** — activity heatmap:
- count closes that happened in this time bucket
- compare to expected count: `bucket_width / update_period`
- ratio → glyph/color intensity

| ratio        | glyph | color   |
|-------------|-------|---------|
| 0 (nothing) | `·`   | dim     |
| < expected  | `▄`   | yellow? |
| ≈ expected  | `█`   | green   |
| > expected  | `█`   | bright  |

**Future columns** — intent markers:
- `|` at `estimated_closing_date` bucket (hard deadline)
- dim expected-pace markers? (TBD)
- empty otherwise

## Signals used

| signal            | source              | role in widget                  |
|------------------|--------------------|---------------------------------|
| close events      | closed descendants  | past heatmap intensity          |
| `update_period`   | user input          | expected rate for ratio compute |
| `estimated_closing_date` | user input | `|` marker in future half      |
| `opened_at`       | user input          | left boundary of span           |

## Open questions

- Binary (any close?) vs ratio (closes / expected) per bucket — start with binary?
- What to show when `update_period` is null — only the deadline marker, or hide the row?
- Color scheme: green/yellow/red, or just intensity (dim → bright)?
- Width: 11 chars (`YQMWDtDWMQY`) feels right but needs testing in actual terminal widths
- Future half: show expected-pace as dim marks, or keep it clean (deadline only)?
