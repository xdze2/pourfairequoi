"""Tests for timeline: Event model, disk I/O round-trip, and view columns."""
from __future__ import annotations

import tempfile
from datetime import date
from pathlib import Path

import pytest

from pfq.disk_io import create_node, load_vault, save_node_fields
from pfq.model import Event, Node
from pfq.modals import EventEditModal
from pfq.view import _last_event_label, _next_event_label, _parse_iso, build_home_view

VAULT = Path(__file__).parent / "test_vault"


# ── test_vault / Fix bike ──────────────────────────────────────────────────────


@pytest.fixture
def graph():
    return load_vault(VAULT)


def test_fix_bike_timeline_loaded(graph):
    node = graph.get_node("BA0001")
    assert len(node.timeline) == 3


def test_fix_bike_timeline_types(graph):
    node = graph.get_node("BA0001")
    types = [e.type for e in node.timeline]
    assert types == ["created", "journal", "due_date"]


def test_fix_bike_journal_event(graph):
    node = graph.get_node("BA0001")
    journal = next(e for e in node.timeline if e.type == "journal")
    assert journal.date == "2026-03-15"
    assert journal.text == "bought the tools"


def test_fix_bike_due_date_when(graph):
    node = graph.get_node("BA0001")
    due = next(e for e in node.timeline if e.type == "due_date")
    assert due.date == "2026-05-01"
    assert due.when == "end of april"


def test_fix_bike_last_event(graph):
    today = date(2026, 4, 22)
    node = graph.get_node("BA0001")
    label = _last_event_label(node, today)
    assert label == "1mo ago"  # 2026-03-15 is 38 days before 2026-04-22 → crosses 30d threshold


def test_fix_bike_next_event(graph):
    today = date(2026, 4, 22)
    node = graph.get_node("BA0001")
    label = _next_event_label(node, today)
    assert label == "in 1w"  # 2026-05-01 is 9 days away → "in 1w"


# ── _parse_iso ─────────────────────────────────────────────────────────────────


def test_parse_iso_valid():
    assert _parse_iso("2026-04-21") == date(2026, 4, 21)


def test_parse_iso_invalid():
    assert _parse_iso("tomorrow") is None
    assert _parse_iso("april 2027") is None
    assert _parse_iso("") is None
    assert _parse_iso(None) is None


# ── EventEditModal._resolve_date ───────────────────────────────────────────────


def test_resolve_iso_input():
    d, w = EventEditModal._resolve_date("2026-04-21")
    assert d == "2026-04-21"
    assert w is None  # no when needed for ISO input


def test_resolve_natural_language():
    d, w = EventEditModal._resolve_date("april 2027")
    assert d == "2027-04-01"
    assert w == "april 2027"


def test_resolve_unparseable():
    d, w = EventEditModal._resolve_date("Q3 2026")
    assert d is None
    assert w == "Q3 2026"


def test_resolve_empty():
    d, w = EventEditModal._resolve_date(None)
    assert d is None
    assert w is None


# ── Event serialization round-trip ─────────────────────────────────────────────


def test_event_roundtrip_with_when(tmp_path):
    node = create_node("Test node", tmp_path)
    node.timeline.append(Event(type="due_date", date="2027-04-01", when="april 2027", text="review"))
    save_node_fields(node)

    graph = load_vault(tmp_path)
    loaded = graph.get_node(node.node_id)
    due = next(e for e in loaded.timeline if e.type == "due_date")
    assert due.date == "2027-04-01"
    assert due.when == "april 2027"
    assert due.text == "review"


def test_event_roundtrip_iso_only(tmp_path):
    node = create_node("Test node", tmp_path)
    node.timeline.append(Event(type="journal", date="2026-04-21", text="worked on this"))
    save_node_fields(node)

    graph = load_vault(tmp_path)
    loaded = graph.get_node(node.node_id)
    journal = next(e for e in loaded.timeline if e.type == "journal")
    assert journal.date == "2026-04-21"
    assert journal.when is None


# ── Auto-recorded events ───────────────────────────────────────────────────────


def test_create_node_records_created_event(tmp_path):
    node = create_node("New node", tmp_path)
    assert len(node.timeline) == 1
    assert node.timeline[0].type == "created"
    assert node.timeline[0].date == date.today().isoformat()


def test_status_change_records_event(tmp_path):
    node = create_node("New node", tmp_path)
    node.status = "doing"
    save_node_fields(node)

    events = [e for e in node.timeline if e.type == "status_change"]
    assert len(events) == 1
    assert events[0].extra["to"] == "doing"
    assert events[0].extra["from"] is None


def test_no_status_change_event_when_unchanged(tmp_path):
    node = create_node("New node", tmp_path)
    node.status = "todo"
    save_node_fields(node)
    count_before = len(node.timeline)

    save_node_fields(node)  # same status — no new event
    assert len(node.timeline) == count_before


# ── View columns ───────────────────────────────────────────────────────────────


def _graph_with_events(tmp_path, events: list[Event]):
    node = create_node("Root node", tmp_path)
    node.timeline.extend(events)
    save_node_fields(node)
    return load_vault(tmp_path)


def test_last_event_label(tmp_path):
    today = date.today()
    graph = _graph_with_events(tmp_path, [
        Event(type="journal", date="2026-01-01"),
        Event(type="journal", date=today.isoformat()),
    ])
    node = graph.get_node(graph.get_roots()[0])
    assert _last_event_label(node, today) == "today"


def test_last_event_excludes_due_date(tmp_path):
    today = date.today()
    graph = _graph_with_events(tmp_path, [
        Event(type="due_date", date=today.isoformat()),
    ])
    node = graph.get_node(graph.get_roots()[0])
    assert _last_event_label(node, today) == "today"  # from 'created' event


def test_next_event_label_relative(tmp_path):
    from datetime import timedelta
    today = date.today()
    graph = _graph_with_events(tmp_path, [
        Event(type="due_date", date=(today + timedelta(days=3)).isoformat()),
    ])
    node = graph.get_node(graph.get_roots()[0])
    assert _next_event_label(node, today) == "in 3d"


def test_next_event_label_when_fallback(tmp_path):
    today = date.today()
    graph = _graph_with_events(tmp_path, [
        Event(type="due_date", date=None, when="Q3 2026"),
    ])
    node = graph.get_node(graph.get_roots()[0])
    assert _next_event_label(node, today) == "Q3 2026"


def test_next_event_empty_when_no_due_date(tmp_path):
    today = date.today()
    graph = _graph_with_events(tmp_path, [
        Event(type="journal", date=today.isoformat()),
    ])
    node = graph.get_node(graph.get_roots()[0])
    assert _next_event_label(node, today) == ""


def test_home_view_columns(tmp_path):
    from datetime import timedelta
    today = date.today()
    graph = _graph_with_events(tmp_path, [
        Event(type="due_date", date=(today + timedelta(days=5)).isoformat()),
    ])
    rows = build_home_view(graph)
    home_rows = [r for r in rows if r.role == "home_root"]
    assert len(home_rows) == 1
    assert home_rows[0].next_event == "in 5d"
    assert home_rows[0].last_event == "today"  # from 'created' event
