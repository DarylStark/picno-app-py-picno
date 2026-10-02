"""Module with the specifications for labels."""

from pydantic import BaseModel

from .model import Person
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


class PersonFilter(BaseModel):
    """Class for Label Filter builder."""

    name: str | None = None
    iname: str | None = None
    name_contains: list[str] | None = None
    iname_contains: list[str] | None = None


def build_person_spec(filter: PersonFilter) -> PersonSpecification | None:
    """Builder for Label Specifications."""
    specs = PersonAllSpecification()

    if filter.name:
        specs.append(NameIsPersonSpec(name=filter.name, case_insensitive=False))

    if filter.iname:
        specs.append(NameIsPersonSpec(name=filter.iname, case_insensitive=True))

    for value in filter.name_contains or []:
        specs.append(NameContainsPersonSpec(text=value, case_insensitive=False))

    for value in filter.iname_contains or []:
        specs.append(NameContainsPersonSpec(text=value, case_insensitive=True))

    return specs if specs else None
