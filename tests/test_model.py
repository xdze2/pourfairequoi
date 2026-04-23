"""Tests for pfq.model — NodeGraph loading, graph traversal, and lifecycle computation."""

from datetime import date, timedelta
from pathlib import Path

import pytest

from pfq.disk_io import load_vault
from pfq.model import NodeGraph, Node, compute_lifecycle

VAULT = Path(__file__).parent / "test_vault"
TODAY = date(2026, 4, 23)


@pytest.fixture
def graph():
    return load_vault(VAULT, today=TODAY)


# ── Loading ────────────────────────────────────────────────────────────────────


def test_load_all_nodes(graph):
    assert len(graph.nodes) == 18


def test_node_fields(graph):
    node = graph.get_node("AA0001")
    assert node.description == "Learn guitar"
    assert node.opened_at == "2026-01-01"
    assert node.update_period == 30
    assert not node.is_closed


def test_closed_node_fields(graph):
    node = graph.get_node("AC0003")
    assert node.closed_at == "2026-04-15"
    assert node.close_reason == "done"
    assert node.is_closed


def test_node_children(graph):
    children = graph.get_children_ids("AA0001")
    assert children == ["AB0002", "AB0003"]


def test_node_no_children(graph):
    assert graph.get_children_ids("AC0003") == []


# ── Why (derived, reversed how) ───────────────────────────────────────────────


def test_why_single_parent(graph):
    assert graph.get_parent_ids("AB0002") == ["AA0001"]


def test_why_shared_node(graph):
    assert set(graph.get_parent_ids("ZZ0001")) == {"AB0003", "BB0002", "EB0001"}


def test_why_root_has_no_parents(graph):
    assert graph.get_parent_ids("AA0001") == []


# ── Roots ──────────────────────────────────────────────────────────────────────


def test_roots(graph):
    assert set(graph.get_roots()) == {"AA0001", "BA0001", "CA0001", "DA0001", "EA0001"}


# ── get_parents_tree ───────────────────────────────────────────────────────────


def ids_at_depth(tree, depth):
    return {n.node_id for n, d in tree if d == depth}


def test_parents_tree_depths(graph):
    tree = graph.get_parents_tree("AC0003")
    assert ids_at_depth(tree, 1) == {"AB0002"}
    assert ids_at_depth(tree, 2) == {"AA0001"}


def test_parents_tree_excludes_current(graph):
    tree = graph.get_parents_tree("AB0002")
    assert all(n.node_id != "AB0002" for n, _ in tree)


def test_parents_tree_root_is_empty(graph):
    assert graph.get_parents_tree("AA0001") == []


def test_parents_tree_max_depth_1(graph):
    tree = graph.get_parents_tree("AC0003", max_depth=1)
    assert ids_at_depth(tree, 1) == {"AB0002"}
    assert ids_at_depth(tree, 2) == set()


def test_parents_tree_shared_node_both_parents_at_depth_1(graph):
    tree = graph.get_parents_tree("ZZ0001")
    assert ids_at_depth(tree, 1) == {"AB0003", "BB0002", "EB0001"}
    assert ids_at_depth(tree, 2) == {"AA0001", "BA0001", "EA0001"}


# ── get_childrens_tree ─────────────────────────────────────────────────────────


def test_childrens_tree_depths(graph):
    tree = graph.get_childrens_tree("AA0001")
    assert ids_at_depth(tree, 1) == {"AB0002", "AB0003"}
    assert ids_at_depth(tree, 2) == {"AC0003", "ZZ0001"}


def test_childrens_tree_excludes_current(graph):
    tree = graph.get_childrens_tree("AA0001")
    assert all(n.node_id != "AA0001" for n, _ in tree)


def test_childrens_tree_leaf_is_empty(graph):
    assert graph.get_childrens_tree("AC0003") == []


def test_childrens_tree_max_depth_1(graph):
    tree = graph.get_childrens_tree("AA0001", max_depth=1)
    assert ids_at_depth(tree, 1) == {"AB0002", "AB0003"}
    assert ids_at_depth(tree, 2) == set()


def test_childrens_tree_shared_node_appears_once(graph):
    tree = graph.get_childrens_tree("BA0001")
    zz_entries = [(n, d) for n, d in tree if n.node_id == "ZZ0001"]
    assert len(zz_entries) == 1


# ── deletion_set ───────────────────────────────────────────────────────────────


def test_deletion_set_node(graph):
    assert graph.deletion_set("AB0002", "node") == {"AB0002"}


def test_deletion_set_soft_unanchored_child(graph):
    assert graph.deletion_set("AB0002", "soft") == {"AB0002", "AC0003"}


def test_deletion_set_soft_shared_child_stays(graph):
    assert graph.deletion_set("AB0003", "soft") == {"AB0003"}


def test_deletion_set_hard(graph):
    assert graph.deletion_set("AB0003", "hard") == {"AB0003", "ZZ0001"}


def test_deletion_set_hard_leaf(graph):
    assert graph.deletion_set("AC0003", "hard") == {"AC0003"}


def test_nodes_unanchored_after_removal_root(graph):
    unanchored = graph.nodes_unanchored_after_removal({"AA0001"})
    assert "AB0002" in unanchored
    assert "AB0003" in unanchored
    assert "AC0003" in unanchored
    assert "ZZ0001" not in unanchored


def test_nodes_unanchored_after_removal_shared_node(graph):
    assert "ZZ0001" not in graph.nodes_unanchored_after_removal({"AB0003"})


# ── _last_active ───────────────────────────────────────────────────────────────
#
# Vault topology and closed nodes:
#   AA0001 → AB0002 → AC0003 [closed 2026-04-15]
#          → AB0003 → ZZ0001 [closed 2026-04-10] ← BB0002 ← BA0001
#   BA0001 → BB0003  (open, no activity)
#   CA0001  (isolated, open)


def test_last_active_leaf_closed_has_no_children(graph):
    # Closed leaf — no children, so _last_active is None (own closed_at doesn't self-apply)
    assert graph.get_node("AC0003")._last_active is None
    assert graph.get_node("ZZ0001")._last_active is None


def test_last_active_leaf_open_no_children(graph):
    assert graph.get_node("BB0003")._last_active is None
    assert graph.get_node("CA0001")._last_active is None


def test_last_active_propagates_from_closed_child(graph):
    # AB0002 has closed child AC0003 (2026-04-15)
    assert graph.get_node("AB0002")._last_active == date(2026, 4, 15)


def test_last_active_propagates_through_shared_node(graph):
    # AB0003 and BB0002 both point to ZZ0001 (closed 2026-04-10)
    assert graph.get_node("AB0003")._last_active == date(2026, 4, 10)
    assert graph.get_node("BB0002")._last_active == date(2026, 4, 10)


def test_last_active_takes_max_across_children(graph):
    # AA0001 has AB0002 (_last_active=2026-04-15) and AB0003 (_last_active=2026-04-10)
    assert graph.get_node("AA0001")._last_active == date(2026, 4, 15)


def test_last_active_none_when_no_closed_descendants(graph):
    # BA0001 children: BB0002 (_last_active=2026-04-10), BB0003 (None)
    assert graph.get_node("BA0001")._last_active == date(2026, 4, 10)


# ── _is_overdue ────────────────────────────────────────────────────────────────


def test_is_overdue_past_date(graph):
    # BA0001 has estimated_closing_date 2026-01-01 (past)
    assert graph.get_node("BA0001")._is_overdue is True


def test_is_overdue_none_when_no_estimate(graph):
    assert graph.get_node("AA0001")._is_overdue is None
    assert graph.get_node("CA0001")._is_overdue is None


# ── _is_active / _last_update ──────────────────────────────────────────────────
#
# TODAY = 2026-04-23
# AB0002: opened_at 2026-03-01, period 14
#   elapsed=53d, periods=3, _last_update = 2026-03-01 + 42d = 2026-04-12
#   _last_active=2026-04-15 > _last_update=2026-04-12  →  _is_active=True
#
# BB0003: opened_at 2026-03-01, period 14
#   same _last_update = 2026-04-12, _last_active=None  →  _is_active=False
#
# AA0001: opened_at 2026-01-01, period 30
#   elapsed=112d, periods=3, _last_update = 2026-01-01 + 90d = 2026-04-01
#   _last_active=2026-04-15 > 2026-04-01  →  _is_active=True


def test_last_update_period_window(graph):
    node = graph.get_node("AB0002")
    assert node._last_update == date(2026, 4, 12)
    # window end is always >= today
    assert node._last_update + timedelta(days=node.update_period) >= TODAY


def test_is_active_true_when_recent_activity(graph):
    assert graph.get_node("AB0002")._is_active is True
    assert graph.get_node("AA0001")._is_active is True


def test_is_active_false_when_no_activity_in_window(graph):
    assert graph.get_node("BB0003")._is_active is False


def test_is_active_none_when_no_period(graph):
    assert graph.get_node("CA0001")._is_active is None
    assert graph.get_node("AB0003")._is_active is None
    assert graph.get_node("BA0001")._is_active is None


def test_is_active_none_for_closed_node(graph):
    # Closed nodes have no period tracking
    assert graph.get_node("AC0003")._is_active is None
    assert graph.get_node("ZZ0001")._is_active is None


# ── first-period grace ────────────────────────────────────────────────────────


def test_first_period_grace_no_activity():
    # opened today, period=1 → still in first period → _is_active should be None, not False
    g = NodeGraph()
    g.add_node(Node(node_id="XX0002", opened_at=TODAY.isoformat(), update_period=1))
    compute_lifecycle(g, today=TODAY)
    node = g.get_node("XX0002")
    assert node._last_update == TODAY
    assert node._is_active is None


def test_first_period_grace_expires_next_day():
    # one day later (periods=1) → no activity → _is_active should be False
    g = NodeGraph()
    tomorrow = TODAY + timedelta(days=1)
    g.add_node(Node(node_id="XX0003", opened_at=TODAY.isoformat(), update_period=1))
    compute_lifecycle(g, today=tomorrow)
    assert g.get_node("XX0003")._is_active is False


# ── future opened_at ───────────────────────────────────────────────────────────


def test_future_opened_at_is_dormant():
    g = NodeGraph()
    g.add_node(Node(
        node_id="XX0001",
        description="Future task",
        opened_at="2026-06-01",
        update_period=14,
    ))
    compute_lifecycle(g, today=TODAY)
    node = g.get_node("XX0001")
    assert node._last_update is None
    assert node._is_active is None
