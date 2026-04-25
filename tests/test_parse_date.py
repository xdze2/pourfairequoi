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

def test_weekday_closest():
    # TODAY is Thursday (Apr 23)
    # fri: tomorrow Apr 24 (1d) vs last fri Apr 17 (6d) → tomorrow
    assert parse_date("fri", TODAY) == date(2026, 4, 24)
    # thu: today is Thu, so next Thu Apr 30 (7d) vs last Thu Apr 16 (7d) → tie → future
    assert parse_date("thu", TODAY) == date(2026, 4, 30)
    # wed: last Wed Apr 22 (1d ago) vs next Wed Apr 29 (6d) → last week
    assert parse_date("wed", TODAY) == date(2026, 4, 22)

def test_weekday_with_day():
    assert parse_date("thu 30", TODAY) == date(2026, 4, 30)
    assert parse_date("wed 6", TODAY) == date(2026, 5, 6)

def test_month_with_day():
    assert parse_date("may 7", TODAY) == date(2026, 5, 7)
    assert parse_date("may 23", TODAY) == date(2026, 5, 23)
    # apr 1: 22 days ago vs 343 days ahead → past is closer
    assert parse_date("apr 1", TODAY) == date(2026, 4, 1)

def test_month_dot():
    assert parse_date("jun.", TODAY) == date(2026, 6, 1)
    # apr 1: 22 days ago vs 343 days ahead → past is closer
    assert parse_date("apr.", TODAY) == date(2026, 4, 1)

def test_month_dot_year():
    assert parse_date("jun. 2027", TODAY) == date(2027, 6, 1)
    assert parse_date("apr. 2025", TODAY) == date(2025, 4, 1)

def test_dd_mm_yyyy():
    assert parse_date("23-04-2026", TODAY) == date(2026, 4, 23)
    assert parse_date("01-01-2027", TODAY) == date(2027, 1, 1)
    assert parse_date("31-12-2025", TODAY) == date(2025, 12, 31)

def test_dd_mm_yyyy_invalid_returns_none():
    assert parse_date("31-02-2026", TODAY) is None  # Feb 31 doesn't exist

def test_dd_mm_closest():
    # 12-04: Apr 12 was 11 days ago vs Apr 12 2027 (354 days) → past closer
    assert parse_date("12-04", TODAY) == date(2026, 4, 12)
    # 25-04: Apr 25 is 2 days ahead vs Apr 25 2025 (363 days ago) → future closer
    assert parse_date("25-04", TODAY) == date(2026, 4, 25)
    # 23-04: today exactly
    assert parse_date("23-04", TODAY) == date(2026, 4, 23)

def test_signed_relative_future():
    assert parse_date("+2d", TODAY) == date(2026, 4, 25)
    assert parse_date("+3w", TODAY) == date(2026, 5, 14)
    assert parse_date("+1m", TODAY) == date(2026, 5, 23)
    assert parse_date("+1y", TODAY) == date(2027, 4, 23)

def test_signed_relative_past():
    assert parse_date("-2d", TODAY) == date(2026, 4, 21)
    assert parse_date("-3w", TODAY) == date(2026, 4, 2)
    assert parse_date("-1m", TODAY) == date(2026, 3, 23)
    assert parse_date("-1y", TODAY) == date(2025, 4, 23)

def test_signed_relative_month_boundary():
    # -1m from Jan 31 → Dec 31 (not Feb 31)
    assert parse_date("-1m", date(2026, 1, 31)) == date(2025, 12, 31)

def test_case_insensitive():
    assert parse_date("FRI", TODAY) == date(2026, 4, 24)
    assert parse_date("JUN.", TODAY) == date(2026, 6, 1)
    assert parse_date("3D", TODAY) == date(2026, 4, 26)

def test_unrecognised_returns_none():
    assert parse_date("3moo", TODAY) is None
    assert parse_date("garbage", TODAY) is None
    assert parse_date("", TODAY) is None
