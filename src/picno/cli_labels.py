"""Module with the `pico labels` options."""

from typer import Argument, Context, Option, Typer

from picno.cli_helpers import (
    FilterParamBuilder,
    create_delete_confirm_callback,
    create_update_confirm_callback,
    with_filters,
)
from picno.filter import Filter
from picno.model import Label
from picno.specs import Specification

from .cli_context import get_initialized_project
from .cli_format import TableColumn, print_table

labels = Typer(name='labels', help='Label management')
filter = Filter(Label)
filter_builder = FilterParamBuilder(filter)


@labels.command(name='ls', help='List labels')
@with_filters(filter_builder)
def ls(
    _filter: Specification[Label],
    ctx: Context,
) -> None:
    """List the labels in the database."""
    (_, _, db, console) = get_initialized_project(ctx)
    # Retrieve the labels
    labels = db.get_labels(specification=_filter)
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
    force: bool = Option(default=False, help="Don't ask for confirmation"),
) -> None:
    """Rename a label."""
    (_, _, db, console) = get_initialized_project(ctx)
    select_callback = create_update_confirm_callback(force, console, 'name')
    db.rename_label(old_name, new_name, select_callback=select_callback)
    console.print(f'Renamed label "{old_name}" to "{new_name}"')


@labels.command(name='rm', help='Delete a label')
@with_filters(filter_builder)
def rm(
    _filter: Specification[Label],
    ctx: Context,
    force: bool = Option(default=False, help="Don't ask for confirmation"),
) -> None:
    """Delete a label."""
    (_, _, db, console) = get_initialized_project(ctx)
    select_callback = create_delete_confirm_callback(force, console, 'name')
    labels = db.delete_labels(
        specification=_filter,
        select_callback=select_callback,
    )
    console.print(f'Deleted {labels} labels')
