INFERRED_STATE_STYLES: dict[str, str] = {
    "done":      "#7ec87f",  # soft green
    "discarded": "#555555",  # dark grey
    "overdue":   "#c47a7a",  # dusty rose
    "forgotten": "#9b8a3a",  # dark yellow
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
    "pulse": {
        "label": "Pulse",
        "kind": "pulse",   # UpdateModal: opened_at + update_period
        "attr": None,
    },
    "target": {
        "label": "Target",
        "kind": "target",  # lifecycle modal (piece 2); WhenModal for now
        "attr": None,
    },
}
