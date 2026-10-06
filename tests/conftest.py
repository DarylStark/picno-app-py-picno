"""Configuration for PyTest."""

from collections.abc import Generator
from datetime import date
from pathlib import Path

import pytest

from picno.database_sql import DatabaseSql


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
    empty_db.create_label('test_label_1')
    empty_db.create_label('test_label_2')
    empty_db.create_label('test_label_3')
    empty_db.create_label('test_label_4')
    empty_db.create_label('test_label_5')
    empty_db.create_label('group1:label1')
    empty_db.create_label('group1:label2')
    empty_db.create_label('group1:label3')
    empty_db.create_label('group1:label4')
    empty_db.create_label('group1:label5')
    empty_db.create_label('group2:label1')
    empty_db.create_label('group2:label2')
    empty_db.create_label('group2:label3')
    empty_db.create_label('group2:label4')
    empty_db.create_label('group2:label5')
    empty_db.create_label('group3:label1')
    empty_db.create_label('group3:label2')
    empty_db.create_label('group3:label3')
    empty_db.create_label('group3:label4')
    empty_db.create_label('group3:label5')

    # Add persons
    empty_db.create_person('Example Person 1')
    empty_db.create_person('Example Person 2')
    empty_db.create_person('Example Person 3')
    empty_db.create_person('Example Person 4')
    empty_db.create_person('Example Person 5', birthdate=date(1986, 10, 26))

    # Add labels to persons
    empty_db.add_label_to_person('Example Person 2', 'test_label_1')
    empty_db.add_label_to_person('Example Person 2', 'test_label_2')
    empty_db.add_label_to_person('Example Person 2', 'group1:label2')
    empty_db.add_label_to_person('Example Person 2', 'group2:label1')

    return empty_db
