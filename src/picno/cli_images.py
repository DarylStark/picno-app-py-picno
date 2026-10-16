"""Module with the `pico images` options."""

import re
from enum import Enum

from typer import Argument, Context, Option, Typer

from picno.cli_filter_arg_generator import CliFilterArgGenerator
from picno.cli_helpers import (
    create_label_confirm_callback,
    create_unlabel_confirm_callback,
    create_update_confirm_callback,
    with_filters,
    with_force_flag,
)
from picno.database import RetrieveOption
from picno.model import (
    Image,
    ResourceStatus,
)
from picno.resource_filter import (
    ResourceFilter,
    ResourceFilterBuilderImage,
)

from .cli_context import get_initialized_project
from .cli_format import TableColumn, print_table

images = Typer(name='images', help='Image management')
filter_gen = CliFilterArgGenerator(ResourceFilterBuilderImage())


class OutputFormat(Enum):
    """Output foramts."""

    TABLE = 'table'
    DETAILS = 'details'


@images.command(name='ls', help='List images')
@with_filters(filter_generator=filter_gen)
def ls(
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
    )
    if images:
        if output_format == OutputFormat.TABLE:
            print_table(
                console,
                images,
                columns=[
                    TableColumn('ID', lambda image: image.id),
                    TableColumn(
                        'Status',
                        lambda image: str(image.status.value).capitalize(),
                    ),
                    TableColumn(
                        'Favourite',
                        lambda image: str(image.favourite),
                    ),
                    TableColumn(
                        'Physical path', lambda image: image.physical_path
                    ),
                    TableColumn('Name', lambda image: image.title),
                    TableColumn('Width', lambda image: image.width),
                    TableColumn('Height', lambda image: image.height),
                    TableColumn('Megapixels', lambda image: image.megapixels),
                    TableColumn('Datetime', lambda image: image.date or ''),
                    TableColumn(
                        'Camera make', lambda image: image.camera_make or ''
                    ),
                    TableColumn(
                        'Camera model', lambda image: image.camera_model or ''
                    ),
                    TableColumn(
                        'Has location',
                        lambda image: (
                            image.latitude is not None
                            and image.longitude is not None
                        ),
                    ),
                    TableColumn(
                        'Labels',
                        lambda image: (
                            ', '.join([label.name for label in image.labels])
                            or ''
                        ),
                    ),
                    TableColumn(
                        'Persons',
                        lambda image: (
                            ', '.join([person.name for person in image.persons])
                            or ''
                        ),
                    ),
                ],
            )
        elif output_format == OutputFormat.DETAILS:
            for image in images:
                console.print(f'[b]Title: [/b]: {image.title}')
                console.print(
                    f'[b]Location: [/b]: {image.latitude}, {image.longitude}'
                )
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


@images.command(name='favourite', help='Favourite specific images')
@with_filters(filter_generator=filter_gen)
@with_force_flag()
def favourite(
    _force: bool,
    _filter: ResourceFilter[Image],
    ctx: Context,
) -> None:
    """List the images in the database."""
    (_, _, db, console) = get_initialized_project(ctx)
    select_callback = create_update_confirm_callback(_force, console, 'title')
    images = db.set_favourite_for_images(
        favourite=True,
        specification=_filter.as_spec(),
        select_callback=select_callback,
    )
    console.print(f'Set {len(images)} images as favourite')


@images.command(name='unfavourite', help='Unfavourite specific images')
@with_filters(filter_generator=filter_gen)
@with_force_flag()
def unfavourite(
    _force: bool,
    _filter: ResourceFilter[Image],
    ctx: Context,
) -> None:
    """List the images in the database."""
    (_, _, db, console) = get_initialized_project(ctx)
    select_callback = create_update_confirm_callback(_force, console, 'title')
    images = db.set_favourite_for_images(
        favourite=False,
        specification=_filter.as_spec(),
        select_callback=select_callback,
    )
    console.print(f'Removed the favourite flag for {len(images)} images')


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
