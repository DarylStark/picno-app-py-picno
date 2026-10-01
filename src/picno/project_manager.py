"""Module with the project manager."""

from .project import Project


class ProjectManager:
    """Project class represents a project."""

    def __init__(self, structure: Project) -> None:
        """Set the project."""
        self._structure = structure
