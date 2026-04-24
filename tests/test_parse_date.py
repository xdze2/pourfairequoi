"""Tests for pfq.dates.parse_date — symmetric with format_date."""
from datetime import date, timedelta

import pytest

from pfq.dates import parse_date

TODAY = date(2026, 4, 23)  # Thursday


def test_iso():
    assert parse_date("2026-06-01", TODAY) == date(2026, 6, 1)

def test_named():
    assert parse_date("today", TODAY) == TODAY
    assert parse_date("tomorrow", TODAY) == date(2026, 4, 24)
    assert parse_date("yesterday", TODAY) == date(2026, 4, 22)

def test_relative_future_days():
    assert parse_date("1d", TODAY) == date(2026, 4, 24)
    assert parse_date("3d", TODAY) == date(2026, 4, 26)

def test_relative_future_weeks():
    assert parse_date("1w", TODAY) == date(2026, 4, 30)
    assert parse_date("2w", TODAY) == date(2026, 5, 7)

def test_relative_future_months():
    assert parse_date("1m", TODAY) == date(2026, 5, 23)
    assert parse_date("1mo", TODAY) == date(2026, 5, 23)
    assert parse_date("3m", TODAY) == date(2026, 7, 23)
    assert parse_date("3mo", TODAY) == date(2026, 7, 23)

def test_relative_future_years():
    assert parse_date("1y", TODAY) == date(2027, 4, 23)

def test_relative_future_explicit():
    assert parse_date("in 1d", TODAY) == date(2026, 4, 24)
    assert parse_date("in 2w", TODAY) == date(2026, 5, 7)
    assert parse_date("in 3m", TODAY) == date(2026, 7, 23)
    assert parse_date("in 3mo", TODAY) == date(2026, 7, 23)
    assert parse_date("in 1y", TODAY) == date(2027, 4, 23)

def test_relative_past_days():
    assert parse_date("3d ago", TODAY) == date(2026, 4, 20)
    assert parse_date("6d ago", TODAY) == date(2026, 4, 17)

def test_relative_past_weeks():
    assert parse_date("1w ago", TODAY) == date(2026, 4, 16)
    assert parse_date("2w ago", TODAY) == date(2026, 4, 9)

def test_relative_past_months():
    assert parse_date("1m ago", TODAY) == date(2026, 3, 23)
    assert parse_date("1mo ago", TODAY) == date(2026, 3, 23)
    assert parse_date("3m ago", TODAY) == date(2026, 1, 23)

def test_relative_past_years():
    assert parse_date("1y ago", TODAY) == date(2025, 4, 23)

def test_weekday_next_occurrence():
    # TODAY is Thursday — next fri is tomorrow
    assert parse_date("fri", TODAY) == date(2026, 4, 24)
    # next thu is 7 days out (not today)
    assert parse_date("thu", TODAY) == date(2026, 4, 30)
    assert parse_date("wed", TODAY) == date(2026, 4, 29)

def test_weekday_with_day():
    assert parse_date("thu 30", TODAY) == date(2026, 4, 30)
    assert parse_date("wed 6", TODAY) == date(2026, 5, 6)

def test_month_with_day():
    assert parse_date("may 7", TODAY) == date(2026, 5, 7)
    assert parse_date("may 23", TODAY) == date(2026, 5, 23)
    # past in current year → next year
    assert parse_date("apr 1", TODAY) == date(2027, 4, 1)

def test_month_dot():
    assert parse_date("jun.", TODAY) == date(2026, 6, 1)
    assert parse_date("apr.", TODAY) == date(2027, 4, 1)  # past month → next year

def test_month_dot_year():
    assert parse_date("jun. 2027", TODAY) == date(2027, 6, 1)
    assert parse_date("apr. 2025", TODAY) == date(2025, 4, 1)

def test_case_insensitive():
    assert parse_date("FRI", TODAY) == date(2026, 4, 24)
    assert parse_date("JUN.", TODAY) == date(2026, 6, 1)
    assert parse_date("3D", TODAY) == date(2026, 4, 26)

def test_unrecognised_returns_none():
    assert parse_date("3moo", TODAY) is None
    assert parse_date("garbage", TODAY) is None
    assert parse_date("", TODAY) is None
