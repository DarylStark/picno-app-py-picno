"""Module with a class to generate Typer args for filters."""

import inspect
from typing import Any

from sqlmodel import SQLModel
from typer import Option

from picno.resource_filter import FilterBuilder, ResourceFilter


class CliFilterArgGenerator[SqlTable: SQLModel]:
    """Class to generate Typer args for filters."""

    def __init__(self, model: type[SqlTable]) -> None:
        """Set default values."""
        self._model = model
        self._resource_filter = FilterBuilder(self._model)
        self._signature_parameters: list[inspect.Parameter] = []

    @property
    def signature_parameters(self) -> list[inspect.Parameter]:
        """Get the signature parameters."""
        if not self._signature_parameters:
            self._generate_parameters()
        return self._signature_parameters

    def _build_annotation(
        self, field_type: type, *, multiple: bool = True
    ) -> Any:  # noqa: ANN401
        """Build annotation for a specific type."""
        if multiple:
            return list[field_type] | None  # ty: ignore[invalid-type-form]
        return field_type | None

    def _generate_parameters_for_str(
        self, field: str
    ) -> list[inspect.Parameter]:
        """Generate a Parameters for a string field."""
        return [
            inspect.Parameter(
                name=field_name,
                kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
                annotation=self._build_annotation(str, multiple=True),
                default=Option(
                    default=None,
                    help='The filter',
                    rich_help_panel='FILTERRRRR',
                ),
            )
            for field_name in (field, f'{field}__all')
        ]

    def _generate_parameters(self) -> None:
        """Generate the signature parameters."""
        for field, field_type in self._resource_filter.fields.items():
            if field_type is str:
                self._signature_parameters.extend(
                    self._generate_parameters_for_str(field)
                )

    def parse_args(
        self, args: dict[str, str | int | bool | list[str] | list[int]]
    ) -> ResourceFilter[SqlTable]:
        """Parse arguments into a ResourceFilter model."""
        return self._resource_filter.convert_arguments_to_filter_objects(args)
