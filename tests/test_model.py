"""Tests for pfq.model — NodeGraph loading and graph traversal."""

from pathlib import Path

import pytest

from pfq.disk_io import load_vault
from pfq.model import NodeGraph

VAULT = Path(__file__).parent / "test_vault"


@pytest.fixture
def graph():
    return load_vault(VAULT)


# ── Loading ────────────────────────────────────────────────────────────────────


def test_load_all_nodes(graph):
    assert len(graph.nodes) == 9


def test_node_fields(graph):
    node = graph.get_node("AA0001")
    assert node.description == "Learn guitar"
    assert node.type == "goal"
    assert node.status == "active"


def test_node_children(graph):
    children = graph.get_children_ids("AA0001")
    assert children == ["AB0002", "AB0003"]


def test_node_no_children(graph):
    children = graph.get_children_ids("AC0003")
    assert children == []


# ── Why (derived, reversed how) ───────────────────────────────────────────────


def test_why_single_parent(graph):
    # AB0002 is only a child of AA0001
    parents = graph.get_parent_ids("AB0002")
    assert parents == ["AA0001"]


def test_why_shared_node(graph):
    # ZZ0001 is a child of both AB0003 and BB0002
    parents = graph.get_parent_ids("ZZ0001")
    assert set(parents) == {"AB0003", "BB0002"}


def test_why_root_has_no_parents(graph):
    parents = graph.get_parent_ids("AA0001")
    assert parents == []


# ── Roots ──────────────────────────────────────────────────────────────────────


def test_roots(graph):
    # Nodes with no parents: AA0001, BA0001, CA0001
    roots = graph.get_roots()
    assert set(roots) == {"AA0001", "BA0001", "CA0001"}


# ── get_parents_tree ───────────────────────────────────────────────────────────


def ids_at_depth(tree, depth):
    return {n.node_id for n, d in tree if d == depth}


def test_parents_tree_depths(graph):
    # AC0003 → (depth 1) AB0002 → (depth 2) AA0001
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
    # ZZ0001 has two direct parents
    tree = graph.get_parents_tree("ZZ0001")
    assert ids_at_depth(tree, 1) == {"AB0003", "BB0002"}
    # and their parents at depth 2
    assert ids_at_depth(tree, 2) == {"AA0001", "BA0001"}


# ── get_childrens_tree ─────────────────────────────────────────────────────────


def test_childrens_tree_depths(graph):
    # AA0001 → (depth 1) AB0002, AB0003 → (depth 2) AC0003, ZZ0001
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
    # Both AB0003 and BB0002 point to ZZ0001 — ZZ0001 must appear only once
    # Starting from BA0001: BB0002 (depth 1), BB0003 (depth 1), ZZ0001 (depth 2)
    tree = graph.get_childrens_tree("BA0001")
    zz_entries = [(n, d) for n, d in tree if n.node_id == "ZZ0001"]
    assert len(zz_entries) == 1


# ── deletion_set ───────────────────────────────────────────────────────────────
#
# Vault topology (abbreviated):
#   AA0001 → AB0002 → AC0003
#          → AB0003 → ZZ0001 ← BB0002 ← BA0001
#   CA0001  (isolated root)


def test_deletion_set_node(graph):
    assert graph.deletion_set("AB0002", "node") == {"AB0002"}


def test_deletion_set_soft_unanchored_child(graph):
    # AC0003 has only AB0002 as parent → becomes unanchored
    assert graph.deletion_set("AB0002", "soft") == {"AB0002", "AC0003"}


def test_deletion_set_soft_shared_child_stays(graph):
    # ZZ0001 has BB0002 as second parent → stays anchored
    assert graph.deletion_set("AB0003", "soft") == {"AB0003"}


def test_deletion_set_hard(graph):
    # hard ignores other parents — ZZ0001 included even though BB0002 also links it
    assert graph.deletion_set("AB0003", "hard") == {"AB0003", "ZZ0001"}


def test_deletion_set_hard_leaf(graph):
    assert graph.deletion_set("AC0003", "hard") == {"AC0003"}


def test_nodes_unanchored_after_removal_root(graph):
    # removing AA0001: AB0002, AB0003, AC0003 lose all root paths
    # ZZ0001 survives via BB0002 → BA0001
    unanchored = graph.nodes_unanchored_after_removal({"AA0001"})
    assert "AB0002" in unanchored
    assert "AB0003" in unanchored
    assert "AC0003" in unanchored
    assert "ZZ0001" not in unanchored


def test_nodes_unanchored_after_removal_shared_node(graph):
    # removing AB0003 only: ZZ0001 still reachable via BB0002
    assert "ZZ0001" not in graph.nodes_unanchored_after_removal({"AB0003"})
