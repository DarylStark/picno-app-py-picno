"""Tests for the model."""

from typing import override

from picno.specs import (
    AndSpecification,
    NotSpecification,
    OrSpecification,
    Specification,
)


class ConstantSpec[T](Specification[T]):
    """Specification that always returns a given value."""

    def __init__(self, constant: bool) -> None:
        """Set the constant."""
        self._constant = constant

    @override
    def is_satisfied_by(self, obj: T) -> bool:
        """Will always return True."""
        return self._constant


def test_and_specification_true_true() -> None:
    """Test the AndSpecification.

    Test by giving True and True. Should always yield True.
    """
    true_spec = ConstantSpec[None](True)
    assert AndSpecification[None](true_spec, true_spec).is_satisfied_by(None)


def test_and_specification_true_false() -> None:
    """Test the AndSpecification.

    Test by giving True and False. Should always yield False.
    """
    true_spec = ConstantSpec[None](True)
    false_spec = ConstantSpec[None](False)
    assert not AndSpecification[None](true_spec, false_spec).is_satisfied_by(
        None
    )


def test_and_specification_false_true() -> None:
    """Test the AndSpecification.

    Test by giving False and True. Should always yield False.
    """
    true_spec = ConstantSpec[None](True)
    false_spec = ConstantSpec[None](False)
    assert not AndSpecification[None](false_spec, true_spec).is_satisfied_by(
        None
    )


def test_and_specification_false_false() -> None:
    """Test the AndSpecification.

    Test by giving False and False. Should always yield False.
    """
    false_spec = ConstantSpec[None](False)
    assert not AndSpecification[None](false_spec, false_spec).is_satisfied_by(
        None
    )


def test_or_specification_true_true() -> None:
    """Test the OrSpecification.

    Test by giving True and True. Should always yield True.
    """
    true_spec = ConstantSpec[None](True)
    assert OrSpecification[None](true_spec, true_spec).is_satisfied_by(None)


def test_or_specification_true_false() -> None:
    """Test the OrSpecification.

    Test by giving True and False. Should always yield True.
    """
    true_spec = ConstantSpec[None](True)
    false_spec = ConstantSpec[None](False)
    assert OrSpecification[None](true_spec, false_spec).is_satisfied_by(None)


def test_or_specification_false_true() -> None:
    """Test the OrSpecification.

    Test by giving False and True. Should always yield True.
    """
    true_spec = ConstantSpec[None](True)
    false_spec = ConstantSpec[None](False)
    assert OrSpecification[None](false_spec, true_spec).is_satisfied_by(None)


def test_or_specification_false_false() -> None:
    """Test the OrSpecification.

    Test by giving False and False. Should always yield False.
    """
    false_spec = ConstantSpec[None](False)
    assert not OrSpecification[None](false_spec, false_spec).is_satisfied_by(
        None
    )


def test_not_specification_true() -> None:
    """Test the NotSpecification.

    Test by giving True. Should always yield False.
    """
    true_spec = ConstantSpec[None](True)
    assert not NotSpecification[None](true_spec).is_satisfied_by(None)


def test_not_specification_false() -> None:
    """Test the NotSpecification.

    Test by giving False. Should always yield True.
    """
    false_spec = ConstantSpec[None](False)
    assert NotSpecification[None](false_spec).is_satisfied_by(None)
