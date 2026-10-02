"""Module with the `pico persons` options."""

from typer import Argument, Context, Option, Typer

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
) -> None:
    """List the persons in the database."""
    (_, _, db, console) = get_initialized_project(ctx)

    spec = build_person_spec(
        PersonFilter(
            name=name,
            iname=iname,
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
            ],
        )
    else:
        console.print('[yellow]No persons match the filter[/yellow]')


@persons.command(name='add', help='Create a person')
def add(
    ctx: Context, name: str = Argument(help='The name of the person to create')
) -> None:
    """Add a person."""
    (_, _, db, console) = get_initialized_project(ctx)
    db.create_person(name=name)
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
