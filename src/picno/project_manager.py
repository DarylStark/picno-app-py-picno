"""Module with the project manager."""

from datetime import UTC, datetime
from fractions import Fraction
from pathlib import Path

from PIL import ExifTags
from PIL import Image as PilImage
from PIL.TiffImagePlugin import IFDRational

from picno.exceptions import FileNotInDataDirectoryError, ImageFileNotFoundError

from .database import Database
from .database_sql import DatabaseSql
from .model import Image
from .project import Project


def _to_float(value: Fraction | tuple | IFDRational | None) -> float | None:
    if value is None:
        return None
    if isinstance(value, Fraction):
        return float(value)
    if isinstance(value, tuple) and len(value) == 2:
        num, den = value
        if den:
            return num / den
        return None
    if isinstance(value, IFDRational):
        return float(value)
    return None


def _dms_to_decimal(
    dms: tuple[IFDRational, IFDRational, IFDRational] | None, ref: str | None
) -> float | None:
    if not dms or ref is None:
        return None

    degrees = _to_float(dms[0])
    minutes = _to_float(dms[1])
    seconds = _to_float(dms[2])
    if degrees is None or minutes is None or seconds is None:
        return None

    decimal = degrees + minutes / 60.0 + seconds / 3600.0
    if ref in ('S', 'W'):
        decimal = -decimal
    return decimal


def _parse_exif_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.strptime(value, '%Y:%m:%d %H:%M:%S')
        return dt.replace(tzinfo=UTC)
    except ValueError:
        return None


class ProjectManager:
    """Project class represents a project."""

    def __init__(self, structure: Project) -> None:
        """Set the project."""
        self._structure = structure
        self._database: Database = DatabaseSql(self._structure.database_str)

        self._structure.set_sync_ignore_list_to_path()

    @property
    def database(self) -> Database:
        """Property to retrieve the database object."""
        return self._database

    def get_image_object_from_file(self, file: Path) -> Image:
        """Create a image object from a file."""
        if not file.is_file():
            raise ImageFileNotFoundError(
                f'Image "{file.resolve()}" is not found'
            )

        image_obj = Image(physical_path=str(file), title=file.name)

        with PilImage.open(file) as img:
            image_obj.width, image_obj.height = img.size
            exif = img.getexif()
            extended = exif.get_ifd(ExifTags.Base.ExifOffset)

            # Basic tags
            image_obj.date = _parse_exif_datetime(
                exif.get(306) or exif.get(36867)
            )
            image_obj.camera_make = exif.get(271)
            image_obj.camera_model = exif.get(272)
            image_obj.lens_model = exif.get(42036)
            image_obj.orientation = exif.get(274)

            # Numeric tags
            image_obj.focal_length = _to_float(extended.get(37386))
            image_obj.f_number = _to_float(extended.get(33437))
            image_obj.exposure_time = _to_float(extended.get(33434))
            iso_val = extended.get(34855)
            image_obj.iso = int(iso_val) if iso_val is not None else None

            # Location
            gps = exif.get_ifd(34853) if exif else {}
            lat = gps.get(2)
            lat_ref = gps.get(1)
            lon = gps.get(4)
            lon_ref = gps.get(3)
            alt = gps.get(6)
            image_obj.latitude = _dms_to_decimal(lat, lat_ref)
            image_obj.longitude = _dms_to_decimal(lon, lon_ref)
            image_obj.altitude = _to_float(alt)

        return image_obj

    def scan_directory(self, directory: Path) -> list[Path]:
        """Scan the data directory for the project.

        Returns a list of images and videos in the directory.
        """
        found_files: list[Path] = []
        for file_path in directory.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in {
                '.jpg',
                '.jpeg',
                '.png',
                '.webp',
            }:
                found_files.append(file_path)

        return found_files

    def _get_relative_path(self, file_path: Path) -> Path:
        """Retrieve the relative path for a file."""
        data_folder = self._structure.data_folder
        try:
            return file_path.relative_to(data_folder)
        except ValueError as exc:
            raise FileNotInDataDirectoryError(
                f'File "{file_path}" is not in directory {data_folder}'
            ) from exc

    def _is_new_image(self, image_path: Path) -> bool:
        """Check if a image is new."""
        return (
            self._database.get_image_on_path(
                self._get_relative_path(image_path)
            )
            is None
        )

    def _get_new_files_in_data_directory(self) -> list[Image]:
        """Sync the media directory.

        Returns a list of new media items.
        """
        new_data: list[Image] = []
        all_media = self.scan_directory(self._structure.data_folder)
        for media in all_media:
            if any(
                media.is_relative_to(ignore_path)
                for ignore_path in self._structure.sync_ignore
            ):
                continue

            if self._is_new_image(media):
                image_obj = self.get_image_object_from_file(media)
                image_obj.physical_file = self._get_relative_path(media)
                new_data.append(image_obj)
        return new_data

    def sync_data_directory(self) -> list[Image]:
        """Sync the media directory.

        Returns a list of new media items.
        """
        return self._database.create_images_from_objects(
            self._get_new_files_in_data_directory()
        )
