"""Module with the specifications for labels."""

from typing import override

from sqlalchemy import ColumnElement
from sqlmodel import and_, col, exists, select

from .model import Label, Person, PersonLabelLink
from .specs import (
    AllSpecification,
    ParentSpecification,
    Specification,
    StrContainsSpecification,
    StrIsSpecification,
)

PersonSpecification = Specification[Person]
PersonAllSpecification = AllSpecification[Person]


class NameIsPersonSpec(ParentSpecification[Person]):
    """Specification for when the name should be the same."""

    def __init__(self, name: str, case_insensitive: bool = True) -> None:
        """Set the given values."""
        super().__init__(
            StrIsSpecification(Person, 'name', name, case_insensitive)
        )


class NameContainsPersonSpec(ParentSpecification[Person]):
    """Specification for when the name contains text."""

    def __init__(self, text: str, case_insensitive: bool = True) -> None:
        """Set the given values."""
        super().__init__(
            StrContainsSpecification(Person, 'name', text, case_insensitive)
        )


class HasLabelPersonSpec(PersonSpecification):
    """Filter on persons with a specific image."""

    def __init__(self, label_name: str) -> None:
        """Set the label name to search for."""
        self._label_name = label_name

    @override
    def as_sql(self) -> ColumnElement[bool]:
        """Create the SQL commands for this object."""
        return exists(
            select(1)
            .select_from(PersonLabelLink)
            .join(Label, col(Label.id) == PersonLabelLink.label_id)
            .where(
                and_(
                    col(PersonLabelLink.person_id) == Person.id,
                    col(Label.name) == self._label_name,
                )
            )
        )
