from pathlib import Path

import duckdb
import pytest

from patent_intelligence import storage


@pytest.fixture
def cursor(tmp_path: Path):
    database = storage.open(tmp_path)
    yield database.cursor()
    database.close()


def columns(cursor, table: str) -> list[str]:
    rows = cursor.execute(
        "SELECT column_name FROM duckdb_columns() WHERE table_name = ? ORDER BY column_index",
        [table],
    ).fetchall()
    return [name for (name,) in rows]


def test_first_migration_creates_the_import_log_and_raw_tables(cursor) -> None:
    assert columns(cursor, "import_log") == [
        "import_id",
        "file_name",
        "content_hash",
        "import_time",
        "records_loaded",
        "records_rejected",
        "app_version",
    ]
    raw = columns(cursor, "raw_office_action")
    assert raw[:2] == ["import_id", "line_number"]
    assert {"id", "oaText", "groupArtUnitNumber", "rejections", "sections"} <= set(raw)
    assert len(raw) == 2 + 31
    assert columns(cursor, "rejected_record") == ["import_id", "line_number", "reason", "raw_line"]


def test_the_same_content_hash_cannot_be_logged_twice(cursor) -> None:
    insert = (
        "INSERT INTO import_log "
        "VALUES (?, 'a.json', 'abc', TIMESTAMP '2026-10-28 12:00:00', 0, 0, '0.1.0')"
    )
    cursor.execute(insert, [1])
    with pytest.raises(duckdb.ConstraintException):
        cursor.execute(insert, [2])


def test_a_raw_record_must_belong_to_an_import(cursor) -> None:
    with pytest.raises(duckdb.ConstraintException):
        cursor.execute("INSERT INTO raw_office_action (import_id, line_number) VALUES (99, 1)")
