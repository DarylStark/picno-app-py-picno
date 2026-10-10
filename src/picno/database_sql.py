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
    ImageDoesNotExistError,
    ImageLabelLinkAlreadyExistsError,
    LabelAlreadyExistsError,
    LabelDoesNotExistError,
    PersonAlreadyExistsError,
    PersonDoesNotExistError,
    PersonLabelLinkAlreadyExistsError,
    ResourceAlreadyExistsError,
    ResourceNotFoundError,
)
from .model import (
    Image,
    ImageLabelLink,
    ImagePersonLink,
    Label,
    LabelLinkTable,
    Person,
    PersonLabelLink,
    PersonLinkTable,
    ResourceStatus,
    TableResource,
)
from .specs import AndSpecification, NotSpecification, Specification
from .specs_images import (
    HasLabelImageSpec,
    HasPersonImageSpec,
    ImageSpecification,
)
from .specs_persons import HasLabelPersonSpec, PersonSpecification

T = TypeVar('T')
LabelLinkTableType = TypeVar('LabelLinkTableType', bound=LabelLinkTable)
PersonLinkTableType = TypeVar('PersonLinkTableType', bound=PersonLinkTable)
TableResourceType = TypeVar('TableResourceType', bound=TableResource)
TableResourceTypeA = TypeVar('TableResourceTypeA', bound=TableResource)


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
        if RetrieveOption.LOAD_PERSON_LABELS in options:
            retrieve_options.append(
                selectinload(cast(InstrumentedAttribute, Person.labels))
            )
        if RetrieveOption.LOAD_IMAGE_LABELS in options:
            retrieve_options.append(
                selectinload(cast(InstrumentedAttribute, Image.labels))
            )
        if RetrieveOption.LOAD_IMAGE_PERSONS in options:
            retrieve_options.append(
                selectinload(cast(InstrumentedAttribute, Image.persons))
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

    def _get_image_from_title_with_session(
        self, session: Session, title: str
    ) -> Image:
        """Retrieves a image or throws an error."""
        image = self._get_resource_from_field_with_session(
            session, Image, 'title', title
        )
        if image is None:
            raise ImageDoesNotExistError(f'Image "{title}" does not exist')
        return image

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
                options=[RetrieveOption.LOAD_PERSON_LABELS],
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

            group_name = label_obj.group
            if group_name is not None:
                current_group = [
                    linked_label
                    for linked_label in person_obj.labels
                    if (linked_label.name or '').startswith(group_name)
                    and (linked_label.name or '') != label_obj.name
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
            try:
                session.commit()
            except IntegrityError as exc:
                raise PersonLabelLinkAlreadyExistsError(
                    f'Person "{person}" is already labelled with "{label}"'
                ) from exc

    @override
    def add_label_to_persons(
        self, label: str, specification: PersonSpecification | None = None
    ) -> list[Person]:
        """Method to add a label to a persons."""
        return self._add_label_to_resource(
            Person,
            PersonLabelLink,
            'person_id',
            label,
            specification=self._create_composite_specification(
                NotSpecification(HasLabelPersonSpec(label_name=label)),
                specification,
            ),
        )

    @override
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
    def remove_label_from_persons(
        self, label: str, specification: PersonSpecification | None = None
    ) -> list[Person]:
        """Method to remove a label from persons."""
        return self._remove_label_from_resource(
            Person,
            PersonLabelLink,
            'person_id',
            label,
            specification=self._create_composite_specification(
                HasLabelPersonSpec(label_name=label),
                specification,
            ),
        )

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
        self,
        specification: ImageSpecification | None = None,
        options: Sequence[RetrieveOption] | None = None,
    ) -> list[Image]:
        """Method to retrieve (a subset of) the labels in the database."""
        retrieve_options = self._convert_options_to_sql_options(options)
        return self._get_resources(
            Image, specification=specification, options=retrieve_options
        )

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

    @override
    def add_label_to_image(self, image: str, label: str) -> None:
        """Method to add a label to a image (on names)."""
        with Session(self._engine) as session:
            image_obj = self._get_resource_from_field(
                Image,
                'title',
                image,
                session=session,
                options=[RetrieveOption.LOAD_IMAGE_LABELS],
            )
            label_obj = self._get_resource_from_field(
                Label, 'name', label, session=session
            )

            if image_obj is None:
                raise ImageDoesNotExistError(f'Image "{image}" does not exist')

            if label_obj is None:
                raise LabelDoesNotExistError(f'Label "{label}" does not exist')

            group_name = label_obj.group
            if group_name is not None:
                current_group = [
                    linked_label
                    for linked_label in image_obj.labels
                    if (linked_label.name or '').startswith(group_name)
                    and (linked_label.name or '') != label_obj.name
                ]
                if current_group:
                    statement = delete(ImageLabelLink).where(
                        and_(
                            ImageLabelLink.image_id == image_obj.id,
                            ImageLabelLink.label_id == current_group[0].id,
                        )
                    )
                    session.exec(statement)

            self._create_resource(
                ImageLabelLink(image_id=image_obj.id, label_id=label_obj.id),
                session=session,
            )
            try:
                session.commit()
            except IntegrityError as exc:
                raise ImageLabelLinkAlreadyExistsError(
                    f'Image "{image}" is already labelled with "{label}"'
                ) from exc

    def _connect_one_resource_to_many_resources(
        self,
        resource_type: type[TableResourceTypeA],
        resource_search_field: str,
        resource_search_value: str,
        resource_field_in_link_table: str,
        resources_type: type[TableResourceType],
        resources_field_in_link_table: str,
        resource_spec: Specification[TableResourceType] | None,
        link_table: type[SQLModel],
        *,
        preprocessor: Callable[
            [TableResourceTypeA, TableResourceType, Session], None
        ]
        | None = None,
    ) -> list[TableResourceType]:
        """Method to connect two resources together."""
        return_list: list[TableResourceType] = []
        with Session(self._engine) as session:
            resource_a = self._get_resource_from_field(
                resource_type,
                resource_search_field,
                resource_search_value,
                session=session,
            )

            if resource_a is None:
                raise ResourceNotFoundError('Resource does not exist')

            resources = self._get_resources(
                resources_type, specification=resource_spec, session=session
            )

            for resource in resources:
                if preprocessor is not None:
                    preprocessor(resource_a, resource, session)

                link_table_args = {
                    resource_field_in_link_table: getattr(
                        resource_a, 'id', None
                    ),
                    resources_field_in_link_table: getattr(
                        resource, 'id', None
                    ),
                }

                link_resource = link_table(**link_table_args)
                self._create_resource(link_resource, session=session)
                return_list.append(resource)
                session.refresh(resource)

            session.commit()
        return return_list

    def _add_label_to_resource(
        self,
        resource_type: type[TableResourceType],
        link_table: type[LabelLinkTableType],
        resource_field: str,
        label: str,
        *,
        specification: Specification[TableResourceType] | None = None,
    ) -> list[TableResourceType]:
        def preprocess(
            label_obj: Label, resource: TableResourceType, session: Session
        ) -> None:
            """Prepreocess the image by removing labels already in the group.

            This is only needed when adding labels that are in a group, meaning
            they are written as 'group:label'. There can only be one label in a
            group per resource.
            """
            if not label_obj.group:
                return

            same_group_labels_ids = [
                group_label.id
                for group_label in getattr(resource, 'labels', [])
                if group_label.group == label_obj.group
            ]

            statement = delete(link_table).where(
                and_(
                    getattr(link_table, resource_field) == resource.id,
                    col(link_table.label_id).in_(same_group_labels_ids),
                )
            )
            session.exec(statement)

        try:
            return self._connect_one_resource_to_many_resources(
                Label,
                'name',
                label,
                'label_id',
                resource_type,
                resource_field,
                specification,
                link_table,
                preprocessor=preprocess,
            )
        except ResourceNotFoundError as exc:
            raise LabelDoesNotExistError(
                f'Label "{label}" does not exist'
            ) from exc

    def _add_person_to_resource(
        self,
        resource_type: type[TableResourceType],
        link_table: type[PersonLinkTableType],
        resource_field: str,
        person: str,
        *,
        specification: Specification[TableResourceType] | None = None,
    ) -> list[TableResourceType]:
        try:
            return self._connect_one_resource_to_many_resources(
                Person,
                'name',
                person,
                'person_id',
                resource_type,
                resource_field,
                specification,
                link_table,
            )
        except ResourceNotFoundError as exc:
            raise PersonDoesNotExistError(
                f'Person "{person}" does not exist'
            ) from exc

    def _create_composite_specification[T](
        self,
        specification: Specification[T],
        specifications: Specification[T] | None = None,
    ) -> Specification[T]:
        """Method to combine two specifications into one."""
        if specifications:
            return AndSpecification(spec_a=specification, spec_b=specifications)
        return specification

    @override
    def add_label_to_images(
        self, label: str, specification: ImageSpecification | None = None
    ) -> list[Image]:
        """Method to add a label to a images."""
        return self._add_label_to_resource(
            Image,
            ImageLabelLink,
            'image_id',
            label,
            specification=self._create_composite_specification(
                NotSpecification(HasLabelImageSpec(label_name=label)),
                specification,
            ),
        )

    @override
    def add_person_to_images(
        self, person: str, specification: ImageSpecification | None = None
    ) -> list[Image]:
        """Method to add a person to a images."""
        return self._add_person_to_resource(
            Image,
            ImagePersonLink,
            'image_id',
            person,
            specification=self._create_composite_specification(
                NotSpecification(HasPersonImageSpec(person_name=person)),
                specification,
            ),
        )

    @override
    def remove_label_from_image(self, image: str, label: str) -> None:
        """Remove a label from a image."""
        with Session(self._engine) as session:
            image_obj = self._get_resource_from_field(
                Image,
                'title',
                image,
                session=session,
                options=[RetrieveOption.LOAD_IMAGE_LABELS],
            )
            label_obj = self._get_resource_from_field(
                Label, 'name', label, session=session
            )

            if image_obj is None:
                raise ImageDoesNotExistError(f'Image "{image}" does not exist')

            if label_obj is None:
                raise LabelDoesNotExistError(f'Label "{label}" does not exist')

            statement = delete(ImageLabelLink).where(
                and_(
                    ImageLabelLink.image_id == image_obj.id,
                    ImageLabelLink.label_id == label_obj.id,
                )
            )

            session.exec(statement)
            session.commit()

    def _disconnect_one_resource_from_many_resources(
        self,
        resource_type: type[TableResourceTypeA],
        resource_search_field: str,
        resource_search_value: str,
        resource_field_in_link_table: str,
        resources_type: type[TableResourceType],
        resources_field_in_link_table: str,
        resource_spec: Specification[TableResourceType] | None,
        link_table: type[SQLModel],
    ) -> list[TableResourceType]:
        """Method to remove a resource from resources."""
        return_list: list[TableResourceType] = []
        with Session(self._engine) as session:
            resource_a = self._get_resource_from_field(
                resource_type,
                resource_search_field,
                resource_search_value,
                session=session,
            )

            if resource_a is None:
                raise ResourceNotFoundError('Resource does not exist')

            resources = self._get_resources(
                resources_type, specification=resource_spec, session=session
            )

            for resource in resources:
                statement = delete(link_table).where(
                    and_(
                        getattr(link_table, resource_field_in_link_table)
                        == resource_a.id,
                        getattr(link_table, resources_field_in_link_table)
                        == resource.id,
                    )
                )
                session.refresh(resource)
                session.exec(statement)
                return_list.append(resource)

            session.commit()

        return return_list

    def _remove_label_from_resource(
        self,
        resource_type: type[TableResourceType],
        link_table: type[LabelLinkTableType],
        resource_field: str,
        label: str,
        *,
        specification: Specification[TableResourceType] | None = None,
    ) -> list[TableResourceType]:
        """Method to remove a label from images."""
        try:
            return self._disconnect_one_resource_from_many_resources(
                Label,
                'name',
                label,
                'label_id',
                resource_type,
                resource_field,
                specification,
                link_table,
            )
        except ResourceNotFoundError as exc:
            raise LabelDoesNotExistError(
                f'Label "{label}" does not exist'
            ) from exc

    @override
    def remove_label_from_images(
        self, label: str, specification: ImageSpecification | None = None
    ) -> list[Image]:
        """Method to remove a label from images."""
        return self._remove_label_from_resource(
            Image,
            ImageLabelLink,
            'image_id',
            label,
            specification=self._create_composite_specification(
                HasLabelImageSpec(label_name=label),
                specification,
            ),
        )

    def _remove_person_from_resource(
        self,
        resource_type: type[TableResourceType],
        link_table: type[PersonLinkTableType],
        resource_field: str,
        person: str,
        *,
        specification: Specification[TableResourceType] | None = None,
    ) -> list[TableResourceType]:
        """Method to remove a person from resources."""
        try:
            return self._disconnect_one_resource_from_many_resources(
                Person,
                'name',
                person,
                'person_id',
                resource_type,
                resource_field,
                specification,
                link_table,
            )
        except ResourceNotFoundError as exc:
            raise PersonDoesNotExistError(
                f'Person "{person}" does not exist'
            ) from exc

    @override
    def remove_person_from_images(
        self, person: str, specification: ImageSpecification | None = None
    ) -> list[Image]:
        """Method to remove a person from images."""
        return self._remove_person_from_resource(
            Image,
            ImagePersonLink,
            'image_id',
            person,
            specification=self._create_composite_specification(
                HasPersonImageSpec(person_name=person),
                specification,
            ),
        )

    @override
    def set_favourite_for_images(
        self,
        favourite: bool,
        *,
        specification: ImageSpecification | None = None,
    ) -> list[Image]:
        """Set the favourite flag for specific images."""
        return_list: list[Image] = []
        with Session(self._engine) as session:
            images = self._get_resources(
                Image, specification=specification, session=session
            )

            for image in images:
                if image.favourite != favourite:
                    image.favourite = favourite
                    return_list.append(image)

            session.commit()

        return return_list

    @override
    def rename_image(self, image_title: str, new_title: str) -> Image:
        """Rename a image."""
        with Session(self._engine) as session:
            image = self._get_image_from_title_with_session(
                session, image_title
            )
            image.title = new_title
            session.add(image)
            try:
                session.commit()
                session.refresh(image)
            except IntegrityError as exc:
                raise ImageAlreadyExistsError(
                    f'A image named "{new_title}" already exists.'
                ) from exc
            return image
