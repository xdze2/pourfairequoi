# Clarify I/O sync strategy

Out of scope for beta. Keep in mind for future architecture decisions.

## Three strategies

**1. Write-through** (current default)
Every mutation immediately writes to disk. Simple, no divergence possible.
Risk: blocks UI thread, slow on large vaults.

**2. Explicit checkpoint** (save/load on demand)
In-memory graph is the truth during a session. Disk touched only at explicit boundaries (`load_vault` / `save_vault`).
Risk: crash between checkpoints = lost work. Requires a dirty flag + save-on-quit.

**3. Write-behind** (async, periodic flush)
Mutations go to memory immediately, background worker flushes on a timer or when idle. UI never blocks.
Risk: highest complexity — write queue, conflict handling if two sessions share a vault, graceful shutdown to drain queue.

## Current state

Halfway to strategy 2: `save_vault` is already called explicitly after structural mutations, but field edits (`save_node`) are still write-through. The seam is there.

## Notes for the future

- A `YamlVault` object (considered during disk_io refactor) maps cleanly onto strategy 2 or 3: owns the dirty flag, flush timer, write queue.
- Strategy 3 only makes sense paired with a real DB backend (SQLite, etc.) — async + YAML-per-file is fragile.
- For a single-user TUI, strategy 2 with a dirty flag and save-on-quit is the sweet spot if write-through ever becomes a bottleneck.
