"""Module with the `picno project` options."""

from typer import Context, Option, Typer

from .cli_context import CliContext
from .exceptions import ProjectAlreadyInitializedError
from .project import Project, ProjectType

project = Typer(name='project', help='Project management')


@project.command(name='init')
def init(
    ctx: Context,
    name: str = Option('Picno project', help='A optional name for the project'),
    managed: bool = Option(False, help='Initialize a managed project'),
) -> None:
    """Initialize a new project."""
    context: CliContext = ctx.obj

    if context.manager:
        raise ProjectAlreadyInitializedError('Project is already initialized')

    if managed:
        raise NotImplementedError('Managed projects are not implemented yet')
    else:
        project = Project(
            name=name,
            data_folder='.',
            project_type=ProjectType.UNMANAGED,
            database_str='sqlite:///./picno.db',
        )
        context.file.write_text(
            project.model_dump_json(indent=4), encoding='utf-8'
        )
