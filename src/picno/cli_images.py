"""Module with the `pico images` options."""

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


@images.command(name='ls', help='List images')
def ls(
    ctx: Context,
    name: str | None = Option(default=None, help='Filter on a specific name'),
    output_format: OutputFormat = Option(
        default=OutputFormat.TABLE, help='The way to output data'
    ),
    iname: str | None = Option(
        default=None, help='Filter on a specific name (case insensitive)'
    ),
    name_contains: list[str] | None = Option(
        default=None, help='Filter on a text in the name <repeatable>'
    ),
    iname_contains: list[str] | None = Option(
        default=None,
        help='Filter on a text in the name (case insensitive) <repeatable>',
    ),
    path_name_contains: list[str] | None = Option(
        default=None, help='Filter on a text in the path name <repeatable>'
    ),
    ipath_name_contains: list[str] | None = Option(
        default=None,
        help='Filter on a text in the path name (case insensitive)<repeatable>',
    ),
    has_location: bool | None = Option(
        default=None, help='Filter on images with a location'
    ),
    status: ResourceStatus | None = Option(
        default=None, help='Filter on images with a specific status'
    ),
) -> None:
    """List the images in the database."""
    (_, _, db, console) = get_initialized_project(ctx)

    filter = ImageFilter(
        name=name,
        iname=iname,
        name_contains=name_contains,
        iname_contains=iname_contains,
        path_name_contains=path_name_contains,
        ipath_name_contains=ipath_name_contains,
        has_location=has_location,
        status=status,
    )

    # Retrieve the images
    images = db.get_images(
        filter.get_specifications(), options=[RetrieveOption.LOAD_IMAGE_LABELS]
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
    name: str | None = Option(default=None, help='Filter on a specific name'),
    iname: str | None = Option(
        default=None, help='Filter on a specific name (case insensitive)'
    ),
    name_contains: list[str] | None = Option(
        default=None, help='Filter on a text in the name <repeatable>'
    ),
    iname_contains: list[str] | None = Option(
        default=None,
        help='Filter on a text in the name (case insensitive) <repeatable>',
    ),
    path_name_contains: list[str] | None = Option(
        default=None, help='Filter on a text in the path name <repeatable>'
    ),
    ipath_name_contains: list[str] | None = Option(
        default=None,
        help='Filter on a text in the path name (case insensitive)<repeatable>',
    ),
    has_location: bool | None = Option(
        default=None, help='Filter on images with a location'
    ),
    status: ResourceStatus | None = Option(
        default=None, help='Filter on images with a specific status'
    ),
) -> None:
    """List the images in the database."""
    (_, _, db, console) = get_initialized_project(ctx)

    filter = ImageFilter(
        name=name,
        iname=iname,
        name_contains=name_contains,
        iname_contains=iname_contains,
        path_name_contains=path_name_contains,
        ipath_name_contains=ipath_name_contains,
        has_location=has_location,
        status=status,
    )
    images = db.set_image_status(
        status=new_status,
        specification=filter.get_specifications(),
    )
    console.print(f'Updated {len(images)} images')


@images.command(name='add-label', help='Add a label to a image')
def add_label(
    ctx: Context,
    name: str = Argument(help='The name of the image to add the label too'),
    label: str = Argument(help='The name of the label to add'),
) -> None:
    """Add a label to a person."""
    (_, _, db, console) = get_initialized_project(ctx)
    db.add_label_to_image(name, label)
    console.print(f'Added label "{label}" to "{name}"')


@images.command(name='remove-label', help='Remoev a label from a image')
def remove_label(
    ctx: Context,
    name: str = Argument(help='The name of the image to remove the label from'),
    label: str = Argument(help='The name of the label to remove'),
) -> None:
    """Remove a label from a person."""
    (_, _, db, console) = get_initialized_project(ctx)
    db.remove_label_from_image(name, label)
    console.print(f'Removed label "{label}" from "{name}"')
