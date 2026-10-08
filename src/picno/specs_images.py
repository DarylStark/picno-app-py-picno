"""Module with the specifications for labels."""

from dataclasses import dataclass
from typing import override

from sqlalchemy import ColumnElement
from sqlmodel import col

from .filter import Filter
from .model import Image, ResourceStatus
from .specs import (
    AllSpecification,
    FieldIsSpecification,
    ParentSpecification,
    Specification,
    StrContainsSpecification,
    StrIsSpecification,
)

ImageSpecification = Specification[Image]
ImageAllSpecification = AllSpecification[Image]


class NameIsImageSpec(ParentSpecification[Image]):
    """Specification for when the name should be the same."""

    def __init__(self, name: str, case_insensitive: bool = True) -> None:
        """Set the given values."""
        super().__init__(
            StrIsSpecification(Image, 'title', name, case_insensitive)
        )


class NameContainsImageSpec(ParentSpecification[Image]):
    """Specification for when the name contains text."""

    def __init__(self, text: str, case_insensitive: bool = True) -> None:
        """Set the given values."""
        super().__init__(
            StrContainsSpecification(Image, 'title', text, case_insensitive)
        )


class PathNameContainsImageSpec(ParentSpecification[Image]):
    """Specification for when the path name contains text."""

    def __init__(self, text: str, case_insensitive: bool = True) -> None:
        """Set the given values."""
        super().__init__(
            StrContainsSpecification(
                Image, 'physical_path', text, case_insensitive
            )
        )


class HasLocationPersonSpec(ImageSpecification):
    """Specification for when the the image should have an location."""

    def __init__(self, value: bool) -> None:
        """Set the value to check for."""
        self._value = value

    @override
    def as_sql(self) -> ColumnElement[bool]:
        """Abstract method to create a SQL query object."""
        if self._value:
            return col(Image.latitude).is_not(None)
        return col(Image.latitude).is_(None)


class StatusIsImageSpec(ParentSpecification[Image]):
    """Specification for when the status should be the same."""

    def __init__(self, status: ResourceStatus) -> None:
        """Set the given values."""
        super().__init__(
            FieldIsSpecification(Image, 'status', status.value, True)
        )


@dataclass(frozen=True)
class ImageFilter(Filter[ImageSpecification]):
    """Class for Image Filter builder."""

    name: str | None = None
    iname: str | None = None
    name_contains: list[str] | None = None
    iname_contains: list[str] | None = None
    path_name_contains: list[str] | None = None
    ipath_name_contains: list[str] | None = None
    has_location: bool | None = None
    status: ResourceStatus | None = None

    def get_specifications(self) -> ImageSpecification | None:
        """Builder for Image Specifications."""
        specs = ImageAllSpecification()

        if self.name:
            specs.append(
                NameIsImageSpec(name=self.name, case_insensitive=False)
            )

        if self.iname:
            specs.append(
                NameIsImageSpec(name=self.iname, case_insensitive=True)
            )

        for value in self.name_contains or []:
            specs.append(
                NameContainsImageSpec(text=value, case_insensitive=False)
            )

        for value in self.iname_contains or []:
            specs.append(
                NameContainsImageSpec(text=value, case_insensitive=True)
            )

        for value in self.path_name_contains or []:
            specs.append(
                PathNameContainsImageSpec(text=value, case_insensitive=False)
            )

        for value in self.ipath_name_contains or []:
            specs.append(
                PathNameContainsImageSpec(text=value, case_insensitive=True)
            )

        if self.has_location is not None:
            specs.append(HasLocationPersonSpec(self.has_location))

        if self.status:
            specs.append(StatusIsImageSpec(self.status))

        return specs if specs else None
