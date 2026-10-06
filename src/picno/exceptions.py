"""Module with exceptions."""


class PicnoError(Exception):
    """Base class for exceptions."""


class ProjectError(PicnoError):
    """Errors for the project itself."""


class ImageFileNotFoundError(ProjectError):
    """Error for when a given image is not found."""


class CliError(PicnoError):
    """Base class for CLI errors."""


class InvalidArgumentInputError(CliError):
    """Error for invalid input into the CLI arguments."""


class ProjectParseError(CliError):
    """Exception when a project file cannot be parsed."""


class ProjectAlreadyInitializedError(CliError):
    """Exception when a project is already initialized."""


class ProjectNotInitializedError(CliError):
    """Exception when the project is not yet initialized."""


class DatabaseError(PicnoError):
    """Base class for database errors."""


class ResourceAlreadyExistsError(DatabaseError):
    """Exception when a generic resource is created that already exists."""


class ResourceNotFoundError(DatabaseError):
    """Exception when a generic resource is not found."""


class PersonAlreadyExistsError(DatabaseError):
    """Exception when a Person is created that already exists."""


class PersonDoesNotExistError(DatabaseError):
    """Exception when a person doesn't exists that is searched for."""


class LabelAlreadyExistsError(DatabaseError):
    """Exception when a Label is created that already exists."""


class LabelDoesNotExistError(DatabaseError):
    """Exception when a label doesn't exists that is searched for."""
