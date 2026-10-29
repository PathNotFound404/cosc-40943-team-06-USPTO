from datetime import datetime
from pathlib import Path

import pytest

from patent_intelligence import storage
from patent_intelligence.cleaning import StagedSummary, build_staged_dataset, staging
from patent_intelligence.cleaning.errors import (
    CleaningFailedError,
    MissingColumnsError,
    NoRawDataError,
)
from patent_intelligence.ingestion import import_file
from tests.ingestion.conftest import (
    FIXTURE,
    IMPORT_TIME,
    fixture_records,
    no_progress,
    write_records,
)

OFFICE_ACTION_COLUMNS = [
    "record_id",
    "application_number",
    "art_unit",
    "work_group",
    "technology_center",
    "examiner_number",
    "document_code",
    "submission_date",
    "filing_date",
    "import_id",
]
REJECTION_COLUMNS = ["record_id", "rejection_type", "rejection_label", "import_id"]


@pytest.fixture
def database(tmp_path: Path):
    database = storage.open(tmp_path / "data")
    yield database
    database.close()


def raw_tables(database) -> dict[str, list[tuple]]:
    cursor = database.cursor()
    return {
        table: cursor.execute(f"SELECT * FROM {table} ORDER BY ALL").fetchall()
        for table in ("import_log", "raw_office_action", "rejected_record")
    }


def columns(database, view: str) -> list[str]:
    return [row[1] for row in database.cursor().execute(f"PRAGMA table_info({view})").fetchall()]


def view_exists(database, view: str) -> bool:
    return bool(
        database.cursor()
        .execute("SELECT count(*) FROM duckdb_views() WHERE view_name = ?", [view])
        .fetchone()[0]
    )


def staged(database, query: str, parameters: list | None = None) -> list[tuple]:
    return database.cursor().execute(query, parameters or []).fetchall()


# --- Main success scenario ----------------------------------------------------------------


def test_main_flow_stages_one_row_per_office_action_and_rejection_and_keeps_raw(
    database,
) -> None:
    import_file(database, FIXTURE, IMPORT_TIME, no_progress)
    before = raw_tables(database)

    summary = build_staged_dataset(database)

    assert summary == StagedSummary(office_actions_staged=20, rejections_staged=20)
    assert columns(database, "staged_office_action") == OFFICE_ACTION_COLUMNS
    assert columns(database, "staged_rejection") == REJECTION_COLUMNS
    records = fixture_records()
    staged_ids = staged(database, "SELECT record_id FROM staged_office_action ORDER BY ALL")
    assert staged_ids == sorted((record["id"],) for record in records)

    first = records[0]
    (row,) = staged(
        database, "SELECT * FROM staged_office_action WHERE record_id = ?", [first["id"]]
    )
    assert row == (
        first["id"],
        first["patentApplicationNumber"],
        str(first["groupArtUnitNumber"]),
        first["workGroup"],
        first["techCenter"],
        first["examinerEmployeeNumber"],
        first["documentCode"],
        datetime(2026, 10, 13),
        datetime(2022, 2, 1),
        1,
    )
    second = records[1]
    assert staged(
        database, "SELECT * FROM staged_rejection WHERE record_id = ?", [second["id"]]
    ) == [(second["id"], "103", "103()", 1)]
    assert raw_tables(database) == before


# --- 1a: no raw records -------------------------------------------------------------------


def test_with_no_raw_records_cleaning_says_there_is_no_data(database) -> None:
    with pytest.raises(NoRawDataError, match="no data to clean"):
        build_staged_dataset(database)
    assert not view_exists(database, "staged_office_action")


# --- 2a: the cleaning script fails --------------------------------------------------------


def test_a_failed_run_keeps_the_previous_staged_views_and_the_raw_records(
    database, monkeypatch: pytest.MonkeyPatch
) -> None:
    import_file(database, FIXTURE, IMPORT_TIME, no_progress)
    build_staged_dataset(database)
    before = raw_tables(database)
    monkeypatch.setattr(
        staging,
        "STAGED_VIEWS",
        {
            "staged_office_action": "SELECT 1 AS replaced",
            "staged_rejection": "SELECT no_such_column FROM raw_office_action",
        },
    )

    with pytest.raises(CleaningFailedError):
        build_staged_dataset(database)

    assert columns(database, "staged_office_action") == OFFICE_ACTION_COLUMNS
    assert staged(database, "SELECT count(*) FROM staged_office_action") == [(20,)]
    assert raw_tables(database) == before


# --- 3a: required columns missing ---------------------------------------------------------


def test_a_missing_required_column_is_named_and_nothing_is_staged(
    database, monkeypatch: pytest.MonkeyPatch
) -> None:
    import_file(database, FIXTURE, IMPORT_TIME, no_progress)
    views = dict(staging.STAGED_VIEWS)
    views["staged_office_action"] = views["staged_office_action"].replace(
        "groupArtUnitNumber AS art_unit,", ""
    )
    monkeypatch.setattr(staging, "STAGED_VIEWS", views)

    with pytest.raises(MissingColumnsError) as raised:
        build_staged_dataset(database)

    assert raised.value.missing == ["staged_office_action.art_unit"]
    assert "staged_office_action.art_unit" in raised.value.message
    assert not view_exists(database, "staged_office_action")
    assert not view_exists(database, "staged_rejection")


# --- Null handling (OI-5) -----------------------------------------------------------------


def test_a_rejection_without_a_type_is_kept_and_the_work_group_is_the_source_value(
    database, tmp_path: Path
) -> None:
    records = fixture_records()
    assert "type" not in records[0]["rejections"][0]
    records[1]["groupArtUnitNumber"] = 2893
    records[1]["workGroup"] = "2810"
    import_file(database, write_records(tmp_path / "week.jsonl", records), IMPORT_TIME, no_progress)

    build_staged_dataset(database)

    assert staged(
        database,
        "SELECT rejection_type, rejection_label FROM staged_rejection WHERE record_id = ?",
        [records[0]["id"]],
    ) == [(None, "()")]
    assert staged(
        database,
        "SELECT art_unit, work_group FROM staged_office_action WHERE record_id = ?",
        [records[1]["id"]],
    ) == [("2893", "2810")]


# --- Duplicate records (docs/design/intake.md) --------------------------------------------


def copy_of(record: dict, timestamp: str | None, document_code: str, rejection: str) -> dict:
    copy = dict(record)
    copy["documentCode"] = document_code
    copy["rejections"] = [{"label": f"{rejection}()", "type": rejection}]
    if timestamp is None:
        del copy["systemLastModifiedTimestamp"]
    else:
        copy["systemLastModifiedTimestamp"] = timestamp
    return copy


def import_records(database, path: Path, records: list[dict]) -> None:
    import_file(database, write_records(path, records), IMPORT_TIME, no_progress)


def chosen(database, record_id: str) -> tuple[list[tuple], list[tuple]]:
    office_actions = staged(
        database,
        "SELECT document_code FROM staged_office_action WHERE record_id = ?",
        [record_id],
    )
    rejections = staged(
        database, "SELECT rejection_type FROM staged_rejection WHERE record_id = ?", [record_id]
    )
    return office_actions, rejections


def test_the_newest_copy_of_a_duplicate_record_is_staged_with_its_rejections(
    database, tmp_path: Path
) -> None:
    record = fixture_records()[0]
    # Imported newest first, so "later import wins" alone would choose wrongly.
    newer = copy_of(record, "2026-10-05T00:00:00.000Z", "NEWER", "102")
    older = copy_of(record, "2026-10-01T00:00:00.000Z", "OLDER", "103")
    undated = copy_of(record, None, "UNDATED", "112")
    import_records(database, tmp_path / "newer.jsonl", [newer])
    import_records(database, tmp_path / "older.jsonl", [older])
    import_records(database, tmp_path / "undated.jsonl", [undated])

    summary = build_staged_dataset(database)

    assert chosen(database, record["id"]) == ([("NEWER",)], [("102",)])
    assert summary == StagedSummary(office_actions_staged=1, rejections_staged=1)
    assert staged(database, "SELECT count(*) FROM raw_office_action") == [(3,)]


def test_on_equal_timestamps_the_later_import_then_the_later_line_is_staged(
    database, tmp_path: Path
) -> None:
    first, second = fixture_records()[:2]
    same = "2026-10-05T00:00:00.000Z"
    import_records(
        database,
        tmp_path / "first.jsonl",
        [copy_of(first, same, "FIRST IMPORT", "102"), copy_of(second, same, "EARLIER LINE", "102")],
    )
    import_records(
        database,
        tmp_path / "second.jsonl",
        [copy_of(first, same, "LATER IMPORT", "103"), copy_of(second, same, "LATER LINE", "103")],
    )
    import_records(
        database,
        tmp_path / "third.jsonl",
        [copy_of(second, same, "NEXT EARLIER LINE", "101"), copy_of(second, same, "LAST", "112")],
    )

    build_staged_dataset(database)

    assert chosen(database, first["id"]) == ([("LATER IMPORT",)], [("103",)])
    assert chosen(database, second["id"]) == ([("LAST",)], [("112",)])
