"""Tests for pfq.app — TUI behaviour."""

from pathlib import Path

import pytest
from textual.widgets import DataTable

from pfq.app import PfqApp

VAULT = Path(__file__).parent / "test_vault"


@pytest.fixture
def app():
    return PfqApp(vault_path=VAULT)


# ── Home page ──────────────────────────────────────────────────────────────────


async def test_home_shows_root_nodes(app):
    async with app.run_test() as pilot:
        await pilot.pause()
        dt = app.query_one(DataTable)
        # 3 roots + their depth-1 children (AA0001→2, BA0001→2, CA0001→0)
        assert dt.row_count == 7


async def test_home_node_ids(app):
    async with app.run_test() as pilot:
        await pilot.pause()
        dt = app.query_one(DataTable)
        row_keys = {str(key.value) for key in dt.rows}
        assert "AA0001" in row_keys
        assert "BA0001" in row_keys
        assert "CA0001" in row_keys


async def test_home_current_node_is_none(app):
    async with app.run_test() as pilot:
        await pilot.pause()
        assert app.current_node_id is None


# ── Navigation: home → node ────────────────────────────────────────────────────


async def test_enter_navigates_to_node(app):
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        assert app.current_node_id is not None


async def test_navigate_sets_correct_node(app):
    async with app.run_test() as pilot:
        await pilot.pause()
        app._navigate_to("AA0001")
        await pilot.pause()
        assert app.current_node_id == "AA0001"


async def test_node_view_has_root_line(app):
    async with app.run_test() as pilot:
        await pilot.pause()
        app._navigate_to("AA0001")
        await pilot.pause()
        dt = app.query_one(DataTable)
        row_keys = {str(key.value) for key in dt.rows}
        assert "__home__" in row_keys


async def test_node_view_shows_children(app):
    async with app.run_test() as pilot:
        await pilot.pause()
        app._navigate_to("AA0001")
        await pilot.pause()
        dt = app.query_one(DataTable)
        row_keys = {str(key.value) for key in dt.rows}
        assert "AB0002" in row_keys
        assert "AB0003" in row_keys


async def test_node_view_shows_parents(app):
    async with app.run_test() as pilot:
        await pilot.pause()
        app._navigate_to("AB0002")
        await pilot.pause()
        dt = app.query_one(DataTable)
        row_keys = {str(key.value) for key in dt.rows}
        assert "AA0001" in row_keys


async def test_node_view_item_count(app):
    # AA0001: root line + 0 parents + current + 2 children (depth1) + 2 children (depth2)
    # children tree: AB0002(1), AB0003(1), AC0003(2), ZZ0001(2) = 4
    async with app.run_test() as pilot:
        await pilot.pause()
        app._navigate_to("AA0001")
        await pilot.pause()
        dt = app.query_one(DataTable)
        assert dt.row_count == 1 + 0 + 1 + 4  # root + parents + current + children


async def test_current_node_focused(app):
    async with app.run_test() as pilot:
        await pilot.pause()
        app._navigate_to("AB0002")
        await pilot.pause()
        dt = app.query_one(DataTable)
        # AB0002 has 1 parent → current is at row index 2 (root + parent + current)
        assert dt.cursor_coordinate.row == 2


# ── Back navigation ────────────────────────────────────────────────────────────


async def test_go_back_from_node_returns_home(app):
    async with app.run_test() as pilot:
        await pilot.pause()
        app._navigate_to("AA0001")
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()
        assert app.current_node_id is None


async def test_go_back_from_node_to_node(app):
    async with app.run_test() as pilot:
        await pilot.pause()
        app._navigate_to("AA0001")
        await pilot.pause()
        app._navigate_to("AB0002")
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()
        assert app.current_node_id == "AA0001"


async def test_h_goes_home(app):
    async with app.run_test() as pilot:
        await pilot.pause()
        app._navigate_to("AA0001")
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
