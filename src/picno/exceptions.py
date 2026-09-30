"""Module with exceptions."""


class PicnoError(Exception):
    """Base class for exceptions."""


class DatabaseError(PicnoError):
    """Base class for database errors."""


class LabelAlreadyExistsError(DatabaseError):
    """Exception when a Label is created that already exists."""
