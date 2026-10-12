"""Configuration for PyTest."""

from collections.abc import Generator
from datetime import date
from pathlib import Path

import pytest

from picno.database_sql import DatabaseSql
from picno.model import Image
from picno.specs_images import NameIsImageSpec
from picno.specs_persons import NameIsPersonSpec


@pytest.fixture
def temp_db_path(tmp_path: Path) -> str:
    """Create a temporary path for a database."""
    return f'sqlite:///{tmp_path / "test.db"}'


@pytest.fixture
def empty_db(temp_db_path: str) -> Generator[DatabaseSql]:
    """Create a empty database to test with."""
    db = DatabaseSql(temp_db_path)
    yield db
    db.close()


@pytest.fixture
def filled_db(empty_db: DatabaseSql) -> DatabaseSql:
    """Create a filles database to test with."""
    # Add labels
    empty_db.create_labels(['test_label_1'])
    empty_db.create_labels(['test_label_2'])
    empty_db.create_labels(['test_label_3'])
    empty_db.create_labels(['test_label_4'])
    empty_db.create_labels(['test_label_5'])
    empty_db.create_labels(['group1:label1'])
    empty_db.create_labels(['group1:label2'])
    empty_db.create_labels(['group1:label3'])
    empty_db.create_labels(['group1:label4'])
    empty_db.create_labels(['group1:label5'])
    empty_db.create_labels(['group2:label1'])
    empty_db.create_labels(['group2:label2'])
    empty_db.create_labels(['group2:label3'])
    empty_db.create_labels(['group2:label4'])
    empty_db.create_labels(['group2:label5'])
    empty_db.create_labels(['group3:label1'])
    empty_db.create_labels(['group3:label2'])
    empty_db.create_labels(['group3:label3'])
    empty_db.create_labels(['group3:label4'])
    empty_db.create_labels(['group3:label5'])

    # Add persons
    empty_db.create_persons(['Example Person 1'])
    empty_db.create_persons(['Example Person 2'])
    empty_db.create_persons(['Example Person 3'])
    empty_db.create_persons(['Example Person 4'])
    empty_db.create_persons(['Example Person 5'], birthdate=date(1986, 10, 26))

    # Add labels to persons
    empty_db.add_label_to_persons(
        'test_label_1', specification=NameIsPersonSpec('Example Person 2')
    )
    empty_db.add_label_to_persons(
        'test_label_2', specification=NameIsPersonSpec('Example Person 2')
    )
    empty_db.add_label_to_persons(
        'group1:label2', specification=NameIsPersonSpec('Example Person 2')
    )
    empty_db.add_label_to_persons(
        'group2:label1', specification=NameIsPersonSpec('Example Person 2')
    )

    # Add images
    empty_db.create_images_from_objects(
        [
            Image(physical_path='./image_001.jpg', title='image_001.jpg'),
            Image(
                physical_path='./image_002.jpg',
                title='image_002.jpg',
                favourite=True,
            ),
            Image(physical_path='./image_003.jpg', title='image_003.jpg'),
            Image(physical_path='./image_004.jpg', title='image_004.jpg'),
            Image(physical_path='./image_005.jpg', title='image_005.jpg'),
        ]
    )

    # Add labels to images
    empty_db.add_label_to_images(
        'test_label_1', specification=NameIsImageSpec('image_001.jpg')
    )
    empty_db.add_label_to_images(
        'group1:label1', specification=NameIsImageSpec('image_001.jpg')
    )

    # Add persons to images
    empty_db.add_person_to_images(
        'Example Person 3', NameIsImageSpec('image_001.jpg')
    )

    return empty_db
