from pathlib import Path

import click

from pfq.app import PfqApp
from pfq.disk_io import DEFAULT_VAULT_PATH


@click.command()
@click.option(
    "--vault",
    default=str(DEFAULT_VAULT_PATH),
    show_default=True,
    help="Path to vault directory.",
)
def cli(vault: str) -> None:
    """PourFaireQuoi — a why/how task manager."""
    PfqApp(vault_path=Path(vault)).run()


if __name__ == "__main__":
    cli()
