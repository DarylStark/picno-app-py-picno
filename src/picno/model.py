"""The database model."""

from pathlib import Path

from pydantic import BaseModel, Field


class Label(BaseModel):
    """Model for a label.

    A label can contain a group and a name. This should be seperated with a
    colon. If there is no colon, only a name is given.
    """

    name: str

    @property
    def group(self) -> str | None:
        """Returns the groupname, if set."""
        if ':' in self.name:
            return self.name.split(':')[0]
        return None

    @property
    def label_name(self) -> str | None:
        """Returns the name of the label.

        If a group is set, it returns the name of the label without the
        groupname. Otherwise, it returns the complete name.
        """
        if ':' in self.name:
            return ':'.join(self.name.split(':')[1:])
        return self.name


class Resource(BaseModel):
    """Base class for resources.

    Contains all the fields and methods required for specific resources. These
    resources have a id, an title, tagged people and labels. The methods make
    sure these fields can be used safely.
    """

    id: int
    labels: list[Label] = Field(default_factory=list)
    people: list[Person] = Field(default_factory=list)


class FileResource(Resource):
    """Base class for resources for files.

    Contains all the fields and methods for file-based resources. These types of
    resources can have a title, but if that isn't filled in, the filename will
    be used as title.
    """

    physical_file: Path
    title: str | None = None

    @property
    def resource_title(self) -> str:
        """Property for the title of the object.

        If no title is set, the filename will be returned.
        """
        if not self.title:
            return self.physical_file.name
        return self.title

    @property
    def exists(self) -> bool:
        """Property to determine if a file (still) exists."""
        return self.physical_file.is_file()


class Person(Resource):
    """Model for persons."""

    name: str


class Image(Resource):
    """Model for a image file."""

    pass


class Video(Resource):
    """Model for a video file."""

    pass
