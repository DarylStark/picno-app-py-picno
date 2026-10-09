"""Tests for the DatabaseSql class."""

from datetime import date

import pytest
from sqlalchemy.orm.exc import DetachedInstanceError

from picno.database import RetrieveOption
from picno.database_sql import DatabaseSql
from picno.exceptions import (
    LabelDoesNotExistError,
    PersonAlreadyExistsError,
    PersonDoesNotExistError,
    PersonLabelLinkAlreadyExistsError,
)
from picno.specs_persons import NameContainsPersonSpec, NameIsPersonSpec


def test_database_sql_empty_db_empty_person_list(empty_db: DatabaseSql) -> None:
    """Test with a empty database.

    Check if we get a empty list of person.
    """
    persons = empty_db.get_persons()

    assert persons == []


def test_database_sql_empty_db_empty_create_person(
    empty_db: DatabaseSql,
) -> None:
    """Test with a empty database.

    Check if we can add persons and get the created person.
    """
    person = empty_db.create_person('Example Person')

    assert person.id is not None
    assert person.name == 'Example Person'


def test_database_sql_empty_db_empty_create_person_with_birthdate(
    empty_db: DatabaseSql,
) -> None:
    """Test with a empty database.

    Check if we can add persons and get the created person.
    """
    person = empty_db.create_person('Example Person', date(1986, 10, 26))

    assert person.id is not None
    assert person.name == 'Example Person'
    assert person.birthdate == date(1986, 10, 26)


def test_database_sql_filled_db_add_person_that_already_exists(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we get an error when creating a person that already exists.
    """
    with pytest.raises(PersonAlreadyExistsError):
        filled_db.create_person('Example Person 1')


def test_database_sql_filled_db_get_one_person_valid_id(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we can retrieve one person on ID.
    """
    person = filled_db.get_person(id=1)
    assert person is not None
    assert person.id == 1

    # Labels are not loaded, so we expect an error on that one.
    with pytest.raises(DetachedInstanceError):
        assert person.labels == []


def test_database_sql_filled_db_get_one_person_valid_id_with_labels(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we can retrieve one person on ID.
    """
    person = filled_db.get_person(
        id=1, options=(RetrieveOption.LOAD_PERSON_LABELS,)
    )
    assert person is not None
    assert person.id == 1
    assert person.labels == []


def test_database_sql_filled_db_get_one_person_invalid_id(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we can retrieve one person on ID.
    """
    person = filled_db.get_person(id=999)
    assert person is None


def test_database_sql_filled_db_get_one_person_by_name_valid_name(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we can retrieve one person on name.
    """
    person = filled_db.get_person_by_name(name='Example Person 1')
    assert person is not None
    assert person.id == 1

    # Labels are not loaded, so we expect an error on that one.
    with pytest.raises(DetachedInstanceError):
        assert person.labels == []


def test_database_sql_filled_db_get_one_person_by_name_valid_name_with_labels(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we can retrieve one person on name.
    """
    person = filled_db.get_person_by_name(
        name='Example Person 1', options=(RetrieveOption.LOAD_PERSON_LABELS,)
    )
    assert person is not None
    assert person.id == 1
    assert person.labels == []


def test_database_sql_filled_db_get_one_person_by_name_invalid_name(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we can retrieve one person on name.
    """
    person = filled_db.get_person_by_name(name='non_existing_name')
    assert person is None


def test_database_sql_filled_db_get_all_persons(filled_db: DatabaseSql) -> None:
    """Test with a filled database.

    Check if we get all required persons.
    """
    persons = filled_db.get_persons()
    assert len(persons) == 5


def test_database_sql_filled_db_update_one_person_already_exists(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we get a exception when updating a person to a name that already
    exists.
    """
    with pytest.raises(PersonAlreadyExistsError):
        filled_db.update_person(1, name='Example Person 2')


def test_database_sql_filled_db_update_one_person_set_birthdate(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we can update the birthdate of a person.
    """
    person = filled_db.update_person(1, birthdate=date(1986, 10, 26))
    assert person is not None
    assert person.id == 1
    assert person.name == 'Example Person 1'
    assert person.birthdate == date(1986, 10, 26)

    updated_person = filled_db.get_person(id=1)
    assert updated_person is not None
    assert updated_person.id == 1
    assert updated_person.name == 'Example Person 1'
    assert updated_person.birthdate == date(1986, 10, 26)


def test_database_sql_filled_db_update_one_person_valid_id(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we can update a person based on id.
    """
    person = filled_db.update_person(1, name='Updated Name')
    assert person is not None
    assert person.id == 1
    assert person.name == 'Updated Name'

    updated_person = filled_db.get_person(id=1)
    assert updated_person is not None
    assert updated_person.id == 1
    assert updated_person.name == 'Updated Name'


def test_database_sql_filled_db_update_one_person_invalid_id(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we get a None value when upating a Person that doesn't exist.
    """
    person = filled_db.update_person(999, name='updated_label')
    assert person is None


def test_database_sql_filled_db_set_birthday_for_person(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we can set the birthday for a person.
    """
    person = filled_db.set_birthdate_for_person(
        'Example Person 1', date(year=1986, month=10, day=26)
    )
    assert person is not None
    assert person.id == 1
    assert person.birthdate == date(year=1986, month=10, day=26)

    updated_person = filled_db.get_person(id=1)
    assert updated_person is not None
    assert updated_person.id == 1
    assert updated_person.birthdate == date(year=1986, month=10, day=26)


def test_database_sql_filled_db_set_birthday_for_person_clear(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we can clear the birthday for a person.
    """
    person = filled_db.set_birthdate_for_person('Example Person 5', None)
    assert person is not None
    assert person.id == 5
    assert person.birthdate is None

    updated_person = filled_db.get_person(id=5)
    assert updated_person is not None
    assert updated_person.id == 5
    assert updated_person.birthdate is None


def test_database_sql_filled_db_set_birthday_for_person_unknown_user(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we get an error when giving a unknown user.
    """
    with pytest.raises(PersonDoesNotExistError):
        _ = filled_db.set_birthdate_for_person('Example Person 999', None)


def test_database_sql_filled_db_delete_one_person_valid_id(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we can delete a person with a valid id.
    """
    deleted = filled_db.delete_person(1)
    assert deleted

    deleted_person = filled_db.get_person(id=1)
    assert deleted_person is None


def test_database_sql_filled_db_delete_one_person_invalid_id(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we get a False value when deleting a Person that doesn't exist.
    """
    deleted = filled_db.delete_person(999)
    assert not deleted


def test_database_sql_filled_db_delete_many_persons_valid_spec(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we can delete multiple persons based on a spec.
    """
    deleted = filled_db.delete_persons(NameContainsPersonSpec('Example Person'))
    assert deleted == 5

    persons = filled_db.get_persons(NameContainsPersonSpec('Example Person'))
    assert len(persons) == 0


def test_database_sql_filled_db_delete_many_persons_no_spec(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we can delete all persons by not giving a spec.
    """
    deleted = filled_db.delete_labels()
    assert deleted == 20

    persons = filled_db.get_labels()
    assert len(persons) == 0


def test_database_sql_filled_db_delete_many_persons_invalid_spec(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Check if we get a 0 result when deleting persons that don't exist.
    """
    deleted = filled_db.delete_persons(NameContainsPersonSpec('not_existing'))
    assert deleted == 0

    persons = filled_db.get_persons()
    assert len(persons) == 5


def test_database_sql_filled_db_delete_person_by_name(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Test if we can remove persons by name.
    """
    filled_db.delete_person_by_name('Example Person 1')
    persons = filled_db.get_persons()
    assert len(persons) == 4


def test_database_sql_filled_db_delete_person_by_name_invalid_ame(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Test if we can get an error when removing a person that doesn't exist.
    """
    with pytest.raises(PersonDoesNotExistError):
        filled_db.delete_person_by_name('Example Person 999')


def test_database_sql_filled_db_add_label_to_person(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Test if we can add labels to persons.
    """
    filled_db.add_label_to_person('Example Person 1', 'test_label_1')
    person = filled_db.get_person(
        1,
        (RetrieveOption.LOAD_PERSON_LABELS,),
    )
    assert person is not None
    assert len(person.labels) == 1


def test_database_sql_filled_db_add_label_to_person_group(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Test if we can add label groups to persons.
    """
    filled_db.add_label_to_person('Example Person 1', 'group1:label1')
    person = filled_db.get_person(
        1,
        (RetrieveOption.LOAD_PERSON_LABELS,),
    )
    assert person is not None
    assert len(person.labels) == 1
    assert person.labels[0].name == 'group1:label1'


def test_database_sql_filled_db_add_label_to_person_regroup(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Test if we can change the specific value in a group for a user.
    """
    filled_db.add_label_to_person('Example Person 1', 'group1:label1')
    filled_db.add_label_to_person('Example Person 1', 'group1:label2')
    person = filled_db.get_person(
        1,
        (RetrieveOption.LOAD_PERSON_LABELS,),
    )
    assert person is not None
    assert len(person.labels) == 1
    assert person.labels[0].name == 'group1:label2'


def test_database_sql_filled_db_add_label_to_person_invalid_person(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Test if we can add labels to persons.
    """
    with pytest.raises(PersonDoesNotExistError):
        filled_db.add_label_to_person('Example Person 999', 'test_label_1')


def test_database_sql_filled_db_add_label_to_person_invalid_label(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Test if we can add labels to persons.
    """
    with pytest.raises(LabelDoesNotExistError):
        filled_db.add_label_to_person('Example Person 1', 'test_label_999')


def test_database_sql_filled_db_add_double_label_to_person(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Test if we cannot add the same label twice to a person.
    """
    filled_db.add_label_to_person('Example Person 1', 'test_label_1')
    with pytest.raises(PersonLabelLinkAlreadyExistsError):
        filled_db.add_label_to_person('Example Person 1', 'test_label_1')


def test_database_sql_filled_db_add_multiple_labels_to_person(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Test if we cannot add multiple labels to a person.
    """
    filled_db.add_label_to_person('Example Person 1', 'test_label_1')
    filled_db.add_label_to_person('Example Person 1', 'test_label_2')
    person = filled_db.get_person(
        1,
        (RetrieveOption.LOAD_PERSON_LABELS,),
    )
    assert person is not None
    assert len(person.labels) == 2


def test_database_sql_filled_db_remove_label_from_person(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Test if we cannot remove labels from a person.
    """
    filled_db.remove_label_from_person('Example Person 2', 'test_label_1')
    filled_db.remove_label_from_person('Example Person 2', 'group1:label2')
    person = filled_db.get_person(
        2,
        (RetrieveOption.LOAD_PERSON_LABELS,),
    )
    assert person is not None
    assert len(person.labels) == 2


def test_database_sql_filled_db_remove_label_from_person_invalid_person(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Test if we can add labels to persons.
    """
    with pytest.raises(PersonDoesNotExistError):
        filled_db.remove_label_from_person('Example Person 999', 'test_label_1')


def test_database_sql_filled_db_remove_label_from_person_invalid_label(
    filled_db: DatabaseSql,
) -> None:
    """Test with a filled database.

    Test if we can add labels to persons.
    """
    with pytest.raises(LabelDoesNotExistError):
        filled_db.remove_label_from_person('Example Person 1', 'test_label_999')


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

    updated_person = filled_db.get_person(id=1)
    assert updated_person is not None
    assert updated_person.id == 1
    assert updated_person.name == 'Example Person 123'


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
        'test_label_2', NameIsPersonSpec(name='Example Person 2')
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
