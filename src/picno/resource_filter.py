"""Module with the ResourceFilter class."""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from types import NoneType, UnionType
from typing import Any, Self, get_args, override

from sqlmodel import SQLModel

from picno.model import (
    Image,
    ImageLabelLink,
    ImagePersonLink,
    Label,
    Person,
    PersonLabelLink,
)
from picno.specs import (
    AllSpecification,
    AnySpecification,
    FieldIsSpecification,
    NotSpecification,
    NumercFieldSpecification,
    NumericOperatorType,
    RelationshipSpec,
    Specification,
    StrSpecification,
)


@dataclass
class FilterValue[SqlTable: SQLModel, ValueType](ABC):
    """Filter values."""

    value: ValueType
    model: type[SqlTable]
    field: str
    is_any: bool = False
    is_negated: bool = False

    @abstractmethod
    def _as_spec(self) -> Specification[SqlTable]:
        """Get the specification for this filter."""

    def as_spec(self) -> Specification[SqlTable]:
        """Get the specification for this filter."""
        spec = self._as_spec()
        if self.is_negated:
            spec = NotSpecification(spec)
        return spec

    @classmethod
    @abstractmethod
    def from_value(
        cls,
        model: type[SqlTable],
        field_name: str,
        value: Any,  # noqa: ANN401
        *,
        is_any: bool = False,
    ) -> Self:
        """Create a object from value."""


@dataclass
class FilterValueStr[SqlTable: SQLModel](FilterValue[SqlTable, str]):
    """A value for a filter for a string."""

    is_exact: bool = False
    is_case_sensitive: bool = False

    @override
    def _as_spec(self) -> Specification[SqlTable]:
        """Generate a specification for this filter."""
        spec = StrSpecification(
            self.model,
            self.field,
            self.value,
            self.is_exact,
            self.is_case_sensitive,
        )
        return spec

    @override
    @classmethod
    def from_value(
        cls,
        model: type[SqlTable],
        field_name: str,
        value: str,
        *,
        is_any: bool = False,
    ) -> FilterValueStr:
        """Create a object from value."""
        match = re.match(
            r'^(?P<cs>\^)?(?P<neg>~)?(?P<exact>=)?(?P<value>.*)$', value
        )

        if not match or not match.group('value'):
            # TODO: Custom exception
            raise ValueError('Filter value is incorrect')

        return FilterValueStr[SqlTable](
            model=model,
            field=field_name,
            value=match.group('value'),
            is_exact=match.group('exact') is not None,
            is_case_sensitive=match.group('cs') is not None,
            is_negated=match.group('neg') is not None,
            is_any=is_any,
        )


@dataclass
class FilterValueInt[SqlTable: SQLModel](
    FilterValue[SqlTable, None | int | str]
):
    """A value for a filter for a string."""

    operator_type: NumericOperatorType = NumericOperatorType.EQ

    high_value: int | str | None = None
    op_set: bool = False

    @override
    def _as_spec(self) -> Specification[SqlTable]:
        """Generate a specification for this filter."""
        if self.op_set is False and self.value is not None:
            spec = NumercFieldSpecification(
                self.model,
                self.field,
                int(self.value),
                operator_type=NumericOperatorType.EQ,
            )
            return spec

        all_spec = AllSpecification[SqlTable]()

        if self.value:
            low_spec = NumercFieldSpecification(
                self.model,
                self.field,
                int(self.value),
                operator_type=NumericOperatorType.GE,
            )
            all_spec.append(low_spec)

        if self.high_value:
            high_spec = NumercFieldSpecification(
                self.model,
                self.field,
                int(self.high_value),
                operator_type=NumericOperatorType.LE,
            )
            all_spec.append(high_spec)

        return all_spec

    @override
    @classmethod
    def from_value(
        cls,
        model: type[SqlTable],
        field_name: str,
        value: None | int | str,
        *,
        is_any: bool = False,
    ) -> FilterValueInt:
        """Create a object from value."""
        is_negated = False
        operator_type = NumericOperatorType.EQ
        if isinstance(value, str):
            match = re.match(
                r'^(?P<low>[0-9]+)?(?P<op>\.{2})?(?P<high>[0-9]+)?$', value
            )
            if not match or (
                match.group('low') is None and match.group('high') is None
            ):
                # TODO: CustomException
                raise ValueError(f'Incorrect value for integer: {value}')

            low = match.group('low')
            high = match.group('high')

            low_value = int(low) if low else None
            high_value = int(high) if high else None
            op_set = match.group('op') is not None
        else:
            high_value = None
            low_value = int(value) if value else None

        if low_value and high_value and (int(low_value) > int(high_value)):
            # TODO: CustomException
            raise ValueError(
                'Low value cannot be lower then high value: '
                f'{low_value} - {high_value}'
            )

        return FilterValueInt[SqlTable](
            model=model,
            field=field_name,
            value=low_value,
            high_value=high_value,
            op_set=op_set,
            is_any=is_any,
            is_negated=is_negated,
            operator_type=operator_type,
        )


@dataclass
class FilterValueGeneric[SqlTable: SQLModel, ValueType](
    FilterValue[SqlTable, ValueType]
):
    """A value for a filter for generic types."""

    @override
    def _as_spec(self) -> Specification[SqlTable]:
        """Generate a specification for this filter."""
        spec = FieldIsSpecification(self.model, self.field, self.value)
        return spec

    @override
    @classmethod
    def from_value[ClsValueType](
        cls,
        model: type[SqlTable],
        field_name: str,
        value: ClsValueType,
        *,
        is_any: bool = False,
    ) -> FilterValueGeneric[SqlTable, ClsValueType]:
        """Create a object from value."""
        return FilterValueGeneric(
            model=model, field=field_name, value=value, is_any=is_any
        )


@dataclass
class FilterValueRelation[SqlTable: SQLModel, ValueType](
    FilterValue[SqlTable, ValueType]
):
    """A value for a filter for a string."""

    relationship_filter: RelationshipFilter | None = None
    is_case_sensitive: bool = False

    @override
    def _as_spec(self) -> Specification[SqlTable]:
        """Generate a specification for this filter."""
        if not self.relationship_filter:
            raise TypeError('Relationshipfilter not set')

        rf = self.relationship_filter

        return RelationshipSpec(
            rf.model_a,
            rf.model_b,
            rf.link_table,
            rf.link_table_field_a,
            rf.link_table_field_b,
            rf.search_field,
            self.value,
        )

    @override
    @classmethod
    def from_value(
        cls,
        model: type[SqlTable],
        field_name: str,
        value: ValueType,
        *,
        is_any: bool = False,
        relationship_filter: RelationshipFilter | None = None,
    ) -> FilterValueRelation:
        is_negated = False
        if isinstance(value, str) and len(value) > 0:
            is_negated = value[0] == '~'
            if is_negated:
                value = value[1:]  # ty: ignore[invalid-assignment]

        """Create a object from value."""
        return FilterValueRelation(
            model=model,
            field=field_name,
            value=value,
            is_negated=is_negated,
            is_any=is_any,
            relationship_filter=relationship_filter,
        )


@dataclass
class RelationshipFilter[
    SqlTableA: SQLModel,
    SqlTableB: SQLModel,
    SqlTableLink: SQLModel,
    ValueType,
]:
    """Class that specifies a filter for a relationship."""

    model_a: type[SqlTableA]
    model_b: type[SqlTableB]
    link_table: type[SqlTableLink]
    link_table_field_a: str
    link_table_field_b: str
    search_field: str
    search_field_type: type


@dataclass
class ResourceFilterField[SqlTable: SQLModel]:
    """A class that specifies a field that is filtered on."""

    field: str
    # TODO: Reanme these fields; they are not specs!
    any_spec: list[FilterValue] = field(default_factory=list)
    all_spec: list[FilterValue] = field(default_factory=list)

    def as_spec(self) -> list[Specification[SqlTable]]:
        """Generate a specification for this filter."""
        specs: list[Specification[SqlTable]] = []

        for spec in self.all_spec:
            specs.append(spec.as_spec())

        if self.any_spec:
            any_spec = AnySpecification[SqlTable]()
            for spec in self.any_spec:
                any_spec.append(spec.as_spec())
            specs.append(any_spec)

        return specs


@dataclass
class ResourceFilter[SqlTable: SQLModel]:
    """A class for a filter for a model."""

    fields: dict[str, ResourceFilterField[SqlTable]]

    def as_spec(self) -> Specification[SqlTable]:
        """Generate a specification for this filter."""
        all_spec = AllSpecification[SqlTable]()

        for field_filter in self.fields.values():
            for spec in field_filter.as_spec():
                all_spec.append(spec)

        return all_spec


@dataclass
class FilterField[ValueType](ABC):
    """Class for a field that can be filtered on."""

    name: str
    type: type[ValueType]

    @abstractmethod
    def build_filter_value_type(
        self, model: type[SQLModel], value: ValueType, is_any: bool
    ) -> FilterValue:
        """Generate a FilterValue type that fits this filter."""


@dataclass
class FilterFieldModelField[ValueType](FilterField[ValueType]):
    """Class for a field that can be filtered on."""

    value_type: type[FilterValue]

    @override
    def build_filter_value_type(
        self, model: type[SQLModel], value: ValueType, is_any: bool
    ) -> FilterValue:
        """Generate a FilterValue type that fits this filter."""
        return self.value_type.from_value(
            model=model, field_name=self.name, value=value, is_any=is_any
        )


@dataclass
class FilterFieldRelation[ValueType](FilterField[ValueType]):
    """Class for a field that can be filtered on."""

    relationship_filter: RelationshipFilter

    @override
    def build_filter_value_type(
        self, model: type[SQLModel], value: ValueType, is_any: bool
    ) -> FilterValue:
        """Generate a FilterValue type that fits this filter."""
        new_value = value
        if self.relationship_filter.search_field_type is int:
            try:
                new_value = int(value)  # ty: ignore[invalid-argument-type]
            except ValueError as exc:
                # TODO: Custom exception
                raise ValueError(
                    'Value could not be converted to int: "{value}"'
                ) from exc

        return FilterValueRelation.from_value(
            model,
            self.name,
            new_value,
            is_any=is_any,
            relationship_filter=self.relationship_filter,
        )


class ResourceFilterBuilder[SqlTable: SQLModel]:
    """A class that can filter resources."""

    def __init__(
        self,
        model: type[SqlTable],
        *,
        relationship_filters: dict[str, RelationshipFilter] | None = None,
    ) -> None:
        """Set the values."""
        self._model = model
        self._fields: dict[str, FilterField] = {}
        self._relationsip_filters = relationship_filters

    def _get_type_from_annotation(self, annotation: Any) -> type:  # ruff: ignore[ANN401]
        """Check if a type list contains a specific object."""
        if isinstance(annotation, UnionType):
            args = [x for x in get_args(annotation) if x is not NoneType]
            if len(args) == 1:
                return args[0]
            # TODO: Custom exception
            raise TypeError(
                'Type annotation should only contain one non-None type. '
                f'Received: {args}'
            )

        return annotation

    def _generate_fields(self) -> None:
        """Generate the field list."""
        self._generate_from_model_fields()
        self._generate_from_model_relationship_fields()

    def _generate_from_model_relationship_fields(self) -> None:
        """Generate fields from the model fields."""
        if self._relationsip_filters is None:
            return

        for (
            filter_name,
            relationship_filter,
        ) in self._relationsip_filters.items():
            """Generate fields from the relationship fields."""
            self._fields[filter_name] = FilterFieldRelation(
                name=filter_name,
                type=relationship_filter.search_field_type,
                relationship_filter=relationship_filter,
            )

    def _generate_from_model_fields(self) -> None:
        """Generate fields from the model fields."""
        for field_name, field_type in self._model.model_fields.items():
            value_types: dict[type, type[FilterValue]] = {
                str: FilterValueStr,
                int: FilterValueInt,
            }
            annotation = self._get_type_from_annotation(field_type.annotation)
            self._fields[field_name] = FilterFieldModelField(
                name=field_name,
                type=annotation,
                value_type=value_types.get(annotation, FilterValueGeneric),
            )

    @property
    def fields(self) -> dict[str, FilterField]:
        """Property for the fields on which can be filtered."""
        if not self._fields:
            self._generate_fields()
        return self._fields

    def _get_argument_properties(self, argument_name: str) -> tuple[str, bool]:
        """Get the field name from a argument and if it's "all" or not.

        Args:
            argument_name (str): the argument name as given on the CLI. For
                example: '--title--all' or '--title'.

        Return:
            A tuple with the field name ('title' for '--title' and
            '--title-all') and wether it is a 'all' argument or not.
        """
        field_splitted = argument_name.split('__', maxsplit=2)
        field_name = field_splitted[0]
        is_any = False
        if len(field_splitted) == 2 and field_splitted[1] == 'any':
            is_any = True

        return (field_name, is_any)

    def _append_filter_value_to_filter(
        self,
        field_name: str,
        value: str | int | bool,
        is_any: bool,
        flt: ResourceFilterField[SqlTable],
    ) -> None:
        """Create a Filter Value and append it to a Filter object."""
        if field_name not in self.fields:
            # TODO: Custom exception
            raise ValueError(f'Field "{field_name}" cannot be filtered on')

        field = self.fields[field_name]
        flt_value = field.build_filter_value_type(self._model, value, is_any)

        if flt_value.is_any:
            flt.any_spec.append(flt_value)
        else:
            flt.all_spec.append(flt_value)

    def convert_arguments_to_filter_objects(
        self, arguments: dict[str, str | int | bool | list[str] | list[int]]
    ) -> ResourceFilter[SqlTable]:
        """Convert given arguments to FilterValue objects."""
        filter_values: dict[str, ResourceFilterField[SqlTable]] = {}
        for argument, value in arguments.items():
            field_name, is_any = self._get_argument_properties(argument)
            flt = filter_values.setdefault(
                field_name, ResourceFilterField[SqlTable](field=field_name)
            )

            if isinstance(value, list):
                for argument_value in value:
                    self._append_filter_value_to_filter(
                        field_name, argument_value, is_any, flt
                    )
            else:
                self._append_filter_value_to_filter(
                    field_name, value, is_any, flt
                )

        return ResourceFilter(fields=filter_values)


class ResourceFilterBuilderPerson(ResourceFilterBuilder):
    """Convenience class for a filter builder for persons."""

    def __init__(self) -> None:
        """Call the base class with the correct values."""
        super().__init__(
            Person,
            relationship_filters={
                'has_label': RelationshipFilter(
                    Person,
                    Label,
                    PersonLabelLink,
                    'person_id',
                    'label_id',
                    'name',
                    str,
                )
            },
        )


class ResourceFilterBuilderImage(ResourceFilterBuilder):
    """Convenience class for a filter builder for images."""

    def __init__(self) -> None:
        """Call the base class with the correct values."""
        super().__init__(
            Image,
            relationship_filters={
                'has_label': RelationshipFilter(
                    Image,
                    Label,
                    ImageLabelLink,
                    'image_id',
                    'label_id',
                    'name',
                    str,
                ),
                'has_person_tagged': RelationshipFilter(
                    Image,
                    Person,
                    ImagePersonLink,
                    'image_id',
                    'person_id',
                    'name',
                    str,
                ),
            },
        )
