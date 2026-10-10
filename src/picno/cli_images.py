"""Module with the `pico images` options."""

import re
from enum import Enum

from typer import Argument, Context, Option, Typer

from picno.database import RetrieveOption
from picno.model import ResourceStatus
from picno.specs_images import ImageFilter

from .cli_context import get_initialized_project
from .cli_format import TableColumn, print_table

images = Typer(name='images', help='Image management')


class OutputFormat(Enum):
    """Output foramts."""

    TABLE = 'table'
    DETAILS = 'details'


filter_args = {
    'name': Option(
        default=None,
        help='Filter on a specific name',
    ),
    'iname': Option(
        default=None,
        help='Filter on a specific name (case insensitive)',
    ),
    'name_contains': Option(
        default=None, help='Filter on a text in the name <repeatable>'
    ),
    'iname_contains': Option(
        default=None,
        help='Filter on a text in the name (case insensitive) <repeatable>',
    ),
    'path_name_contains': Option(
        default=None, help='Filter on a text in the path name <repeatable>'
    ),
    'ipath_name_contains': Option(
        default=None,
        help='Filter on a text in the path name (case insensitive)<repeatable>',
    ),
    'has_location': Option(
        default=None, help='Filter on images with a location'
    ),
    'status': Option(
        default=None, help='Filter on images with a specific status'
    ),
    'favourite': Option(
        default=None, help='Filter on images with that are favourite'
    ),
    'label': Option(
        default=None, help='Filter on a specific label <repeatable>'
    ),
}


@images.command(name='ls', help='List images')
def ls(
    ctx: Context,
    output_format: OutputFormat = Option(
        default=OutputFormat.TABLE, help='The way to output data'
    ),
    name: str | None = filter_args['name'],
    iname: str | None = filter_args['iname'],
    name_contains: list[str] | None = filter_args['name_contains'],
    iname_contains: list[str] | None = filter_args['iname_contains'],
    path_name_contains: list[str] | None = filter_args['path_name_contains'],
    ipath_name_contains: list[str] | None = filter_args['ipath_name_contains'],
    has_location: bool | None = filter_args['has_location'],
    status: ResourceStatus | None = filter_args['status'],
    favourite: bool | None = filter_args['favourite'],
    label: list[str] | None = filter_args['label'],
) -> None:
    """List the images in the database."""
    (_, _, db, console) = get_initialized_project(ctx)
    filter = ImageFilter.build_from_locals(locals())

    # Retrieve the images
    images = db.get_images(
        filter.get_specifications(),
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
                        'Camera', lambda image: image.camera_model or ''
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
def set_status(
    ctx: Context,
    new_status: ResourceStatus = Argument(help='The status to set'),
    name: str | None = filter_args['name'],
    iname: str | None = filter_args['iname'],
    name_contains: list[str] | None = filter_args['name_contains'],
    iname_contains: list[str] | None = filter_args['iname_contains'],
    path_name_contains: list[str] | None = filter_args['path_name_contains'],
    ipath_name_contains: list[str] | None = filter_args['ipath_name_contains'],
    has_location: bool | None = filter_args['has_location'],
    status: ResourceStatus | None = filter_args['status'],
    favourite: bool | None = filter_args['favourite'],
    label: list[str] | None = filter_args['label'],
) -> None:
    """List the images in the database."""
    (_, _, db, console) = get_initialized_project(ctx)
    filter = ImageFilter.build_from_locals(locals())
    images = db.set_image_status(
        status=new_status,
        specification=filter.get_specifications(),
    )
    console.print(f'Updated {len(images)} images')


@images.command(name='label', help='Label specific images')
def label(
    ctx: Context,
    label_name: str = Argument(help='The name of the label to add'),
    name: str | None = filter_args['name'],
    iname: str | None = filter_args['iname'],
    name_contains: list[str] | None = filter_args['name_contains'],
    iname_contains: list[str] | None = filter_args['iname_contains'],
    path_name_contains: list[str] | None = filter_args['path_name_contains'],
    ipath_name_contains: list[str] | None = filter_args['ipath_name_contains'],
    has_location: bool | None = filter_args['has_location'],
    status: ResourceStatus | None = filter_args['status'],
    favourite: bool | None = filter_args['favourite'],
    label: list[str] | None = filter_args['label'],
) -> None:
    """Add a label to images."""
    (_, _, db, console) = get_initialized_project(ctx)
    filter = ImageFilter.build_from_locals(locals())
    images = db.add_label_to_images(
        label_name, specification=filter.get_specifications()
    )
    console.print(f'Added label "{label_name}" to {len(images)} images')


@images.command(name='unlabel', help='Unlabel specific images')
def unlabel(
    ctx: Context,
    label_name: str = Argument(help='The name of the label to remove'),
    name: str | None = filter_args['name'],
    iname: str | None = filter_args['iname'],
    name_contains: list[str] | None = filter_args['name_contains'],
    iname_contains: list[str] | None = filter_args['iname_contains'],
    path_name_contains: list[str] | None = filter_args['path_name_contains'],
    ipath_name_contains: list[str] | None = filter_args['ipath_name_contains'],
    has_location: bool | None = filter_args['has_location'],
    status: ResourceStatus | None = filter_args['status'],
    favourite: bool | None = filter_args['favourite'],
    label: list[str] | None = filter_args['label'],
) -> None:
    """Remove a label from images."""
    (_, _, db, console) = get_initialized_project(ctx)
    filter = ImageFilter.build_from_locals(locals())
    images = db.remove_label_from_images(
        label_name, specification=filter.get_specifications()
    )
    console.print(f'Removed label "{label_name}" from {len(images)} images')


@images.command(name='favourite', help='Favourite specific images')
def favourite(
    ctx: Context,
    name: str | None = filter_args['name'],
    iname: str | None = filter_args['iname'],
    name_contains: list[str] | None = filter_args['name_contains'],
    iname_contains: list[str] | None = filter_args['iname_contains'],
    path_name_contains: list[str] | None = filter_args['path_name_contains'],
    ipath_name_contains: list[str] | None = filter_args['ipath_name_contains'],
    has_location: bool | None = filter_args['has_location'],
    status: ResourceStatus | None = filter_args['status'],
    favourite: bool | None = filter_args['favourite'],
    label: list[str] | None = filter_args['label'],
) -> None:
    """List the images in the database."""
    (_, _, db, console) = get_initialized_project(ctx)
    filter = ImageFilter.build_from_locals(locals())
    images = db.set_favourite_for_images(
        favourite=True,
        specification=filter.get_specifications(),
    )
    console.print(f'Set {len(images)} images as favourite')


@images.command(name='unfavourite', help='Unfavourite specific images')
def unfavourite(
    ctx: Context,
    name: str | None = filter_args['name'],
    iname: str | None = filter_args['iname'],
    name_contains: list[str] | None = filter_args['name_contains'],
    iname_contains: list[str] | None = filter_args['iname_contains'],
    path_name_contains: list[str] | None = filter_args['path_name_contains'],
    ipath_name_contains: list[str] | None = filter_args['ipath_name_contains'],
    has_location: bool | None = filter_args['has_location'],
    status: ResourceStatus | None = filter_args['status'],
    favourite: bool | None = filter_args['favourite'],
    label: list[str] | None = filter_args['label'],
) -> None:
    """List the images in the database."""
    (_, _, db, console) = get_initialized_project(ctx)
    filter = ImageFilter.build_from_locals(locals())
    images = db.set_favourite_for_images(
        favourite=False,
        specification=filter.get_specifications(),
    )
    console.print(f'Removed the favourite flag for {len(images)} images')


@images.command(name='mv', help='Rename a image')
def mv(
    ctx: Context,
    old_title: str = Argument(help='Current title of the image'),
    new_title: str = Argument(help='New title of the image'),
) -> None:
    """Rename a image."""
    (_, _, db, console) = get_initialized_project(ctx)
    db.rename_image(old_title, new_title)
    console.print(f'Renamed image "{old_title}" to "{new_title}"')


@images.command(name='exec', help='Execute a command for specific images')
def exec(
    ctx: Context,
    executor: str = Argument(help='The executor to run'),
    options: list[str] | None = Option(
        default=None, help='Give options for the executor'
    ),
    name: str | None = filter_args['name'],
    iname: str | None = filter_args['iname'],
    name_contains: list[str] | None = filter_args['name_contains'],
    iname_contains: list[str] | None = filter_args['iname_contains'],
    path_name_contains: list[str] | None = filter_args['path_name_contains'],
    ipath_name_contains: list[str] | None = filter_args['ipath_name_contains'],
    has_location: bool | None = filter_args['has_location'],
    status: ResourceStatus | None = filter_args['status'],
    favourite: bool | None = filter_args['favourite'],
    label: list[str] | None = filter_args['label'],
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

    filter = ImageFilter.build_from_locals(locals())
    pm.exec_for_images(
        executor=executor,
        specification=filter.get_specifications(),
        options=option_dict,
    )


@images.command(name='tag-person', help='Tag a person for specific labels')
def tag_person(
    ctx: Context,
    person_name: str = Argument(help='The name of the person to tag'),
    name: str | None = filter_args['name'],
    iname: str | None = filter_args['iname'],
    name_contains: list[str] | None = filter_args['name_contains'],
    iname_contains: list[str] | None = filter_args['iname_contains'],
    path_name_contains: list[str] | None = filter_args['path_name_contains'],
    ipath_name_contains: list[str] | None = filter_args['ipath_name_contains'],
    has_location: bool | None = filter_args['has_location'],
    status: ResourceStatus | None = filter_args['status'],
    favourite: bool | None = filter_args['favourite'],
    label: list[str] | None = filter_args['label'],
) -> None:
    """Add a person to images."""
    (_, _, db, console) = get_initialized_project(ctx)
    filter = ImageFilter.build_from_locals(locals())
    images = db.add_person_to_images(
        person_name, specification=filter.get_specifications()
    )
    console.print(f'Added person "{person_name}" to {len(images)} images')


@images.command(name='untag-person', help='Untag a person from specific images')
def untag_person(
    ctx: Context,
    person_name: str = Argument(help='The name of the person to untag'),
    name: str | None = filter_args['name'],
    iname: str | None = filter_args['iname'],
    name_contains: list[str] | None = filter_args['name_contains'],
    iname_contains: list[str] | None = filter_args['iname_contains'],
    path_name_contains: list[str] | None = filter_args['path_name_contains'],
    ipath_name_contains: list[str] | None = filter_args['ipath_name_contains'],
    has_location: bool | None = filter_args['has_location'],
    status: ResourceStatus | None = filter_args['status'],
    favourite: bool | None = filter_args['favourite'],
    label: list[str] | None = filter_args['label'],
) -> None:
    """Remove a person from images."""
    (_, _, db, console) = get_initialized_project(ctx)
    filter = ImageFilter.build_from_locals(locals())
    images = db.remove_person_from_images(
        person_name, specification=filter.get_specifications()
    )
    console.print(f'Removed person "{person_name}" from {len(images)} images')
