"""Date formatting and parsing with logarithmic precision.

Closer dates get day-level precision; further dates drop to week, month, or year.
All functions take explicit `today` so they are pure and testable.
"""
from __future__ import annotations

import re
from datetime import date, timedelta
from typing import Optional

_MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}
_DAYS = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}


def parse_date(text: str, today: date) -> Optional[date]:
    """Parse a short human date string into a date, symmetric with format_date.

    Accepts (case-insensitive):
      ISO:        2026-06-01
      Named:      today, tomorrow, yesterday
      Relative:   3d, 2w, 1m, 1y          (future)
                  3d ago, 2w ago, 1m ago  (past)
      Numeric:    12-04, 12-04-2026       (DD-MM or DD-MM-YYYY)
      Weekday:    fri, sat                 (closest occurrence)
      Weekday+n:  fri 18, thu 30          (closest matching weekday+day)
      Month+n:    may 14, jun 21          (closest matching month+day)
      Month.:     jun., apr.              (closest first-of-month)
      Month. yr:  jun. 2027, apr. 2025
    Returns None if unrecognised.
    """
    t = text.strip().lower()
    if not t:
        return None

    # ISO
    try:
        return date.fromisoformat(t)
    except ValueError:
        pass

    # DD-MM-YYYY
    m = re.fullmatch(r"(\d{1,2})-(\d{1,2})-(\d{4})", t)
    if m:
        try:
            return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        except ValueError:
            return None

    # DD-MM  →  closest occurrence (past or future)
    m = re.fullmatch(r"(\d{1,2})-(\d{1,2})", t)
    if m:
        day, month = int(m.group(1)), int(m.group(2))
        candidates = []
        for year in (today.year - 1, today.year, today.year + 1):
            try:
                candidates.append(date(year, month, day))
            except ValueError:
                pass
        return _closest(candidates, today) if candidates else None

    # Named
    if t == "today":
        return today
    if t == "tomorrow":
        return today + timedelta(days=1)
    if t == "yesterday":
        return today + timedelta(days=-1)

    # Relative future: 3d / 2w / 2wk / 1m / 1y
    m = re.fullmatch(r"(\d+)\s*(d|wk|w|mo|m|y)", t)
    if m:
        n, unit = int(m.group(1)), m.group(2)
        if unit == "d":
            return today + timedelta(days=n)
        if unit in ("w", "wk"):
            return today + timedelta(weeks=n)
        if unit in ("m", "mo"):
            month = today.month + n
            year = today.year + (month - 1) // 12
            month = (month - 1) % 12 + 1
            day = min(today.day, _month_days(year, month))
            return date(year, month, day)
        if unit == "y":
            return date(today.year + n, today.month, today.day)

    # Relative future explicit: in 2w / in 2wk / in 3m / in 1y
    m = re.fullmatch(r"in\s+(\d+)\s*(d|wk|w|mo|m|y)", t)
    if m:
        n, unit = int(m.group(1)), m.group(2)
        if unit == "d":
            return today + timedelta(days=n)
        if unit in ("w", "wk"):
            return today + timedelta(weeks=n)
        if unit in ("m", "mo"):
            month = today.month + n
            year = today.year + (month - 1) // 12
            month = (month - 1) % 12 + 1
            day = min(today.day, _month_days(year, month))
            return date(year, month, day)
        if unit == "y":
            return date(today.year + n, today.month, today.day)

    # Relative past: 3d ago / 2w ago / 2wk ago / 1m ago / 1y ago
    m = re.fullmatch(r"(\d+)\s*(d|wk|w|mo|m|y)\s+ago", t)
    if m:
        n, unit = int(m.group(1)), m.group(2)
        if unit == "d":
            return today - timedelta(days=n)
        if unit in ("w", "wk"):
            return today - timedelta(weeks=n)
        if unit in ("m", "mo"):
            total = today.year * 12 + (today.month - 1) - n
            year, month = divmod(total, 12)
            month += 1
            day = min(today.day, _month_days(year, month))
            return date(year, month, day)
        if unit == "y":
            return date(today.year - n, today.month, today.day)

    # Weekday only: "fri" → closest occurrence (past or future)
    if t in _DAYS:
        target_dow = _DAYS[t]
        delta = (target_dow - today.weekday()) % 7
        past = today - timedelta(days=(today.weekday() - target_dow) % 7 or 7)
        future = today + timedelta(days=delta or 7)
        return _closest([past, future], today)

    # Weekday + day: "fri 18" → closest date with that weekday and day
    m = re.fullmatch(r"([a-z]{3})\s+(\d{1,2})", t)
    if m and m.group(1) in _DAYS:
        dow, day = _DAYS[m.group(1)], int(m.group(2))
        candidates = []
        for delta_months in range(-12, 13):
            total = today.year * 12 + (today.month - 1) + delta_months
            year, month = divmod(total, 12)
            month += 1
            try:
                candidate = date(year, month, day)
            except ValueError:
                continue
            if candidate.weekday() == dow:
                candidates.append(candidate)
        return _closest(candidates, today) if candidates else None

    # Month + day: "may 14" → closest occurrence (past or future)
    m = re.fullmatch(r"([a-z]{3})\.?\s+(\d{1,2})", t)
    if m and m.group(1) in _MONTHS:
        month, day = _MONTHS[m.group(1)], int(m.group(2))
        candidates = []
        for year in (today.year - 1, today.year, today.year + 1):
            try:
                candidates.append(date(year, month, day))
            except ValueError:
                pass
        return _closest(candidates, today) if candidates else None

    # Month. only: "jun." → closest first-of-month (past or future)
    m = re.fullmatch(r"([a-z]{3})\.", t)
    if m and m.group(1) in _MONTHS:
        month = _MONTHS[m.group(1)]
        candidates = [date(y, month, 1) for y in (today.year - 1, today.year, today.year + 1)]
        return _closest(candidates, today)

    # Month. year: "jun. 2027"
    m = re.fullmatch(r"([a-z]{3})\.\s+(\d{4})", t)
    if m and m.group(1) in _MONTHS:
        return date(int(m.group(2)), _MONTHS[m.group(1)], 1)

    return None


def _closest(candidates: list[date], today: date) -> date:
    """Return the date closest to today; break ties in favour of the future."""
    return min(candidates, key=lambda d: (abs((d - today).days), d < today))


def _month_days(year: int, month: int) -> int:
    """Return the number of days in a given month."""
    if month == 12:
        return (date(year + 1, 1, 1) - date(year, 12, 1)).days
    return (date(year, month + 1, 1) - date(year, month, 1)).days


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
