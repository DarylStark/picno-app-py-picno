"""Module with the `pico persons` options."""

from typer import Argument, Context, Option, Typer

from picno.cli_helpers import date_string_to_date
from picno.database import RetrieveOption

from .cli_context import get_initialized_project
from .cli_format import TableColumn, print_table
from .specs_persons import PersonFilter

persons = Typer(name='persons', help='Person management')

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
    'label': Option(
        default=None,
        help='Filter on a specific label <repeatable>',
        rich_help_panel='Filtering',
    ),
}


@persons.command(name='ls', help='List persons')
def ls(
    ctx: Context,
    name: str | None = filter_args['name'],
    iname: str | None = filter_args['iname'],
    name_contains: list[str] | None = filter_args['name_contains'],
    iname_contains: list[str] | None = filter_args['iname_contains'],
    label: list[str] | None = filter_args['label'],
) -> None:
    """List the persons in the database."""
    (_, _, db, console) = get_initialized_project(ctx)
    filter = PersonFilter.build_from_locals(locals())

    # Retrieve the persons
    persons = db.get_persons(
        filter.get_specifications(), options=[RetrieveOption.LOAD_PERSON_LABELS]
    )
    if persons:
        print_table(
            console,
            persons,
            columns=[
                TableColumn('ID', lambda person: person.id),
                TableColumn('Name', lambda person: person.name),
                TableColumn('Birthdate', lambda person: person.birthdate or ''),
                TableColumn(
                    'Labels',
                    lambda person: (
                        ', '.join([label.name for label in person.labels]) or ''
                    ),
                ),
            ],
        )
    else:
        console.print('[yellow]No persons match the filter[/yellow]')


@persons.command(name='add', help='Create a person')
def add(
    ctx: Context,
    name: list[str] = Argument(help='The name of the person to create'),
    birthdate: str | None = Option(
        default=None, help='The birthdate of the person to create (YYYY-MM-DD)'
    ),
) -> None:
    """Add a person."""
    (_, _, db, console) = get_initialized_project(ctx)
    persons = db.create_persons(
        names=name, birthdate=date_string_to_date(birthdate)
    )
    console.print(f'Created {len(persons)} persons')


@persons.command(name='mv', help='Rename a person')
def mv(
    ctx: Context,
    old_name: str = Argument(help='Current name of the person'),
    new_name: str = Argument(help='New name of the person'),
) -> None:
    """Rename a person."""
    (_, _, db, console) = get_initialized_project(ctx)
    db.rename_person(old_name, new_name)
    console.print(f'Renamed person "{old_name}" to "{new_name}"')


@persons.command(name='set-birthdate', help='Set the birthdate for a person')
def set_birthdate(
    ctx: Context,
    name: str = Argument(help='Name of the person to set the birthdate for'),
    birthdate: str = Argument(help='Birthdate for the person (YYYY-MM-DD)'),
) -> None:
    """Set the birthdate for a person."""
    (_, _, db, console) = get_initialized_project(ctx)
    db.set_birthdate_for_person(name, date_string_to_date(birthdate))
    console.print(f'Set birthdate for "{name}" to "{birthdate}"')


@persons.command(
    name='delete-birthdate', help='Delete the birthdate for a person'
)
def delete_birthdate(
    ctx: Context,
    name: str = Argument(help='Name of the person to delete the birthdate for'),
) -> None:
    """Delete the birthdate for a person."""
    (_, _, db, console) = get_initialized_project(ctx)
    db.set_birthdate_for_person(name, None)
    console.print(f'Deleted birthdate for "{name}"')


@persons.command(name='rm', help='Delete a person')
def rm(
    ctx: Context,
    name: str = Argument(help='The name of the person to delete'),
) -> None:
    """Delete a person."""
    (_, _, db, console) = get_initialized_project(ctx)
    db.delete_person_by_name(name)
    console.print(f'Deleted person "{name}"')


@persons.command(name='label', help='Label specific persons')
def label(
    ctx: Context,
    label_name: str = Argument(help='The name of the label to add'),
    name: str | None = filter_args['name'],
    iname: str | None = filter_args['iname'],
    name_contains: list[str] | None = filter_args['name_contains'],
    iname_contains: list[str] | None = filter_args['iname_contains'],
    label: list[str] | None = filter_args['label'],
) -> None:
    """Remove a label from persons."""
    (_, _, db, console) = get_initialized_project(ctx)
    filter = PersonFilter.build_from_locals(locals())

    persons = db.add_label_to_persons(
        label_name, specification=filter.get_specifications()
    )
    console.print(f'Added label "{label_name}" to {len(persons)} persons')


@persons.command(name='unlabel', help='Unlabel specific persons')
def unlabel(
    ctx: Context,
    label_name: str = Argument(help='The name of the label to remove'),
    name: str | None = filter_args['name'],
    iname: str | None = filter_args['iname'],
    name_contains: list[str] | None = filter_args['name_contains'],
    iname_contains: list[str] | None = filter_args['iname_contains'],
    label: list[str] | None = filter_args['label'],
) -> None:
    """Add a label to persons."""
    (_, _, db, console) = get_initialized_project(ctx)
    filter = PersonFilter.build_from_locals(locals())

    persons = db.remove_label_from_persons(
        label_name, specification=filter.get_specifications()
    )
    console.print(f'Removed label "{label_name}" from {len(persons)} persons')
