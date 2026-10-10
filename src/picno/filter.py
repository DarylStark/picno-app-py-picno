"""Module with a abstract filter class."""

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Self


@dataclass(frozen=True)
class Filter[T](ABC):
    """Class for Label Filter builder."""

    @classmethod
    def build_from_locals(cls, scope: Mapping[str, Any]) -> Self:
        """Create object from `locals()`."""
        filter_data: dict[str, Any] = {
            key: value
            for key, value in scope.items()
            if key in cls.__dataclass_fields__
        }
        return cls(**filter_data)

    @abstractmethod
    def get_specifications(self) -> T | None:
        """Builder for specific specifications."""
