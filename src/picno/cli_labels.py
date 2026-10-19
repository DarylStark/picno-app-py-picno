"""Module with the `pico labels` options."""

from typer import Argument, Option, Typer
from typer._click.core import Context

from picno.cli_filter_arg_generator import CliFilterArgGenerator
from picno.cli_helpers import (
    OutputFormat,
    create_delete_confirm_callback,
    create_update_confirm_callback,
    with_filters,
    with_force_flag,
    with_sort_field,
)
from picno.cli_output import OutputFormatLabel
from picno.database import SortField
from picno.model import Label
from picno.resource_filter import ResourceFilter, ResourceFilterBuilder

from .cli_context import get_initialized_project

labels = Typer(name='labels', help='Label management')
filter_gen = CliFilterArgGenerator(ResourceFilterBuilder(Label))


@labels.command(name='ls', help='List labels')
@with_filters(filter_generator=filter_gen)
@with_sort_field(default_sort='name,id')
def ls(
    _sort: list[SortField] | None,
    _filter: ResourceFilter[Label],
    ctx: Context,
    output_format: OutputFormat = Option(
        default=OutputFormat.TABLE, help='The way to output data'
    ),
) -> None:
    """List the labels in the database."""
    (_, _, db, console) = get_initialized_project(ctx)
    # Retrieve the labels
    labels = db.get_labels(specification=_filter.as_spec(), sorting=_sort)

    formatter = OutputFormatLabel(console)

    if labels:
        if output_format == OutputFormat.TABLE:
            formatter.as_table(labels, title='Labels')
        elif output_format == OutputFormat.DETAILS:
            formatter.as_details(labels)
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
@with_force_flag()
def mv(
    _force: bool,
    ctx: Context,
    old_name: str = Argument(help='Current name of the label'),
    new_name: str = Argument(help='New name of the label'),
) -> None:
    """Rename a label."""
    (_, _, db, console) = get_initialized_project(ctx)
    select_callback = create_update_confirm_callback(_force, console, 'name')
    db.rename_label(old_name, new_name, select_callback=select_callback)
    console.print(f'Renamed label "{old_name}" to "{new_name}"')


@labels.command(name='rm', help='Delete a label')
@with_filters(filter_generator=filter_gen)
@with_force_flag()
def rm(
    _force: bool,
    _filter: ResourceFilter[Label],
    ctx: Context,
) -> None:
    """Delete a label."""
    (_, _, db, console) = get_initialized_project(ctx)
    select_callback = create_delete_confirm_callback(_force, console, 'name')
    labels = db.delete_labels(
        specification=_filter.as_spec(),
        select_callback=select_callback,
    )
    console.print(f'Deleted {labels} labels')
