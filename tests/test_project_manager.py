"""Tests for the ProjectManager class."""

from pathlib import Path

import pytest

from picno.exceptions import ImageFileNotFoundError
from picno.project import Project, ProjectType
from picno.project_manager import ProjectManager


def test_get_image_object_from_file_invalid_file() -> None:
    """Test if we get an error when importing a non-existing file."""
    manager = ProjectManager(
        Project(
            name='Unmanaged project',
            data_folder='./tests/unmanaged_project',
            project_type=ProjectType.UNMANAGED,
            database_str='sqlite:///./picno.db',
        )
    )

    with pytest.raises(ImageFileNotFoundError):
        manager.get_image_object_from_file(
            Path('./tests/unmanaged_project/not_existing.jpg')
        )


def test_get_image_object_from_file_valid_file() -> None:
    """Test if we get the correct information from a real file."""
    manager = ProjectManager(
        Project(
            name='Unmanaged project',
            data_folder='./tests/unmanaged_project',
            project_type=ProjectType.UNMANAGED,
            database_str='sqlite:///./picno.db',
        )
    )

    filename = Path('./tests/unmanaged_project/image_001.jpg')
    image = manager.get_image_object_from_file(filename)

    assert image.physical_file == filename
    assert (
        image.resource_title == 'image_001.jpg'
    )  # TODO: Extension should be gone
    assert image.exists
    assert image.width == 100
    assert image.height == 68
    assert image.camera_make == 'Canon'
    assert image.camera_model == 'Canon EOS 40D'
    assert image.orientation == 1
    assert image.focal_length == 135.0
    assert image.f_number == 7.1
    assert image.exposure_time == 0.00625
    assert image.iso == 100


def test_scan_data_directory() -> None:
    """Test scanning the data directory."""
    manager = ProjectManager(
        Project(
            name='Unmanaged project',
            data_folder='./tests/unmanaged_project',
            project_type=ProjectType.UNMANAGED,
            database_str='sqlite:///./picno.db',
        )
    )
    new_files = manager.scan_directory(Path('./tests/unmanaged_project'))
    assert len(new_files) == 4
