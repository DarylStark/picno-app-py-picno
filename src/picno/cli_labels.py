"""Module with the `pico labels` options."""

from typer import Argument, Context, Option, Typer

from .cli_context import get_initialized_project
from .cli_format import TableColumn, print_table
from .specs_labels import (
    LabelFilter,
    build_label_spec,
)

labels = Typer(name='labels', help='Label management')


@labels.command(name='ls', help='List labels')
def ls(
    ctx: Context,
    name: str | None = Option(default=None, help='Filter on a specific name'),
    iname: str | None = Option(
        default=None, help='Filter on a specific name (case insensitive)'
    ),
    group_name: str | None = Option(
        default=None, help='Filter on a specific groupname'
    ),
    igroup_name: str | None = Option(
        default=None, help='Filter on a specific groupname (case insensitive)'
    ),
    name_contains: list[str] | None = Option(
        default=None, help='Filter on a text in the name <repeatable>'
    ),
    iname_contains: list[str] | None = Option(
        default=None,
        help='Filter on a text in the name (case insensitive) <repeatable>',
    ),
) -> None:
    """List the labels in the database."""
    (_, _, db, console) = get_initialized_project(ctx)

    spec = build_label_spec(
        LabelFilter(
            name=name,
            iname=iname,
            name_contains=name_contains,
            iname_contains=iname_contains,
            group_name=group_name,
            igroup_name=igroup_name,
        )
    )

    # Retrieve the labels
    labels = db.get_labels(spec)
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
    ctx: Context, name: str = Argument(help='The name of the label to create')
) -> None:
    """Add a label."""
    (_, _, db, console) = get_initialized_project(ctx)
    db.create_label(name=name)
    console.print(f'Created label "{name}"')


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
def rm(
    ctx: Context,
    name: str = Argument(help='The name of the label to delete'),
) -> None:
    """Delete a label."""
    (_, _, db, console) = get_initialized_project(ctx)
    db.delete_label_by_name(name)
    console.print(f'Deleted label "{name}"')
