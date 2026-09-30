"""Module with the database abstraction."""

from abc import ABC, abstractmethod

from .model import Label
from .specs_labels import LabelSpecification


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
