"""Module with the SQL implementation for the database."""

from collections.abc import Callable, Sequence
from datetime import date
from pathlib import Path
from sqlite3 import Connection as SQLiteConnection
from sqlite3 import Cursor as SQLiteCursor
from typing import TypeVar, cast, override

from sqlalchemy import event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import InstrumentedAttribute, selectinload
from sqlalchemy.orm.interfaces import ORMOption
from sqlmodel import Session, SQLModel, and_, col, create_engine, delete, select
from sqlmodel.sql.expression import SelectOfScalar

from .database import Database, LabelSpecification, RetrieveOption
from .exceptions import (
    ImageAlreadyExistsError,
    LabelAlreadyExistsError,
    LabelDoesNotExistError,
    PersonAlreadyExistsError,
    PersonDoesNotExistError,
    ResourceAlreadyExistsError,
    ResourceNotFoundError,
)
from .model import Image, Label, Person, PersonLabelLink, ResourceStatus
from .specs import Specification
from .specs_images import ImageSpecification
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

    def _convert_options_to_sql_options(
        self, options: Sequence[RetrieveOption] | None = None
    ) -> list[ORMOption]:
        """Convert the RetrieveOptions to options SQLModel can understand."""
        if options is None:
            return []

        retrieve_options: list[ORMOption] = []
        if RetrieveOption.LOAD_LABELS in options:
            retrieve_options.append(
                selectinload(cast(InstrumentedAttribute, Person.labels))
            )
        return retrieve_options

    def _set_options_in_statement(
        self,
        statement: SelectOfScalar,
        *,
        options: Sequence[RetrieveOption] | None = None,
    ) -> SelectOfScalar:
        """Set the options in a statement."""
        sql_options = self._convert_options_to_sql_options(options=options)
        for option in sql_options:
            statement = statement.options(option)
        return statement

    def _create_resource(self, obj: T, *, session: Session | None = None) -> T:
        """Method to create resources in the database."""
        if session is None:
            with Session(self._engine) as created_session:
                obj = self._create_resource_with_session(created_session, obj)
                try:
                    created_session.commit()
                except IntegrityError as exc:
                    created_session.rollback()
                    raise ResourceAlreadyExistsError from exc
                created_session.refresh(obj)
                return obj
        return self._create_resource_with_session(session, obj)

    def _create_resource_with_session(self, session: Session, obj: T) -> T:
        """Method to create resources in the database."""
        session.add(obj)
        return obj

    def _get_resource(
        self,
        model: type[T],
        id: int,
        *,
        options: list[ORMOption] | None = None,
        session: Session | None = None,
    ) -> T | None:
        """Generic method to retrieve a single item."""
        if session is None:
            with Session(self._engine) as created_session:
                return self._get_resource_with_session(
                    created_session, model=model, id=id, options=options
                )
        return self._get_resource_with_session(
            session, model=model, id=id, options=options
        )

    def _get_resource_with_session(
        self,
        session: Session,
        model: type[T],
        id: int,
        *,
        options: list[ORMOption] | None = None,
    ) -> T | None:
        """Generic method to retrieve a single item."""
        return session.get(model, id, options=options)

    def _get_resource_from_field(
        self,
        model: type[T],
        field_name: str,
        field_value: str,
        *,
        session: Session | None = None,
        options: Sequence[RetrieveOption] | None = None,
    ) -> T | None:
        """Generic method to retrieve a single item on a arbitrary value."""
        if session is None:
            with Session(self._engine) as created_session:
                return self._get_resource_from_field_with_session(
                    created_session,
                    model,
                    field_name,
                    field_value,
                    options=options,
                )
        return self._get_resource_from_field_with_session(
            session,
            model,
            field_name,
            field_value,
            options=options,
        )

    def _get_resource_from_field_with_session(
        self,
        session: Session,
        model: type[T],
        field_name: str,
        field_value: str,
        *,
        options: Sequence[RetrieveOption] | None = None,
    ) -> T | None:
        """Generic method to retrieve a single item on a arbitrary value."""
        field_name_sql = getattr(model, field_name)
        query = col(field_name_sql) == field_value
        statement = select(model).where(query)
        statement = self._set_options_in_statement(statement, options=options)
        return session.exec(statement).one_or_none()

    def _get_resources(
        self,
        model: type[T],
        *,
        specification: Specification[T] | None = None,
        options: list[ORMOption] | None = None,
        session: Session | None = None,
    ) -> list[T]:
        """Method to retrieve (a subset of) the resources in the database."""
        if session is None:
            with Session(self._engine) as created_session:
                return self._get_resources_with_session(
                    created_session,
                    model,
                    specification=specification,
                    options=options,
                )
        return self._get_resources_with_session(
            session,
            model,
            specification=specification,
            options=options,
        )

    def _get_resources_with_session(
        self,
        session: Session,
        model: type[T],
        *,
        specification: Specification[T] | None = None,
        options: list[ORMOption] | None = None,
    ) -> list[T]:
        """Method to retrieve (a subset of) the resources in the database."""
        statement = select(model)
        if specification:
            statement = statement.where(specification.as_sql())

        for option in options or []:
            statement = statement.options(option)

        # TODO: Sorting
        return list(session.exec(statement).all())

    def _update_resource(
        self,
        model: type[T],
        id: int,
        obj_updater: Callable[[T], T],
        *,
        session: Session | None = None,
    ) -> T | None:
        """Method to update one resource."""
        if session is None:
            with Session(self._engine) as created_session:
                resource = self._update_resource_with_session(
                    created_session, model, id, obj_updater
                )
                if resource is None:
                    return None
                try:
                    created_session.commit()
                    created_session.refresh(resource)
                except IntegrityError as exc:
                    created_session.rollback()
                    raise ResourceAlreadyExistsError from exc
                return resource
        return self._update_resource_with_session(
            session, model, id, obj_updater
        )

    def _update_resource_with_session(
        self,
        session: Session,
        model: type[T],
        id: int,
        obj_updater: Callable[[T], T],
    ) -> T | None:
        """Method to update one resource."""
        resource = session.get(model, id)

        if resource is None:
            return None

        resource = obj_updater(resource)
        return resource

    def _delete_resource(
        self, model: type[T], id: int, *, session: Session | None = None
    ) -> bool:
        """Method to delete one resource."""
        if session is None:
            with Session(self._engine) as created_session:
                if self._delete_resource_with_session(
                    created_session, model, id
                ):
                    created_session.commit()
                    return True
                return False
        return self._delete_resource_with_session(session, model, id)

    def _delete_resource_with_session(
        self, session: Session, model: type[T], id: int
    ) -> bool:
        """Method to delete one resource."""
        resource = session.get(model, id)

        if resource is None:
            return False

        session.delete(resource)
        return True

    def _delete_resource_from_field(
        self,
        model: type[T],
        field_name: str,
        field_value: str,
        *,
        session: Session | None = None,
    ) -> None:
        """Generic method to delete a single item on a arbitrary value."""
        if session is None:
            with Session(self._engine) as created_session:
                self._delete_resource_from_field_with_session(
                    created_session, model, field_name, field_value
                )
                created_session.commit()
                return
        self._get_resource_from_field_with_session(
            session, model, field_name, field_value
        )

    def _delete_resource_from_field_with_session(
        self,
        session: Session,
        model: type[T],
        field_name: str,
        field_value: str,
    ) -> None:
        """Generic method to delete a single item on a arbitrary value."""
        obj = self._get_resource_from_field_with_session(
            session, model, field_name, field_value
        )
        if obj is not None:
            session.delete(obj)
            return
        raise ResourceNotFoundError('Resource is not found')

    def _delete_resources(
        self,
        model: type[T],
        *,
        specification: Specification[T] | None = None,
        session: Session | None = None,
    ) -> int:
        """Delete resources matching a specification.

        Returns:
            The number of resources deleted.
        """
        if session is None:
            with Session(self._engine) as created_session:
                count = self._delete_resources_with_session(
                    created_session, model, specification=specification
                )
                if count:
                    created_session.commit()
                return count
        return self._delete_resources_with_session(
            session, model, specification=specification
        )

    def _delete_resources_with_session(
        self,
        session: Session,
        model: type[T],
        *,
        specification: Specification[T] | None = None,
    ) -> int:
        """Delete resources matching a specification.

        Returns:
            The number of resources deleted.
        """
        statement = delete(model)
        if specification:
            statement = statement.where(specification.as_sql())

        result = session.exec(statement)
        return result.rowcount

    def _person_is_labelled(
        self,
        person_id: int | None,
        label_id: int | None,
        *,
        session: Session | None = None,
    ) -> bool:
        """Check if a person is already labelled with a specific label."""
        if person_id is None or label_id is None:
            return False
        if session is None:
            with Session(self._engine) as created_session:
                return self._person_is_labelled_with_session(
                    created_session, person_id, label_id
                )
        return self._person_is_labelled_with_session(
            session, person_id, label_id
        )

    def _person_is_labelled_with_session(
        self, session: Session, person_id: int, label_id: int
    ) -> bool:
        """Check if a person is already labelled with a specific label."""
        exists = session.exec(
            select(PersonLabelLink).where(
                PersonLabelLink.person_id == person_id,
                PersonLabelLink.label_id == label_id,
            )
        ).one_or_none()
        return exists is not None

    def _get_person_from_name_with_session(
        self, session: Session, name: str
    ) -> Person:
        """Retrieves a person or throws an error."""
        person = self._get_resource_from_field_with_session(
            session, Person, 'name', name
        )
        if person is None:
            raise PersonDoesNotExistError(f'Person "{name}" does not exist')
        return person

    def _get_label_from_name_with_session(
        self, session: Session, name: str
    ) -> Label:
        """Retrieves a label or throws an error."""
        label = self._get_resource_from_field_with_session(
            session, Label, 'name', name
        )
        if label is None:
            raise LabelDoesNotExistError(f'Label "{name}" does not exist')
        return label

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
    def get_label_by_name(
        self, name: str, options: Sequence[RetrieveOption] | None = None
    ) -> Label | None:
        """Method to retrieve one label by name."""
        return self._get_resource_from_field(
            Label, 'name', name, options=options
        )

    @override
    def get_labels(
        self, specification: LabelSpecification | None = None
    ) -> list[Label]:
        """Method to retrieve (a subset of) the labels in the database."""
        return self._get_resources(Label, specification=specification)

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
    def rename_label(self, label_name: str, new_name: str) -> Label:
        """Rename a label."""
        with Session(self._engine) as session:
            label = self._get_label_from_name_with_session(session, label_name)
            label.name = new_name
            session.add(label)
            try:
                session.commit()
                session.refresh(label)
            except IntegrityError as exc:
                raise LabelAlreadyExistsError(
                    f'A label named "{new_name}" already exists.'
                ) from exc
            return label

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
        return self._delete_resources(Label, specification=specification)

    @override
    def delete_label_by_name(self, name: str) -> None:
        """Method to delete a label by name."""
        try:
            self._delete_resource_from_field(Label, 'name', name)
        except ResourceNotFoundError as exc:
            raise LabelDoesNotExistError(
                f'Label "{name}" does not exist'
            ) from exc

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
        retrieve_options = self._convert_options_to_sql_options(options)
        return self._get_resource(Person, id, options=retrieve_options)

    @override
    def get_person_by_name(
        self, name: str, options: Sequence[RetrieveOption] | None = None
    ) -> Person | None:
        """Method to retrieve one person by name."""
        return self._get_resource_from_field(
            Person, 'name', name, options=options
        )

    @override
    def get_persons(
        self,
        specification: PersonSpecification | None = None,
        options: Sequence[RetrieveOption] | None = None,
    ) -> list[Person]:
        """Method to retrieve (a subset of) the persons in the database."""
        retrieve_options = self._convert_options_to_sql_options(options)
        return self._get_resources(
            Person, specification=specification, options=retrieve_options
        )

    @override
    def update_person(
        self,
        id: int,
        name: str | None = None,
        birthdate: date | None = None,
    ) -> Person | None:
        """Method to update one label."""

        def update_resource(res: Person) -> Person:
            if name is not None:
                res.name = name
            if birthdate is not None:
                res.birthdate = birthdate
            return res

        try:
            return self._update_resource(Person, id, update_resource)
        except ResourceAlreadyExistsError as exc:
            raise PersonAlreadyExistsError(
                f'A person named "{name}" already exists.'
            ) from exc

    @override
    def rename_person(self, person_name: str, new_name: str) -> Person:
        """Rename a person."""
        with Session(self._engine) as session:
            person = self._get_person_from_name_with_session(
                session, person_name
            )
            person.name = new_name
            session.add(person)
            try:
                session.commit()
                session.refresh(person)
            except IntegrityError as exc:
                raise PersonAlreadyExistsError(
                    f'A person named "{new_name}" already exists.'
                ) from exc
            return person

    @override
    def set_birthdate_for_person(
        self, person_name: str, new_birthdate: date | None = None
    ) -> Person:
        """Set the birthday for a person."""
        with Session(self._engine) as session:
            person = self._get_person_from_name_with_session(
                session, person_name
            )
            person.birthdate = new_birthdate
            session.add(person)
            session.commit()
            session.refresh(person)
            return person

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
        return self._delete_resources(Person, specification=specification)

    @override
    def delete_person_by_name(self, name: str) -> None:
        """Method to delete a person by name."""
        try:
            self._delete_resource_from_field(Person, 'name', name)
        except ResourceNotFoundError as exc:
            raise PersonDoesNotExistError(
                f'Person "{name}" does not exist'
            ) from exc

    @override
    def add_label_to_person(self, person: str, label: str) -> None:
        """Method to add a label to a person (on names)."""
        with Session(self._engine) as session:
            person_obj = self._get_resource_from_field(
                Person,
                'name',
                person,
                session=session,
                options=[RetrieveOption.LOAD_LABELS],
            )
            label_obj = self._get_resource_from_field(
                Label, 'name', label, session=session
            )

            if person_obj is None:
                raise PersonDoesNotExistError(
                    f'Person "{person}" does not exist'
                )

            if label_obj is None:
                raise LabelDoesNotExistError(f'Label "{label}" does not exist')

            if self._person_is_labelled(
                person_obj.id, label_obj.id, session=session
            ):
                return None

            group_name = label_obj.group
            if group_name is not None:
                current_group = [
                    linked_label
                    for linked_label in person_obj.labels
                    if (linked_label.name or '').startswith(group_name)
                ]
                if current_group:
                    statement = delete(PersonLabelLink).where(
                        and_(
                            PersonLabelLink.person_id == person_obj.id,
                            PersonLabelLink.label_id == current_group[0].id,
                        )
                    )
                    session.exec(statement)

            self._create_resource(
                PersonLabelLink(person_id=person_obj.id, label_id=label_obj.id),
                session=session,
            )
            session.commit()

    def remove_label_from_person(self, person: str, label: str) -> None:
        """Remove a label from a person."""
        with Session(self._engine) as session:
            person_obj = self._get_resource_from_field(
                Person, 'name', person, session=session
            )
            label_obj = self._get_resource_from_field(
                Label, 'name', label, session=session
            )

            if person_obj is None:
                raise PersonDoesNotExistError(
                    f'Person "{person}" does not exist'
                )

            if label_obj is None:
                raise LabelDoesNotExistError(f'Label "{label}" does not exist')

            statement = delete(PersonLabelLink).where(
                and_(
                    PersonLabelLink.person_id == person_obj.id,
                    PersonLabelLink.label_id == label_obj.id,
                )
            )

            session.exec(statement)
            session.commit()

    @override
    def create_image_from_object(self, image: Image) -> Image:
        """Create and image from a Image object."""
        try:
            return self._create_resource(image)
        except IntegrityError as exc:
            raise ImageAlreadyExistsError(
                'Image with this name already exists'
            ) from exc

    @override
    def create_images_from_objects(
        self, images: Sequence[Image]
    ) -> list[Image]:
        """Create and image from a Image object."""
        return_list: list[Image] = []
        with Session(self._engine) as session:
            for image in images:
                return_list.append(
                    self._create_resource_with_session(session, image)
                )

            try:
                session.commit()
            except IntegrityError as exc:
                session.rollback()
                raise ImageAlreadyExistsError(
                    'Image with this name already exists'
                ) from exc
        return return_list

    @override
    def get_image_on_path(self, path: Path) -> Image | None:
        """Get a image from it's relative path."""
        return self._get_resource_from_field(
            Image, field_name='physical_path', field_value=str(path)
        )

    @override
    def get_images(
        self, specification: ImageSpecification | None = None
    ) -> list[Image]:
        """Method to retrieve (a subset of) the labels in the database."""
        return self._get_resources(Image, specification=specification)

    @override
    def set_image_status(
        self,
        status: ResourceStatus,
        specification: ImageSpecification | None = None,
    ) -> list[Image]:
        """Method to set the status of specific images."""
        return_list: list[Image] = []
        with Session(self._engine) as session:
            resources = self._get_resources_with_session(
                session, Image, specification=specification
            )
            for resource in resources:
                if resource.status != status:
                    resource.status = status
                    return_list.append(resource)
            session.commit()
        return return_list
