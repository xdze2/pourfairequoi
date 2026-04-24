from pathlib import Path

import click

from pfq.app import PfqApp
from pfq.disk_io import DEFAULT_VAULT_PATH


@click.command()
@click.argument("vault_path", default=str(DEFAULT_VAULT_PATH), required=False)
def cli(vault_path: str) -> None:
    """PourFaireQuoi — a why/how task manager.

    VAULT_PATH is the vault directory to open (default: data/).
    """
    path = Path(vault_path)
    if not path.exists():
        raise click.ClickException(f"Vault not found: {path}\nCreate it first with: mkdir -p {path}")
    if not path.is_dir():
        raise click.ClickException(f"Not a directory: {path}")
    PfqApp(vault_path=path).run()


if __name__ == "__main__":
    cli()
