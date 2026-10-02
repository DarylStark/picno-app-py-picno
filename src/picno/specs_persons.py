"""Module with the specifications for labels."""

from typing import override

from pydantic import BaseModel
from sqlalchemy import ColumnElement

from .model import Person
from .specs import AllSpecification, Specification, StrIsSpecification

PersonSpecification = Specification[Person]
PersonAllSpecification = AllSpecification[Person]


class NameIsPersonSpec(PersonSpecification):
    """Specification for when the name should be the same."""

    def __init__(self, name: str, case_insensitive: bool = True) -> None:
        """Set the given values."""
        self._parent_spec = StrIsSpecification(
            Person, 'name', name, case_insensitive
        )

    @override
    def is_satisfied_by(self, obj: Person) -> bool:
        return self._parent_spec.is_satisfied_by(obj)

    @override
    def as_sql(self) -> ColumnElement[bool]:
        """Returns the SQL code for the specification."""
        return self._parent_spec.as_sql()


class PersonFilter(BaseModel):
    """Class for Label Filter builder."""

    name: str | None = None
    iname: str | None = None


def build_person_spec(filter: PersonFilter) -> PersonSpecification | None:
    """Builder for Label Specifications."""
    specs = PersonAllSpecification()

    if filter.name:
        specs.append(NameIsPersonSpec(name=filter.name, case_insensitive=False))

    if filter.iname:
        specs.append(NameIsPersonSpec(name=filter.iname, case_insensitive=True))

    return specs if specs else None
