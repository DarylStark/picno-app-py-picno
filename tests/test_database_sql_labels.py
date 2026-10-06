"""Tests for the DatabaseSql class."""

import pytest

from picno.database_sql import DatabaseSql
from picno.exceptions import (
    LabelAlreadyExistsError,
    LabelDoesNotExistError,
)
from picno.specs_labels import NameContainsLabelSpec


def test_database_sql_empty_db_empty_label_list(empty_db: DatabaseSql) -> None:
    """Test with a empty database.

    Check if we get a empty list of labels.
    """
    labels = empty_db.get_labels()

    assert labels == []


def test_database_sql_empty_db_empty_create_label(
    empty_db: DatabaseSql,
) -> None:
    """Test with a empty database.

    Check if we can add labels and get the created label.
    """
    label = empty_db.create_label('cat')

    assert label.id is not None
    assert label.name == 'cat'


def test_database_sql_filled_db_add_label_that_already_exists(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we get an error when creating a label taht already exists.
    """
    with pytest.raises(LabelAlreadyExistsError):
        filled_db.create_label('test_label_1')


def test_database_sql_filled_db_get_one_label_valid_id(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we can retrieve one label on ID.
    """
    label = filled_db.get_label(id=1)
    assert label is not None
    assert label.id == 1


def test_database_sql_filled_db_get_one_label_invalid_id(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we can retrieve one label on ID.
    """
    label = filled_db.get_label(id=999)
    assert label is None


def test_database_sql_filled_db_get_one_label_by_name_valid_name(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we can retrieve one label on name.
    """
    label = filled_db.get_label_by_name('test_label_1')
    assert label is not None
    assert label.id == 1


def test_database_sql_filled_db_get_one_label_by_name_invalid_name(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we can retrieve one label on name.
    """
    label = filled_db.get_label_by_name('not_existing')
    assert label is None


def test_database_sql_filled_db_get_all_labels(filled_db: DatabaseSql) -> None:
    """Test with a filled database.

    Check if we get all required labels.
    """
    labels = filled_db.get_labels()
    assert len(labels) == 20


def test_database_sql_filled_db_get_labels_filtered_on_name_insesitive(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we get all labels when we filter on name with the case insensitive
    flag set.
    """
    labels = filled_db.get_labels(NameContainsLabelSpec('tEst', True))
    assert len(labels) == 5


def test_database_sql_filled_db_get_labels_filtered_on_name_sesitive(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we get all labels when we filter on name with the case insensitive
    flag not set.
    """
    labels = filled_db.get_labels(NameContainsLabelSpec('test', False))
    assert len(labels) == 5


def test_database_sql_filled_db_update_one_label_already_exists(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we get a exception when updating a label to a name that already
    exists.
    """
    with pytest.raises(LabelAlreadyExistsError):
        filled_db.update_label(1, 'test_label_5')


def test_database_sql_filled_db_update_one_label_valid_id(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we can update a label based on id.
    """
    label = filled_db.update_label(1, 'updated_label')
    assert label is not None
    assert label.id == 1
    assert label.name == 'updated_label'

    updated_label = filled_db.get_label(id=1)
    assert updated_label is not None
    assert updated_label.id == 1
    assert updated_label.name == 'updated_label'


def test_database_sql_filled_db_update_one_label_invalid_id(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we get a None value when upating a Label that doesn't exist.
    """
    label = filled_db.update_label(999, 'updated_label')
    assert label is None


def test_database_sql_filled_db_rename_label(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we can rename a label.
    """
    label = filled_db.rename_label('test_label_1', 'test_label_999')
    assert label is not None
    assert label.id == 1
    assert label.name == 'test_label_999'

    updated_person = filled_db.get_label(id=1)
    assert updated_person is not None
    assert updated_person.id == 1
    assert updated_person.name == 'test_label_999'


def test_database_sql_filled_db_rename_label_unknown_name(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we get an error when giving a unknown name.
    """
    with pytest.raises(LabelDoesNotExistError):
        _ = filled_db.rename_label('test_label_999', 'test')


def test_database_sql_filled_db_rename_label_already_existing(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we get an error when giving a new name that is already present in
    the database.
    """
    with pytest.raises(LabelAlreadyExistsError):
        _ = filled_db.rename_label('test_label_1', 'test_label_2')


def test_database_sql_filled_db_delete_one_label_valid_id(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we can delete a label with a valid id.
    """
    deleted = filled_db.delete_label(1)
    assert deleted

    updated_label = filled_db.get_label(id=1)
    assert updated_label is None


def test_database_sql_filled_db_delete_one_label_invalid_id(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we get a False value when deleting a Label that doesn't exist.
    """
    deleted = filled_db.delete_label(999)
    assert not deleted


def test_database_sql_filled_db_delete_many_labels_valid_spec(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we can delete multiple labels based on a spec.
    """
    deleted = filled_db.delete_labels(NameContainsLabelSpec('test'))
    assert deleted == 5

    labels = filled_db.get_labels(NameContainsLabelSpec('test'))
    assert len(labels) == 0


def test_database_sql_filled_db_delete_many_labels_no_spec(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we can delete all labels by not giving a spec.
    """
    deleted = filled_db.delete_labels()
    assert deleted == 20

    labels = filled_db.get_labels()
    assert len(labels) == 0


def test_database_sql_filled_db_delete_many_labels_invalid_spec(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we get a 0 result when deleting labels that don't exist.
    """
    deleted = filled_db.delete_labels(NameContainsLabelSpec('not_existing'))
    assert deleted == 0

    labels = filled_db.get_labels()
    assert len(labels) == 20


def test_database_sql_filled_db_delete_label_by_name(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Test if we can remove labels by name.
    """
    filled_db.delete_label_by_name('test_label_1')
    labels = filled_db.get_labels()
    assert len(labels) == 19


def test_database_sql_filled_db_delete_label_by_name_invalid_ame(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Test if we can get an error when removing a label that doesn't exist.
    """
    with pytest.raises(LabelDoesNotExistError):
        filled_db.delete_label_by_name('test_label_999')
