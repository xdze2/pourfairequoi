"""Tests for pfq.model — NodeGraph loading and graph traversal."""

from pathlib import Path

import pytest

from pfq.model import NodeGraph

VAULT = Path(__file__).parent / "test_vault"


@pytest.fixture
def graph():
    return NodeGraph.load_from_disk(VAULT)


# ── Loading ────────────────────────────────────────────────────────────────────


def test_load_all_nodes(graph):
    assert len(graph.nodes) == 9


def test_node_fields(graph):
    node = graph.get_node("AA0001_learn_guitar")
    assert node.description == "Learn guitar"
    assert node.type == "goal"
    assert node.status == "active"


def test_node_how_children(graph):
    node = graph.get_node("AA0001_learn_guitar")
    assert node.how == ["AB0002_practice_chords", "AB0003_get_a_guitar"]


def test_node_no_children(graph):
    node = graph.get_node("AC0003_find_tutorials")
    assert node.how == []


# ── Why (derived, reversed how) ───────────────────────────────────────────────


def test_why_single_parent(graph):
    # AB0002_practice_chords is only a child of AA0001_learn_guitar
    parents = graph.get_node_parents("AB0002_practice_chords")
    assert parents == ["AA0001_learn_guitar"]


def test_why_shared_node(graph):
    # ZZ0001_go_to_shop is a child of both AB0003_get_a_guitar and BB0002_buy_inner_tube
    parents = graph.get_node_parents("ZZ0001_go_to_shop")
    assert set(parents) == {"AB0003_get_a_guitar", "BB0002_buy_inner_tube"}


def test_why_root_has_no_parents(graph):
    parents = graph.get_node_parents("AA0001_learn_guitar")
    assert parents == []


# ── Roots ──────────────────────────────────────────────────────────────────────


def test_roots(graph):
    # Nodes with no parents: AA0001, BA0001, CA0001
    roots = graph.get_roots()
    assert set(roots) == {"AA0001_learn_guitar", "BA0001_fix_bike", "CA0001_idle_idea"}


# ── get_parents_tree ───────────────────────────────────────────────────────────


def ids_at_depth(tree, depth):
    return {n.node_id for n, d in tree if d == depth}


def test_parents_tree_depths(graph):
    # AC0003 → (depth 1) AB0002 → (depth 2) AA0001
    tree = graph.get_parents_tree("AC0003_find_tutorials")
    assert ids_at_depth(tree, 1) == {"AB0002_practice_chords"}
    assert ids_at_depth(tree, 2) == {"AA0001_learn_guitar"}


def test_parents_tree_excludes_current(graph):
    tree = graph.get_parents_tree("AB0002_practice_chords")
    assert all(n.node_id != "AB0002_practice_chords" for n, _ in tree)


def test_parents_tree_root_is_empty(graph):
    assert graph.get_parents_tree("AA0001_learn_guitar") == []


def test_parents_tree_max_depth_1(graph):
    tree = graph.get_parents_tree("AC0003_find_tutorials", max_depth=1)
    assert ids_at_depth(tree, 1) == {"AB0002_practice_chords"}
    assert ids_at_depth(tree, 2) == set()


def test_parents_tree_shared_node_both_parents_at_depth_1(graph):
    # ZZ0001 has two direct parents
    tree = graph.get_parents_tree("ZZ0001_go_to_shop")
    assert ids_at_depth(tree, 1) == {"AB0003_get_a_guitar", "BB0002_buy_inner_tube"}
    # and their parents at depth 2
    assert ids_at_depth(tree, 2) == {"AA0001_learn_guitar", "BA0001_fix_bike"}


# ── get_childrens_tree ─────────────────────────────────────────────────────────


def test_childrens_tree_depths(graph):
    # AA0001 → (depth 1) AB0002, AB0003 → (depth 2) AC0003, ZZ0001
    tree = graph.get_childrens_tree("AA0001_learn_guitar")
    assert ids_at_depth(tree, 1) == {"AB0002_practice_chords", "AB0003_get_a_guitar"}
    assert ids_at_depth(tree, 2) == {"AC0003_find_tutorials", "ZZ0001_go_to_shop"}


def test_childrens_tree_excludes_current(graph):
    tree = graph.get_childrens_tree("AA0001_learn_guitar")
    assert all(n.node_id != "AA0001_learn_guitar" for n, _ in tree)


def test_childrens_tree_leaf_is_empty(graph):
    assert graph.get_childrens_tree("AC0003_find_tutorials") == []


def test_childrens_tree_max_depth_1(graph):
    tree = graph.get_childrens_tree("AA0001_learn_guitar", max_depth=1)
    assert ids_at_depth(tree, 1) == {"AB0002_practice_chords", "AB0003_get_a_guitar"}
    assert ids_at_depth(tree, 2) == set()


def test_childrens_tree_shared_node_appears_once(graph):
    # Both AB0003 and BB0002 point to ZZ0001 — ZZ0001 must appear only once
    # Starting from BA0001: BB0002 (depth 1), BB0003 (depth 1), ZZ0001 (depth 2)
    tree = graph.get_childrens_tree("BA0001_fix_bike")
    zz_entries = [(n, d) for n, d in tree if n.node_id == "ZZ0001_go_to_shop"]
    assert len(zz_entries) == 1
