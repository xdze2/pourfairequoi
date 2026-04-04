import click
from pathlib import Path

from .app import PfqApp
from .model import load_all, migrate_task, new_filepath, save_task


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
        "type": "task",
        "status": "todo",
        "start_date": date.today().isoformat(),
    }
    save_task(path, data)
    click.echo(f"Created {path}")
    PfqApp(path).run()


@cli.command()
@click.option("--vault", default="data", type=click.Path(path_type=Path), show_default=True)
@click.option("--dry-run", is_flag=True, help="Show what would be migrated without writing.")
def migrate(vault: Path, dry_run: bool):
    """Migrate task files from old format (why/how/... sections) to new links format."""
    if not vault.exists():
        click.echo(f"Vault not found: {vault}")
        return
    store = load_all(vault)
    count = 0
    for path, data in store.items():
        old_fields = {"why", "how", "need", "required_by", "but", "or", "alternative_to"}
        if not any(f in data for f in old_fields):
            continue
        label = "[dry-run] " if dry_run else ""
        click.echo(f"{label}{path.name}")
        if not dry_run:
            migrate_task(data)
            save_task(path, data)
        count += 1
    if count == 0:
        click.echo("Nothing to migrate.")
    elif dry_run:
        click.echo(f"\n{count} file(s) would be migrated.")
    else:
        click.echo(f"\nMigrated {count} file(s).")


@cli.command()
@click.option("--vault", default="data", type=click.Path(path_type=Path), show_default=True)
@click.option("--dry-run", is_flag=True, help="Show what would be cleaned without writing.")
def clean(vault: Path, dry_run: bool):
    """Remove empty items and empty sections from all task files."""
    from .config import FIELDS
    from .model import load_task
    if not vault.exists():
        click.echo(f"Vault not found: {vault}")
        return
    files = sorted(p for p in vault.iterdir() if p.suffix in (".yaml", ".yml"))
    total = 0
    for path in files:
        data = load_task(path)
        changes = []
        for key, ftype in FIELDS.items():
            if key not in data:
                continue
            val = data[key]
            if val is None or str(val).strip() == "":
                changes.append(f"  {key}: removed empty field")
                del data[key]
        # clean empty links
        links = data.get("links")
        if isinstance(links, list):
            cleaned = [l for l in links if l.get("description") or l.get("target_node")]
            if len(cleaned) < len(links):
                changes.append(f"  links: removed {len(links) - len(cleaned)} empty link(s)")
                data["links"] = cleaned
            if not data["links"]:
                changes.append("  links: removed empty section")
                del data["links"]
        if changes:
            label = "[dry-run] " if dry_run else ""
            click.echo(f"{label}{path.name}")
            for c in changes:
                click.echo(c)
            if not dry_run:
                save_task(path, data)
            total += 1
    if total == 0:
        click.echo("Nothing to clean.")
    elif not dry_run:
        click.echo(f"\nCleaned {total} file(s).")


if __name__ == "__main__":
    cli()
