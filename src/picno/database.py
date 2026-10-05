"""Module with the database abstraction."""

from abc import ABC, abstractmethod
from collections.abc import Sequence
from datetime import date
from enum import Enum

from .model import Label, Person
from .specs_labels import LabelSpecification
from .specs_persons import PersonSpecification


class _ClearField:
    """Empty class that indicates that a field should be cleared.

    Useful for fields that are Null-able. By using this, we can give a update
    method to command to clear a field, without providing it None.
    """


CLEARFIELD = _ClearField()


class RetrieveOption(Enum):
    """Options for retrieving resources."""

    LOAD_LABELS = 1


class Database(ABC):
    """Abstract class for databases."""

    @abstractmethod
    def close(self) -> None:
        """Close the database."""

    @abstractmethod
    def create_label(self, name: str) -> Label:
        """Method to add a label to the database."""

    @abstractmethod
    def get_label(self, id: int) -> Label | None:
        """Method to retrieve one label."""

    @abstractmethod
    def get_label_by_name(
        self, name: str, options: Sequence[RetrieveOption] | None = None
    ) -> Label | None:
        """Method to retrieve one label by name."""

    @abstractmethod
    def get_labels(
        self, specification: LabelSpecification | None = None
    ) -> list[Label]:
        """Method to retrieve (a subset of) the labels in the database."""

    @abstractmethod
    def update_label(self, id: int, new_name: str) -> Label | None:
        """Method to update one label."""

    @abstractmethod
    def delete_label(self, id: int) -> bool:
        """Method to delete one label."""

    @abstractmethod
    def delete_labels(
        self, specification: LabelSpecification | None = None
    ) -> int:
        """Delete labels matching a specification.

        Returns:
            The number of labels deleted.
        """

    @abstractmethod
    def create_person(self, name: str, birthdate: date | None = None) -> Person:
        """Method to add a person to the database."""

    @abstractmethod
    def get_person(
        self, id: int, options: Sequence[RetrieveOption] | None = None
    ) -> Person | None:
        """Method to retrieve one person."""

    @abstractmethod
    def get_person_by_name(
        self, name: str, options: Sequence[RetrieveOption] | None = None
    ) -> Person | None:
        """Method to retrieve one person by name."""

    @abstractmethod
    def get_persons(
        self,
        specification: PersonSpecification | None = None,
        options: Sequence[RetrieveOption] | None = None,
    ) -> list[Person]:
        """Method to retrieve (a subset of) the persons in the database."""

    @abstractmethod
    def update_person(
        self,
        id: int,
        name: str | None = None,
        birthdate: date | None | _ClearField = None,
    ) -> Person | None:
        """Method to update one person."""

    @abstractmethod
    def delete_person(self, id: int) -> bool:
        """Method to delete one person."""

    @abstractmethod
    def delete_persons(
        self, specification: PersonSpecification | None = None
    ) -> int:
        """Delete persons matching a specification.

        Returns:
            The number of persons deleted.
        """

    @abstractmethod
    def add_label_to_person(self, person: str, label: str) -> None:
        """Method to add a label to a person (on names)."""

    @abstractmethod
    def remove_label_from_person(self, person: str, label: str) -> None:
        """Remove a label from a person."""
