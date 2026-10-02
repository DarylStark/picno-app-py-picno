"""Module with the `pico persons` options."""

from typer import Argument, Context, Option, Typer

from picno.cli_helpers import date_string_to_date
from picno.database import CLEARFIELD

from .cli_context import get_initialized_project
from .cli_format import TableColumn, print_table
from .exceptions import PersonDoesNotExistError
from .specs_persons import NameIsPersonSpec, PersonFilter, build_person_spec

persons = Typer(name='persons', help='Person management')


@persons.command(name='ls', help='List persons')
def ls(
    ctx: Context,
    name: str | None = Option(default=None, help='Filter on a specific name'),
    iname: str | None = Option(
        default=None, help='Filter on a specific name (case insensitive)'
    ),
    name_contains: list[str] | None = Option(
        default=None, help='Filter on a text in the name <repeatable>'
    ),
    iname_contains: list[str] | None = Option(
        default=None,
        help='Filter on a text in the name (case insensitive) <repeatable>',
    ),
) -> None:
    """List the persons in the database."""
    (_, _, db, console) = get_initialized_project(ctx)

    spec = build_person_spec(
        PersonFilter(
            name=name,
            iname=iname,
            name_contains=name_contains,
            iname_contains=iname_contains,
        )
    )

    # Retrieve the persons
    persons = db.get_persons(spec)
    if persons:
        print_table(
            console,
            persons,
            columns=[
                TableColumn('ID', lambda person: person.id),
                TableColumn('Name', lambda person: person.name),
                TableColumn('Birthdate', lambda person: person.birthdate or ''),
            ],
        )
    else:
        console.print('[yellow]No persons match the filter[/yellow]')


@persons.command(name='add', help='Create a person')
def add(
    ctx: Context,
    name: str = Argument(help='The name of the person to create'),
    birthdate: str | None = Option(
        default=None, help='The birthdate of the person to create (YYYY-MM-DD)'
    ),
) -> None:
    """Add a person."""
    (_, _, db, console) = get_initialized_project(ctx)
    db.create_person(name=name, birthdate=date_string_to_date(birthdate))
    console.print(f'Created person "{name}"')


@persons.command(name='mv', help='Rename a person')
def mv(
    ctx: Context,
    old_name: str = Argument(help='Current name of the person'),
    new_name: str = Argument(help='New name of the person'),
) -> None:
    """Rename a person."""
    (_, _, db, console) = get_initialized_project(ctx)

    person = db.get_persons(
        NameIsPersonSpec(name=old_name, case_insensitive=False)
    )
    if len(person) == 1:
        db.update_person(person[0].id or 0, new_name)
        console.print(f'Renamed person "{old_name}" to "{new_name}"')
    else:
        raise PersonDoesNotExistError(f'Person "{old_name}" does not exist')


@persons.command(name='set-birthdate', help='Set the birthdate for a person')
def set_birthdate(
    ctx: Context,
    name: str = Argument(help='Name of the person to set the birthdate for'),
    birthdate: str = Argument(help='Birthdate for the person (YYYY-MM-DD)'),
) -> None:
    """Set the birthdate for a person."""
    (_, _, db, console) = get_initialized_project(ctx)

    person = db.get_persons(NameIsPersonSpec(name=name, case_insensitive=False))
    if len(person) == 1:
        db.update_person(
            person[0].id or 0, birthdate=date_string_to_date(birthdate)
        )
        console.print(f'Set birthdate for "{name}" to "{birthdate}"')
    else:
        raise PersonDoesNotExistError(f'Person "{name}" does not exist')


@persons.command(
    name='delete-birthdate', help='Delete the birthdate for a person'
)
def delete_birthdate(
    ctx: Context,
    name: str = Argument(help='Name of the person to delete the birthdate for'),
) -> None:
    """Delete the birthdate for a person."""
    (_, _, db, console) = get_initialized_project(ctx)

    person = db.get_persons(NameIsPersonSpec(name=name, case_insensitive=False))
    if len(person) == 1:
        db.update_person(person[0].id or 0, birthdate=CLEARFIELD)
        console.print(f'Deleted birthdate for "{name}"')
    else:
        raise PersonDoesNotExistError(f'Person "{name}" does not exist')


@persons.command(name='rm', help='Delete a person')
def rm(
    ctx: Context,
    name: str = Argument(help='The name of the person to delete'),
) -> None:
    """Delete a person."""
    (_, _, db, console) = get_initialized_project(ctx)

    person = db.get_persons(NameIsPersonSpec(name=name, case_insensitive=False))
    if len(person) == 1:
        db.delete_person(person[0].id or 0)
        console.print(f'Deleted person "{name}"')
    else:
        raise PersonDoesNotExistError(f'Person "{name}" does not exist')
