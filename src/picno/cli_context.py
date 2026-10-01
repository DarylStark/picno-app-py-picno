"""Module with the definition of the CliContext."""

from dataclasses import dataclass
from pathlib import Path

from rich.console import Console
from typer import Context

from picno.database import Database

from .exceptions import ProjectNotInitializedError
from .project_manager import ProjectManager


@dataclass
class CliContext:
    """Dataclass for the CLI context."""

    file: Path
    console: Console
    manager: ProjectManager | None = None


def get_initialized_project(
    ctx: Context,
) -> tuple[CliContext, ProjectManager, Database, Console]:
    """Get the context of a initialized project.

    Generates an exception when the project is not initialized yet.
    """
    context: CliContext = ctx.obj

    if not context.manager:
        raise ProjectNotInitializedError('Project is not initialized')

    return (context, context.manager, context.manager.database, context.console)
