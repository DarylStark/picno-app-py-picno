"""Module with the specifications for labels."""

from dataclasses import dataclass
from typing import override

from sqlalchemy import ColumnElement
from sqlmodel import and_, func

from .filter import Filter
from .model import Label
from .specs import (
    AllSpecification,
    ParentSpecification,
    Specification,
    StrContainsSpecification,
    StrIsSpecification,
)

LabelSpecification = Specification[Label]
LabelAllSpecification = AllSpecification[Label]


class NameIsLabelSpec(ParentSpecification[Label]):
    """Specification for when the name should be the same."""

    def __init__(self, name: str, case_insensitive: bool = True) -> None:
        """Set the given values."""
        super().__init__(
            StrIsSpecification(Label, 'name', name, case_insensitive)
        )


class NameContainsLabelSpec(ParentSpecification[Label]):
    """Specification for when the name contains text."""

    def __init__(self, text: str, case_insensitive: bool = True) -> None:
        """Set the given values."""
        super().__init__(
            StrContainsSpecification(Label, 'name', text, case_insensitive)
        )


class GroupIsLabelSpec(LabelSpecification):
    """Filter on specific a group."""

    def __init__(self, group: str, case_insensitive: bool = True) -> None:
        """Set the groupname to filter on."""
        self._group = group
        self._case_insensitive = case_insensitive

    def _as_sql_case_sensitive(self) -> ColumnElement[bool]:
        colon_pos = func.instr(Label.name, ':')
        return and_(
            colon_pos > 0,
            func.substr(Label.name, 1, colon_pos - 1) == self._group,
        )

    def _as_sql_case_insensitive(self) -> ColumnElement[bool]:
        colon_pos = func.instr(Label.name, ':')
        return and_(
            colon_pos > 0,
            func.lower(func.substr(Label.name, 1, colon_pos - 1))
            == self._group.lower(),
        )

    @override
    def as_sql(self) -> ColumnElement[bool]:
        """Returns the SQL code for the specification."""
        if self._case_insensitive:
            return self._as_sql_case_insensitive()
        return self._as_sql_case_sensitive()


@dataclass(frozen=True)
class LabelFilter(Filter[LabelSpecification]):
    """Class for Label Filter builder."""

    name: str | None = None
    iname: str | None = None
    group_name: str | None = None
    igroup_name: str | None = None
    name_contains: list[str] | None = None
    iname_contains: list[str] | None = None

    def get_specifications(self) -> LabelSpecification | None:
        """Builder for Label Specifications."""
        specs = LabelAllSpecification()

        if self.name:
            specs.append(
                NameIsLabelSpec(name=self.name, case_insensitive=False)
            )

        if self.iname:
            specs.append(
                NameIsLabelSpec(name=self.iname, case_insensitive=True)
            )

        if self.group_name:
            specs.append(
                GroupIsLabelSpec(group=self.group_name, case_insensitive=False)
            )

        if self.igroup_name:
            specs.append(
                GroupIsLabelSpec(group=self.igroup_name, case_insensitive=True)
            )

        for value in self.name_contains or []:
            specs.append(
                NameContainsLabelSpec(text=value, case_insensitive=False)
            )

        for value in self.iname_contains or []:
            specs.append(
                NameContainsLabelSpec(text=value, case_insensitive=True)
            )

        return specs if specs else None
