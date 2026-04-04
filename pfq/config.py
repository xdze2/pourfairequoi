# Allowed fields in display order.
# "str"  = single-line value
# "text" = multiline free-form text
# "list" = list of items
FIELDS: dict[str, str] = {
    "description": "str",
    "type":        "str",
    "status":      "str",
    "start_date":  "str",
    "due_date":    "str",
    "notes":       "text",
    "why":         "list",
    "need":        "list",
    "how":         "list",
    "but":         "list",
    "or":          "list",
    "required_by": "list",
}

# Bidirectional inverse pairs — when linking B from field F of A,
# a backlink is automatically added to B's INVERSE_FIELDS[F].
INVERSE_FIELDS: dict[str, str] = {
    "how":         "why",
    "why":         "how",
    "need":        "required_by",
    "required_by": "need",
}

# status → (label, rich style)
STATUSES: dict[str, tuple[str, str]] = {
    "todo":      ("todo",      "dim"),
    "active":    ("active",    "bold green"),
    "stuck":     ("stuck",     "bold yellow"),
    "done":      ("done",      "green"),
    "discarded": ("discarded", "dim red"),
}

# type → (label, rich style)
TYPES: dict[str, tuple[str, str]] = {
    "goal":       ("goal",       "bold cyan"),
    "task":       ("task",       "white"),
    "constraint": ("constraint", "bold magenta"),
}
