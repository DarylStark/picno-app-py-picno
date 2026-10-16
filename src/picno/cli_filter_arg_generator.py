"""Module with a class to generate Typer args for filters."""

import inspect
from enum import Enum
from typing import Any

from sqlmodel import SQLModel
from typer import Option

from picno.resource_filter import ResourceFilter, ResourceFilterBuilder


class CliFilterArgGenerator[SqlTable: SQLModel]:
    """Class to generate Typer args for filters."""

    def __init__(
        self,
        filter_builder: ResourceFilterBuilder[SqlTable],
        *,
        help_text_group: str = 'Fitler',
    ) -> None:
        """Set default values."""
        self._resource_filter = filter_builder
        self._signature_parameters: list[inspect.Parameter] = []
        self._help_text_group = help_text_group

    @property
    def signature_parameters(self) -> list[inspect.Parameter]:
        """Get the signature parameters."""
        if not self._signature_parameters:
            self._generate_parameters()
        return self._signature_parameters

    def _build_annotation(self, field_type: type) -> Any:  # noqa: ANN401
        """Build annotation for a specific type."""
        return list[field_type] | None  # ty: ignore[invalid-type-form]

    def _build_parameter(
        self, field_name: str, field_type: type, *, help_text: str | None = None
    ) -> inspect.Parameter:
        param_help_text = (
            f'Filter on the field "{field_name.split("__", maxsplit=1)[0]}"'
        )

        if help_text:
            param_help_text = f'{param_help_text} ({help_text})'

        return inspect.Parameter(
            name=field_name,
            kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
            annotation=self._build_annotation(field_type),
            default=Option(
                default=None,
                help=param_help_text,
                rich_help_panel=self._help_text_group,
            ),
        )

    def _generate_parameters_generic(
        self, field: str, field_type: type
    ) -> list[inspect.Parameter]:
        """Generate a Parameters for a string field."""
        return [self._build_parameter(field, field_type)]

    def _generate_parameters_for_str(
        self, field: str
    ) -> list[inspect.Parameter]:
        """Generate a Parameters for a string field."""
        return [
            self._build_parameter(
                field_name,
                str,
                help_text='<string value>',
            )
            for field_name in (field, f'{field}__any')
        ]

    def _generate_parameters_for_int(
        self, field: str
    ) -> list[inspect.Parameter]:
        """Generate a Parameters for a string field."""
        return [
            self._build_parameter(
                field_name,
                str,
                help_text='<integer value>',
            )
            for field_name in (field, f'{field}__any')
        ]

    def _generate_parameters(self) -> None:
        """Generate the signature parameters."""
        for field, field_type in self._resource_filter.fields.items():
            if field_type.type is str:
                self._signature_parameters.extend(
                    self._generate_parameters_for_str(field)
                )
            elif field_type.type is int:
                self._signature_parameters.extend(
                    self._generate_parameters_for_int(field)
                )
            elif field_type.type is bool or issubclass(field_type.type, Enum):
                self._signature_parameters.extend(
                    self._generate_parameters_generic(field, field_type.type)
                )
        self._signature_parameters.sort(key=lambda x: x.name)

    def parse_args(
        self,
        args: dict[str, str | int | bool | list[str] | list[int]],
        all_kwargs: dict[Any, str],
    ) -> ResourceFilter[SqlTable]:
        """Parse arguments into a ResourceFilter model."""
        return self._resource_filter.convert_arguments_to_filter_objects(args)
