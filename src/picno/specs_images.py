"""Module with the specifications for labels."""

from typing import override

from sqlalchemy import ColumnElement, and_
from sqlmodel import col, exists, select

from .model import (
    Image,
    ImageLabelLink,
    ImagePersonLink,
    Label,
    Person,
)
from .specs import (
    AllSpecification,
    ParentSpecification,
    Specification,
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


class Sha256IsImageSpec(ParentSpecification[Image]):
    """Specification for when the sha256 should be the same."""

    def __init__(self, sha256: str) -> None:
        """Set the given values."""
        super().__init__(
            StrIsSpecification(Image, 'sha256', sha256, case_insensitive=False)
        )


class PathNameIsImageSpec(ParentSpecification[Image]):
    """Specification for when the path should be the same."""

    def __init__(self, path: str, case_insensitive: bool = True) -> None:
        """Set the given values."""
        super().__init__(
            StrIsSpecification(Image, 'physical_path', path, case_insensitive)
        )


class HasLabelImageSpec(ImageSpecification):
    """Filter on images with a specific image."""

    def __init__(self, label_name: str) -> None:
        """Set the label name to search for."""
        self._label_name = label_name

    @override
    def as_sql(self) -> ColumnElement[bool]:
        """Create the SQL commands for this object."""
        return exists(
            select(1)
            .select_from(ImageLabelLink)
            .join(Label, col(Label.id) == ImageLabelLink.label_id)
            .where(
                and_(
                    col(ImageLabelLink.image_id) == Image.id,
                    col(Label.name) == self._label_name,
                )
            )
        )


class HasPersonImageSpec(ImageSpecification):
    """Filter on images with a specific person."""

    def __init__(self, person_name: str) -> None:
        """Set the person name to search for."""
        self._person_name = person_name

    @override
    def as_sql(self) -> ColumnElement[bool]:
        """Create the SQL commands for this object."""
        return exists(
            select(1)
            .select_from(ImagePersonLink)
            .join(Person, col(Person.id) == ImagePersonLink.person_id)
            .where(
                and_(
                    col(ImagePersonLink.image_id) == Image.id,
                    col(Person.name) == self._person_name,
                )
            )
        )
