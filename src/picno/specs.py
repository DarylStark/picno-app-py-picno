"""Module with the generic specification."""

from abc import ABC, abstractmethod
from enum import Enum
from typing import override

from sqlalchemy import and_, true
from sqlalchemy.sql.elements import ColumnElement
from sqlmodel import SQLModel, col, exists, false, or_, select


class Specification[SqlTable](ABC):
    """Generic baseclass for Specifications."""

    @abstractmethod
    def as_sql(self) -> ColumnElement[bool]:
        """Abstract method to create a SQL query object."""


class AndSpecification[SqlTable](Specification[SqlTable]):
    """Specification for AND logic."""

    def __init__(
        self, spec_a: Specification[SqlTable], spec_b: Specification[SqlTable]
    ) -> None:
        """Set the specification."""
        self._spec_a = spec_a
        self._spec_b = spec_b

    @override
    def as_sql(self) -> ColumnElement[bool]:
        """Return the query for the specification."""
        return self._spec_a.as_sql() & self._spec_b.as_sql()


class OrSpecification[SqlTable](Specification[SqlTable]):
    """Specification for OR logic."""

    def __init__(
        self, spec_a: Specification[SqlTable], spec_b: Specification[SqlTable]
    ) -> None:
        """Set the specification."""
        self._spec_a = spec_a
        self._spec_b = spec_b

    @override
    def as_sql(self) -> ColumnElement[bool]:
        """Return the query for the specification."""
        return self._spec_a.as_sql() & self._spec_b.as_sql()


class NotSpecification[SqlTable](Specification[SqlTable]):
    """Specification for NOT logic."""

    def __init__(self, spec: Specification[SqlTable]) -> None:
        """Set the specification."""
        self._spec = spec

    @override
    def as_sql(self) -> ColumnElement[bool]:
        """Return the query for the specification."""
        return ~self._spec.as_sql()


class AllSpecification[SqlTable](Specification[SqlTable]):
    """Specification for ALL logic."""

    def __init__(self) -> None:
        """Create empty list of specifications."""
        self._specs: list[Specification[SqlTable]] = []

    def append(
        self, spec: Specification[SqlTable]
    ) -> AllSpecification[SqlTable]:
        """Add a specification."""
        self._specs.append(spec)
        return self

    @override
    def as_sql(self) -> ColumnElement[bool]:
        """Return the query for the specification."""
        if not self._specs:
            return true()
        return and_(*(spec.as_sql() for spec in self._specs))


class AnySpecification[SqlTable](Specification[SqlTable]):
    """Specification for ALL logic."""

    def __init__(self) -> None:
        """Create empty list of specifications."""
        self._specs: list[Specification[SqlTable]] = []

    def append(
        self, spec: Specification[SqlTable]
    ) -> AnySpecification[SqlTable]:
        """Add a specification."""
        self._specs.append(spec)
        return self

    @override
    def as_sql(self) -> ColumnElement[bool]:
        """Return the query for the specification."""
        if not self._specs:
            return false()
        return or_(*(spec.as_sql() for spec in self._specs))


class ParentSpecification[SqlTable](Specification[SqlTable]):
    """Specification with a parent.

    Can be used to simplify specifications.
    """

    def __init__(self, parent: Specification[SqlTable]) -> None:
        """Set the parent specification."""
        self._parent_spec = parent

    @override
    def as_sql(self) -> ColumnElement[bool]:
        """Returns the SQL code for the specification."""
        return self._parent_spec.as_sql()


class FieldIsSpecification[SqlTable, T2](Specification[SqlTable]):
    """Specification that checks if a specific field is equal."""

    def __init__(
        self,
        model: type[SqlTable],
        field_name: str,
        expected_value: T2,
        case_insensitive: bool = True,
    ) -> None:
        """Set the default values."""
        self._model = model
        self._field_name = field_name
        self._expected_value = expected_value
        self._case_insensitive = case_insensitive

    @override
    def as_sql(self) -> ColumnElement[bool]:
        """Return the query for the specification."""
        field = getattr(self._model, self._field_name)
        if self._case_insensitive:
            return col(field).ilike(self._expected_value)
        return col(field) == self._expected_value


class RelationshipSpec[
    SqlTableA: SQLModel,
    SqlTableB: SQLModel,
    SqlTableC: SQLModel,
](Specification[SqlTableA]):
    """Filter on model A via relationship to model B through link table."""

    def __init__(
        self,
        model_a: type[SqlTableA],
        model_b: type[SqlTableB],
        link_table: type[SqlTableC],
        link_table_field_a: str,
        link_table_field_b: str,
        search_field: str,
        search_value: str | None,
    ) -> None:
        """Set given values."""
        self._search_value = search_value
        self._model_a = model_a
        self._model_b = model_b
        self._link_table = link_table
        self._link_table_field_a = link_table_field_a
        self._link_table_field_b = link_table_field_b
        self._search_field = search_field

    @override
    def as_sql(self) -> ColumnElement[bool]:
        model_a_id = getattr(self._model_a, 'id')  # noqa: B009
        model_b_id = getattr(self._model_b, 'id')  # noqa: B009
        link_a = getattr(self._link_table, self._link_table_field_a)
        link_b = getattr(self._link_table, self._link_table_field_b)
        search_col = getattr(self._model_b, self._search_field)

        return exists(
            select(1)
            .select_from(self._link_table)
            .join(self._model_b, model_b_id == link_b)
            .where(
                and_(
                    link_a == model_a_id,
                    search_col == self._search_value,
                )
            )
        )


class StrIsSpecification[SqlTable](Specification[SqlTable]):
    """Specification that checks if a specific string is equal."""

    def __init__(
        self,
        model: type[SqlTable],
        field_name: str,
        expected_value: str,
        case_insensitive: bool = True,
    ) -> None:
        """Set the default values."""
        self._model = model
        self._field_name = field_name
        self._expected_value = expected_value
        self._case_insensitive = case_insensitive

    @override
    def as_sql(self) -> ColumnElement[bool]:
        """Return the query for the specification."""
        field = getattr(self._model, self._field_name)
        if self._case_insensitive:
            return col(field).ilike(self._expected_value)
        return col(field) == self._expected_value


class StrContainsSpecification[SqlTable](Specification[SqlTable]):
    """Specification that checks if a specific string is equal."""

    def __init__(
        self,
        model: type[SqlTable],
        field_name: str,
        search_value: str,
        case_insensitive: bool = True,
    ) -> None:
        """Set the default values."""
        self._model = model
        self._field_name = field_name
        self._search_value = search_value
        self._case_insensitive = case_insensitive

    @override
    def as_sql(self) -> ColumnElement[bool]:
        """Return the query for the specification."""
        field = getattr(self._model, self._field_name)
        if self._case_insensitive:
            return col(field).ilike(f'%{self._search_value}%')
        return col(field).contains(self._search_value)


class SpecType(Enum):
    """Enum for specification types."""

    EQ = 0
    LE = 1
    LT = 2
    GE = 3
    GT = 4


class NumercFieldSpecification[SqlTable: SQLModel, NumT: int | float](
    Specification[SqlTable]
):
    """Specification for numeric fields."""

    def __init__(
        self,
        model: type[SqlTable],
        field_name: str,
        expected_value: NumT,
        *,
        spec_type: SpecType = SpecType.EQ,
    ) -> None:
        """Set the default values."""
        self._model = model
        self._field_name = field_name
        self._expected_value = expected_value
        self._spec_type = spec_type

    @override
    def as_sql(self) -> ColumnElement[bool]:
        """Return the query for the specification."""
        field = getattr(self._model, self._field_name)
        if self._spec_type == SpecType.EQ:
            return field == self._expected_value
        elif self._spec_type == SpecType.LE:
            return field <= self._expected_value
        elif self._spec_type == SpecType.LT:
            return field < self._expected_value
        elif self._spec_type == SpecType.GE:
            return field >= self._expected_value
        elif self._spec_type == SpecType.GT:
            return field > self._expected_value


class StrSpecification[SqlTable](Specification[SqlTable]):
    """Specification that checks if a specific string is equal."""

    def __init__(
        self,
        model: type[SqlTable],
        field: str,
        value: str,
        is_exact: bool = False,
        case_sensitive: bool = True,
    ) -> None:
        """Set the default values."""
        self._model = model
        self._field = field
        self._value = value
        self._is_exact = is_exact
        self._case_sensitive = case_sensitive

    def _as_sql_exact(self) -> ColumnElement[bool]:
        """Return the query for the specification."""
        field = getattr(self._model, self._field)
        if not self._case_sensitive:
            return col(field).ilike(self._value)
        return col(field) == self._value

    def _as_sql_not_exact(self) -> ColumnElement[bool]:
        """Return the query for the specification."""
        field = getattr(self._model, self._field)
        if not self._case_sensitive:
            return col(field).ilike(f'%{self._value}%')
        return col(field).contains(self._value)

    @override
    def as_sql(self) -> ColumnElement[bool]:
        """Return the query for the specification."""
        if self._is_exact:
            return self._as_sql_exact()
        return self._as_sql_not_exact()
