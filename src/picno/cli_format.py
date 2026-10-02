"""Format functions for the CLI output."""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

from rich.console import Console
from rich.table import Table


@dataclass(frozen=True)
class TableColumn:
    """Column for a table."""

    header: str
    getter: Callable[[Any], Any]


def print_table(
    console: Console,
    rows: Sequence[Any],
    columns: Sequence[TableColumn],
    title: str | None = None,
) -> None:
    """Method to automatically print a table."""
    table = Table(title=title)

    for col in columns:
        table.add_column(col.header)

    for row in rows:
        table.add_row(*(str(col.getter(row)) for col in columns))

    console.print(table)
