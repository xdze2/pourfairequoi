# Allowed fields in display order.
# "str" = single value field, "list" = list of items.
FIELDS: dict[str, str] = {
    "description": "str",
    "status": "str",
    "start_date": "str",
    "why": "list",
    "need": "list",
    "how": "list",
    "but": "list",
    "or": "list",
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

STATUSES: list[str] = [
    "todo",
    "active",
    "stuck",
    "done",
    "abandoned",
]
