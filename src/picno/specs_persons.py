"""Module with the specifications for labels."""

from .model import Person
from .specs import AllSpecification, Specification

PersonSpecification = Specification[Person]
PersonAllSpecification = AllSpecification[Person]
