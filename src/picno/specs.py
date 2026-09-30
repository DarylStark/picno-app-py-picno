"""Module with the generic specification."""

from abc import ABC, abstractmethod
from typing import override

from sqlalchemy.sql.elements import ColumnElement


class Specification[T](ABC):
    """Generic baseclass for Specifications."""

    @abstractmethod
    def is_satisfied_by(self, obj: T) -> bool:
        """Abstract method to check if a object satisfies the spec."""

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
    def is_satisfied_by(self, obj: T) -> bool:
        """Returns if both specs are satisfied."""
        return self._spec_a.is_satisfied_by(
            obj
        ) and self._spec_b.is_satisfied_by(obj)

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
    def is_satisfied_by(self, obj: T) -> bool:
        """Returns if both specs are satisfied."""
        return self._spec_a.is_satisfied_by(
            obj
        ) or self._spec_b.is_satisfied_by(obj)

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
    def is_satisfied_by(self, obj: T) -> bool:
        """Returns if both specs are satisfied."""
        return not self._spec.is_satisfied_by(obj)

    @override
    def as_sql(self) -> ColumnElement[bool]:
        """Return the query for the specification."""
        return ~self._spec.as_sql()
