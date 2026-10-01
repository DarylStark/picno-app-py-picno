"""Module with exceptions."""


class PicnoError(Exception):
    """Base class for exceptions."""


class CliError(PicnoError):
    """Base class for CLI errors."""


class ProjectParseError(CliError):
    """Exception when a project file cannot be parsed."""


class ProjectAlreadyInitializedError(CliError):
    """Exception when a project is already initialized."""


class ProjectNotInitializedError(CliError):
    """Exception when the project is not yet initialized."""


class LabelDoesNotExistError(CliError):
    """Exception when a label doesn't exists that is searched for."""


class DatabaseError(PicnoError):
    """Base class for database errors."""


class LabelAlreadyExistsError(DatabaseError):
    """Exception when a Label is created that already exists."""
