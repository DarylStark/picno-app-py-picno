"""Module with the `pico media` options."""

from pathlib import Path

from rich.progress import Progress
from typer import Context, Typer

from picno.model import Image

from .cli_context import get_initialized_project

media = Typer(name='media', help='Media management')


@media.command(name='sync', help='Sync unmanaged directory of media')
def sync(ctx: Context) -> None:
    """List the labels in the database."""
    (_, project, _, console) = get_initialized_project(ctx)

    added_image_count = 0

    with Progress(console=console) as progress_bar:
        scan_task = progress_bar.add_task('Scanning...', complete=0, total=None)
        process_task = progress_bar.add_task('Processing...', total=100)
        sync_adding = progress_bar.add_task('Adding new files...', total=100)

        def cb_scan_start() -> None:
            progress_bar.update(scan_task, description='Scanning directory')

        def cb_scan_done(files: list[Path]) -> None:
            progress_bar.update(
                scan_task,
                description=f'Found {len(files)} files',
                completed=1,
                total=1,
            )

        def cb_process(total: int, done: int) -> None:
            progress_bar.update(process_task, total=total, completed=done)

        def cb_sync_adding_start(images: list[Image]) -> None:
            progress_bar.update(
                sync_adding,
                description='Syncing',
                total=None,
                completed=0,
            )

        def cb_sync_adding_done(images: list[Image]) -> None:
            progress_bar.update(
                sync_adding,
                completed=1,
                total=1,
            )

            nonlocal added_image_count
            added_image_count = len(images)

        project.sync_data_directory(
            callback_scanning_starting=cb_scan_start,
            callback_scanning_done=cb_scan_done,
            callback_processing_image=cb_process,
            callback_sync_adding_starting=cb_sync_adding_start,
            callback_sync_adding_done=cb_sync_adding_done,
        )

    console.print(f'Added {added_image_count} images to the database')
