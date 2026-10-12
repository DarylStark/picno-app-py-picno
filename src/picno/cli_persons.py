"""Module with the `pico persons` options."""

import inspect
from collections.abc import Callable

from typer import Argument, Context, Option, Typer

from .cli_context import get_initialized_project
from .cli_format import TableColumn, print_table
from .cli_helpers import date_string_to_date, shared_args
from .database import RetrieveOption
from .specs_persons import PersonFilter

persons = Typer(name='persons', help='Person management')


def with_persons_filter(param_name: str) -> Callable:
    """Create a decorator for a Persons Filter."""

    def decorator(func: Callable) -> Callable:
        """Decorator to add filters to CLI commands."""
        return shared_args(
            [
                inspect.Parameter(
                    'name',
                    kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    annotation=str | None,
                    default=Option(
                        default=None,
                        help='Filter on specific name',
                        rich_help_panel='Filtering',
                    ),
                ),
                inspect.Parameter(
                    'iname',
                    kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    annotation=str | None,
                    default=Option(
                        default=None,
                        help='Filter on a specific name (case insensitive)',
                        rich_help_panel='Filtering',
                    ),
                ),
                inspect.Parameter(
                    'name_contains',
                    kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    annotation=str | None,
                    default=Option(
                        default=None,
                        help='Filter on a text in the name <repeatable>',
                        rich_help_panel='Filtering',
                    ),
                ),
                inspect.Parameter(
                    'iname_contains',
                    kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    annotation=str | None,
                    default=Option(
                        default=None,
                        help=(
                            'Filter on a text in the name (case insensitive) '
                            '<repeatable>'
                        ),
                        rich_help_panel='Filtering',
                    ),
                ),
                inspect.Parameter(
                    'label',
                    kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    annotation=list[str] | None,
                    default=Option(
                        default=None,
                        help='Filter on a specific label <repeatable>',
                        rich_help_panel='Filtering',
                    ),
                ),
            ],
            param_name=param_name,
            param_builder=PersonFilter.build_from_locals,
        )(func)

    return decorator


@persons.command(name='ls', help='List persons')
@with_persons_filter('_filter')
def ls(
    _filter: PersonFilter,
    ctx: Context,
) -> None:
    """List the persons in the database."""
    (_, _, db, console) = get_initialized_project(ctx)

    # Retrieve the persons
    persons = db.get_persons(
        _filter.get_specifications(),
        options=[RetrieveOption.LOAD_PERSON_LABELS],
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
@with_persons_filter('_filter')
def set_birthdate(
    _filter: PersonFilter,
    ctx: Context,
    birthdate: str = Argument(help='Birthdate for the person (YYYY-MM-DD)'),
) -> None:
    """Set the birthdate for a person."""
    (_, _, db, console) = get_initialized_project(ctx)
    persons = db.set_birthdate_for_persons(
        date_string_to_date(birthdate),
        specification=_filter.get_specifications(),
    )
    console.print(f'Set birthdate for {len(persons)} persons')


@persons.command(
    name='delete-birthdate', help='Delete the birthdate for a person'
)
@with_persons_filter('_filter')
def delete_birthdate(
    _filter: PersonFilter,
    ctx: Context,
) -> None:
    """Delete the birthdate for a person."""
    (_, _, db, console) = get_initialized_project(ctx)
    persons = db.set_birthdate_for_persons(
        None, specification=_filter.get_specifications()
    )
    console.print(f'Deleted birthdate for {len(persons)} persons')


@persons.command(name='rm', help='Delete a person')
@with_persons_filter('_filter')
def rm(
    _filter: PersonFilter,
    ctx: Context,
) -> None:
    """Delete a person."""
    (_, _, db, console) = get_initialized_project(ctx)
    persons = db.delete_persons(_filter.get_specifications())
    console.print(f'Deleted {persons} persons')


@persons.command(name='label', help='Label specific persons')
@with_persons_filter('_filter')
def label(
    _filter: PersonFilter,
    ctx: Context,
    label_name: str = Argument(help='The name of the label to add'),
) -> None:
    """Remove a label from persons."""
    (_, _, db, console) = get_initialized_project(ctx)
    persons = db.add_label_to_persons(
        label_name, specification=_filter.get_specifications()
    )
    console.print(f'Added label "{label_name}" to {len(persons)} persons')


@persons.command(name='unlabel', help='Unlabel specific persons')
@with_persons_filter('_filter')
def unlabel(
    _filter: PersonFilter,
    ctx: Context,
    label_name: str = Argument(help='The name of the label to remove'),
) -> None:
    """Add a label to persons."""
    (_, _, db, console) = get_initialized_project(ctx)
    persons = db.remove_label_from_persons(
        label_name, specification=_filter.get_specifications()
    )
    console.print(f'Removed label "{label_name}" from {len(persons)} persons')
