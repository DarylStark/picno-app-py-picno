"""Tests for the DatabaseSql class."""

from datetime import date

import pytest

from picno.database import RetrieveOption
from picno.database_sql import DatabaseSql
from picno.exceptions import (
    LabelDoesNotExistError,
    PersonAlreadyExistsError,
    PersonDoesNotExistError,
)
from picno.specs_persons import NameContainsPersonSpec, NameIsPersonSpec


def test_database_sql_empty_db_empty_person_list(empty_db: DatabaseSql) -> None:
    """Test with a empty database.

    Check if we get a empty list of person.
    """
    persons = empty_db.get_persons()

    assert persons == []


def test_database_sql_empty_db_empty_create_persons(
    empty_db: DatabaseSql,
) -> None:
    """Test with a empty database.

    Check if we can add persons and get the created person.
    """
    persons = empty_db.create_persons(['Example Person', 'Example Person2'])

    assert len(persons) == 2
    for person in persons:
        assert person.id is not None


def test_database_sql_empty_db_empty_create_persons_with_birthdate(
    empty_db: DatabaseSql,
) -> None:
    """Test with a empty database.

    Check if we can add persons and get the created person.
    """
    persons = empty_db.create_persons(
        ['Example Person 1', 'Example Person 2'], birthdate=date(1986, 10, 26)
    )

    assert len(persons) == 2
    for person in persons:
        assert person.birthdate == date(1986, 10, 26)


def test_database_sql_filled_db_create_persons_that_already_exists(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we get an error when creating a person that already exists.
    """
    with pytest.raises(PersonAlreadyExistsError):
        filled_db.create_persons(['Example Person 1', 'Example Person 999'])


def test_database_sql_filled_db_get_all_persons(filled_db: DatabaseSql) -> None:
    """Test with a filled database.

    Check if we get all required persons.
    """
    persons = filled_db.get_persons()
    assert len(persons) == 5


def test_database_sql_filled_db_set_birthday_for_person(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we can set the birthday for a person.
    """
    persons = filled_db.set_birthdate_for_persons(
        date(year=1986, month=10, day=26),
        specification=NameIsPersonSpec('Example Person 1'),
    )
    assert len(persons) == 1
    for person in persons:
        assert person.birthdate == date(year=1986, month=10, day=26)

    updated_persons = filled_db.get_persons(
        specification=NameIsPersonSpec('Example Person 1'),
    )
    assert len(updated_persons) == 1
    assert updated_persons[0].id == 1
    assert updated_persons[0].birthdate == date(year=1986, month=10, day=26)


def test_database_sql_filled_db_set_birthday_for_person_clear(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we can clear the birthday for a person.
    """
    persons = filled_db.set_birthdate_for_persons(
        None, specification=NameIsPersonSpec('Example Person 5')
    )
    assert len(persons) == 1
    for person in persons:
        assert person.birthdate is None

    updated_persons = filled_db.get_persons(
        specification=NameIsPersonSpec('Example Person 5')
    )
    assert len(updated_persons) == 1
    assert updated_persons[0].id == 5
    assert updated_persons[0].birthdate is None


def test_database_sql_filled_db_set_birthday_for_person_already_good(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we get 0 when we set the birthdate to the already known value.
    """
    persons = filled_db.set_birthdate_for_persons(
        date(1986, 10, 26), specification=NameIsPersonSpec('Example Person 5')
    )
    assert len(persons) == 0
    for person in persons:
        assert person.birthdate is None

    updated_persons = filled_db.get_persons(
        specification=NameIsPersonSpec('Example Person 5')
    )
    assert len(updated_persons) == 1
    assert updated_persons[0].id == 5
    assert updated_persons[0].birthdate == date(1986, 10, 26)


def test_database_sql_filled_db_set_birthday_for_all_persons(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we get 4 when updating all birthdates.
    """
    persons = filled_db.set_birthdate_for_persons(date(1986, 10, 26))
    assert len(persons) == 4


def test_database_sql_filled_db_delete_many_persons_valid_spec(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we can delete multiple persons based on a spec.
    """
    deleted = filled_db.delete_persons(
        specification=NameContainsPersonSpec('Example Person')
    )
    assert deleted == 5

    persons = filled_db.get_persons(
        specification=NameContainsPersonSpec('Example Person')
    )
    assert len(persons) == 0


def test_database_sql_filled_db_delete_many_persons_no_spec(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we can delete all persons by not giving a spec.
    """
    deleted = filled_db.delete_persons()
    assert deleted == 5

    persons = filled_db.get_persons()
    assert len(persons) == 0


def test_database_sql_filled_db_delete_many_persons_invalid_spec(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we get a 0 result when deleting persons that don't exist.
    """
    deleted = filled_db.delete_persons(
        specification=NameContainsPersonSpec('not_existing')
    )
    assert deleted == 0

    persons = filled_db.get_persons()
    assert len(persons) == 5


def test_database_sql_filled_db_rename_person(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we can set the birthday for a person.
    """
    person = filled_db.rename_person('Example Person 1', 'Example Person 123')
    assert person is not None
    assert person.id == 1
    assert person.name == 'Example Person 123'

    updated_persons = filled_db.get_persons(
        specification=NameIsPersonSpec('Example Person 123')
    )
    assert len(updated_persons) == 1
    assert updated_persons[0].id == 1
    assert updated_persons[0].name == 'Example Person 123'


def test_database_sql_filled_db_rename_person_unknown_user(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we get an error when giving a unknown user.
    """
    with pytest.raises(PersonDoesNotExistError):
        _ = filled_db.rename_person('Example Person 999', 'test')


def test_database_sql_filled_db_rename_person_already_existing(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we get an error when giving a new name that is already present in
    the database.
    """
    with pytest.raises(PersonAlreadyExistsError):
        _ = filled_db.rename_person('Example Person 1', 'Example Person 2')


def test_database_sql_filled_db_add_label_to_persons(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we can add labels to persons.
    """
    persons = filled_db.add_label_to_persons(
        'test_label_5', specification=NameIsPersonSpec(name='Example Person 1')
    )
    assert len(persons) == 1
    persons = filled_db.get_persons(
        specification=NameIsPersonSpec(name='Example Person 1'),
        options=[RetrieveOption.LOAD_PERSON_LABELS],
    )
    assert len(persons[0].labels) == 1


def test_database_sql_filled_db_add_label_to_all_persons(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we can add labels to persons.
    """
    persons = filled_db.add_label_to_persons('test_label_5')
    assert len(persons) == 5


def test_database_sql_filled_db_add_label_to_persons_wrong_label(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we can add labels to persons.
    """
    with pytest.raises(LabelDoesNotExistError):
        filled_db.add_label_to_persons('test_label_999')


def test_database_sql_filled_db_add_label_to_all_persons_double(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we can add labels to persons.
    """
    persons = filled_db.add_label_to_persons(
        'test_label_2', specification=NameIsPersonSpec(name='Example Person 2')
    )
    assert len(persons) == 0


def test_database_sql_filled_db_add_label_to_persons_group(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we can add labels to persons.
    """
    filled_db.add_label_to_persons(
        'group3:label1', specification=NameIsPersonSpec(name='Example Person 2')
    )
    persons = filled_db.get_persons(
        specification=NameIsPersonSpec(name='Example Person 2'),
        options=[RetrieveOption.LOAD_PERSON_LABELS],
    )
    assert len(persons[0].labels) == 5


def test_database_sql_filled_db_add_label_to_persons_regroup(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we can add labels to persons.
    """
    filled_db.add_label_to_persons(
        'group1:label1', specification=NameIsPersonSpec(name='Example Person 2')
    )
    persons = filled_db.get_persons(
        specification=NameIsPersonSpec(name='Example Person 2'),
        options=[RetrieveOption.LOAD_PERSON_LABELS],
    )
    assert len(persons[0].labels) == 4


#####


def test_database_sql_filled_db_remove_label_from_persons(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we can remove labels from persons.
    """
    persons = filled_db.remove_label_from_persons('test_label_1')
    assert len(persons) == 1


def test_database_sql_filled_db_remove_label_from_persons_non_label(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we can remove labels from persons.
    """
    persons = filled_db.remove_label_from_persons('test_label_5')
    assert len(persons) == 0


def test_database_sql_filled_db_remove_label_from_persons_not_existing_label(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we can remove labels from persons.
    """
    with pytest.raises(LabelDoesNotExistError):
        filled_db.remove_label_from_persons('test_label_999')
