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
