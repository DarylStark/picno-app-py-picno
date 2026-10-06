"""Module with a abstract filter class."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class Filter[T](ABC):
    """Class for Label Filter builder."""

    @abstractmethod
    def get_specifications(self) -> T | None:
        """Builder for specific specifications."""
