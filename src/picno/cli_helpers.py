"""Module with CLI helper functions."""

import inspect
from collections.abc import Callable, Sequence
from datetime import date
from enum import Enum
from typing import Any, TypeVar

from rich.console import Console
from rich.prompt import Confirm
from sqlmodel import SQLModel

from picno.cli_filter_arg_generator import CliFilterArgGenerator

from .exceptions import InvalidArgumentInputError


class Noun(Enum):
    """Enum class for nouns."""

    DELETING = 'Deleting'
    UPDATING = 'Updating'
    LABELLING = 'Labelling'
    UNLABELLING = 'Unlabelling'


def date_string_to_date(date_str: str | None) -> date | None:
    """Convert a date string into a date object.

    Arguments:
        date_str (str | None): the date in YYYY-MM-DD format or a None object.

    Returns:
        A `date` object if the given date could be converted, or None if the
        date couldn't be converted.
    """
    try:
        parsed_date = date.fromisoformat(date_str) if date_str else None
    except ValueError as e:
        raise InvalidArgumentInputError(
            'Date should be in YYYY-MM-DD format'
        ) from e
    return parsed_date


def shared_filter_args[T](
    shared_args: list[inspect.Parameter],
    param_name: str,
    param_builder: Callable[[dict[str, Any]], T | None],
) -> Callable:
    """Decorator to add filters to CLI commands."""

    def decorator(func: Callable) -> Callable:
        sig = inspect.signature(func)
        params = list(sig.parameters.values())

        def inner(*args: list[Any], **kwargs: dict[str, Any]) -> None:
            shared_kwargs = {
                shared_kwarg.name: kwargs[shared_kwarg.name]
                for shared_kwarg in shared_args
            }
            filter = param_builder(
                {
                    filter: value
                    for filter, value in shared_kwargs.items()
                    if value is not None
                }
            )
            kwargs = {
                kwarg[0]: kwarg[1]
                for kwarg in kwargs.items()
                if kwarg[0] not in shared_kwargs
            }
            return func(filter, *args, **kwargs)

        # Remove filter from params
        params = [param for param in params if param.name != param_name]

        # Create the new function signature
        inner.__signature__ = inspect.Signature(params + shared_args)  # ty: ignore[unresolved-attribute]
        return inner

    return decorator


def with_filters(
    filter_generator: CliFilterArgGenerator, *, param_name: str = '_filter'
) -> Callable:
    """Create a decorator for a filter arguments."""

    def decorator(func: Callable) -> Callable:
        """Decorator to add filters to CLI commands."""
        filter_args: list[inspect.Parameter] = (
            filter_generator.signature_parameters
        )

        return shared_filter_args(
            filter_args,
            param_name=param_name,
            param_builder=filter_generator.parse_args,
        )(func)

    return decorator


class NumberSpecifier(Enum):
    """Specifiers for numbers."""

    LE = 'le'
    LT = 'lt'
    GE = 'ge'
    GT = 'gt'


SqlTable = TypeVar('SqlTable', bound=SQLModel)


def create_confirm_callback[T](
    force: bool,
    console: Console,
    noun: Noun,
    resource_name_attr: str,
) -> Callable[[Sequence[T]], bool] | None:
    """Create a confirm callback."""
    if force:
        return None

    def confirm(resources: Sequence[T]) -> bool:
        if len(resources) == 0:
            return True
        question = f'{noun.value} [b]{len(resources)}[/b] resources:\n\n'
        resources = sorted(
            resources,
            key=lambda r: getattr(r, resource_name_attr, '--unknown').lower(),
        )
        max_resources_to_display = console.height - 7
        for resource in resources[0:max_resources_to_display]:
            question += ' - "' + getattr(resource, resource_name_attr) + '"\n'
        question += '\n'
        if len(resources) > max_resources_to_display:
            left = len(resources) - max_resources_to_display
            question += (
                f'[i]  (... and {left} other resources '
                'not displayed ...)[/i]\n\n'
            )
        question += 'Do you want to continue?'
        return Confirm.ask(question, console=console)

    return confirm


def create_delete_confirm_callback[T](
    force: bool,
    console: Console,
    resource_name_attr: str,
) -> Callable[[Sequence[T]], bool] | None:
    """Create a confirm callback for deleting items."""
    return create_confirm_callback(
        force, console, Noun.DELETING, resource_name_attr
    )


def create_update_confirm_callback[T](
    force: bool,
    console: Console,
    resource_name_attr: str,
) -> Callable[[Sequence[T]], bool] | None:
    """Create a confirm callback for deleting items."""
    return create_confirm_callback(
        force, console, Noun.UPDATING, resource_name_attr
    )


def create_label_confirm_callback[T](
    force: bool,
    console: Console,
    resource_name_attr: str,
) -> Callable[[Sequence[T]], bool] | None:
    """Create a confirm callback for deleting items."""
    return create_confirm_callback(
        force, console, Noun.LABELLING, resource_name_attr
    )


def create_unlabel_confirm_callback[T](
    force: bool,
    console: Console,
    resource_name_attr: str,
) -> Callable[[Sequence[T]], bool] | None:
    """Create a confirm callback for deleting items."""
    return create_confirm_callback(
        force, console, Noun.UNLABELLING, resource_name_attr
    )
