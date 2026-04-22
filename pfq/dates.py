"""Date formatting with logarithmic precision.

Closer dates get day-level precision; further dates drop to week, month, or year.
All functions take explicit `today` so they are pure and testable.
"""
from __future__ import annotations

from datetime import date


def format_date(d: date, today: date) -> str:
    """Format a date as a short human string relative to today.

    Future:
      today          → "today"
      +1d            → "tomorrow"
      +2–6d          → "fri"
      +7–13d         → "fri 18"
      +14d–2mo       → "may 14"
      +2mo–12mo      → "jun."
      +12mo+         → "jun. 2027"

    Past:
      today          → "today"
      -1d            → "yesterday"
      -2–6d          → "3d ago"
      -7–27d         → "2w ago"
      -28d–3mo       → "6w ago"
      -3mo–12mo      → "apr."
      -12mo+         → "apr. 2025"
    """
    delta = (d - today).days

    if delta == 0:
        return "today"

    if delta > 0:
        return _format_future(d, delta)
    else:
        return _format_past(d, -delta)


def _format_future(d: date, days: int) -> str:
    if days == 1:
        return "tomorrow"
    if days < 7:
        return d.strftime("%a").lower()           # "fri"
    if days < 14:
        return d.strftime("%a %-d").lower()       # "fri 18"
    if days < 60:
        return d.strftime("%b %-d").lower()       # "may 14"
    if days < 365:
        return d.strftime("%b.").lower()          # "jun."
    return d.strftime("%b. %Y").lower()           # "jun. 2027"


def _format_past(d: date, days: int) -> str:
    if days == 1:
        return "yesterday"
    if days < 7:
        return f"{days}d ago"                     # "3d ago"
    if days < 28:
        return f"{days // 7}w ago"               # "2w ago"
    if days < 90:
        return f"{days // 7}w ago"               # "6w ago"
    if days < 365:
        return d.strftime("%b.").lower()          # "apr."
    return d.strftime("%b. %Y").lower()           # "apr. 2025"
