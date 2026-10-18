"""Module with the database abstraction."""

from abc import ABC, abstractmethod
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import date
from enum import Enum

from .model import Image, Label, Person, ResourceStatus
from .specs_images import ImageSpecification
from .specs_labels import LabelSpecification
from .specs_persons import PersonSpecification

SelectCallbackLabel = Callable[[Sequence[Label]], bool]
SelectCallbackPerson = Callable[[Sequence[Person]], bool]
SelectCallbackImage = Callable[[Sequence[Image]], bool]


class SortOrder(Enum):
    """Specify a sorting order."""

    ASC = 1
    DESC = 2


@dataclass
class SortField:
    """Class to specify a sorting."""

    field: str
    order: SortOrder
    case_insensitive_sort = True


class RetrieveOption(Enum):
    """Options for retrieving resources."""

    LOAD_PERSON_LABELS = 1
    LOAD_IMAGE_LABELS = 2
    LOAD_IMAGE_PERSONS = 3


class Database(ABC):
    """Abstract class for databases."""

    @abstractmethod
    def close(self) -> None:
        """Close the database."""

    @abstractmethod
    def create_labels(self, names: list[str]) -> list[Label]:
        """Method to add multiple labels to the database."""

    @abstractmethod
    def get_labels(
        self,
        *,
        specification: LabelSpecification | None = None,
        sorting: Sequence[SortField] | None = None,
    ) -> list[Label]:
        """Method to retrieve (a subset of) the labels in the database."""

    @abstractmethod
    def rename_label(
        self,
        label_name: str,
        new_name: str,
        *,
        select_callback: SelectCallbackLabel | None = None,
    ) -> Label:
        """Rename a label."""

    @abstractmethod
    def delete_labels(
        self,
        *,
        specification: LabelSpecification | None = None,
        select_callback: SelectCallbackLabel | None = None,
    ) -> int:
        """Delete labels matching a specification.

        Returns:
            The number of labels deleted.
        """

    @abstractmethod
    def create_persons(
        self, names: list[str], *, birthdate: date | None = None
    ) -> list[Person]:
        """Method to add multiple persons to the database."""

    @abstractmethod
    def get_persons(
        self,
        *,
        specification: PersonSpecification | None = None,
        options: Sequence[RetrieveOption] | None = None,
        sorting: Sequence[SortField] | None = None,
    ) -> list[Person]:
        """Method to retrieve (a subset of) the persons in the database."""

    @abstractmethod
    def rename_person(
        self,
        person_name: str,
        new_name: str,
        *,
        select_callback: SelectCallbackPerson | None = None,
    ) -> Person:
        """Rename a person."""

    @abstractmethod
    def set_birthdate_for_persons(
        self,
        new_birthdate: date | None = None,
        *,
        specification: PersonSpecification | None = None,
        select_callback: SelectCallbackPerson | None = None,
    ) -> list[Person]:
        """Set the birthdate for persons."""

    @abstractmethod
    def delete_persons(
        self,
        *,
        specification: PersonSpecification | None = None,
        select_callback: SelectCallbackPerson | None = None,
    ) -> int:
        """Delete persons matching a specification.

        Returns:
            The number of persons deleted.
        """

    @abstractmethod
    def add_label_to_persons(
        self,
        label: str,
        *,
        specification: PersonSpecification | None = None,
        select_callback: SelectCallbackPerson | None = None,
    ) -> list[Person]:
        """Method to add a label to a persons."""

    @abstractmethod
    def remove_label_from_persons(
        self,
        label: str,
        *,
        specification: PersonSpecification | None = None,
        select_callback: SelectCallbackPerson | None = None,
    ) -> list[Person]:
        """Method to remove a label from persons."""

    @abstractmethod
    def create_images_from_objects(
        self, images: Sequence[Image]
    ) -> list[Image]:
        """Create multiple images from mulitple image objects."""

    @abstractmethod
    def get_images(
        self,
        *,
        specification: ImageSpecification | None = None,
        options: Sequence[RetrieveOption] | None = None,
        sorting: Sequence[SortField] | None = None,
    ) -> list[Image]:
        """Method to retrieve (a subset of) the labels in the database."""

    @abstractmethod
    def set_image_status(
        self,
        status: ResourceStatus,
        *,
        specification: ImageSpecification | None = None,
        select_callback: SelectCallbackImage | None = None,
    ) -> list[Image]:
        """Method to set the status of specific images."""

    @abstractmethod
    def add_label_to_images(
        self,
        label: str,
        *,
        specification: ImageSpecification | None = None,
        select_callback: SelectCallbackImage | None = None,
    ) -> list[Image]:
        """Method to add a label to a images."""

    @abstractmethod
    def add_person_to_images(
        self,
        person: str,
        *,
        specification: ImageSpecification | None = None,
        select_callback: SelectCallbackImage | None = None,
    ) -> list[Image]:
        """Method to add a person to a images."""

    @abstractmethod
    def remove_label_from_images(
        self,
        label: str,
        *,
        specification: ImageSpecification | None = None,
        select_callback: SelectCallbackImage | None = None,
    ) -> list[Image]:
        """Method to remove a label from images."""

    @abstractmethod
    def remove_person_from_images(
        self,
        person: str,
        *,
        specification: ImageSpecification | None = None,
        select_callback: SelectCallbackImage | None = None,
    ) -> list[Image]:
        """Method to remove a person from images."""

    @abstractmethod
    def set_favorite_for_images(
        self,
        favorite: bool,
        *,
        specification: ImageSpecification | None = None,
        select_callback: SelectCallbackImage | None = None,
    ) -> list[Image]:
        """Set the favorite flag for specific images."""

    @abstractmethod
    def rename_image(
        self,
        image_title: str,
        new_title: str,
        *,
        select_callback: SelectCallbackImage | None = None,
    ) -> Image:
        """Rename a image."""
