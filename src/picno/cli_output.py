"""Module with the classes for data output."""

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import override

from rich import box
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from sqlmodel import SQLModel

from picno.model import Image, Label, Person


@dataclass(frozen=True)
class ModelField[SqlTable: SQLModel]:
    """Column for a table."""

    title: str
    getter: Callable[[SqlTable], str | int | float | datetime | None]


@dataclass(frozen=True)
class Details:
    """Dataclass for detail fields."""

    title: str
    subtitle: str | None = None
    details: dict[str, dict[str, str]] = field(default_factory=dict)


class OutputFormat[SqlTable: SQLModel](ABC):
    """Output formatter."""

    def __init__(
        self,
        model: type[SqlTable],
        fields: list[ModelField[SqlTable]],
        console: Console,
    ) -> None:
        """Set the console."""
        self._model = model
        self._fields = fields
        self._console = console

    def as_table(
        self, data: list[SqlTable], *, title: str | None = None
    ) -> None:
        """Print the data as a table."""
        table = Table(
            title=title,
            box=box.SIMPLE,
            row_styles=['on grey15', ''],
            highlight=True,
        )

        for col in self._fields:
            table.add_column(col.title)

        for row in data:
            table.add_row(*(str(col.getter(row)) for col in self._fields))

        self._console.print(table)

    @abstractmethod
    def _details(self, obj: SqlTable) -> Details:
        """Abstract method to get the correct details."""

    def as_details(self, data: list[SqlTable]) -> None:
        """Print the data as a table."""
        for row in data:
            details = self._details(row)

            output: list[str] = []

            output.append(f'[b][u][yellow]{details.title}[/yellow][/u][/b]')

            if details.subtitle:
                output.append(f'[grey15][i]{details.subtitle}[/i][/grey15]\n')

            for group_title, group_details in details.details.items():
                details = f'[b][u]{group_title.capitalize()}[/u][/b]\n\n'
                for detail_name, detail_value in group_details.items():
                    details += (
                        f'[b]{detail_name.capitalize()}:[/b] {detail_value}\n'
                    )
                output.append(details)

            details = Panel(Group(*output))
            self._console.print(details)


class OutputFormatImages(OutputFormat[Image]):
    """Specific output formatter for images."""

    def __init__(self, console: Console) -> None:
        """Create the correct object."""
        super().__init__(
            Image,
            [
                ModelField('ID', lambda image: image.id),
                ModelField(
                    'Status',
                    lambda image: str(image.status.value).capitalize(),
                ),
                ModelField(
                    ':glowing_star:',
                    lambda image: ':glowing_star:' if image.favorite else '',
                ),
                ModelField('Title', lambda image: image.title),
                ModelField('Physical path', lambda image: image.physical_path),
                ModelField('Width', lambda image: image.width),
                ModelField('Height', lambda image: image.height),
                ModelField('Megapixels', lambda image: image.megapixels),
                ModelField('Datetime', lambda image: image.date or ''),
                ModelField(
                    'Camera make', lambda image: image.camera_make or ''
                ),
                ModelField(
                    'Camera model', lambda image: image.camera_model or ''
                ),
                ModelField(
                    'Has location',
                    lambda image: (
                        image.latitude is not None
                        and image.longitude is not None
                    ),
                ),
                ModelField(
                    'Labels',
                    lambda image: (
                        ', '.join([label.name for label in image.labels]) or ''
                    ),
                ),
                ModelField(
                    'Persons',
                    lambda image: (
                        ', '.join([person.name for person in image.persons])
                        or ''
                    ),
                ),
            ],
            console,
        )

    @override
    def _details(self, obj: Image) -> Details:  # noqa: PLR0912
        """Generate details for the details-view."""
        # Titles
        title = obj.title or ''
        subtitle = obj.physical_path

        details: dict[str, dict[str, str]] = {}

        # Dimensions
        if obj.width and obj.height:
            details['dimensions'] = {
                'size': f'{obj.width} x {obj.height}',
                'aspect_ration': str(obj.aspect_ratio),
                'megapixels': str(obj.megapixels),
            }

        # Exif data - Camera
        camera_details: dict[str, str] = {}
        for camera_field in (
            'camera_make',
            'camera_model',
            'lens_model',
            'focal_length',
            'f_number',
            'exposude_time',
            'iso',
        ):
            if getattr(obj, camera_field, None) is not None:
                camera_details[camera_field.replace('_', ' ')] = getattr(
                    obj, camera_field
                )

        if camera_details:
            details['camera'] = camera_details

        # Exif data - Location
        location_details: dict[str, str] = {}
        for location_field in (
            'latitude',
            'longitude',
            'altitude',
        ):
            if getattr(obj, location_field, None) is not None:
                location_details[location_field.replace('_', ' ')] = getattr(
                    obj, location_field
                )

        if location_details:
            details['location'] = location_details

        # Exif data - Photo
        photo_details: dict[str, str] = {}
        for photo_field in (
            'color_space',
            'has_alpha',
            'orientation',
        ):
            if getattr(obj, photo_field, None) is not None:
                photo_details[photo_field.replace('_', ' ')] = getattr(
                    obj, photo_field
                )

        if photo_details:
            details['photo'] = photo_details

        relations: dict[str, str] = {}
        if obj.labels:
            relations['labels'] = ' / '.join(
                [label.name for label in obj.labels]
            )
        if obj.persons:
            relations['persons'] = ' / '.join(
                [person.name for person in obj.persons]
            )

        if photo_details:
            details['relations'] = relations

        return Details(title=title, subtitle=subtitle, details=details)


class OutputFormatPerson(OutputFormat[Person]):
    """Specific output formatter for persons."""

    def __init__(self, console: Console) -> None:
        """Create the correct object."""
        super().__init__(
            Person,
            [
                ModelField('ID', lambda person: person.id),
                ModelField('Name', lambda person: person.name),
                ModelField(
                    'Birthdate', lambda person: str(person.birthdate) or ''
                ),
                ModelField(
                    'Labels',
                    lambda person: (
                        ', '.join([label.name for label in person.labels]) or ''
                    ),
                ),
            ],
            console,
        )

    @override
    def _details(self, obj: Person) -> Details:
        """Generate details for the details-view."""
        title = obj.name or ''
        return Details(title=title)


class OutputFormatLabel(OutputFormat[Label]):
    """Specific output formatter for labels."""

    def __init__(self, console: Console) -> None:
        """Create the correct object."""
        super().__init__(
            Label,
            [
                ModelField('ID', lambda label: label.id),
                ModelField('Name', lambda label: label.name),
                ModelField('Group', lambda label: label.group or ''),
                ModelField(
                    'Name in group', lambda label: label.label_name or ''
                ),
            ],
            console,
        )

    @override
    def _details(self, obj: Label) -> Details:
        """Generate details for the details-view."""
        title = obj.name or ''
        return Details(title=title)
