"""Module with the ResourceFilter class."""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from types import NoneType, UnionType
from typing import Any, Self, get_args, override

from sqlmodel import SQLModel

from picno.specs import (
    AllSpecification,
    AnySpecification,
    FieldIsSpecification,
    NotSpecification,
    NumercFieldSpecification,
    NumericOperatorType,
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
            r'^(?P<ci>\^)?(?P<neg>!)?(?P<exact>=)?(?P<value>.*)$', value
        )

        if not match or not match.group('value'):
            # TODO: Custom exception
            raise ValueError('Filter value is incorrect')

        return FilterValueStr[SqlTable](
            model=model,
            field=field_name,
            value=match.group('value'),
            is_exact=match.group('exact') is not None,
            is_case_sensitive=match.group('ci') is not None,
            is_negated=match.group('neg') is not None,
            is_any=is_any,
        )


@dataclass
class FilterValueInt[SqlTable: SQLModel](FilterValue[SqlTable, int | str]):
    """A value for a filter for a string."""

    operator_type: NumericOperatorType = NumericOperatorType.EQ

    @override
    def _as_spec(self) -> Specification[SqlTable]:
        """Generate a specification for this filter."""
        # TODO: Implement
        spec = NumercFieldSpecification(
            self.model,
            self.field,
            int(self.value),
            operator_type=self.operator_type,
        )
        return spec

    @override
    @classmethod
    def from_value(
        cls,
        model: type[SqlTable],
        field_name: str,
        value: int | str,
        *,
        is_any: bool = False,
    ) -> FilterValueInt:
        """Create a object from value."""
        is_negated = False
        operator_type = NumericOperatorType.EQ
        if isinstance(value, str):
            match = re.match(r'^(?P<op>(>|<|~|>=|<=))?(?P<nr>[0-9]+)$', value)
            if not match or not match.group('nr'):
                raise ValueError(f'Incorrect value for integer: {value}')

            operators = {
                '<': NumericOperatorType.LT,
                '>': NumericOperatorType.GT,
                '>=': NumericOperatorType.GE,
                '<=': NumericOperatorType.LE,
            }

            op = match.group('op')
            if op:
                if op == '~':
                    is_negated = True
                operator_type = operators.get(op, NumericOperatorType.EQ)
            real_value = match.group('nr')
        else:
            real_value = value

        return FilterValueInt[SqlTable](
            model=model,
            field=field_name,
            value=int(real_value),
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
class ResourceFieldFilter[SqlTable: SQLModel]:
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

    fields: dict[str, ResourceFieldFilter[SqlTable]]

    def as_spec(self) -> Specification[SqlTable]:
        """Generate a specification for this filter."""
        all_spec = AllSpecification[SqlTable]()

        for field_filter in self.fields.values():
            for spec in field_filter.as_spec():
                all_spec.append(spec)

        return all_spec


@dataclass
class FilterField[ValueType]:
    """Class for a field that can be filtered on."""

    name: str
    type: type[ValueType]
    value_type: type[FilterValue]


class FilterBuilder[SqlTable: SQLModel]:
    """A class that can filter resources."""

    def __init__(self, model: type[SqlTable]) -> None:
        """Set the values."""
        self._model = model
        self._fields: dict[str, FilterField] = {}

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

    def _generate_from_model_fields(self) -> None:
        """Generate fields from the model fields."""
        for field_name, field_type in self._model.model_fields.items():
            value_types: dict[type, type[FilterValue]] = {
                str: FilterValueStr,
                int: FilterValueInt,
            }
            annotation = self._get_type_from_annotation(field_type.annotation)
            self._fields[field_name] = FilterField(
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
        flt: ResourceFieldFilter[SqlTable],
    ) -> None:
        """Create a Filter Value and append it to a Filter object."""
        if field_name not in self.fields:
            # TODO: Custom exception
            raise ValueError(f'Field "{field_name}" cannot be filtered on')

        field = self.fields[field_name]
        flt_value = field.value_type.from_value(
            model=self._model, field_name=field_name, value=value, is_any=is_any
        )

        if flt_value.is_any:
            flt.any_spec.append(flt_value)
        else:
            flt.all_spec.append(flt_value)

    def convert_arguments_to_filter_objects(
        self, arguments: dict[str, str | int | bool | list[str] | list[int]]
    ) -> ResourceFilter[SqlTable]:
        """Convert given arguments to FilterValue objects."""
        filter_values: dict[str, ResourceFieldFilter[SqlTable]] = {}
        for argument, value in arguments.items():
            field_name, is_any = self._get_argument_properties(argument)
            flt = filter_values.setdefault(
                field_name, ResourceFieldFilter[SqlTable](field=field_name)
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
