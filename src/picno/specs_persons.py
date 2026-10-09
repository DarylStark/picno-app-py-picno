"""Module with the specifications for labels."""

from dataclasses import dataclass
from typing import override

from sqlalchemy import ColumnElement
from sqlmodel import and_, col, exists, select

from .filter import Filter
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


@dataclass(frozen=True)
class PersonFilter(Filter[PersonSpecification]):
    """Class for Label Filter builder."""

    name: str | None = None
    iname: str | None = None
    name_contains: list[str] | None = None
    iname_contains: list[str] | None = None

    def get_specifications(self) -> PersonSpecification | None:
        """Builder for Person Specifications."""
        specs = PersonAllSpecification()

        if self.name:
            specs.append(
                NameIsPersonSpec(name=self.name, case_insensitive=False)
            )

        if self.iname:
            specs.append(
                NameIsPersonSpec(name=self.iname, case_insensitive=True)
            )

        for value in self.name_contains or []:
            specs.append(
                NameContainsPersonSpec(text=value, case_insensitive=False)
            )

        for value in self.iname_contains or []:
            specs.append(
                NameContainsPersonSpec(text=value, case_insensitive=True)
            )

        return specs if specs else None
