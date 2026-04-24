"""Tests for pfq.dates.format_date."""
from datetime import date, timedelta

import pytest

from pfq.dates import format_date

TODAY = date(2026, 4, 23)  # Thursday


def d(days: int) -> date:
    return TODAY + timedelta(days=days)


# ── Future ─────────────────────────────────────────────────────────────────────

def test_today():
    assert format_date(TODAY, TODAY) == "today"

def test_tomorrow():
    assert format_date(d(1), TODAY) == "tomorrow"

def test_future_this_week():
    assert format_date(d(2), TODAY) == "sat"   # Saturday Apr 25
    assert format_date(d(6), TODAY) == "wed"   # Wednesday Apr 29

def test_future_next_week():
    assert format_date(d(7), TODAY) == "thu 30"
    assert format_date(d(13), TODAY) == "wed 6"

def test_future_same_month_ish():
    assert format_date(d(14), TODAY) == "may 7"
    assert format_date(d(30), TODAY) == "may 23"
    assert format_date(d(59), TODAY) == "jun 21"

def test_future_months():
    assert format_date(d(60), TODAY) == "jun."
    assert format_date(d(120), TODAY) == "aug."
    assert format_date(d(364), TODAY) == "apr."

def test_future_next_year():
    assert format_date(d(365), TODAY) == "apr. 2027"
    assert format_date(d(500), TODAY) == "sep. 2027"


# ── Past ───────────────────────────────────────────────────────────────────────

def test_yesterday():
    assert format_date(d(-1), TODAY) == "yesterday"

def test_past_days():
    assert format_date(d(-2), TODAY) == "2d ago"
    assert format_date(d(-6), TODAY) == "6d ago"

def test_past_weeks():
    assert format_date(d(-7), TODAY) == "1w ago"
    assert format_date(d(-27), TODAY) == "3w ago"

def test_past_weeks_extended():
    assert format_date(d(-28), TODAY) == "4w ago"
    assert format_date(d(-89), TODAY) == "12w ago"

def test_past_months():
    assert format_date(d(-90), TODAY) == "jan."
    assert format_date(d(-200), TODAY) == "oct."
    assert format_date(d(-364), TODAY) == "apr."

def test_past_last_year():
    assert format_date(d(-365), TODAY) == "apr. 2025"
    assert format_date(d(-500), TODAY) == "dec. 2024"
