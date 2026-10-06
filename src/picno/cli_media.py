"""Module with the `pico media` options."""

from typer import Context, Typer

from .cli_context import get_initialized_project

media = Typer(name='media', help='Media management')


@media.command(name='sync', help='Sync unmanaged directory of media')
def sync(ctx: Context) -> None:
    """List the labels in the database."""
    (_, project, _, console) = get_initialized_project(ctx)
    new_files = project.sync_data_directory()
    console.print(f'Added {len(new_files)} new files.')
