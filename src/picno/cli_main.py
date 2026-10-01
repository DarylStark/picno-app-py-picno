"""Module with the main entry point of the CLI application."""

from pathlib import Path

from pydantic import ValidationError
from typer import Context, Option, Typer

from .cli_context import CliContext
from .cli_labels import labels
from .cli_project import project
from .exceptions import CliError, DatabaseError, ProjectParseError
from .project import Project
from .project_manager import ProjectManager

app = Typer(name='Picno')
app.add_typer(project)
app.add_typer(labels)


@app.callback()
def context(
    ctx: Context,
    project_file: Path = Option(
        default=Path('picno.json'), help='The project file to use'
    ),
) -> None:
    """Default context for all CLI operations."""
    ctx.obj = CliContext(file=project_file)

    # Create a manager if a project is given
    if project_file.is_file():
        try:
            ctx.obj.manager = ProjectManager(
                Project.model_validate_json(project_file.read_text())
            )
        except ValidationError as err:
            raise ProjectParseError from err


def main() -> None:
    """Main entry point for the CLI app."""
    # TODO: Make these errors look better
    try:
        app()
    except CliError as e:
        print(f'CLI error: {e}')
    except DatabaseError as e:
        print(f'Database error: {e}')
    except Exception as e:
        print(f'Unknown error: {e}')
