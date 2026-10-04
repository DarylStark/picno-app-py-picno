"""Module with the SQL implementation for the database."""

from collections.abc import Callable, Sequence
from datetime import date
from sqlite3 import Connection as SQLiteConnection
from sqlite3 import Cursor as SQLiteCursor
from typing import TypeVar, cast, override

from sqlalchemy import event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import InstrumentedAttribute, selectinload
from sqlalchemy.orm.interfaces import ORMOption
from sqlmodel import Session, SQLModel, and_, create_engine, delete, select

from .database import Database, LabelSpecification, RetrieveOption, _ClearField
from .exceptions import (
    LabelAlreadyExistsError,
    PersonAlreadyExistsError,
    ResourceAlreadyExistsError,
)
from .model import Label, Person, PersonLabelLink
from .specs import Specification
from .specs_persons import PersonSpecification

T = TypeVar('T')


class DatabaseSql(Database):
    """Database implementation for SQL databases."""

    def __init__(self, database_url: str) -> None:
        """Create the needed engine."""
        self._engine = create_engine(database_url, echo=False)

        @event.listens_for(self._engine, 'connect')
        def set_sqlite_pragma(
            dbapi_connection: SQLiteConnection,
            connection_record: object,
        ) -> None:
            cursor: SQLiteCursor = dbapi_connection.cursor()
            cursor.execute('PRAGMA case_sensitive_like = ON')
            cursor.execute('PRAGMA foreign_keys = ON')
            cursor.close()

        self._create_tables()

    def _create_tables(self) -> None:
        """Method to create the needed tables."""
        SQLModel.metadata.create_all(self._engine)

    def _create_resource(self, obj: T) -> T:
        """Method to create resources in the database."""
        with Session(self._engine) as session:
            session.add(obj)
            try:
                session.commit()
            except IntegrityError as exc:
                session.rollback()
                raise ResourceAlreadyExistsError from exc
            session.refresh(obj)
        return obj

    def _get_resource(
        self, model: type[T], id: int, options: list[ORMOption] | None = None
    ) -> T | None:
        """Generic method to retrieve a single item."""
        with Session(self._engine) as session:
            return session.get(model, id, options=options)

    def _get_resources(
        self,
        model: type[T],
        specification: Specification[T] | None = None,
        options: list[ORMOption] | None = None,
    ) -> list[T]:
        """Method to retrieve (a subset of) the resources in the database."""
        with Session(self._engine) as session:
            statement = select(model)
            if specification:
                statement = statement.where(specification.as_sql())

                for option in options or []:
                    statement.options(option)

            # TODO: Sorting
            return list(session.exec(statement).all())

    def _update_resource(
        self, model: type[T], id: int, updater: Callable[[T], T]
    ) -> T | None:
        """Method to update one resource."""
        with Session(self._engine) as session:
            resource = session.get(model, id)

            if resource is None:
                return None

            resource = updater(resource)

            try:
                session.commit()
            except IntegrityError as exc:
                session.rollback()
                raise ResourceAlreadyExistsError from exc

            session.refresh(resource)
            return resource

    def _delete_resource(self, model: type[T], id: int) -> bool:
        """Method to delete one resource."""
        with Session(self._engine) as session:
            resource = session.get(model, id)

            if resource is None:
                return False

            session.delete(resource)
            session.commit()
        return True

    def _delete_resources(
        self, model: type[T], specification: Specification[T] | None = None
    ) -> int:
        """Delete resources matching a specification.

        Returns:
            The number of resources deleted.
        """
        with Session(self._engine) as session:
            statement = delete(model)
            if specification:
                statement = statement.where(specification.as_sql())

            result = session.exec(statement)
            session.commit()
            return result.rowcount

    @override
    def close(self) -> None:
        """Close the database."""
        self._engine.dispose()

    @override
    def create_label(self, name: str) -> Label:
        """Create a new label."""
        new_resource = Label(name=name)
        try:
            return self._create_resource(new_resource)
        except ResourceAlreadyExistsError as exc:
            raise LabelAlreadyExistsError(
                f'A label named {name} already exists.'
            ) from exc

    @override
    def get_label(self, id: int) -> Label | None:
        """Method to retrieve one label."""
        return self._get_resource(Label, id)

    @override
    def get_labels(
        self, specification: LabelSpecification | None = None
    ) -> list[Label]:
        """Method to retrieve (a subset of) the labels in the database."""
        return self._get_resources(Label, specification)

    @override
    def update_label(self, id: int, new_name: str) -> Label | None:
        """Method to update one label."""

        def update_resource(res: Label) -> Label:
            res.name = new_name
            return res

        try:
            return self._update_resource(Label, id, update_resource)
        except ResourceAlreadyExistsError as exc:
            raise LabelAlreadyExistsError(
                f'A label named "{new_name}" already exists.'
            ) from exc

    @override
    def delete_label(self, id: int) -> bool:
        """Method to delete one label."""
        return self._delete_resource(Label, id)

    @override
    def delete_labels(
        self, specification: LabelSpecification | None = None
    ) -> int:
        """Delete labels matching a specification.

        Returns:
            The number of labels deleted.
        """
        return self._delete_resources(Label, specification)

    @override
    def create_person(self, name: str, birthdate: date | None = None) -> Person:
        """Create a new person."""
        new_resource = Person(name=name, birthdate=birthdate)
        try:
            return self._create_resource(new_resource)
        except ResourceAlreadyExistsError as exc:
            raise PersonAlreadyExistsError(
                f'A person named "{name}" already exists.'
            ) from exc

    @override
    def get_person(
        self, id: int, options: Sequence[RetrieveOption] | None = None
    ) -> Person | None:
        """Method to retrieve one Person."""
        options = options or []
        retrieve_options: list[ORMOption] = []
        if RetrieveOption.LOAD_LABELS in options:
            retrieve_options.append(
                selectinload(cast(InstrumentedAttribute, Person.labels))
            )

        return self._get_resource(Person, id, retrieve_options)

    @override
    def get_persons(
        self, specification: PersonSpecification | None = None
    ) -> list[Person]:
        """Method to retrieve (a subset of) the persons in the database."""
        return self._get_resources(Person, specification)

    @override
    def update_person(
        self,
        id: int,
        name: str | None = None,
        birthdate: date | None | _ClearField = None,
    ) -> Person | None:
        """Method to update one label."""

        def update_resource(res: Person) -> Person:
            if name is not None:
                res.name = name
            if isinstance(birthdate, _ClearField):
                res.birthdate = None
            elif birthdate is not None:
                res.birthdate = birthdate
            return res

        try:
            return self._update_resource(Person, id, update_resource)
        except ResourceAlreadyExistsError as exc:
            raise PersonAlreadyExistsError(
                f'A person named "{name}" already exists.'
            ) from exc

    @override
    def delete_person(self, id: int) -> bool:
        """Method to delete one person."""
        return self._delete_resource(Person, id)

    @override
    def delete_persons(
        self, specification: PersonSpecification | None = None
    ) -> int:
        """Delete persons matching a specification.

        Returns:
            The number of persons deleted.
        """
        return self._delete_resources(Person, specification)

    @override
    def add_label_to_person(self, person: str, label: str) -> None:
        """Method to add a label to a person (on names)."""
        with Session(self._engine) as session:
            person_obj = session.exec(
                select(Person).where(Person.name == person)
            ).one_or_none()

            label_obj = session.exec(
                select(Label).where(Label.name == label)
            ).one_or_none()

            if person_obj is None or label_obj is None:
                return  # TODO: raise an exception

            exists = session.exec(
                select(PersonLabelLink).where(
                    PersonLabelLink.person_id == person_obj.id,
                    PersonLabelLink.label_id == label_obj.id,
                )
            ).one_or_none()

            if exists is not None:
                return

            # TODO: check if the label group hasn't been added yet.

            session.add(
                PersonLabelLink(person_id=person_obj.id, label_id=label_obj.id)
            )
            session.commit()

    def remove_label_from_person(self, person: str, label: str) -> None:
        """Remove a label from a person."""
        with Session(self._engine) as session:
            person_obj = session.exec(
                select(Person).where(Person.name == person)
            ).one_or_none()

            label_obj = session.exec(
                select(Label).where(Label.name == label)
            ).one_or_none()

            if person_obj is None or label_obj is None:
                return

            statement = delete(PersonLabelLink).where(
                and_(
                    PersonLabelLink.person_id == person_obj.id,
                    PersonLabelLink.label_id == label_obj.id,
                )
            )

            session.exec(statement)
            session.commit()
