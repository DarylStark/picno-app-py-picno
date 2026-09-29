"""Tests for the model."""

from pathlib import Path

from pytest import approx

from picno.model import Dimensions, FileResource, Label, Video, VideoQuality


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


def test_dimensions_aspect_ratio() -> None:
    """Test the `aspect_ratio` method of the `Dimensions` model.

    Tests if the `aspect_ratio` gives the correct value.
    """
    dimensions = Dimensions(width=3456, height=2160)
    assert dimensions.aspect_ratio == 1.6


def test_dimensions_megapixels() -> None:
    """Test the `megapixel` method of the `Dimensions` model.

    Tests if the `megapixel` gives the correct value.
    """
    dimensions = Dimensions(width=3456, height=2160)
    assert dimensions.megapixels == 7.46496


def test_video_pixel_density_no_bitrate() -> None:
    """Test the `pixel_density` method of the `Video` model.

    Test that it doesn't give a value back when there is no bitrate.
    """
    video = Video(
        id=1,
        physical_file=__file__,
        dimensions=Dimensions(width=1920, height=1080),
        duration=10,
        fps=30,
    )
    assert video.pixel_density is None


def test_video_pixel_density_no_fps() -> None:
    """Test the `pixel_density` method of the `Video` model.

    Test that it doesn't give a value back when there is no fps.
    """
    video = Video(
        id=1,
        physical_file=__file__,
        dimensions=Dimensions(width=1920, height=1080),
        duration=10,
        bitrate_in_bps=8_000_000,
    )
    assert video.pixel_density is None


def test_video_pixel_density_bitrate_and_fps() -> None:
    """Test the `pixel_density` method of the `Video` model.

    Test that it gives the correct value when a bitrate and fps is given.
    """
    video = Video(
        id=1,
        physical_file=__file__,
        dimensions=Dimensions(width=1920, height=1080),
        duration=10,
        fps=30,
        bitrate_in_bps=8_000_000,
    )
    assert video.pixel_density == approx(0.1286, rel=1e-3, abs=1e-6)


def test_video_quality_no_bitrate() -> None:
    """Test the `quality` method of the `Video` model.

    Test that it doesn't give a value back when there is no bitrate.
    """
    video = Video(
        id=1,
        physical_file=__file__,
        dimensions=Dimensions(width=1920, height=1080),
        duration=10,
        fps=30,
    )
    assert video.quality is None


def test_video_quality_no_fps() -> None:
    """Test the `quality` method of the `Video` model.

    Test that it doesn't give a value back when there is no fps.
    """
    video = Video(
        id=1,
        physical_file=__file__,
        dimensions=Dimensions(width=1920, height=1080),
        duration=10,
        bitrate_in_bps=8_000_000,
    )
    assert video.quality is None


def test_video_quality_bitrate_and_fps() -> None:
    """Test the `quality` method of the `Video` model.

    Test that it gives the correct value when a bitrate and fps is given.
    """
    video = Video(
        id=1,
        physical_file=__file__,
        dimensions=Dimensions(width=1920, height=1080),
        duration=10,
        fps=30,
        bitrate_in_bps=8_000_000,
    )
    assert video.quality is VideoQuality.LOW
