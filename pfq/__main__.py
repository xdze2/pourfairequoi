import click
from pathlib import Path

from .app import PfqApp
from .config import FIELDS
from .model import new_filepath, save_task


@click.group()
def cli():
    """pfq — a reasoning-focused task manager."""


@cli.command()
@click.argument("file", type=click.Path(exists=True, path_type=Path))
def open(file: Path):
    """Open a task file."""
    PfqApp(file).run()


@cli.command()
@click.argument("description")
def new(description: str):
    """Create a new task and open it."""
    from datetime import date
    path = new_filepath(description)
    data: dict = {
        "description": description,
        "status": "todo",
        "start_date": date.today().isoformat(),
    }
    for key, ftype in FIELDS.items():
        if ftype == "list" and key not in data:
            data[key] = []
    save_task(path, data)
    click.echo(f"Created {path}")
    PfqApp(path).run()


if __name__ == "__main__":
    cli()
