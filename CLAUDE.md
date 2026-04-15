# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
pip install -e .          # install in editable mode (do this once)
pfq                       # launch the TUI
python screenshot.py      # capture SVG screenshots of the TUI
```

No test suite or linter is configured.

## Architecture

### Core concept
Nodes form a DAG. `how:` links are stored in the parent (parent declares its children).
`why` is always **derived** by scanning the store — never stored. This eliminates consistency bugs.



### Module roles

| File | Role |
|---|---|
| `pfq/model.py` | `Store` class + pure data helpers |
| `pfq/config.py` | Constants: `FIELDS`, `STATUSES`, `TYPES`, `HORIZONS`, `CONSTRAIN_TYPES` |
| `pfq/app.py` | Full Textual TUI |
| `pfq/__main__.py` | Click CLI (`pfq new`, `pfq open`, `pfq migrate`, `pfq clean`) |
