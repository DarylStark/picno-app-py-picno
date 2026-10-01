"""Module with the `pico labels` options."""

from typer import Argument, Context, Option, Typer

from .cli_context import get_initialized_project
from .exceptions import LabelDoesNotExistError
from .specs_labels import (
    LabelFilter,
    NameIsLabelSpec,
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
    (_, _, db) = get_initialized_project(ctx)

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
    for label in labels:
        print(label)


@labels.command(name='add', help='Create a label')
def add(
    ctx: Context, name: str = Argument(help='The name of the label to create')
) -> None:
    """Add a label."""
    (_, _, db) = get_initialized_project(ctx)
    db.create_label(name=name)


@labels.command(name='mv', help='Rename a label')
def mv(
    ctx: Context,
    old_name: str = Argument(help='Current name of the label'),
    new_name: str = Argument(help='New name of the label'),
) -> None:
    """Rename a label."""
    (_, _, db) = get_initialized_project(ctx)

    label = db.get_labels(
        NameIsLabelSpec(name=old_name, case_insensitive=False)
    )
    if len(label) == 1:
        db.update_label(label[0].id or 0, new_name)
    else:
        raise LabelDoesNotExistError(f'Label "{old_name}" does not exist')


@labels.command(name='rm', help='Delete a label')
def rm(
    ctx: Context,
    name: str = Argument(help='The name of the label to delete'),
) -> None:
    """Delete a label."""
    (_, _, db) = get_initialized_project(ctx)

    label = db.get_labels(NameIsLabelSpec(name=name, case_insensitive=False))
    if len(label) == 1:
        db.delete_label(label[0].id or 0)
    else:
        raise LabelDoesNotExistError(f'Label "{name}" does not exist')
