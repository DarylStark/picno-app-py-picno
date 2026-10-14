"""Module with a Filter class for Images."""

from dataclasses import dataclass, field
from enum import Enum
from types import NoneType, UnionType
from typing import Any, get_args

from sqlmodel import Column, SQLModel

from picno.specs import (
    AllSpecification,
    AnySpecification,
    FieldIsSpecification,
    NotSpecification,
    NumercFieldSpecification,
    Specification,
    SpecType,
    StrContainsSpecification,
)

# TODO: Add filtering on relationships


def _annotation_contains_type(annotation: Any, search_type: type) -> bool:  # ruff: ignore[ANN401]
    """Check if a type list contains a specific object."""
    if isinstance(annotation, UnionType):
        return any(
            _annotation_contains_type(arg, search_type)
            for arg in get_args(annotation)
        )

    return annotation is search_type or issubclass(annotation, search_type)


def _annotation_real_type(annotation: Any) -> type | None:  # noqa: ANN401
    if isinstance(annotation, UnionType):
        args = [
            arg
            for arg in get_args(annotation)
            if arg is not None and arg is not NoneType
        ]
        if len(args) == 1:
            return args[0]
        return None
    return annotation


def _get_column(model: type[SQLModel], column: str) -> Column | None:
    table = getattr(model, '__table__', None)
    if table is None:
        return None

    col = table.columns.get(column)
    if isinstance(col, Column):
        return col

    return None


@dataclass
class FilterField:
    """Field to filter on."""

    name: str
    is_unique: bool
    field_type: type


@dataclass
class FilterValue[ValueType]:
    """Dataclass for a filter value."""

    value: ValueType
    case_sensistive: bool = False
    contains: bool = False
    negate: bool = False


@dataclass
class FilterGivenValue[ValueType]:
    """The filter values."""

    name: str
    precise_value: FilterValue[ValueType] | None = None
    precise_value_gt: ValueType | None = None
    precise_value_ge: ValueType | None = None
    precise_value_lt: ValueType | None = None
    precise_value_le: ValueType | None = None
    any_field: list[FilterValue[ValueType]] = field(default_factory=list)


class Filter[SqlTable: SQLModel]:
    """Filter type."""

    def __init__(self, model: type[SqlTable]) -> None:
        """Retrieve the correct filtering fields."""
        self._filter_fields: dict[str, FilterField] = {}
        self._model = model

        possible_types = [str, int, bool, Enum]

        for field_name, field_type in self._model.model_fields.items():
            column = _get_column(self._model, field_name)
            if column is None:
                continue
            is_unique = getattr(column, 'unique', True)

            field_annotation_type = None
            for possible_type in possible_types:
                if _annotation_contains_type(
                    field_type.annotation, possible_type
                ):
                    field_annotation_type = _annotation_real_type(
                        field_type.annotation
                    )
                    pass

            if field_annotation_type is None:
                continue

            self._filter_fields[field_name] = FilterField(
                name=field_name,
                is_unique=is_unique,
                field_type=field_annotation_type,
            )

    def _get_field_is_spec(
        self, field_name: str, filter: FilterValue
    ) -> list[Specification]:
        value = filter.value
        if not isinstance(filter.value, list):
            value = [filter.value]

        if filter.contains:
            return [
                StrContainsSpecification(
                    model=self._model,
                    field_name=field_name,
                    search_value=v,
                    case_insensitive=filter.case_sensistive,
                )
                for v in value
            ]
        return [
            FieldIsSpecification(
                model=self._model,
                field_name=field_name,
                expected_value=filter.value,
                case_insensitive=filter.case_sensistive,
            )
            for v in value
        ]

    def get_specification(  # noqa: PLR0912
        self, given_values: list[FilterGivenValue]
    ) -> Specification[SqlTable] | None:
        """Create a specification from given filter values."""
        if len(given_values) == 0:
            return None

        all_spec = AllSpecification[SqlTable]()
        for given_value in given_values:
            if given_value.precise_value:
                for spec in self._get_field_is_spec(
                    given_value.name, given_value.precise_value
                ):
                    if given_value.precise_value.negate:
                        all_spec.append(NotSpecification(spec))
                    else:
                        all_spec.append(spec)

            if given_value.any_field:
                any_spec = AnySpecification()
                for filter in given_value.any_field:
                    for spec in self._get_field_is_spec(
                        given_value.name, filter
                    ):
                        if filter.negate:
                            any_spec.append(NotSpecification(spec))
                        else:
                            any_spec.append(spec)
                all_spec.append(any_spec)

            for operator in [
                ('precise_value_lt', SpecType.LT),
                ('precise_value_gt', SpecType.GT),
                ('precise_value_le', SpecType.LE),
                ('precise_value_ge', SpecType.GE),
            ]:
                field = getattr(given_value, operator[0], 0)
                if field:
                    all_spec.append(
                        NumercFieldSpecification[SqlTable, int](
                            self._model,
                            given_value.name,
                            field,
                            spec_type=operator[1],
                        )
                    )

        return all_spec

    @property
    def filter_fields(self) -> dict[str, FilterField]:
        """Property for all filter fields."""
        return self._filter_fields
