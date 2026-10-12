"""Module with CLI helper functions."""

import inspect
from collections.abc import Callable
from dataclasses import fields
from datetime import date
from types import UnionType
from typing import Any, get_args, get_origin

from typer import Option

from picno.filter import Filter

from .exceptions import InvalidArgumentInputError


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
    param_builder: Callable[[dict[str, Any]], T],
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
            # filter = param_type.build_from_locals(shared_kwargs)
            filter = param_builder(shared_kwargs)
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


def contains_list_type(tp: Any) -> bool:  # ruff: ignore[ANN401]
    """Check if a type list contains a `list` object."""
    origin = get_origin(tp)

    if origin is UnionType:
        return any(contains_list_type(arg) for arg in get_args(tp))

    return origin is list


def with_filtering(
    filter: type[Filter],
    *,
    param_name: str = '_filter',
    filter_prefix: str | None = None,
    filter_group: str = 'Filter',
) -> Callable:
    """Create a decorator for a filter arguments."""

    def decorator(func: Callable) -> Callable:
        """Decorator to add filters to CLI commands."""
        filter_args: list[inspect.Parameter] = []

        for field in fields(filter):
            help_text_notes: list[str] = []
            field_name_splitted = field.name.split('__')
            field_name = field_name_splitted[0]
            arg_name = field.name
            flags = (
                field_name_splitted[1].split('_')
                if len(field_name_splitted) == 2
                else []
            )
            if 'ci' in flags:
                help_text_notes.append('case insensitive')
            if 'contains' in flags:
                help_text_notes.append('containing')

            if contains_list_type(field.type):
                help_text_notes.append('repeatable')

            help_text = f'Filter on field "{field_name}"'
            if help_text_notes:
                help_text += f' ({", ".join(help_text_notes)})'

            if filter_prefix:
                arg_name = f'{filter_prefix}_{field.name}'

            filter_args.append(
                inspect.Parameter(
                    arg_name,
                    kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    annotation=field.type,
                    default=Option(
                        default=None,
                        help=help_text,
                        rich_help_panel=filter_group,
                    ),
                )
            )

        return shared_filter_args(
            filter_args,
            param_name=param_name,
            param_builder=filter.build_from_locals,
        )(func)

    return decorator
