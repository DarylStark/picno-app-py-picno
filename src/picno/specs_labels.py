"""Module with the specifications for labels."""

from typing import override

from sqlalchemy import ColumnElement
from sqlmodel import col

from .model import Label
from .specs import Specification

LabelSpecification = Specification[Label]


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
