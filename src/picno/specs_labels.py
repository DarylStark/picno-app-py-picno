"""Module with the specifications for labels."""

from typing import override

from pydantic import BaseModel
from sqlalchemy import ColumnElement
from sqlmodel import col

from .model import Label
from .specs import AllSpecification, Specification

LabelSpecification = Specification[Label]
LabelAllSpecification = AllSpecification[Label]


class NameIsLabelSpec(LabelSpecification):
    """Specification for when the name should be the same."""

    def __init__(self, name: str, case_insensitive: bool = True) -> None:
        """Set the given values."""
        self._name = name
        self._case_insensitive = case_insensitive

    @override
    def is_satisfied_by(self, obj: Label) -> bool:
        if self._case_insensitive:
            return self._name.lower() == obj.name.lower()
        return self._name == obj.name

    @override
    def as_sql(self) -> ColumnElement[bool]:
        """Returns the SQL code for the specification."""
        if self._case_insensitive:
            return col(Label.name).ilike(self._name)
        return col(Label.name) == self._name


class NameContainsLabelSpec(LabelSpecification):
    """Specification for when the name contains text."""

    def __init__(self, text: str, case_insensitive: bool = True) -> None:
        """Set the given values."""
        self._text = text
        self._case_insensitive = case_insensitive

    @override
    def is_satisfied_by(self, obj: Label) -> bool:
        if self._case_insensitive:
            return self._text.lower() in obj.name.lower()
        return self._text in obj.name

    @override
    def as_sql(self) -> ColumnElement[bool]:
        """Returns the SQL code for the specification."""
        if self._case_insensitive:
            return col(Label.name).ilike(f'%{self._text}%')
        return col(Label.name).contains(self._text)


class LabelFilter(BaseModel):
    """Class for Label Filter builder."""

    name: str | None = None
    iname: str | None = None
    name_contains: list[str] | None = None
    iname_contains: list[str] | None = None


def build_label_spec(filter: LabelFilter) -> LabelSpecification | None:
    """Builder for Label Specifications."""
    specs = LabelAllSpecification()

    if filter.name:
        specs.append(NameIsLabelSpec(name=filter.name, case_insensitive=False))

    if filter.iname:
        specs.append(NameIsLabelSpec(name=filter.iname, case_insensitive=True))

    for value in filter.name_contains or []:
        specs.append(NameContainsLabelSpec(text=value, case_insensitive=False))

    for value in filter.iname_contains or []:
        specs.append(NameContainsLabelSpec(text=value, case_insensitive=True))

    return specs if specs else None
