"""Module with CLI helper functions."""

import inspect
from collections.abc import Callable
from datetime import date
from typing import Any

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


def shared_args[T](
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
