# Maps status value → Rich color string. Keys are matched case-insensitively.
# Add or override values here to customize the palette.
STATUS_STYLES: dict[str, str] = {
    "done":     "#7ec87f",  # soft green
    "active":   "#7ab8d4",  # dusty blue
    "doable":   "#85c4a0",  # sage
    "todo":     "#c4b870",  # muted gold
    "blocked":  "#c47a7a",  # dusty rose
    "explore":  "#a98fc4",  # soft purple
    "on hold":  "#8a8a8a",  # grey
    "stuck":    "#c49a7a",  # warm terracotta
}

NODE_TYPES = [
    "goal",
    "project",
    "task",
    "event",
    "question",
    "decision",
    "milestone",
    "constraint",
]

# Keyed by DataTable column key.
# kind: "text" → Input widget, "select" → Select widget (auto-dismiss on change)
# attr: Node field name to read/write
FIELDS: dict[str, dict] = {
    "desc": {
        "label": "Description",
        "kind": "text",
        "attr": "description",
    },
    "type": {
        "label": "Type",
        "kind": "select",
        "attr": "type",
        "options": NODE_TYPES,
    },
    "status": {
        "label": "Status",
        "kind": "text",
        "attr": "status",
    },
}
