"""Module with the `pico labels` options."""

from typer import Argument, Context, Typer

from picno.cli_helpers import with_filtering

from .cli_context import get_initialized_project
from .cli_format import TableColumn, print_table
from .specs_labels import LabelFilter

labels = Typer(name='labels', help='Label management')


@labels.command(name='ls', help='List labels')
@with_filtering(LabelFilter)
def ls(
    _filter: LabelFilter,
    ctx: Context,
) -> None:
    """List the labels in the database."""
    (_, _, db, console) = get_initialized_project(ctx)
    # Retrieve the labels
    labels = db.get_labels(_filter.get_specifications())
    if labels:
        print_table(
            console,
            labels,
            columns=[
                TableColumn('ID', lambda label: label.id),
                TableColumn('Name', lambda label: label.name),
                TableColumn('Group', lambda label: label.group or ''),
                TableColumn(
                    'Name in group', lambda label: label.label_name or ''
                ),
            ],
        )
    else:
        console.print('[yellow]No labels match the filter[/yellow]')


@labels.command(name='add', help='Create a label')
def add(
    ctx: Context,
    name: list[str] = Argument(help='The name of the label to create'),
) -> None:
    """Add a label."""
    (_, _, db, console) = get_initialized_project(ctx)
    labels = db.create_labels(names=name)
    console.print(f'Created {len(labels)} labels')


@labels.command(name='mv', help='Rename a label')
def mv(
    ctx: Context,
    old_name: str = Argument(help='Current name of the label'),
    new_name: str = Argument(help='New name of the label'),
) -> None:
    """Rename a label."""
    (_, _, db, console) = get_initialized_project(ctx)
    db.rename_label(old_name, new_name)
    console.print(f'Renamed label "{old_name}" to "{new_name}"')


@labels.command(name='rm', help='Delete a label')
@with_filtering(LabelFilter)
def rm(
    _filter: LabelFilter,
    ctx: Context,
) -> None:
    """Delete a label."""
    (_, _, db, console) = get_initialized_project(ctx)
    labels = db.delete_labels(_filter.get_specifications())
    console.print(f'Deleted {labels} labels')
