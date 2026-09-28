"""Tests for the model."""

from pathlib import Path

from picno.model import FileResource, Label


def test_label_no_group() -> None:
    """Test the `group` method of a label that has no group."""
    label = Label(name='test_label')
    assert label.group is None
    assert label.label_name == 'test_label'


def test_label_with_group() -> None:
    """Test the `group` method of a label that has a group."""
    label = Label(name='group:test_label')
    assert label.group == 'group'
    assert label.label_name == 'test_label'


def test_file_resource_title_no_title() -> None:
    """Test the `title` method of the `FileResource` model.

    Checks if the filename is returned when no real title is set.
    """
    resource = FileResource(
        id=1, physical_file='/home/user/Pictures/IMG_100_01.jpg'
    )
    assert resource.resource_title == 'IMG_100_01.jpg'


def test_file_resource_title_with_title() -> None:
    """Test the `title` method of the `FileResource` model.

    Checks if the real title is set when a title is set, and not the filename.
    """
    resource = FileResource(
        id=1,
        title='Test image',
        physical_file='/home/user/Pictures/IMG_100_01.jpg',
    )
    assert resource.resource_title == 'Test image'


def test_file_resource_exists_no_file() -> None:
    """Test the `exists` method of the `FileResource` model.

    Tests if the `exists` method returns `False` when the file doesn't exist.
    """
    resource = FileResource(
        id=1, physical_file='/home/user/Pictures/IMG_100_01.jpg'
    )
    assert resource.exists is False


def test_file_resource_exists_pointing_to_directory() -> None:
    """Test the `exists` method of the `FileResource` model.

    Tests if the `exists` method returns `False` when the given filename is
    actually a directory.
    """
    resource = FileResource(id=1, physical_file=Path(__file__).parent)
    assert resource.exists is False


def test_file_resource_exists_existing_file() -> None:
    """Test the `exists` method of the `FileResource` model.

    Tests if the `exists` method returns `True` when the file does exist.
    """
    resource = FileResource(
        id=1,
        physical_file=__file__,
    )
    assert resource.exists
