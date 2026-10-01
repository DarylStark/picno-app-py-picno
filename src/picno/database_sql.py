"""Module with the SQL implementation for the database."""

from sqlite3 import Connection as SQLiteConnection
from sqlite3 import Cursor as SQLiteCursor
from typing import override

from sqlalchemy import event
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, SQLModel, create_engine, delete, select

from .database import Database, LabelSpecification
from .exceptions import LabelAlreadyExistsError
from .model import Label


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
            cursor.close()

        self._create_tables()

    def _create_tables(self) -> None:
        SQLModel.metadata.create_all(self._engine)

    @override
    def create_label(self, name: str) -> Label:
        """Create a new label."""
        new_label = Label(name=name)

        with Session(self._engine) as session:
            session.add(new_label)
            try:
                session.commit()
            except IntegrityError as exc:
                session.rollback()
                raise LabelAlreadyExistsError(
                    f'A label named {name!r} already exists.'
                ) from exc
            session.refresh(new_label)

        return new_label

    @override
    def get_label(self, id: int) -> Label | None:
        """Method to retrieve one label."""
        with Session(self._engine) as session:
            return session.get(Label, id)

    @override
    def get_labels(
        self, specification: LabelSpecification | None = None
    ) -> list[Label]:
        """Method to retrieve (a subset of) the labels in the database."""
        with Session(self._engine) as session:
            statement = select(Label)
            if specification:
                statement = statement.where(specification.as_sql())
            return list(session.exec(statement).all())

    @override
    def update_label(self, id: int, new_name: str) -> Label | None:
        """Method to update one label."""
        with Session(self._engine) as session:
            label = session.get(Label, id)

            if label is None:
                return None

            label.name = new_name

            try:
                session.commit()
            except IntegrityError as exc:
                session.rollback()
                raise LabelAlreadyExistsError(
                    f'A label named {new_name!r} already exists.'
                ) from exc

            session.refresh(label)
            return label

    @override
    def delete_label(self, id: int) -> bool:
        """Method to delete one label."""
        with Session(self._engine) as session:
            label = session.get(Label, id)

            if label is None:
                return False

            session.delete(label)
            session.commit()
            return True

    @override
    def delete_labels(
        self, specification: LabelSpecification | None = None
    ) -> int:
        """Delete labels matching a specification.

        Returns:
            The number of labels deleted.
        """
        with Session(self._engine) as session:
            statement = delete(Label)
            if specification:
                statement = statement.where(specification.as_sql())

            result = session.exec(statement)
            session.commit()
            return result.rowcount
