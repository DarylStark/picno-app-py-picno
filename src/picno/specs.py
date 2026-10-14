"""Module with the generic specification."""

from abc import ABC, abstractmethod
from enum import Enum
from typing import override

from sqlalchemy import and_, true
from sqlalchemy.sql.elements import ColumnElement
from sqlmodel import SQLModel, col, false, or_


class Specification[SqlTable](ABC):
    """Generic baseclass for Specifications."""

    @abstractmethod
    def as_sql(self) -> ColumnElement[bool]:
        """Abstract method to create a SQL query object."""


class AndSpecification[SqlTable](Specification[SqlTable]):
    """Specification for AND logic."""

    def __init__(
        self, spec_a: Specification[SqlTable], spec_b: Specification[SqlTable]
    ) -> None:
        """Set the specification."""
        self._spec_a = spec_a
        self._spec_b = spec_b

    @override
    def as_sql(self) -> ColumnElement[bool]:
        """Return the query for the specification."""
        return self._spec_a.as_sql() & self._spec_b.as_sql()


class OrSpecification[SqlTable](Specification[SqlTable]):
    """Specification for OR logic."""

    def __init__(
        self, spec_a: Specification[SqlTable], spec_b: Specification[SqlTable]
    ) -> None:
        """Set the specification."""
        self._spec_a = spec_a
        self._spec_b = spec_b

    @override
    def as_sql(self) -> ColumnElement[bool]:
        """Return the query for the specification."""
        return self._spec_a.as_sql() & self._spec_b.as_sql()


class NotSpecification[SqlTable](Specification[SqlTable]):
    """Specification for NOT logic."""

    def __init__(self, spec: Specification[SqlTable]) -> None:
        """Set the specification."""
        self._spec = spec

    @override
    def as_sql(self) -> ColumnElement[bool]:
        """Return the query for the specification."""
        return ~self._spec.as_sql()


class AllSpecification[SqlTable](Specification[SqlTable]):
    """Specification for ALL logic."""

    def __init__(self) -> None:
        """Create empty list of specifications."""
        self._specs: list[Specification[SqlTable]] = []

    def append(
        self, spec: Specification[SqlTable]
    ) -> AllSpecification[SqlTable]:
        """Add a specification."""
        self._specs.append(spec)
        return self

    @override
    def as_sql(self) -> ColumnElement[bool]:
        """Return the query for the specification."""
        if not self._specs:
            return true()
        return and_(*(spec.as_sql() for spec in self._specs))


class AnySpecification[SqlTable](Specification[SqlTable]):
    """Specification for ALL logic."""

    def __init__(self) -> None:
        """Create empty list of specifications."""
        self._specs: list[Specification[SqlTable]] = []

    def append(
        self, spec: Specification[SqlTable]
    ) -> AnySpecification[SqlTable]:
        """Add a specification."""
        self._specs.append(spec)
        return self

    @override
    def as_sql(self) -> ColumnElement[bool]:
        """Return the query for the specification."""
        if not self._specs:
            return false()
        return or_(*(spec.as_sql() for spec in self._specs))


class ParentSpecification[SqlTable](Specification[SqlTable]):
    """Specification with a parent.

    Can be used to simplify specifications.
    """

    def __init__(self, parent: Specification[SqlTable]) -> None:
        """Set the parent specification."""
        self._parent_spec = parent

    @override
    def as_sql(self) -> ColumnElement[bool]:
        """Returns the SQL code for the specification."""
        return self._parent_spec.as_sql()


class FieldIsSpecification[SqlTable, T2](Specification[SqlTable]):
    """Specification that checks if a specific field is equal."""

    def __init__(
        self,
        model: type[SqlTable],
        field_name: str,
        expected_value: T2,
        case_insensitive: bool = True,
    ) -> None:
        """Set the default values."""
        self._model = model
        self._field_name = field_name
        self._expected_value = expected_value
        self._case_insensitive = case_insensitive

    @override
    def as_sql(self) -> ColumnElement[bool]:
        """Return the query for the specification."""
        field = getattr(self._model, self._field_name)
        if self._case_insensitive:
            return col(field).ilike(self._expected_value)
        return col(field) == self._expected_value


class StrIsSpecification[SqlTable](Specification[SqlTable]):
    """Specification that checks if a specific string is equal."""

    def __init__(
        self,
        model: type[SqlTable],
        field_name: str,
        expected_value: str,
        case_insensitive: bool = True,
    ) -> None:
        """Set the default values."""
        self._model = model
        self._field_name = field_name
        self._expected_value = expected_value
        self._case_insensitive = case_insensitive

    @override
    def as_sql(self) -> ColumnElement[bool]:
        """Return the query for the specification."""
        field = getattr(self._model, self._field_name)
        if self._case_insensitive:
            return col(field).ilike(self._expected_value)
        return col(field) == self._expected_value


class StrContainsSpecification[SqlTable](Specification[SqlTable]):
    """Specification that checks if a specific string is equal."""

    def __init__(
        self,
        model: type[SqlTable],
        field_name: str,
        search_value: str,
        case_insensitive: bool = True,
    ) -> None:
        """Set the default values."""
        self._model = model
        self._field_name = field_name
        self._search_value = search_value
        self._case_insensitive = case_insensitive

    @override
    def as_sql(self) -> ColumnElement[bool]:
        """Return the query for the specification."""
        field = getattr(self._model, self._field_name)
        if self._case_insensitive:
            return col(field).ilike(f'%{self._search_value}%')
        return col(field).contains(self._search_value)


class SpecType(Enum):
    """Enum for specification types."""

    EQ = 0
    LE = 1
    LT = 2
    GE = 3
    GT = 4


class NumercFieldSpecification[SqlTable: SQLModel, NumT: int | float](
    Specification[SqlTable]
):
    """Specification for numeric fields."""

    def __init__(
        self,
        model: type[SqlTable],
        field_name: str,
        expected_value: NumT,
        *,
        spec_type: SpecType = SpecType.EQ,
    ) -> None:
        """Set the default values."""
        self._model = model
        self._field_name = field_name
        self._expected_value = expected_value
        self._spec_type = spec_type

    @override
    def as_sql(self) -> ColumnElement[bool]:
        """Return the query for the specification."""
        field = getattr(self._model, self._field_name)
        if self._spec_type == SpecType.EQ:
            return field == self._expected_value
        elif self._spec_type == SpecType.LE:
            return field <= self._expected_value
        elif self._spec_type == SpecType.LT:
            return field < self._expected_value
        elif self._spec_type == SpecType.GE:
            return field >= self._expected_value
        elif self._spec_type == SpecType.GT:
            return field > self._expected_value
