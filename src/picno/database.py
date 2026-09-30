"""Module with the database abstraction."""

from abc import ABC, abstractmethod

from .model import Label
from .specs import Specification

LabelSpecification = Specification[Label]


class Database(ABC):
    """Abstract class for databases."""

    @abstractmethod
    def get_labels(
        self, specification: LabelSpecification | None = None
    ) -> list[Label]:
        """Method to retrieve (a subset of) the labels in the database."""
