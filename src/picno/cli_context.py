"""Module with the definition of the CliContext."""

from dataclasses import dataclass
from pathlib import Path

from .project_manager import ProjectManager


@dataclass
class CliContext:
    """Dataclass for the CLI context."""

    file: Path
    manager: ProjectManager | None = None
