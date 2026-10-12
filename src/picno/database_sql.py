"""Module with the SQL implementation for the database."""

from collections.abc import Callable, Sequence
from datetime import date
from sqlite3 import Connection as SQLiteConnection
from sqlite3 import Cursor as SQLiteCursor
from typing import Any, TypeVar, cast, override

from sqlalchemy import Delete, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import InstrumentedAttribute, selectinload
from sqlalchemy.orm.interfaces import ORMOption
from sqlmodel import Session, SQLModel, and_, col, create_engine, delete, select
from sqlmodel.sql.expression import SelectOfScalar

from picno.specs_labels import NameIsLabelSpec

from .database import (
    Database,
    LabelSpecification,
    RetrieveOption,
    SelectCallbackImage,
    SelectCallbackLabel,
    SelectCallbackPerson,
)
from .exceptions import (
    CallbackAbortedError,
    ImageAlreadyExistsError,
    ImageDoesNotExistError,
    LabelAlreadyExistsError,
    LabelDoesNotExistError,
    PersonAlreadyExistsError,
    PersonDoesNotExistError,
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
    NameIsImageSpec,
)
from .specs_persons import (
    HasLabelPersonSpec,
    NameIsPersonSpec,
    PersonSpecification,
)

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
        self, options: Sequence[RetrieveOption] | None
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

    def _build_composite_specification[T](
        self,
        specification: Specification[T],
        specifications: Specification[T] | None,
    ) -> Specification[T]:
        """Method to combine two specifications into one."""
        if specifications:
            return AndSpecification(spec_a=specification, spec_b=specifications)
        return specification

    def _build_select_statement(
        self, model: type[T], *, specification: Specification[T] | None = None
    ) -> SelectOfScalar[T]:
        statement = select(model)
        if specification:
            statement = statement.where(specification.as_sql())
        return statement

    def _build_delete_statement(
        self, model: type[T], *, specification: Specification[T] | None = None
    ) -> Delete:
        statement = delete(model)
        if specification:
            statement = statement.where(specification.as_sql())
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

    def _create_resources(
        self, objs: list[T], *, session: Session | None = None
    ) -> list[T]:
        """Method to create many resourcess in the database."""
        if session is None:
            with Session(self._engine) as created_session:
                objs = self._create_resources_with_session(
                    created_session, objs
                )
                try:
                    created_session.commit()
                except IntegrityError as exc:
                    created_session.rollback()
                    raise ResourceAlreadyExistsError from exc
                for obj in objs:
                    created_session.refresh(obj)
                return objs
        return self._create_resources_with_session(session, objs)

    def _create_resources_with_session(
        self, session: Session, objs: list[T]
    ) -> list[T]:
        """Method to create many resourcess in the database."""
        for obj in objs:
            session.add(obj)
        return objs

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
        options: Sequence[RetrieveOption] | None = None,
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
        options: Sequence[RetrieveOption] | None = None,
    ) -> list[T]:
        """Method to retrieve (a subset of) the resources in the database."""
        statement = select(model)
        if specification:
            statement = statement.where(specification.as_sql())
        statement = self._set_options_in_statement(statement, options=options)

        # TODO: Sorting
        return list(session.exec(statement).all())

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
        select_callback: Callable[[Sequence[TableResourceType]], bool]
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

            if select_callback and not select_callback(resources):
                raise CallbackAbortedError

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
        *,
        select_callback: Callable[[Sequence[TableResourceType]], bool]
        | None = None,
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

            if select_callback and not select_callback(resources):
                raise CallbackAbortedError

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

    def _update_resources(
        self,
        model: type[T],
        new_data: dict[str, Any],
        *,
        specification: Specification[T] | None = None,
        select_callback: Callable[[Sequence[T]], bool] | None = None,
        callback_before_updating: bool = False,
    ) -> list[T]:
        updated_resources: list[T] = []
        with Session(self._engine) as session:
            resources = self._get_resources_with_session(
                session, model, specification=specification
            )

            if (
                select_callback
                and callback_before_updating
                and not select_callback(resources)
            ):
                session.rollback()
                raise CallbackAbortedError

            for resource in resources:
                for field, value in new_data.items():
                    setattr(resource, field, value)
                    if session.is_modified(resource):
                        updated_resources.append(resource)

            if (
                select_callback
                and not callback_before_updating
                and not select_callback(updated_resources)
            ):
                session.rollback()
                raise CallbackAbortedError

            session.commit()

            for resource in updated_resources:
                session.refresh(resource)
        return updated_resources

    def _add_label_to_resource(
        self,
        resource_type: type[TableResourceType],
        link_table: type[LabelLinkTableType],
        resource_field: str,
        label: str,
        *,
        specification: Specification[TableResourceType] | None = None,
        select_callback: Callable[[Sequence[TableResourceType]], bool]
        | None = None,
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
                select_callback=select_callback,
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
        select_callback: Callable[[Sequence[TableResourceType]], bool]
        | None = None,
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
                select_callback=select_callback,
            )
        except ResourceNotFoundError as exc:
            raise PersonDoesNotExistError(
                f'Person "{person}" does not exist'
            ) from exc

    def _remove_label_from_resource(
        self,
        resource_type: type[TableResourceType],
        link_table: type[LabelLinkTableType],
        resource_field: str,
        label: str,
        *,
        specification: Specification[TableResourceType] | None = None,
        select_callback: Callable[[Sequence[TableResourceType]], bool]
        | None = None,
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
                select_callback=select_callback,
            )
        except ResourceNotFoundError as exc:
            raise LabelDoesNotExistError(
                f'Label "{label}" does not exist'
            ) from exc

    def _remove_person_from_resource(
        self,
        resource_type: type[TableResourceType],
        link_table: type[PersonLinkTableType],
        resource_field: str,
        person: str,
        *,
        specification: Specification[TableResourceType] | None = None,
        select_callback: Callable[[Sequence[TableResourceType]], bool]
        | None = None,
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
                select_callback=select_callback,
            )
        except ResourceNotFoundError as exc:
            raise PersonDoesNotExistError(
                f'Person "{person}" does not exist'
            ) from exc

    def _delete_resources(
        self,
        model: type[T],
        *,
        specification: Specification[T] | None = None,
        select_callback: Callable[[Sequence[T]], bool] | None = None,
        session: Session | None = None,
    ) -> int:
        """Delete resources matching a specification.

        Returns:
            The number of resources deleted.
        """
        if session is None:
            with Session(self._engine) as created_session:
                count = self._delete_resources_with_session(
                    created_session,
                    model,
                    specification=specification,
                    select_callback=select_callback,
                )
                if count:
                    created_session.commit()
                return count
        return self._delete_resources_with_session(
            session,
            model,
            specification=specification,
            select_callback=select_callback,
        )

    def _delete_resources_with_session(
        self,
        session: Session,
        model: type[T],
        *,
        specification: Specification[T] | None = None,
        select_callback: Callable[[Sequence[T]], bool] | None = None,
    ) -> int:
        """Delete resources matching a specification.

        Returns:
            The number of resources deleted.
        """
        if select_callback:
            statement_select = self._build_select_statement(
                model, specification=specification
            )
            items = session.exec(statement_select).all()
            if not select_callback(items):
                raise CallbackAbortedError

        statement_delete = self._build_delete_statement(
            model, specification=specification
        )
        result = session.exec(statement_delete)
        return result.rowcount

    @override
    def close(self) -> None:
        """Close the database."""
        self._engine.dispose()

    @override
    def create_labels(self, names: list[str]) -> list[Label]:
        """Method to add multiple labels to the database."""
        objs: list[Label] = [Label(name=name) for name in names]
        try:
            return self._create_resources(objs)
        except ResourceAlreadyExistsError as exc:
            raise LabelAlreadyExistsError('Douplicate labels added') from exc

    @override
    def get_labels(
        self, specification: LabelSpecification | None = None
    ) -> list[Label]:
        """Method to retrieve (a subset of) the labels in the database."""
        return self._get_resources(Label, specification=specification)

    @override
    def rename_label(
        self,
        label_name: str,
        new_name: str,
        select_callback: SelectCallbackLabel | None = None,
    ) -> Label:
        """Rename a label."""
        try:
            rv = self._update_resources(
                Label,
                {'name': new_name},
                specification=NameIsLabelSpec(label_name, False),
                select_callback=select_callback,
                callback_before_updating=True,
            )
        except IntegrityError as exc:
            raise LabelAlreadyExistsError(
                f'A label named "{new_name}" already exists.'
            ) from exc

        if len(rv) == 1:
            return rv[0]

        raise LabelDoesNotExistError(f'Image {label_name} not found')

    @override
    def delete_labels(
        self,
        specification: LabelSpecification | None = None,
        select_callback: SelectCallbackLabel | None = None,
    ) -> int:
        """Delete labels matching a specification.

        Returns:
            The number of labels deleted.
        """
        return self._delete_resources(
            Label, specification=specification, select_callback=select_callback
        )

    @override
    def create_persons(
        self, names: list[str], birthdate: date | None = None
    ) -> list[Person]:
        """Method to add multiple persons to the database."""
        objs: list[Person] = [
            Person(name=name, birthdate=birthdate) for name in names
        ]
        try:
            return self._create_resources(objs)
        except ResourceAlreadyExistsError as exc:
            raise PersonAlreadyExistsError('Douplicate persons added') from exc

    @override
    def get_persons(
        self,
        specification: PersonSpecification | None = None,
        options: Sequence[RetrieveOption] | None = None,
    ) -> list[Person]:
        """Method to retrieve (a subset of) the persons in the database."""
        return self._get_resources(
            Person, specification=specification, options=options
        )

    @override
    def rename_person(
        self,
        person_name: str,
        new_name: str,
        select_callback: SelectCallbackPerson | None = None,
    ) -> Person:
        """Rename a person."""
        try:
            rv = self._update_resources(
                Person,
                {'name': new_name},
                specification=NameIsPersonSpec(person_name, False),
                select_callback=select_callback,
                callback_before_updating=True,
            )
        except IntegrityError as exc:
            raise PersonAlreadyExistsError(
                f'A person named "{new_name}" already exists.'
            ) from exc

        if len(rv) == 1:
            return rv[0]

        raise PersonDoesNotExistError(f'Person {person_name} not found')

    @override
    def set_birthdate_for_persons(
        self,
        new_birthdate: date | None = None,
        *,
        specification: PersonSpecification | None = None,
        select_callback: SelectCallbackPerson | None = None,
    ) -> list[Person]:
        """Set the birthday for persons."""
        return self._update_resources(
            Person,
            new_data={'birthdate': new_birthdate},
            specification=specification,
            select_callback=select_callback,
        )

    @override
    def delete_persons(
        self,
        specification: PersonSpecification | None = None,
        select_callback: SelectCallbackPerson | None = None,
    ) -> int:
        """Delete persons matching a specification.

        Returns:
            The number of persons deleted.
        """
        return self._delete_resources(
            Person, specification=specification, select_callback=select_callback
        )

    @override
    def add_label_to_persons(
        self,
        label: str,
        specification: PersonSpecification | None = None,
        select_callback: SelectCallbackPerson | None = None,
    ) -> list[Person]:
        """Method to add a label to a persons."""
        return self._add_label_to_resource(
            Person,
            PersonLabelLink,
            'person_id',
            label,
            specification=self._build_composite_specification(
                NotSpecification(HasLabelPersonSpec(label_name=label)),
                specification,
            ),
            select_callback=select_callback,
        )

    @override
    def remove_label_from_persons(
        self,
        label: str,
        specification: PersonSpecification | None = None,
        select_callback: SelectCallbackPerson | None = None,
    ) -> list[Person]:
        """Method to remove a label from persons."""
        return self._remove_label_from_resource(
            Person,
            PersonLabelLink,
            'person_id',
            label,
            specification=self._build_composite_specification(
                HasLabelPersonSpec(label_name=label),
                specification,
            ),
            select_callback=select_callback,
        )

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
    def get_images(
        self,
        specification: ImageSpecification | None = None,
        options: Sequence[RetrieveOption] | None = None,
    ) -> list[Image]:
        """Method to retrieve (a subset of) the labels in the database."""
        return self._get_resources(
            Image, specification=specification, options=options
        )

    @override
    def set_image_status(
        self,
        status: ResourceStatus,
        specification: ImageSpecification | None = None,
        select_callback: SelectCallbackImage | None = None,
    ) -> list[Image]:
        """Method to set the status of specific images."""
        rv = self._update_resources(
            Image,
            {'status': status},
            specification=specification,
            select_callback=select_callback,
            callback_before_updating=False,
        )

        return rv

    @override
    def add_label_to_images(
        self,
        label: str,
        specification: ImageSpecification | None = None,
        select_callback: SelectCallbackImage | None = None,
    ) -> list[Image]:
        """Method to add a label to a images."""
        return self._add_label_to_resource(
            Image,
            ImageLabelLink,
            'image_id',
            label,
            specification=self._build_composite_specification(
                NotSpecification(HasLabelImageSpec(label_name=label)),
                specification,
            ),
            select_callback=select_callback,
        )

    @override
    def add_person_to_images(
        self,
        person: str,
        specification: ImageSpecification | None = None,
        select_callback: SelectCallbackImage | None = None,
    ) -> list[Image]:
        """Method to add a person to a images."""
        return self._add_person_to_resource(
            Image,
            ImagePersonLink,
            'image_id',
            person,
            specification=self._build_composite_specification(
                NotSpecification(HasPersonImageSpec(person_name=person)),
                specification,
            ),
            select_callback=select_callback,
        )

    @override
    def remove_label_from_images(
        self,
        label: str,
        specification: ImageSpecification | None = None,
        select_callback: SelectCallbackImage | None = None,
    ) -> list[Image]:
        """Method to remove a label from images."""
        return self._remove_label_from_resource(
            Image,
            ImageLabelLink,
            'image_id',
            label,
            specification=self._build_composite_specification(
                HasLabelImageSpec(label_name=label),
                specification,
            ),
            select_callback=select_callback,
        )

    @override
    def remove_person_from_images(
        self,
        person: str,
        specification: ImageSpecification | None = None,
        select_callback: SelectCallbackImage | None = None,
    ) -> list[Image]:
        """Method to remove a person from images."""
        return self._remove_person_from_resource(
            Image,
            ImagePersonLink,
            'image_id',
            person,
            specification=self._build_composite_specification(
                HasPersonImageSpec(person_name=person),
                specification,
            ),
            select_callback=select_callback,
        )

    @override
    def set_favourite_for_images(
        self,
        favourite: bool,
        *,
        specification: ImageSpecification | None = None,
        select_callback: SelectCallbackImage | None = None,
    ) -> list[Image]:
        """Set the favourite flag for specific images."""
        return self._update_resources(
            Image,
            {'favourite': favourite},
            specification=specification,
            select_callback=select_callback,
            callback_before_updating=False,
        )

    @override
    def rename_image(
        self,
        image_title: str,
        new_title: str,
        select_callback: SelectCallbackImage | None = None,
    ) -> Image:
        """Rename a image."""
        try:
            rv = self._update_resources(
                Image,
                {'title': new_title},
                specification=NameIsImageSpec(image_title, False),
                select_callback=select_callback,
                callback_before_updating=True,
            )
        except IntegrityError as exc:
            raise ImageAlreadyExistsError(
                f'A image named "{new_title}" already exists.'
            ) from exc

        if len(rv) == 1:
            return rv[0]

        raise ImageDoesNotExistError(f'Image {image_title} not found')
