"""CLI interface for mindbase."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from mindbase import __version__
from mindbase.db import (
    add_entry,
    count_entries,
    delete_entry,
    export_entries,
    get_connection,
    get_entry,
    import_entries,
    list_all_tags,
    list_entries,
    search_entries,
    update_entry,
)
from mindbase.models import Entry
from mindbase.utils import format_tags, open_editor, truncate

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="mindbase")
@click.option("--db", type=click.Path(), default=None, help="Database file path")
@click.pass_context
def cli(ctx: click.Context, db: str | None) -> None:
    """mindbase - A local knowledge base CLI tool."""
    ctx.ensure_object(dict)
    ctx.obj["db_path"] = Path(db) if db else None


@cli.command()
@click.argument("title")
@click.option("-c", "--content", default="", help="Entry content")
@click.option("-t", "--tags", default="", help="Comma-separated tags")
@click.option("-e", "--editor", is_flag=True, help="Open editor for content")
@click.pass_context
def add(ctx: click.Context, title: str, content: str, tags: str, editor: bool) -> None:
    """Add a new entry."""
    if editor:
        content = open_editor(f"# {title}\n\n")

    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
    entry = Entry(title=title, content=content, tags=tag_list)

    conn = get_connection(ctx.obj["db_path"])
    try:
        entry = add_entry(conn, entry)
        console.print(f"[green]Entry #{entry.id} added successfully![/green]")
    finally:
        conn.close()


@cli.command()
@click.argument("entry_id", type=int)
@click.pass_context
def show(ctx: click.Context, entry_id: int) -> None:
    """Show an entry in detail."""
    conn = get_connection(ctx.obj["db_path"])
    try:
        entry = get_entry(conn, entry_id)
        if not entry:
            console.print(f"[red]Entry #{entry_id} not found.[/red]")
            sys.exit(1)

        header = f"[bold]#{entry.id}[/bold] {entry.title}"
        if entry.tags:
            header += f"  [dim]{format_tags(entry.tags)}[/dim]"

        body = entry.content if entry.content else "[dim]No content[/dim]"
        md = Markdown(body)

        panel = Panel(
            md,
            title=header,
            subtitle=f"Updated: {entry.updated_at:%Y-%m-%d %H:%M}",
        )
        console.print(panel)
    finally:
        conn.close()


@cli.command(name="list")
@click.option("-t", "--tag", default=None, help="Filter by tag")
@click.option("-n", "--limit", default=30, help="Max entries to show")
@click.pass_context
def list_cmd(ctx: click.Context, tag: str | None, limit: int) -> None:
    """List entries."""
    conn = get_connection(ctx.obj["db_path"])
    try:
        entries = list_entries(conn, tag=tag, limit=limit)
        if not entries:
            console.print("[dim]No entries found.[/dim]")
            return

        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("ID", width=6)
        table.add_column("Title", min_width=20)
        table.add_column("Tags", min_width=10)
        table.add_column("Updated", width=16)

        for e in entries:
            table.add_row(
                str(e.id),
                truncate(e.title, 50),
                format_tags(e.tags),
                f"{e.updated_at:%Y-%m-%d %H:%M}",
            )

        console.print(table)
        total = count_entries(conn)
        console.print(f"\n[dim]Showing {len(entries)} of {total} entries[/dim]")
    finally:
        conn.close()


@cli.command()
@click.argument("query")
@click.option("-n", "--limit", default=20, help="Max results")
@click.pass_context
def search(ctx: click.Context, query: str, limit: int) -> None:
    """Search entries by keyword."""
    conn = get_connection(ctx.obj["db_path"])
    try:
        entries = search_entries(conn, query, limit=limit)
        if not entries:
            console.print(f"[dim]No results for '{query}'[/dim]")
            return

        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("ID", width=6)
        table.add_column("Title", min_width=20)
        table.add_column("Tags", min_width=10)
        table.add_column("Preview", min_width=30)

        for e in entries:
            table.add_row(
                str(e.id),
                truncate(e.title, 40),
                format_tags(e.tags),
                truncate(e.content, 60),
            )

        console.print(table)
        console.print(f"\n[dim]{len(entries)} result(s) for '{query}'[/dim]")
    finally:
        conn.close()


@cli.command()
@click.argument("entry_id", type=int)
@click.option("-t", "--title", default=None, help="New title")
@click.option("-c", "--content", default=None, help="New content")
@click.option("--tags", default=None, help="New comma-separated tags")
@click.option("-e", "--editor", is_flag=True, help="Open editor for content")
@click.pass_context
def edit(
    ctx: click.Context,
    entry_id: int,
    title: str | None,
    content: str | None,
    tags: str | None,
    editor: bool,
) -> None:
    """Edit an existing entry."""
    conn = get_connection(ctx.obj["db_path"])
    try:
        entry = get_entry(conn, entry_id)
        if not entry:
            console.print(f"[red]Entry #{entry_id} not found.[/red]")
            sys.exit(1)

        if title is not None:
            entry.title = title
        if content is not None:
            entry.content = content
        if tags is not None:
            entry.tags = [t.strip() for t in tags.split(",") if t.strip()]
        if editor:
            entry.content = open_editor(entry.content)

        entry = update_entry(conn, entry)
        console.print(f"[green]Entry #{entry.id} updated![/green]")
    finally:
        conn.close()


@cli.command()
@click.argument("entry_id", type=int)
@click.option("-y", "--yes", is_flag=True, help="Skip confirmation")
@click.pass_context
def delete(ctx: click.Context, entry_id: int, yes: bool) -> None:
    """Delete an entry."""
    conn = get_connection(ctx.obj["db_path"])
    try:
        entry = get_entry(conn, entry_id)
        if not entry:
            console.print(f"[red]Entry #{entry_id} not found.[/red]")
            sys.exit(1)

        if not yes:
            click.confirm(
                f"Delete entry #{entry_id} '{entry.title}'?", abort=True
            )

        delete_entry(conn, entry_id)
        console.print(f"[green]Entry #{entry_id} deleted.[/green]")
    finally:
        conn.close()


@cli.command()
@click.pass_context
def tags(ctx: click.Context) -> None:
    """List all tags."""
    conn = get_connection(ctx.obj["db_path"])
    try:
        tag_list = list_all_tags(conn)
        if not tag_list:
            console.print("[dim]No tags yet.[/dim]")
            return

        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Tag", min_width=15)
        table.add_column("Entries", width=8, justify="right")

        for name, count in tag_list:
            table.add_row(f"#{name}", str(count))

        console.print(table)
    finally:
        conn.close()


@cli.command()
@click.option("-o", "--output", type=click.Path(), default=None, help="Output file (default: stdout)")
@click.pass_context
def export(ctx: click.Context, output: str | None) -> None:
    """Export all entries as JSON."""
    conn = get_connection(ctx.obj["db_path"])
    try:
        data = export_entries(conn)
        json_str = json.dumps(data, ensure_ascii=False, indent=2)

        if output:
            Path(output).write_text(json_str, encoding="utf-8")
            console.print(f"[green]Exported {len(data)} entries to {output}[/green]")
        else:
            click.echo(json_str)
    finally:
        conn.close()


@cli.command(name="import")
@click.argument("file", type=click.Path(exists=True))
@click.pass_context
def import_cmd(ctx: click.Context, file: str) -> None:
    """Import entries from a JSON file."""
    data = json.loads(Path(file).read_text(encoding="utf-8"))
    if not isinstance(data, list):
        console.print("[red]Invalid format: expected a JSON array.[/red]")
        sys.exit(1)

    conn = get_connection(ctx.obj["db_path"])
    try:
        count = import_entries(conn, data)
        console.print(f"[green]Imported {count} entries.[/green]")
    finally:
        conn.close()


@cli.command()
@click.pass_context
def stats(ctx: click.Context) -> None:
    """Show knowledge base statistics."""
    conn = get_connection(ctx.obj["db_path"])
    try:
        total = count_entries(conn)
        tag_list = list_all_tags(conn)
        tag_count = len(tag_list)

        console.print(Panel.fit(
            f"[bold]mindbase statistics[/bold]\n\n"
            f"  Entries: [cyan]{total}[/cyan]\n"
            f"  Tags:    [cyan]{tag_count}[/cyan]",
            border_style="cyan",
        ))
    finally:
        conn.close()


@cli.command()
@click.option("-n", "--limit", default=10, help="Number of recent entries")
@click.pass_context
def recent(ctx: click.Context, limit: int) -> None:
    """Show most recently updated entries."""
    conn = get_connection(ctx.obj["db_path"])
    try:
        entries = list_entries(conn, limit=limit)
        if not entries:
            console.print("[dim]No entries yet.[/dim]")
            return

        for e in entries:
            tag_str = f"  [dim]{format_tags(e.tags)}[/dim]" if e.tags else ""
            preview = truncate(e.content, 60) if e.content else ""
            console.print(
                f"[bold cyan]#{e.id}[/bold cyan] {e.title}{tag_str}"
            )
            if preview:
                console.print(f"   [dim]{preview}[/dim]")
            console.print()
    finally:
        conn.close()


@cli.command()
@click.argument("entry_id", type=int)
@click.pass_context
def open(ctx: click.Context, entry_id: int) -> None:
    """Open an entry in your editor for quick editing."""
    conn = get_connection(ctx.obj["db_path"])
    try:
        entry = get_entry(conn, entry_id)
        if not entry:
            console.print(f"[red]Entry #{entry_id} not found.[/red]")
            sys.exit(1)

        new_content = open_editor(entry.content)
        if new_content != entry.content:
            entry.content = new_content
            update_entry(conn, entry)
            console.print(f"[green]Entry #{entry.id} updated![/green]")
        else:
            console.print("[dim]No changes.[/dim]")
    finally:
        conn.close()


if __name__ == "__main__":
    cli()
