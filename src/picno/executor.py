"""Module with the Executor base class."""

from abc import ABC, abstractmethod

from picno.model import Image


class Executor(ABC):
    """Base class for executors."""

    @abstractmethod
    def start(self) -> None:
        """Start method."""

    @abstractmethod
    def done(self) -> None:
        """Method run when done."""

    @abstractmethod
    def process_image(self, image: Image) -> None:
        """Process a image."""
