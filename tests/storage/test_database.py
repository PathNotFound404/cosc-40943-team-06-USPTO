from pathlib import Path

import duckdb
import pytest

from patent_intelligence import storage
from patent_intelligence.storage.database import DATABASE_FILE_NAME
from patent_intelligence.storage.migrate import apply_migrations


def test_open_creates_the_database_file_and_records_migrations(tmp_path: Path) -> None:
    database = storage.open(tmp_path / "data")
    try:
        assert (tmp_path / "data" / DATABASE_FILE_NAME).exists()
        applied = database.cursor().execute("SELECT count(*) FROM schema_migration").fetchone()
        assert applied is not None
    finally:
        database.close()


def test_migrations_are_applied_once_in_order(tmp_path: Path) -> None:
    folder = tmp_path / "migrations"
    folder.mkdir()
    (folder / "002_second.sql").write_text("INSERT INTO trail VALUES ('second');")
    (folder / "001_first.sql").write_text(
        "CREATE TABLE trail (step TEXT); INSERT INTO trail VALUES ('first');"
    )

    connection = duckdb.connect(str(tmp_path / "test.duckdb"))
    try:
        assert apply_migrations(connection, folder) == [1, 2]
        assert apply_migrations(connection, folder) == []
        assert connection.execute("SELECT step FROM trail").fetchall() == [("first",), ("second",)]
    finally:
        connection.close()


def test_a_failed_migration_leaves_nothing_behind(tmp_path: Path) -> None:
    folder = tmp_path / "migrations"
    folder.mkdir()
    (folder / "001_broken.sql").write_text(
        "CREATE TABLE half (a INT); SELECT * FROM missing_table;"
    )
    connection = duckdb.connect(str(tmp_path / "test.duckdb"))
    try:
        with pytest.raises(duckdb.Error):
            apply_migrations(connection, folder)
        tables = connection.execute("SELECT table_name FROM duckdb_tables()").fetchall()
        assert ("half",) not in tables
        assert connection.execute("SELECT count(*) FROM schema_migration").fetchone() == (0,)
    finally:
        connection.close()


def test_a_folder_that_cannot_be_created_raises_storage_error(tmp_path: Path) -> None:
    a_file = tmp_path / "not-a-folder"
    a_file.write_text("")
    with pytest.raises(storage.StorageError) as raised:
        storage.open(a_file / "data")
    assert "could not be opened" in raised.value.message


def test_transaction_rolls_back_on_error_and_commits_on_success(tmp_path: Path) -> None:
    database = storage.open(tmp_path)
    try:
        cursor = database.cursor()
        cursor.execute("CREATE TABLE note (text TEXT)")
        with pytest.raises(RuntimeError), database.transaction(cursor):
            cursor.execute("INSERT INTO note VALUES ('lost')")
            raise RuntimeError("stop")
        with database.transaction(cursor):
            cursor.execute("INSERT INTO note VALUES ('kept')")
        assert cursor.execute("SELECT text FROM note").fetchall() == [("kept",)]
    finally:
        database.close()
