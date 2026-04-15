"""Tests for pfq.app — TUI behaviour."""

from pathlib import Path

import pytest
from textual.widgets import ListView

from pfq.app import PfqApp

VAULT = Path(__file__).parent / "test_vault"


@pytest.fixture
def app():
    return PfqApp(vault_path=VAULT)


# ── Home page ──────────────────────────────────────────────────────────────────


async def test_home_shows_root_nodes(app):
    async with app.run_test() as pilot:
        await pilot.pause()
        lv = app.query_one(ListView)
        # 3 root nodes: AA0001, BA0001, CA0001
        assert len(lv) == 3


async def test_home_node_ids(app):
    async with app.run_test() as pilot:
        await pilot.pause()
        lv = app.query_one(ListView)
        ids = {item.id for item in lv.query(ListView.__class__._find_child_type()).results()} \
              if False else {item.id for item in lv.children}
        assert "n_AA0001_learn_guitar" in ids
        assert "n_BA0001_fix_bike" in ids
        assert "n_CA0001_idle_idea" in ids


async def test_home_current_node_is_none(app):
    async with app.run_test() as pilot:
        await pilot.pause()
        assert app.current_node_id is None


# ── Navigation: home → node ────────────────────────────────────────────────────


async def test_enter_navigates_to_node(app):
    async with app.run_test() as pilot:
        await pilot.pause()
        lv = app.query_one(ListView)
        # select AA0001 (sorted first alphabetically)
        lv.index = 0
        await pilot.press("enter")
        await pilot.pause()
        assert app.current_node_id is not None


async def test_navigate_sets_correct_node(app):
    async with app.run_test() as pilot:
        await pilot.pause()
        await app._navigate_to("AA0001_learn_guitar")
        await pilot.pause()
        assert app.current_node_id == "AA0001_learn_guitar"


async def test_node_view_has_root_line(app):
    async with app.run_test() as pilot:
        await pilot.pause()
        await app._navigate_to("AA0001_learn_guitar")
        await pilot.pause()
        lv = app.query_one(ListView)
        ids = {item.id for item in lv.children}
        assert "go_home" in ids


async def test_node_view_shows_children(app):
    async with app.run_test() as pilot:
        await pilot.pause()
        await app._navigate_to("AA0001_learn_guitar")
        await pilot.pause()
        lv = app.query_one(ListView)
        ids = {item.id for item in lv.children}
        assert "n_AB0002_practice_chords" in ids
        assert "n_AB0003_get_a_guitar" in ids


async def test_node_view_shows_parents(app):
    async with app.run_test() as pilot:
        await pilot.pause()
        await app._navigate_to("AB0002_practice_chords")
        await pilot.pause()
        lv = app.query_one(ListView)
        ids = {item.id for item in lv.children}
        assert "n_AA0001_learn_guitar" in ids


async def test_node_view_item_count(app):
    # AA0001: root line + 0 parents + current + 2 children (depth1) + 2 children (depth2)
    # children tree: AB0002(1), AB0003(1), AC0003(2), ZZ0001(2) = 4
    async with app.run_test() as pilot:
        await pilot.pause()
        await app._navigate_to("AA0001_learn_guitar")
        await pilot.pause()
        lv = app.query_one(ListView)
        assert len(lv) == 1 + 0 + 1 + 4  # root + parents + current + children


async def test_current_node_focused(app):
    async with app.run_test() as pilot:
        await pilot.pause()
        await app._navigate_to("AB0002_practice_chords")
        await pilot.pause()
        lv = app.query_one(ListView)
        # AB0002 has 1 parent → current is at index 2 (root + parent + current)
        assert lv.index == 2


# ── Back navigation ────────────────────────────────────────────────────────────


async def test_go_back_from_node_returns_home(app):
    async with app.run_test() as pilot:
        await pilot.pause()
        await app._navigate_to("AA0001_learn_guitar")
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()
        assert app.current_node_id is None


async def test_go_back_from_node_to_node(app):
    async with app.run_test() as pilot:
        await pilot.pause()
        await app._navigate_to("AA0001_learn_guitar")
        await pilot.pause()
        await app._navigate_to("AB0002_practice_chords")
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()
        assert app.current_node_id == "AA0001_learn_guitar"


async def test_h_goes_home(app):
    async with app.run_test() as pilot:
        await pilot.pause()
        await app._navigate_to("AA0001_learn_guitar")
        await pilot.pause()
        await pilot.press("h")
        await pilot.pause()
        assert app.current_node_id is None


async def test_back_from_home_does_nothing(app):
    async with app.run_test() as pilot:
        await pilot.pause()
        history_before = len(app.history)
        await pilot.press("escape")
        await pilot.pause()
        assert app.current_node_id is None
        assert len(app.history) == history_before
