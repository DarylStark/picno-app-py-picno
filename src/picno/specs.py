"""Module with the generic specification."""

from abc import ABC, abstractmethod
from typing import override

from sqlalchemy import and_, true
from sqlalchemy.sql.elements import ColumnElement
from sqlmodel import col


class Specification[T](ABC):
    """Generic baseclass for Specifications."""

    @abstractmethod
    def as_sql(self) -> ColumnElement[bool]:
        """Abstract method to create a SQL query object."""


class AndSpecification[T](Specification[T]):
    """Specification for AND logic."""

    def __init__(
        self, spec_a: Specification[T], spec_b: Specification[T]
    ) -> None:
        """Set the specification."""
        self._spec_a = spec_a
        self._spec_b = spec_b

    @override
    def as_sql(self) -> ColumnElement[bool]:
        """Return the query for the specification."""
        return self._spec_a.as_sql() & self._spec_b.as_sql()


class OrSpecification[T](Specification[T]):
    """Specification for OR logic."""

    def __init__(
        self, spec_a: Specification[T], spec_b: Specification[T]
    ) -> None:
        """Set the specification."""
        self._spec_a = spec_a
        self._spec_b = spec_b

    @override
    def as_sql(self) -> ColumnElement[bool]:
        """Return the query for the specification."""
        return self._spec_a.as_sql() & self._spec_b.as_sql()


class NotSpecification[T](Specification[T]):
    """Specification for NOT logic."""

    def __init__(self, spec: Specification[T]) -> None:
        """Set the specification."""
        self._spec = spec

    @override
    def as_sql(self) -> ColumnElement[bool]:
        """Return the query for the specification."""
        return ~self._spec.as_sql()


class AllSpecification[T](Specification[T]):
    """Specification for ALL logic."""

    def __init__(self) -> None:
        """Create empty list of specifications."""
        self._specs: list[Specification[T]] = []

    def append(self, spec: Specification[T]) -> AllSpecification[T]:
        """Add a specification."""
        self._specs.append(spec)
        return self

    @override
    def as_sql(self) -> ColumnElement[bool]:
        """Return the query for the specification."""
        if not self._specs:
            return true()
        return and_(*(spec.as_sql() for spec in self._specs))


class ParentSpecification[T](Specification[T]):
    """Specification with a parent.

    Can be used to simplify specifications.
    """

    def __init__(self, parent: Specification[T]) -> None:
        """Set the parent specification."""
        self._parent_spec = parent

    @override
    def as_sql(self) -> ColumnElement[bool]:
        """Returns the SQL code for the specification."""
        return self._parent_spec.as_sql()


class StrIsSpecification[T](Specification[T]):
    """Specification that checks if a specific string is equal."""

    def __init__(
        self,
        model: type[T],
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


class StrContainsSpecification[T](Specification[T]):
    """Specification that checks if a specific string is equal."""

    def __init__(
        self,
        model: type[T],
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
