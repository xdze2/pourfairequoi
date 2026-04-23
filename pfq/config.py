INFERRED_STATE_STYLES: dict[str, str] = {
    "done":      "#7ec87f",  # soft green
    "discarded": "#555555",  # dark grey
    "overdue":   "#c47a7a",  # dusty rose
    "forgotten": "#8a8a8a",  # grey
    "slowing":   "#c4b870",  # muted gold
    "active":    "#7ab8d4",  # dusty blue
}

STATUS_GLYPHS: dict[str, str] = {
    "active":    "▸",
    "forgotten": "·",
    "overdue":   "!",
    "done":      "✓",
    "discarded": "✗",
}

# Keyed by DataTable column key.
FIELDS: dict[str, dict] = {
    "desc": {
        "label": "Description",
        "kind": "text",
        "attr": "description",
    },
    "comment": {
        "label": "Comment",
        "kind": "textarea",
        "attr": "comment",
    },
    "status": {
        "label": "State",
        "kind": "state",
        "attr": None,   # handled by StateModal, not a single attr
    },
    "when": {
        "label": "When",
        "kind": "when",
        "attr": None,   # handled by WhenModal, not a single attr
    },
}
