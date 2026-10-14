"""Module with a Filter class for Images."""

from dataclasses import dataclass, field
from enum import Enum
from types import NoneType, UnionType
from typing import Any, get_args

from sqlmodel import Column, SQLModel

from picno.model import Image, ImageLabelLink, ImagePersonLink, Label, Person
from picno.specs import (
    AllSpecification,
    AnySpecification,
    FieldIsSpecification,
    NotSpecification,
    NumercFieldSpecification,
    RelationshipSpec,
    Specification,
    SpecType,
    StrContainsSpecification,
)

# TODO: Add filtering for nullable fields (--camera-makt--not-set, for instance)


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
class RelationshipFilter:
    """Filter fields for a relationship."""

    other_table: type[SQLModel]
    link_table: type[SQLModel]
    link_table_field: str
    link_table_other_field: str
    search_field: str


@dataclass
class FilterField:
    """Field to filter on."""

    name: str
    field_type: type
    is_unique: bool = False
    relationship: RelationshipFilter | None = None


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


@dataclass
class RelationShipFilter:
    """Field for a relationship filter."""

    name: str


class Filter[SqlTable: SQLModel]:
    """Filter type."""

    def __init__(
        self,
        model: type[SqlTable],
        *,
        relationship_filters: dict[str, RelationshipFilter] | None = None,
    ) -> None:
        """Retrieve the correct filtering fields."""
        self._filter_fields: dict[str, FilterField] = {}
        self._model = model
        self._relationship_filters = relationship_filters or {}

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

        if relationship_filters:
            for relation_name, relation_details in relationship_filters.items():
                self._filter_fields[relation_name] = FilterField(
                    name=relation_name,
                    is_unique=False,
                    field_type=str,
                    relationship=relation_details,
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
            if given_value.name in self._relationship_filters:
                filter = self._relationship_filters[given_value.name]
                if not given_value.precise_value:
                    continue
                all_spec.append(
                    RelationshipSpec(
                        model_a=self._model,
                        model_b=filter.other_table,
                        link_table=filter.link_table,
                        link_table_field_a=filter.link_table_field,
                        link_table_field_b=filter.link_table_other_field,
                        search_field=filter.search_field,
                        search_value=given_value.precise_value.value,
                    )
                )
                continue

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


class ImageFilter(Filter[Image]):
    """Filter for images."""

    def __init__(self) -> None:
        """Set default values."""
        super().__init__(
            Image,
            relationship_filters={
                'label': RelationshipFilter(
                    other_table=Label,
                    link_table=ImageLabelLink,
                    link_table_field='image_id',
                    link_table_other_field='label_id',
                    search_field='name',
                ),
                'person': RelationshipFilter(
                    other_table=Person,
                    link_table=ImagePersonLink,
                    link_table_field='image_id',
                    link_table_other_field='person_id',
                    search_field='name',
                ),
            },
        )
