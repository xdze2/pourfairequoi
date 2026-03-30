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
}

STATUSES: list[str] = [
    "todo",
    "active",
    "stuck",
    "done",
    "abandoned",
]
