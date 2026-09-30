"""Module with the database abstraction."""

from abc import ABC, abstractmethod
from typing import override


class Specification[T](ABC):
    """Generic baseclass for Specifications."""

    @abstractmethod
    def is_satisfied_by(self, obj: T) -> bool:
        """Abstract method to check if a object satisfies the spec."""


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


class NotSpecification[T](Specification[T]):
    """Specification for NOT logic."""

    def __init__(self, spec: Specification[T]) -> None:
        """Set the specification."""
        self._spec = spec

    @override
    def is_satisfied_by(self, obj: T) -> bool:
        """Returns if both specs are satisfied."""
        return not self._spec.is_satisfied_by(obj)
