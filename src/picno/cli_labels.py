"""Module with the `pico labels` options."""

from typer import Argument, Context, Option, Typer

from .cli_context import get_initialized_project
from .cli_format import TableColumn, print_table
from .specs_labels import LabelFilter

labels = Typer(name='labels', help='Label management')

filter_args = {
    'name': Option(
        default=None,
        help='Filter on a specific name',
        rich_help_panel='Filtering',
    ),
    'iname': Option(
        default=None,
        help='Filter on a specific name (case insensitive)',
        rich_help_panel='Filtering',
    ),
    'group_name': Option(
        default=None,
        help='Filter on a specific groupname',
        rich_help_panel='Filtering',
    ),
    'igroup_name': Option(
        default=None,
        help='Filter on a specific groupname (case insensitive)',
        rich_help_panel='Filtering',
    ),
    'name_contains': Option(
        default=None,
        help='Filter on a text in the name <repeatable>',
        rich_help_panel='Filtering',
    ),
    'iname_contains': Option(
        default=None,
        help='Filter on a text in the name (case insensitive) <repeatable>',
        rich_help_panel='Filtering',
    ),
}


@labels.command(name='ls', help='List labels')
def ls(
    ctx: Context,
    name: str | None = filter_args['name'],
    iname: str | None = filter_args['iname'],
    group_name: str | None = filter_args['group_name'],
    igroup_name: str | None = filter_args['igroup_name'],
    name_contains: list[str] | None = filter_args['name_contains'],
    iname_contains: list[str] | None = filter_args['iname_contains'],
) -> None:
    """List the labels in the database."""
    (_, _, db, console) = get_initialized_project(ctx)
    filter = LabelFilter.build_from_locals(locals())

    # Retrieve the labels
    labels = db.get_labels(filter.get_specifications())
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
def rm(
    ctx: Context,
    name: str | None = filter_args['name'],
    iname: str | None = filter_args['iname'],
    group_name: str | None = filter_args['group_name'],
    igroup_name: str | None = filter_args['igroup_name'],
    name_contains: list[str] | None = filter_args['name_contains'],
    iname_contains: list[str] | None = filter_args['iname_contains'],
) -> None:
    """Delete a label."""
    (_, _, db, console) = get_initialized_project(ctx)
    filter = LabelFilter.build_from_locals(locals())
    labels = db.delete_labels(filter.get_specifications())
    console.print(f'Deleted {labels} labels')
