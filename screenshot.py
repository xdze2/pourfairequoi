"""Generate SVG screenshots of the pfq app for documentation and logs.

Usage:
    venv/bin/python screenshot.py [--vault PATH] [--out DIR]

Captures:
    01_home.svg          — home view (roots + children)
    02_node.svg          — node view (first root's first child)
    03_companion.svg     — companion panel open (F2)
    04_edit_modal.svg    — description edit modal
    05_delete_modal.svg  — delete/unlink multi-choice modal

Output: screenshots/ by default.
"""

import asyncio
import sys
from pathlib import Path

import click

from pfq.app import PfqApp
from pfq.disk_io import load_vault


async def capture(vault_path: Path, out: Path) -> None:
    out.mkdir(exist_ok=True)

    graph = load_vault(vault_path)
    roots = sorted(graph.get_roots())

    # Pick a node to navigate to: first child of first root that has children
    target_node_id = None
    for root_id in roots:
        children = graph.get_children_ids(root_id)
        if children:
            target_node_id = children[0]
            break
    if target_node_id is None and roots:
        target_node_id = roots[0]

    app = PfqApp(vault_path)

    async with app.run_test(size=(120, 40)) as pilot:

        # 1. Home view
        await pilot.pause()
        app.save_screenshot("01_home.svg", path=str(out))
        click.echo("  ✓ 01_home.svg")

        # 2. Node view
        if target_node_id:
            app._navigate_to(target_node_id)
            await pilot.pause()
            app.save_screenshot("02_node.svg", path=str(out))
            click.echo(f"  ✓ 02_node.svg  ({target_node_id})")

        # 3. Companion panel (F2)
        await pilot.press("f2")
        await pilot.pause(0.5)
        app.save_screenshot("03_companion.svg", path=str(out))
        click.echo("  ✓ 03_companion.svg")
        await pilot.press("f2")

        # 4. Edit modal
        if target_node_id:
            app._navigate_to(target_node_id)
            await pilot.pause()
            await pilot.press("e")
            await pilot.pause()
            app.save_screenshot("04_edit_modal.svg", path=str(out))
            click.echo("  ✓ 04_edit_modal.svg")
            await pilot.press("escape")

        # 5. Delete modal
        if target_node_id:
            app._navigate_to(target_node_id)
            await pilot.pause()
            # move cursor to a child row if one exists
            children = app.graph.get_children_ids(target_node_id)
            if children:
                await pilot.press("down")
                await pilot.pause()
            await pilot.press("d")
            await pilot.pause()
            app.save_screenshot("05_delete_modal.svg", path=str(out))
            click.echo("  ✓ 05_delete_modal.svg")
            await pilot.press("escape")


@click.command()
@click.option("--vault", default="tests/test_vault", type=click.Path(), show_default=True, help="Vault directory")
@click.option("--out", default="screenshots", type=click.Path(), show_default=True, help="Output directory")
def main(vault: str, out: str) -> None:
    """Capture SVG screenshots of the pfq TUI."""
    vault_path = Path(vault)
    out_path = Path(out)

    if not vault_path.exists():
        click.echo(f"Vault not found: {vault_path}", err=True)
        sys.exit(1)

    click.echo(f"Vault:  {vault_path}")
    click.echo(f"Output: {out_path}/")
    asyncio.run(capture(vault_path, out_path))
    click.echo("Done.")


if __name__ == "__main__":
    main()
