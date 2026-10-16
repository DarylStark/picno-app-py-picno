"""Module with CLI helper functions."""

import inspect
from collections.abc import Callable, Sequence
from datetime import date
from enum import Enum
from typing import Any

from rich.console import Console
from rich.prompt import Confirm
from typer import Option
from typer._click.core import Context

from picno.cli_context import get_initialized_project
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


def replace_args_with_arg[T](
    shared_args: list[inspect.Parameter],
    param_name: str,
    param_builder: Callable[[dict[str, Any], dict[str, Any]], T | None],
) -> Callable:
    """Decorator to replace multiple args with one arg.

    Can be used if you want to create a function with one or more args that
    are going to be replaces by one arg. For instance, if you want a function
    that takes in the args `id` and `name` and use that into one parameter
    called `resource`, you call this method like this:

        @replace_args_with_arg(
            [
                inspect.Parameter(name='id'),
                inspect.Parameter(name='name')
            ],
            'resource',
            make_resource(id, name)
        )
        def (resource):
            # ... do something with resource

    The `make_resource` function will take the "fake" parameters and create the
    resource object that is passed to the function.

    This can be used for instance when you want to add filters to mulitple
    functions that always have to be parsed the same way.
    """

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
                },
                kwargs,
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
    """Add filters from a CliFilterArgGenerator to the function.

    Will parse the given filters and give a ResourceFilter object in the given
    parameter called `param`.
    """

    def decorator(func: Callable) -> Callable:
        """Decorator to add filters to CLI commands."""
        filter_args: list[inspect.Parameter] = (
            filter_generator.signature_parameters
        )

        return replace_args_with_arg(
            filter_args,
            param_name=param_name,
            param_builder=filter_generator.parse_args,
        )(func)

    return decorator


def process_force(params: dict[Any, bool], all_kwargs: dict[Any, str]) -> bool:  # noqa: F821
    """Processor the `force` flag."""
    ctx = all_kwargs.get('ctx')
    if not isinstance(ctx, Context):
        raise TypeError('No valid context given')

    if 'force' in params and 'ctx' in all_kwargs:
        (cli_ctx, _, _, _) = get_initialized_project(ctx)
        return cli_ctx.quiet or params.get('force', False)
    return params.get('force', True)


def with_force_flag(*, param_name: str = '_force') -> Callable:
    """Add a force flag to a Typer CLI method.

    Connect the `force` flag to the `process_force` method that and gives the
    return value to the `_force` flag.
    """

    def decorator(func: Callable) -> Callable:
        """Decorator to add filters to CLI commands."""
        return replace_args_with_arg(
            [
                inspect.Parameter(
                    name='force',
                    kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    annotation=bool,
                    default=Option(
                        default=False,
                        help='Do not prompt for confirmation.',
                    ),
                )
            ],
            param_name=param_name,
            param_builder=process_force,
        )(func)

    return decorator


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
