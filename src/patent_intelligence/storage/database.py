"""The one DuckDB connection, and the cursors and transactions other components use."""

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import duckdb

from patent_intelligence.errors import AppError
from patent_intelligence.storage.migrate import apply_migrations

DATABASE_FILE_NAME = "patent-intelligence.duckdb"


class StorageError(AppError):
    """The database in the data folder could not be opened or prepared."""


class Database:
    """The open database. Components get a cursor from it and never connect themselves."""

    def __init__(self, connection: duckdb.DuckDBPyConnection) -> None:
        self._connection = connection

    def cursor(self) -> duckdb.DuckDBPyConnection:
        """Return a new cursor. Use each cursor from one thread only."""
        return self._connection.cursor()

    @contextmanager
    def transaction(self, cursor: duckdb.DuckDBPyConnection) -> Iterator[duckdb.DuckDBPyConnection]:
        """Run the block in one transaction on `cursor`; roll back on any error."""
        cursor.begin()
        try:
            yield cursor
        except BaseException:
            cursor.rollback()
            raise
        cursor.commit()

    def close(self) -> None:
        self._connection.close()


def open(data_folder: Path) -> Database:
    """Open (or create) the database in `data_folder` and apply pending migrations."""
    try:
        data_folder.mkdir(parents=True, exist_ok=True)
        spill_folder = data_folder / "tmp"
        spill_folder.mkdir(exist_ok=True)
        connection = duckdb.connect(str(data_folder / DATABASE_FILE_NAME))
    except (OSError, duckdb.Error) as error:
        raise StorageError(
            f"The data folder {data_folder} could not be opened. "
            "Check that it exists and that you can write to it."
        ) from error
    # DuckDB's default memory limit is a share of this computer's memory; large work spills
    # to the data folder instead of exhausting it (architecture 8.2.8, OE-hardware-adaptive).
    connection.execute(f"SET temp_directory = '{_sql_text(spill_folder.as_posix())}'")
    try:
        apply_migrations(connection)
    except duckdb.Error as error:
        connection.close()
        raise StorageError(
            "The database could not be prepared. Details were written to the log file."
        ) from error
    return Database(connection)


def _sql_text(value: str) -> str:
    return value.replace("'", "''")
