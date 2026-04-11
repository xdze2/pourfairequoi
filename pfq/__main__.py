import click
from pathlib import Path

from .app import PfqApp
from .model import Store, get_constrain, get_how, load_task, migrate_task, save_task


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

    store = Store()
    path, data = store.new_node(description)
    data.update({
        "description": description,
        "type": "task",
        "status": "todo",
        "start_date": date.today().isoformat(),
    })
    store.save(path, data)
    click.echo(f"Created {path}")
    PfqApp(path).run()


@cli.command()
@click.option(
    "--vault", default="data", type=click.Path(path_type=Path), show_default=True
)
@click.option(
    "--dry-run", is_flag=True, help="Show what would be migrated without writing."
)
def migrate(vault: Path, dry_run: bool):
    """Migrate task files from old flat links: format to how:/constrain: format."""
    if not vault.exists():
        click.echo(f"Vault not found: {vault}")
        return
    store = Store(vault)
    count = 0
    for path, data in store.items():
        if "links" not in data:
            continue
        label = "[dry-run] " if dry_run else ""
        click.echo(f"{label}{path.name}")
        if not dry_run:
            migrate_task(data)
            store.save(path, data)
        count += 1
    if count == 0:
        click.echo("Nothing to migrate.")
    elif dry_run:
        click.echo(f"\n{count} file(s) would be migrated.")
    else:
        click.echo(f"\nMigrated {count} file(s).")


@cli.command()
@click.option(
    "--vault", default="data", type=click.Path(path_type=Path), show_default=True
)
@click.option(
    "--dry-run", is_flag=True, help="Show what would be cleaned without writing."
)
def clean(vault: Path, dry_run: bool):
    """Remove empty fields and empty entries from all task files."""
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
        # empty scalar/text fields
        for key in list(FIELDS):
            if key not in data:
                continue
            val = data[key]
            if val is None or str(val).strip() == "":
                changes.append(f"  {key}: removed empty field")
                del data[key]
        # empty how entries (no description and no target_node)
        how = get_how(data)
        if how:
            cleaned = [e for e in how if e.get("description") or e.get("target_node")]
            if len(cleaned) < len(how):
                changes.append(
                    f"  how: removed {len(how) - len(cleaned)} empty entry/entries"
                )
                data["how"] = cleaned
            if not data.get("how"):
                changes.append("  how: removed empty section")
                data.pop("how", None)
        # empty constrain entries
        constrain = get_constrain(data)
        if constrain:
            cleaned = [
                e for e in constrain if e.get("description") or e.get("target_node")
            ]
            if len(cleaned) < len(constrain):
                changes.append(
                    f"  constrain: removed {len(constrain) - len(cleaned)} empty entry/entries"
                )
                data["constrain"] = cleaned
            if not data.get("constrain"):
                changes.append("  constrain: removed empty section")
                data.pop("constrain", None)
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
