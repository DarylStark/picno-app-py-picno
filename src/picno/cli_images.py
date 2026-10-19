"""Module with the `pico images` options."""

import re

from typer import Argument, Context, Option, Typer

from picno.cli_filter_arg_generator import CliFilterArgGenerator
from picno.cli_helpers import (
    OutputFormat,
    create_label_confirm_callback,
    create_unlabel_confirm_callback,
    create_update_confirm_callback,
    with_filters,
    with_force_flag,
    with_sort_field,
)
from picno.cli_output import OutputFormatImages
from picno.database import RetrieveOption, SortField
from picno.model import (
    Image,
    ResourceStatus,
)
from picno.resource_filter import (
    ResourceFilter,
    ResourceFilterBuilderImage,
)

from .cli_context import get_initialized_project

images = Typer(name='images', help='Image management')
filter_gen = CliFilterArgGenerator(ResourceFilterBuilderImage())


@images.command(name='ls', help='List images')
@with_filters(filter_generator=filter_gen)
@with_sort_field(default_sort='title,id')
def ls(
    _sort: list[SortField] | None,
    _filter: ResourceFilter[Image],
    ctx: Context,
    output_format: OutputFormat = Option(
        default=OutputFormat.TABLE, help='The way to output data'
    ),
) -> None:
    """List the images in the database."""
    (_, _, db, console) = get_initialized_project(ctx)
    # Retrieve the images
    images = db.get_images(
        specification=_filter.as_spec(),
        options=[
            RetrieveOption.LOAD_IMAGE_LABELS,
            RetrieveOption.LOAD_IMAGE_PERSONS,
        ],
        sorting=_sort,
    )

    formatter = OutputFormatImages(console)

    if images:
        if output_format == OutputFormat.TABLE:
            formatter.as_table(images, title='Images')
        elif output_format == OutputFormat.DETAILS:
            formatter.as_details(images)
    else:
        console.print('[yellow]No images match the filter[/yellow]')


@images.command(name='set-status', help='Set the status for images')
@with_filters(filter_generator=filter_gen)
@with_force_flag()
def set_status(
    _force: bool,
    _filter: ResourceFilter[Image],
    ctx: Context,
    new_status: ResourceStatus = Argument(help='The status to set'),
) -> None:
    """List the images in the database."""
    (_, _, db, console) = get_initialized_project(ctx)
    select_callback = create_update_confirm_callback(_force, console, 'title')
    images = db.set_image_status(
        status=new_status,
        specification=_filter.as_spec(),
        select_callback=select_callback,
    )
    console.print(f'Updated {len(images)} images')


@images.command(name='label', help='Label specific images')
@with_filters(filter_generator=filter_gen)
@with_force_flag()
def label(
    _force: bool,
    _filter: ResourceFilter[Image],
    ctx: Context,
    label_name: str = Argument(help='The name of the label to add'),
) -> None:
    """Add a label to images."""
    (_, _, db, console) = get_initialized_project(ctx)
    select_callback = create_label_confirm_callback(_force, console, 'title')
    images = db.add_label_to_images(
        label_name,
        specification=_filter.as_spec(),
        select_callback=select_callback,
    )
    console.print(f'Added label "{label_name}" to {len(images)} images')


@images.command(name='unlabel', help='Unlabel specific images')
@with_filters(filter_generator=filter_gen)
@with_force_flag()
def unlabel(
    _force: bool,
    _filter: ResourceFilter[Image],
    ctx: Context,
    label_name: str = Argument(help='The name of the label to remove'),
) -> None:
    """Remove a label from images."""
    (_, _, db, console) = get_initialized_project(ctx)
    select_callback = create_unlabel_confirm_callback(_force, console, 'title')
    images = db.remove_label_from_images(
        label_name,
        specification=_filter.as_spec(),
        select_callback=select_callback,
    )
    console.print(f'Removed label "{label_name}" from {len(images)} images')


@images.command(name='favorite', help='Favorite specific images')
@with_filters(filter_generator=filter_gen)
@with_force_flag()
def favorite(
    _force: bool,
    _filter: ResourceFilter[Image],
    ctx: Context,
) -> None:
    """List the images in the database."""
    (_, _, db, console) = get_initialized_project(ctx)
    select_callback = create_update_confirm_callback(_force, console, 'title')
    images = db.set_favorite_for_images(
        favorite=True,
        specification=_filter.as_spec(),
        select_callback=select_callback,
    )
    console.print(f'Set {len(images)} images as favorite')


@images.command(name='unfavorite', help='Unfavorite specific images')
@with_filters(filter_generator=filter_gen)
@with_force_flag()
def unfavorite(
    _force: bool,
    _filter: ResourceFilter[Image],
    ctx: Context,
) -> None:
    """List the images in the database."""
    (_, _, db, console) = get_initialized_project(ctx)
    select_callback = create_update_confirm_callback(_force, console, 'title')
    images = db.set_favorite_for_images(
        favorite=False,
        specification=_filter.as_spec(),
        select_callback=select_callback,
    )
    console.print(f'Removed the favorite flag for {len(images)} images')


@images.command(name='mv', help='Rename a image')
@with_force_flag()
def mv(
    _force: bool,
    ctx: Context,
    old_title: str = Argument(help='Current title of the image'),
    new_title: str = Argument(help='New title of the image'),
) -> None:
    """Rename a image."""
    (_, _, db, console) = get_initialized_project(ctx)
    select_callback = create_update_confirm_callback(_force, console, 'title')
    db.rename_image(old_title, new_title, select_callback=select_callback)
    console.print(f'Renamed image "{old_title}" to "{new_title}"')


@images.command(name='exec', help='Execute a command for specific images')
@with_filters(filter_generator=filter_gen)
def exec(
    _filter: ResourceFilter[Image],
    ctx: Context,
    executor: str = Argument(help='The executor to run'),
    options: list[str] | None = Option(
        default=None, help='Give options for the executor'
    ),
) -> None:
    """Execute a specific command for specific images."""
    (_, pm, _, console) = get_initialized_project(ctx)

    # Parse the options
    option_dict: dict[str, str] | None = None
    if options:
        option_dict = {}
        for option in options:
            if not re.match(r'^[a-zA-Z0-9_]+=[a-zA-Z0-9_-]+$', option):
                raise ValueError(
                    'Option should follow the pattern option=value'
                )
            option_dict[option.split('=')[0]] = option.split('=')[1]

    pm.exec_for_images(
        executor=executor,
        specification=_filter.as_spec(),
        options=option_dict,
    )


@images.command(name='tag-person', help='Tag a person for specific labels')
@with_filters(filter_generator=filter_gen)
@with_force_flag()
def tag_person(
    _force: bool,
    _filter: ResourceFilter[Image],
    ctx: Context,
    person_name: str = Argument(help='The name of the person to tag'),
) -> None:
    """Add a person to images."""
    (_, _, db, console) = get_initialized_project(ctx)
    select_callback = create_update_confirm_callback(_force, console, 'title')
    images = db.add_person_to_images(
        person_name,
        specification=_filter.as_spec(),
        select_callback=select_callback,
    )
    console.print(f'Added person "{person_name}" to {len(images)} images')


@images.command(name='untag-person', help='Untag a person from specific images')
@with_filters(filter_generator=filter_gen)
@with_force_flag()
def untag_person(
    _force: bool,
    _filter: ResourceFilter[Image],
    ctx: Context,
    person_name: str = Argument(help='The name of the person to untag'),
) -> None:
    """Remove a person from images."""
    (_, _, db, console) = get_initialized_project(ctx)
    select_callback = create_update_confirm_callback(_force, console, 'title')
    images = db.remove_person_from_images(
        person_name,
        specification=_filter.as_spec(),
        select_callback=select_callback,
    )
    console.print(f'Removed person "{person_name}" from {len(images)} images')
