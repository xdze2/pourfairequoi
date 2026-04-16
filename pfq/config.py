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
