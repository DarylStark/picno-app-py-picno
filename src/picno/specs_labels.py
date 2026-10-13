"""Module with the specifications for labels."""

from .model import Label
from .specs import (
    AllSpecification,
    ParentSpecification,
    Specification,
    StrContainsSpecification,
    StrIsSpecification,
)

LabelSpecification = Specification[Label]
LabelAllSpecification = AllSpecification[Label]


class NameIsLabelSpec(ParentSpecification[Label]):
    """Specification for when the name should be the same."""

    def __init__(self, name: str, case_insensitive: bool = True) -> None:
        """Set the given values."""
        super().__init__(
            StrIsSpecification(Label, 'name', name, case_insensitive)
        )


class NameContainsLabelSpec(ParentSpecification[Label]):
    """Specification for when the name contains text."""

    def __init__(self, text: str, case_insensitive: bool = True) -> None:
        """Set the given values."""
        super().__init__(
            StrContainsSpecification(Label, 'name', text, case_insensitive)
        )
