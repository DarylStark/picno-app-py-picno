"""Module with the Project class."""

from enum import Enum
from pathlib import Path

from pydantic import BaseModel


class ProjectType(Enum):
    """Possible project types."""

    MANAGED = 'managed'
    UNMANAGED = 'unmanaged'


class Project(BaseModel):
    """Model for the project JSON file."""

    name: str
    data_folder: Path
    project_type: ProjectType = ProjectType.UNMANAGED
    database_str: str
    sync_ignore: list[Path] = []

    def set_sync_ignore_list_to_path(self) -> None:
        """Add the parent path to the sync_ignore list."""
        self.sync_ignore = [
            (self.data_folder / Path(p)).resolve() for p in self.sync_ignore
        ]
