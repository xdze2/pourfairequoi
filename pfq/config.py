from __future__ import annotations
from dataclasses import dataclass


# Scalar / text fields (displayed as rows in the task pane)
# "str"  = single-line value
# "text" = multiline free-form text
FIELDS: dict[str, str] = {
    "description": "str",
    "type": "str",
    "status": "str",
    "horizon": "str",
    "start_date": "str",
    "due_date": "str",
    "notes": "text",
    "conclusion": "text",
}


# Lateral link types (stored in constrain: section)
@dataclass
class ConstrainType:
    name: str
    label: str
    sort_order: int


CONSTRAIN_TYPES: list[ConstrainType] = [
    ConstrainType("but", "but", 0),
    ConstrainType("alternative_to", "alternative to", 1),
]

CONSTRAIN_TYPE_MAP: dict[str, ConstrainType] = {ct.name: ct for ct in CONSTRAIN_TYPES}


# status → (label, rich style)
STATUSES: dict[str, tuple[str, str]] = {
    "explore": ("explore", "dim magenta"),
    "todo": ("todo", "bold yellow"),
    "doable": ("doable", "dim yellow"),
    "active": ("active", "bold green"),
    "stuck": ("stuck", "bold red"),
    "done": ("done", "green"),
    "discarded": ("discarded", "dim red"),
}

# type → (label, rich style)
TYPES: dict[str, tuple[str, str]] = {
    "goal": ("goal", "bold cyan"),
    "project": ("project", "cyan"),
    "task": ("task", "white"),
    "event": ("event", "blue"),
    "decision": ("decision", "bold magenta"),
    "milestone": ("milestone", "bold white"),
    "constraint": ("constraint", "bold magenta"),
}

# horizon → (label, rich style)
HORIZONS: dict[str, tuple[str, str]] = {
    "day": ("day", "dim"),
    "week": ("week", "dim"),
    "month": ("month", "white"),
    "year": ("year", "cyan"),
    "vision": ("vision", "bold cyan"),
}
