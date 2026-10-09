"""Tests for the DatabaseSql class."""

import pytest

from picno.database import RetrieveOption
from picno.database_sql import DatabaseSql
from picno.exceptions import (
    ImageDoesNotExistError,
    ImageLabelLinkAlreadyExistsError,
    LabelDoesNotExistError,
)
from picno.specs_images import NameIsImageSpec


def test_database_sql_empty_db_empty_image_list(empty_db: DatabaseSql) -> None:
    """Test with a empty database.

    Check if we get a empty list of images.
    """
    images = empty_db.get_images()

    assert images == []


def test_database_sql_filled_db_get_all_images(filled_db: DatabaseSql) -> None:
    """Test with a filled database.

    Check if we get all required images.
    """
    images = filled_db.get_images()
    assert len(images) == 5


def test_database_sql_filled_db_get_all_images_with_labels(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we get labels when retrieving images.
    """
    images = filled_db.get_images(options=[RetrieveOption.LOAD_IMAGE_LABELS])
    assert len(images[0].labels) == 2
    assert len(images[1].labels) == 0


def test_database_sql_filled_db_add_label_to_image(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we can add labels to images
    """
    filled_db.add_label_to_image('image_001.jpg', 'test_label_5')
    images = filled_db.get_images(
        specification=NameIsImageSpec(name='image_001.jpg'),
        options=[RetrieveOption.LOAD_IMAGE_LABELS],
    )
    assert len(images[0].labels) == 3


def test_database_sql_filled_db_add_double_label_to_image(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we can add labels to images
    """
    filled_db.add_label_to_image('image_001.jpg', 'test_label_5')
    with pytest.raises(ImageLabelLinkAlreadyExistsError):
        filled_db.add_label_to_image('image_001.jpg', 'test_label_5')


def test_database_sql_filled_db_add_label_to_image_group(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we can add labels to images
    """
    filled_db.add_label_to_image('image_001.jpg', 'group2:label1')
    images = filled_db.get_images(
        specification=NameIsImageSpec(name='image_001.jpg'),
        options=[RetrieveOption.LOAD_IMAGE_LABELS],
    )
    assert len(images[0].labels) == 3


def test_database_sql_filled_db_add_label_to_image_regroup(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we can add labels to images
    """
    filled_db.add_label_to_image('image_001.jpg', 'group1:label2')
    images = filled_db.get_images(
        specification=NameIsImageSpec(name='image_001.jpg'),
        options=[RetrieveOption.LOAD_IMAGE_LABELS],
    )
    assert len(images[0].labels) == 2


def test_database_sql_filled_db_add_label_to_image_invalid_image(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we can add labels to images
    """
    with pytest.raises(ImageDoesNotExistError):
        filled_db.add_label_to_image('image_999.jpg', 'group1:label2')


def test_database_sql_filled_db_add_label_to_image_invalid_label(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we can add labels to images
    """
    with pytest.raises(LabelDoesNotExistError):
        filled_db.add_label_to_image('image_001.jpg', 'non_existing_label')


def test_database_sql_filled_db_remove_label_from_image(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Test if we cannot remove labels from a images.
    """
    filled_db.remove_label_from_image('image_001.jpg', 'test_label_1')
    filled_db.remove_label_from_image('image_001.jpg', 'group1:label1')
    images = filled_db.get_images(
        specification=NameIsImageSpec(name='image_001.jpg'),
        options=[RetrieveOption.LOAD_IMAGE_LABELS],
    )
    assert len(images[0].labels) == 0


def test_database_sql_filled_db_remove_label_from_image_invalid_image(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Test if we can add labels to images.
    """
    with pytest.raises(ImageDoesNotExistError):
        filled_db.remove_label_from_image('image_999.jpg', 'test_label_1')


def test_database_sql_filled_db_remove_label_from_image_invalid_label(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Test if we can add labels to images.
    """
    with pytest.raises(LabelDoesNotExistError):
        filled_db.remove_label_from_image('image_001.jpg', 'test_label_999')


def test_database_sql_filled_db_favourite_image(filled_db: DatabaseSql) -> None:
    """Test with a filled database.

    Test if we can favourite images.
    """
    set_favourite = filled_db.set_favourite_for_images(
        True,
        specification=NameIsImageSpec(name='image_001.jpg'),
    )
    assert len(set_favourite) == 1
    images = filled_db.get_images(
        specification=NameIsImageSpec(name='image_001.jpg')
    )
    assert len(images) == 1
    assert images[0].favourite


def test_database_sql_filled_db_unfavourite_image(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Test if we can unfavourite images.
    """
    set_favourite = filled_db.set_favourite_for_images(
        False,
        specification=NameIsImageSpec(name='image_002.jpg'),
    )

    assert len(set_favourite) == 1

    images = filled_db.get_images(
        specification=NameIsImageSpec(name='image_002.jpg')
    )
    assert len(images) == 1
    assert not images[0].favourite


def test_database_sql_filled_db_add_label_to_images(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we can add labels to images
    """
    images = filled_db.add_label_to_images(
        'test_label_5', specification=NameIsImageSpec(name='image_001.jpg')
    )
    assert len(images) == 1
    images = filled_db.get_images(
        specification=NameIsImageSpec(name='image_001.jpg'),
        options=[RetrieveOption.LOAD_IMAGE_LABELS],
    )
    assert len(images[0].labels) == 3


def test_database_sql_filled_db_add_label_to_all_images(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we can add labels to images
    """
    images = filled_db.add_label_to_images('test_label_5')
    assert len(images) == 5


def test_database_sql_filled_db_add_label_to_images_wrong_label(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we can add labels to images
    """
    with pytest.raises(LabelDoesNotExistError):
        filled_db.add_label_to_images('test_label_999')


def test_database_sql_filled_db_add_label_to_all_images_double(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we can add labels to images
    """
    images = filled_db.add_label_to_images(
        'test_label_1', NameIsImageSpec(name='image_001.jpg')
    )
    assert len(images) == 0


def test_database_sql_filled_db_add_label_to_images_group(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we can add labels to images
    """
    filled_db.add_label_to_images(
        'group2:label1', specification=NameIsImageSpec(name='image_001.jpg')
    )
    images = filled_db.get_images(
        specification=NameIsImageSpec(name='image_001.jpg'),
        options=[RetrieveOption.LOAD_IMAGE_LABELS],
    )
    assert len(images[0].labels) == 3


def test_database_sql_filled_db_add_label_to_images_regroup(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we can add labels to images
    """
    filled_db.add_label_to_images(
        'group1:label2', specification=NameIsImageSpec(name='image_001.jpg')
    )
    images = filled_db.get_images(
        specification=NameIsImageSpec(name='image_001.jpg'),
        options=[RetrieveOption.LOAD_IMAGE_LABELS],
    )
    assert len(images[0].labels) == 2


def test_database_sql_filled_db_remove_label_from_images(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we can add labels to images
    """
    images = filled_db.remove_label_from_images('test_label_1')
    assert len(images) == 1


def test_database_sql_filled_db_remove_label_from_images_non_label(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we can add labels to images
    """
    images = filled_db.remove_label_from_images('test_label_5')
    assert len(images) == 0


def test_database_sql_filled_db_remove_label_from_images_not_existing_label(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we can add labels to images
    """
    with pytest.raises(LabelDoesNotExistError):
        filled_db.remove_label_from_images('test_label_999')
