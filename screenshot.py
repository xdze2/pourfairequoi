"""
Automated screenshot capture for pfq TUI.
Runs the app headlessly, navigates to specified tasks, and saves SVG screenshots.

Usage:
    python screenshot.py                    # all scenes
    python screenshot.py --out docs/shots   # custom output dir
"""

import asyncio
import argparse
from pathlib import Path

from pfq.app import PfqApp
from pfq.model import Store, get_how


async def shot(app: PfqApp, pilot, name: str, out: Path) -> None:
    await pilot.pause(0.2)
    path = out / f"{name}.svg"
    app.save_screenshot(str(path))
    print(f"  saved {path}")


async def run_screenshots(vault: Path, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    store = Store(vault)
    paths = sorted(store.keys())

    app = PfqApp()
    async with app.run_test(size=(160, 40)) as pilot:

        # Scene 1: home page (default view)
        await shot(app, pilot, "01_home", out)

        # Scene 2: open first file
        if paths:
            await pilot.press("enter")
            await shot(app, pilot, "02_task_view", out)

        # Scene 3: open a file with the most how children
        richest = max(paths, key=lambda p: len(get_how(store[p])), default=None)
        if richest:
            app._open_node(richest)
            await pilot.pause(0.1)
            await shot(app, pilot, "03_task_with_links", out)

        # Scene 4: link picker
        await pilot.press("l")
        await pilot.pause(0.1)
        await shot(app, pilot, "04_link_picker", out)
        await pilot.press("escape")

        # Scene 5: home page again
        await pilot.press("h")
        await pilot.pause(0.1)
        await shot(app, pilot, "05_home_return", out)


def main() -> None:
    parser = argparse.ArgumentParser(description="Capture pfq TUI screenshots")
    parser.add_argument("--vault", default="data", help="Path to data vault")
    parser.add_argument("--out", default="docs/screenshots", help="Output directory")
    args = parser.parse_args()

    vault = Path(args.vault)
    out = Path(args.out)

    print(f"Capturing screenshots → {out}/")
    asyncio.run(run_screenshots(vault, out))
    print("Done.")


if __name__ == "__main__":
    main()
