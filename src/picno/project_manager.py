"""Module with the project manager."""

from fractions import Fraction
from pathlib import Path

from PIL import ExifTags
from PIL import Image as PilImage
from PIL.TiffImagePlugin import IFDRational

from picno.exceptions import ImageFileNotFoundError

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


class ProjectManager:
    """Project class represents a project."""

    def __init__(self, structure: Project) -> None:
        """Set the project."""
        self._structure = structure
        self._database: Database = DatabaseSql(self._structure.database_str)

    @property
    def database(self) -> Database:
        """Property to retrieve the database object."""
        return self._database

    def add_image_from_file(self, file: Path) -> Image:
        """Create a image object from a file."""
        if not file.is_file():
            raise ImageFileNotFoundError(
                f'Image "{file.resolve()}" is not found'
            )

        image_obj = Image(physical_file=file)

        with PilImage.open(file) as img:
            image_obj.width, image_obj.height = img.size
            exif = img.getexif()
            extended = exif.get_ifd(ExifTags.Base.ExifOffset)

            # Basic tags
            image_obj.date = exif.get(306) or exif.get(36867)
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
