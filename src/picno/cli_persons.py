"""Module with the `pico persons` options."""

from typer import Argument, Context, Option, Typer

from picno.cli_filter_arg_generator import CliFilterArgGenerator
from picno.model import Person
from picno.resource_filter import (
    ResourceFilter,
    ResourceFilterBuilderPerson,
)

from .cli_context import get_initialized_project
from .cli_format import TableColumn, print_table
from .cli_helpers import (
    create_delete_confirm_callback,
    create_label_confirm_callback,
    create_unlabel_confirm_callback,
    create_update_confirm_callback,
    date_string_to_date,
    with_filters,
    with_force_flag,
    with_sort_field,
)
from .database import RetrieveOption, SortField

persons = Typer(name='persons', help='Person management')
filter_gen = CliFilterArgGenerator(ResourceFilterBuilderPerson())


@persons.command(name='ls', help='List persons')
@with_filters(filter_gen)
@with_sort_field(default_sort='name,id')
def ls(
    _sort: list[SortField] | None,
    _filter: ResourceFilter[Person],
    ctx: Context,
) -> None:
    """List the persons in the database."""
    (_, _, db, console) = get_initialized_project(ctx)

    # Retrieve the persons
    persons = db.get_persons(
        specification=_filter.as_spec(),
        options=[RetrieveOption.LOAD_PERSON_LABELS],
        sorting=_sort,
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
@with_force_flag()
def mv(
    _force: bool,
    ctx: Context,
    old_name: str = Argument(help='Current name of the person'),
    new_name: str = Argument(help='New name of the person'),
) -> None:
    """Rename a person."""
    (_, _, db, console) = get_initialized_project(ctx)
    select_callback = create_update_confirm_callback(_force, console, 'name')
    db.rename_person(old_name, new_name, select_callback=select_callback)
    console.print(f'Renamed person "{old_name}" to "{new_name}"')


@persons.command(name='set-birthdate', help='Set the birthdate for a person')
@with_filters(filter_gen)
@with_force_flag()
def set_birthdate(
    _force: bool,
    _filter: ResourceFilter[Person],
    ctx: Context,
    birthdate: str = Argument(help='Birthdate for the person (YYYY-MM-DD)'),
) -> None:
    """Set the birthdate for a person."""
    (_, _, db, console) = get_initialized_project(ctx)
    select_callback = create_update_confirm_callback(_force, console, 'name')
    persons = db.set_birthdate_for_persons(
        date_string_to_date(birthdate),
        specification=_filter.as_spec(),
        select_callback=select_callback,
    )
    console.print(f'Set birthdate for {len(persons)} persons')


@persons.command(
    name='delete-birthdate', help='Delete the birthdate for a person'
)
@with_filters(filter_gen)
@with_force_flag()
def delete_birthdate(
    _force: bool,
    _filter: ResourceFilter[Person],
    ctx: Context,
) -> None:
    """Delete the birthdate for a person."""
    (_, _, db, console) = get_initialized_project(ctx)
    select_callback = create_update_confirm_callback(_force, console, 'name')
    persons = db.set_birthdate_for_persons(
        None,
        specification=_filter.as_spec(),
        select_callback=select_callback,
    )
    console.print(f'Deleted birthdate for {len(persons)} persons')


@persons.command(name='rm', help='Delete a person')
@with_filters(filter_gen)
@with_force_flag()
def rm(
    _force: bool,
    _filter: ResourceFilter[Person],
    ctx: Context,
) -> None:
    """Delete a person."""
    (_, _, db, console) = get_initialized_project(ctx)
    select_callback = create_delete_confirm_callback(_force, console, 'name')
    persons = db.delete_persons(
        specification=_filter.as_spec(),
        select_callback=select_callback,
    )
    console.print(f'Deleted {persons} persons')


@persons.command(name='label', help='Label specific persons')
@with_filters(filter_gen)
@with_force_flag()
def label(
    _force: bool,
    _filter: ResourceFilter[Person],
    ctx: Context,
    label_name: str = Argument(help='The name of the label to add'),
) -> None:
    """Remove a label from persons."""
    (_, _, db, console) = get_initialized_project(ctx)
    select_callback = create_label_confirm_callback(_force, console, 'name')
    persons = db.add_label_to_persons(
        label_name,
        specification=_filter.as_spec(),
        select_callback=select_callback,
    )
    console.print(f'Added label "{label_name}" to {len(persons)} persons')


@persons.command(name='unlabel', help='Unlabel specific persons')
@with_filters(filter_gen)
@with_force_flag()
def unlabel(
    _force: bool,
    _filter: ResourceFilter[Person],
    ctx: Context,
    label_name: str = Argument(help='The name of the label to remove'),
) -> None:
    """Add a label to persons."""
    (_, _, db, console) = get_initialized_project(ctx)
    select_callback = create_unlabel_confirm_callback(_force, console, 'name')
    persons = db.remove_label_from_persons(
        label_name,
        specification=_filter.as_spec(),
        select_callback=select_callback,
    )
    console.print(f'Removed label "{label_name}" from {len(persons)} persons')
