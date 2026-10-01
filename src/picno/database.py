"""Module with the database abstraction."""

from abc import ABC, abstractmethod

from .model import Label, Person
from .specs_labels import LabelSpecification
from .specs_persons import PersonSpecification


class Database(ABC):
    """Abstract class for databases."""

    @abstractmethod
    def create_label(self, name: str) -> Label:
        """Method to add a label to the database."""

    @abstractmethod
    def get_label(self, id: int) -> Label | None:
        """Method to retrieve one label."""

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
    def create_person(self, name: str) -> Person:
        """Method to add a person to the database."""

    @abstractmethod
    def get_person(self, id: int) -> Person | None:
        """Method to retrieve one person."""

    @abstractmethod
    def get_persons(
        self, specification: PersonSpecification | None = None
    ) -> list[Person]:
        """Method to retrieve (a subset of) the persons in the database."""

    @abstractmethod
    def update_person(self, id: int, name: str) -> Person | None:
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
