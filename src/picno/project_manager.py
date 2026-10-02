"""Module with the project manager."""

from .database import Database
from .database_sql import DatabaseSql
from .project import Project


class ProjectManager:
    """Project class represents a project."""

    def __init__(self, structure: Project) -> None:
        """Set the project."""
        self._structure = structure
        self._database: Database = DatabaseSql(self._structure.database_str)

    @property
    def database(self) -> Database:
        """Property to retrieve the database object."""
        return self._database
