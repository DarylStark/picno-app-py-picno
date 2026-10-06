"""Module with the main entry point of the CLI application."""

import io
import sys
from pathlib import Path

from pydantic import ValidationError
from rich.console import Console
from typer import Context, Option, Typer

from .cli_context import CliContext
from .cli_labels import labels
from .cli_media import media
from .cli_persons import persons
from .cli_project import project
from .exceptions import CliError, DatabaseError, ProjectParseError
from .project import Project
from .project_manager import ProjectManager

app = Typer(name='Picno')
app.add_typer(project)
app.add_typer(labels)
app.add_typer(persons)
app.add_typer(media)


@app.callback()
def context(
    ctx: Context,
    project_file: Path = Option(
        default=Path('picno.json'), help='The project file to use'
    ),
    quiet: bool = Option(default=False, help='Supress output'),
) -> None:
    """Default context for all CLI operations."""
    if quiet:
        console = Console(
            file=io.StringIO(), force_terminal=False, color_system=None
        )
    else:
        console = Console()

    ctx.obj = CliContext(file=project_file, console=console)

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
    err_console = Console(file=sys.stderr)

    try:
        app()
        sys.exit(0)
    except CliError as e:
        err_console.print(f'[red][b]CLI error:[/b][/red] {e}')
    except DatabaseError as e:
        err_console.print(f'[red][b]Database error:[/b][/red] {e}')
    except Exception as e:
        err_console.print(f'[red][b]Unknown error:[/b][/red] {e}')
    sys.exit(1)
