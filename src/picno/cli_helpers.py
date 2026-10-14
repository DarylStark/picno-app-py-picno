"""Module with CLI helper functions."""

import inspect
from collections.abc import Callable, Sequence
from datetime import date
from enum import Enum
from itertools import product
from typing import Any, TypeVar

from rich.console import Console
from rich.prompt import Confirm
from sqlmodel import SQLModel
from typer import Option

from picno.specs import Specification

from .exceptions import InvalidArgumentInputError
from .filter import (
    Filter,
    FilterField,
    FilterGivenValue,
    FilterValue,
)


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
    builder: FilterParamBuilder, *, param_name: str = '_filter'
) -> Callable:
    """Create a decorator for a filter arguments."""

    def decorator(func: Callable) -> Callable:
        """Decorator to add filters to CLI commands."""
        filter_args: list[inspect.Parameter] = builder.fields
        filter_args.sort(key=lambda x: x.name)

        return shared_filter_args(
            filter_args,
            param_name=param_name,
            param_builder=builder.convert_args_filter,
        )(func)

    return decorator


class NumberSpecifier(Enum):
    """Specifiers for numbers."""

    LE = 'le'
    LT = 'lt'
    GE = 'ge'
    GT = 'gt'


SqlTable = TypeVar('SqlTable', bound=SQLModel)


class FilterParamBuilder[SqlTable: SQLModel]:
    """Class to build filter parameters based on object."""

    def __init__(
        self,
        filter_obj: Filter[SqlTable],
        filter_group: str = 'Filter',
        filter_prefix: str | None = None,
    ) -> None:
        """Set values."""
        self._filter: Filter[SqlTable] = filter_obj
        self._filter_group = filter_group
        self._filter_prefix = filter_prefix
        self._fields = self.create_params()

    def _get_name_for_param(
        self,
        field_type: FilterField,
        *,
        contains: bool = False,
        case_insensitive: bool = False,
        any: bool = False,
        number_specifier: NumberSpecifier | None = None,
        not_flag: bool = False,
    ) -> str:
        name = field_type.name
        flags: list[str] = []
        if not_flag:
            flags.append('not')
        if contains:
            flags.append('contains')
        if case_insensitive:
            flags.append('ci')
        if any:
            flags.append('any')

        if number_specifier is not None:
            flags.append(number_specifier.value)

        if flags:
            combined = '_'.join(flags)
            name = f'{name}__{combined}'

        if not self._filter_prefix:
            return name
        return f'{self._filter_prefix}_{name}'

    def _get_help_text_for_param(self, field: FilterField) -> str:
        return '<Not yet defined>'

    def _get_type_annotation(
        self, field_type: FilterField, *, always_list: bool = False
    ) -> Any:  # noqa: ANN401
        if not always_list:
            return field_type.field_type | None
        return list[field_type.field_type] | None  # ty: ignore[invalid-type-form]

    def _create_param(
        self,
        field_type: FilterField,
        *,
        contains: bool = False,
        case_insensitive: bool = False,
        any: bool = False,
        not_flag: bool = False,
        number_specifier: NumberSpecifier | None = None,
    ) -> inspect.Parameter:
        return inspect.Parameter(
            name=self._get_name_for_param(
                field_type,
                contains=contains,
                case_insensitive=case_insensitive,
                any=any,
                not_flag=not_flag,
                number_specifier=number_specifier,
            ),
            kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
            annotation=self._get_type_annotation(
                field_type, always_list=any | contains
            ),
            default=Option(
                default=None,
                help=self._get_help_text_for_param(field_type),
                rich_help_panel=self._filter_group,
            ),
        )

    def _create_params_for_str(
        self, field_type: FilterField
    ) -> list[inspect.Parameter]:
        rv = []
        if field_type.relationship is None:
            rv = [
                self._create_param(
                    field_type,
                    contains=value[0],
                    case_insensitive=value[1],
                    any=value[2],
                    not_flag=value[3],
                )
                for value in list(product([False, True], repeat=4))
            ]
        else:
            rv = [
                self._create_param(
                    field_type,
                    contains=False,
                    case_insensitive=False,
                    any=False,
                    not_flag=False,
                )
            ]
        return rv

    def _create_params_for_int(
        self, field_type: FilterField
    ) -> list[inspect.Parameter]:
        rv = [
            self._create_param(field_type, number_specifier=specifier)
            for specifier in [
                None,
                NumberSpecifier.GE,
                NumberSpecifier.GT,
                NumberSpecifier.LE,
                NumberSpecifier.LT,
            ]
        ]
        rv.extend(
            [
                self._create_param(
                    field_type, number_specifier=specifier, not_flag=True
                )
                for specifier in [
                    None,
                    NumberSpecifier.GE,
                    NumberSpecifier.GT,
                    NumberSpecifier.LE,
                    NumberSpecifier.LT,
                ]
            ]
        )
        rv.append(self._create_param(field_type, any=True))
        return rv

    def _create_params_for_generic_field(
        self, field_type: FilterField, *, any_field: bool = False
    ) -> list[inspect.Parameter]:
        anies = [False]
        if any_field:
            anies.append(True)
        rv = [
            self._create_param(field_type, any=value, not_flag=False)
            for value in anies
        ]
        rv.extend(
            [
                self._create_param(field_type, any=value, not_flag=True)
                for value in anies
            ]
        )
        return rv

    def _create_params_for_filterfield(
        self, field_type: FilterField
    ) -> list[inspect.Parameter]:
        if field_type.field_type is str:
            return self._create_params_for_str(field_type)
        elif field_type.field_type is int:
            return self._create_params_for_int(field_type)
        elif field_type.field_type is bool:
            return self._create_params_for_generic_field(field_type)
        elif issubclass(field_type.field_type, Enum):
            return self._create_params_for_generic_field(
                field_type, any_field=True
            )
        return []

    def create_params(
        self,
    ) -> list[inspect.Parameter]:
        """Method to create function parameters for filtering."""
        params: list[inspect.Parameter] = []
        for _, field_type in self._filter.filter_fields.items():
            params.extend(self._create_params_for_filterfield(field_type))

        return params

    @property
    def fields(self) -> list[inspect.Parameter]:
        """Get the fields."""
        return self._fields

    def convert_args_filter(
        self, values: dict[str, Any]
    ) -> Specification[SqlTable] | None:
        """Convert given filters to a filter object."""
        filters: dict[str, FilterGivenValue] = {}
        for field, value in values.items():
            splitted_field = field.split('__')
            field_name = splitted_field[0]
            item = filters.get(field_name, FilterGivenValue(name=field_name))
            flags: list[str] = []
            if len(splitted_field) == 2:
                flags = splitted_field[1].split('_')

            case_sensitive = 'ci' in flags
            contains = 'contains' in flags
            any_field = 'any' in flags
            ge_field = 'ge' in flags
            gt_field = 'gt' in flags
            le_field = 'le' in flags
            lt_field = 'lt' in flags
            negate = 'not' in flags

            filter_value = FilterValue(
                value=value,
                case_sensistive=case_sensitive,
                contains=contains,
                negate=negate,
            )

            if any_field:
                item.any_field = [
                    FilterValue(
                        value=any_value,
                        case_sensistive=case_sensitive,
                        contains=contains,
                    )
                    for any_value in value
                ]
            elif ge_field:
                item.precise_value_ge = value
            elif gt_field:
                item.precise_value_gt = value
            elif le_field:
                item.precise_value_le = value
            elif lt_field:
                item.precise_value_lt = value
            else:
                item.precise_value = filter_value

            filters[field_name] = item
        return self._filter.get_specification(list(filters.values()))


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
