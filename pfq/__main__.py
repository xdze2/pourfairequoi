import click
from pathlib import Path

from .app import PfqApp
from .config import FIELDS
from .model import add_backlink, check_backlinks, find_file_by_id, new_filepath, save_task


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """pfq — a reasoning-focused task manager."""
    if ctx.invoked_subcommand is None:
        PfqApp().run()


@cli.command()
@click.argument("file", type=click.Path(exists=True, path_type=Path))
def open(file: Path):
    """Open a task file directly."""
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


@cli.command()
@click.option("--vault", default="data", type=click.Path(path_type=Path), show_default=True)
def check(vault: Path):
    """Report missing or broken backlinks."""
    if not vault.exists():
        click.echo(f"Vault not found: {vault}")
        return
    issues = check_backlinks(vault)
    if not issues:
        click.echo("All backlinks OK.")
        return
    for i in issues:
        if i["type"] == "broken_link":
            click.echo(f"[broken]   {i['file']}  {i['field']}: #{i['link_id']} — file not found")
        elif i["type"] == "missing_backlink":
            click.echo(
                f"[missing]  {i['target']}  {i['inverse_field']}: "
                f"should contain #{i['source_id']}  (from {i['file']})"
            )
    click.echo(f"\n{len(issues)} issue(s) found.")


@cli.command()
@click.option("--vault", default="data", type=click.Path(path_type=Path), show_default=True)
@click.option("--dry-run", is_flag=True, help="Show what would be fixed without writing.")
def fix(vault: Path, dry_run: bool):
    """Auto-fix missing backlinks (skips broken links)."""
    if not vault.exists():
        click.echo(f"Vault not found: {vault}")
        return
    issues = check_backlinks(vault)
    fixable = [i for i in issues if i["type"] == "missing_backlink"]
    if not fixable:
        click.echo("Nothing to fix.")
        return
    for i in fixable:
        target = find_file_by_id(i["source_id"], vault)
        if not target:
            continue
        target_path = vault / i["target"]
        label = "[dry-run] " if dry_run else ""
        click.echo(f"{label}Adding #{i['source_id']} to {i['target']}  [{i['inverse_field']}]")
        if not dry_run:
            add_backlink(target_path, i["inverse_field"], i["source_id"], i["description"])
    if not dry_run:
        click.echo(f"Fixed {len(fixable)} backlink(s).")


if __name__ == "__main__":
    cli()
