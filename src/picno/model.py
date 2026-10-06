"""The database model."""

from datetime import date, datetime
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, computed_field, model_validator
from sqlmodel import Field, Relationship, SQLModel


class TableResource(SQLModel):
    """Base class for resources that get a SQL table."""

    id: int | None = Field(default=None, primary_key=True)


class PersonLabelLink(SQLModel, table=True):
    """Link model for Persons and Labels."""

    __tablename__ = 'person_label_link'

    person_id: int | None = Field(
        default=None,
        foreign_key='person.id',
        primary_key=True,
        ondelete='CASCADE',
    )
    label_id: int | None = Field(
        default=None,
        foreign_key='label.id',
        primary_key=True,
        ondelete='CASCADE',
    )


class Label(TableResource, table=True):
    """Model for a label.

    A label can contain a group and a name. This should be seperated with a
    colon. If there is no colon, only a name is given.
    """

    name: str = Field(unique=True)

    people: list[Person] = Relationship(
        back_populates='labels',
        link_model=PersonLabelLink,
    )

    @computed_field
    @property
    def group(self) -> str | None:
        """Returns the groupname, if set."""
        if ':' in self.name:
            return self.name.split(':')[0]
        return None

    @computed_field
    @property
    def label_name(self) -> str | None:
        """Returns the name of the label.

        If a group is set, it returns the name of the label without the
        groupname. Otherwise, it returns the complete name.
        """
        if ':' in self.name:
            return ':'.join(self.name.split(':')[1:])
        return None


class Person(TableResource, table=True):
    """Model for persons."""

    name: str = Field(unique=True)
    birthdate: date | None = Field(default=None)

    labels: list[Label] = Relationship(
        back_populates='people',
        link_model=PersonLabelLink,
    )


class Scene(TableResource):
    """Model for a scene in a video."""

    title: str
    start: float
    end: float


class FileResource(SQLModel):
    """Base class for resources for files.

    Contains all the fields and methods for file-based resources. These types of
    resources can have a title, but if that isn't filled in, the filename will
    be used as title.
    """

    physical_path: str
    title: str | None = Field(default=None, unique=True)

    @model_validator(mode='after')
    def set_title_from_path(self) -> FileResource:
        """Automatically fill the title."""
        if not self.title:
            self.title = Path(self.physical_path).name
        return self

    @property
    def physical_file(self) -> Path:
        """Get the `Path` object for the file."""
        return Path(self.physical_path)

    @physical_file.setter
    def physical_file(self, value: Path) -> None:
        """Setter for the phycal file."""
        self.physical_path = str(value)


class Dimensions(SQLModel):
    """Model for dimensions.

    Can be used for images and videofiles to specify how big the frames for the
    video are or how big the image is.
    """

    width: int = 0
    height: int = 0

    @computed_field
    @property
    def aspect_ratio(self) -> float:
        """Returns the aspect ration for the dimensions."""
        return self.width / self.height

    @computed_field
    @property
    def megapixels(self) -> float:
        """Returns the amount of megapixels for the dimensions."""
        return (self.width * self.height) / 1_000_000


class BaseExifData(BaseModel):
    """Base models for exif data.

    Contains generic field that are used for video and images.
    """

    date: datetime | None = None
    camera_make: str | None = None
    camera_model: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    altitude: float | None = None


class ImageExifData(BaseExifData):
    """Base model for Exif Data for images."""

    lens_model: str | None = None
    focal_length: float | None = None
    f_number: float | None = None
    exposure_time: float | None = None
    iso: int | None = None
    orientation: int | None = 1


class VideoExifData(BaseExifData):
    """Base model for Exif Data for videos."""


class Image(ImageExifData, Dimensions, FileResource, TableResource, table=True):
    """Model for a image file."""

    color_space: str | None = None
    has_alpha: bool = False


class VideoQuality(Enum):
    """Enum for the possible qualities for videos."""

    LOW = 'low'
    AVERAGE = 'average'
    HIGH = 'high'
    VERY_HIGH = 'very_high'


class Video(VideoExifData, Dimensions, FileResource, TableResource, table=True):
    """Model for a video file."""

    duration: float
    fps: float | None = None
    bitrate_in_bps: int | None = None
    video_codec: str | None = None
    audio_coded: str | None = None
    has_audio: bool = False
    audio_channels: int | None = None
    container_format: str | None = None

    @computed_field
    @property
    def pixel_density(self) -> float | None:
        """Calculate the "pixel density" for the video.

        Values:
        -      < 0.05 = low quality
        - 0.05 - 0.10 = acceptable / average quality
        - 0.10 - 0.20 = high quality
        -      > 0.20 = very high quality
        """
        if not self.bitrate_in_bps or not self.fps:
            return None
        return self.bitrate_in_bps / (self.width * self.height * self.fps)

    @computed_field
    @property
    def quality(self) -> VideoQuality | None:
        """Returns the video quality based on pixel density."""
        pdd = self.pixel_density
        if pdd is None:
            return None
        if pdd < 0.05:
            return VideoQuality.LOW
        elif pdd < 0.10:
            return VideoQuality.AVERAGE
        elif pdd < 0.20:
            return VideoQuality.HIGH
        return VideoQuality.VERY_HIGH
