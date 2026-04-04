from __future__ import annotations
from dataclasses import dataclass


# Scalar / text fields (displayed as rows in the task pane)
# "str"  = single-line value
# "text" = multiline free-form text
FIELDS: dict[str, str] = {
    "description": "str",
    "type":        "str",
    "status":      "str",
    "start_date":  "str",
    "due_date":    "str",
    "notes":       "text",
}


@dataclass
class LinkType:
    name: str
    backlink: str | None   # name of inverse link type, or None
    direction: str         # "up" | "down" | "lateral"
    label: str             # display label in UI
    sort_order: int        # display order in the links section (lower = first)


LINK_TYPES: list[LinkType] = [
    LinkType("why",            "how",            "up",      "why",           -2),
    LinkType("how",            "why",            "down",    "how",            2),
    LinkType("need",           "required_by",    "down",    "need",           1),
    LinkType("required_by",    "need",           "up",      "required by",   -1),
    LinkType("but",            None,             "lateral", "but",            0),
    LinkType("alternative_to", "alternative_to", "lateral", "alternative to", 0),
]

LINK_TYPE_MAP: dict[str, LinkType] = {lt.name: lt for lt in LINK_TYPES}


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
