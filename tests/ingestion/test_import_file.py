"""UC-FEAT-decompile-files: the main flow and every extension (docs/design/intake.md)."""

import hashlib
import json
import logging
import os
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path

import pytest

from patent_intelligence import storage
from patent_intelligence.ingestion import import_file
from patent_intelligence.ingestion.errors import (
    LayoutMismatchError,
    UnreadableFileError,
    UnsupportedFileError,
)
from patent_intelligence.ingestion.layout import EXPECTED_FIELDS, JSON_FIELDS
from tests.ingestion.conftest import (
    FIXTURE,
    IMPORT_TIME,
    counts,
    fixture_records,
    no_progress,
    write_records,
)

NOTHING_STORED = {"import_log": 0, "raw_office_action": 0, "rejected_record": 0}


# --- Main success scenario -------------------------------------------------------------


def test_main_flow_loads_every_record_with_one_import_id_and_logs_the_import(database) -> None:
    summary = import_file(database, FIXTURE, IMPORT_TIME, no_progress)

    assert (summary.records_loaded, summary.records_rejected) == (20, 0)
    assert summary.already_imported is False
    cursor = database.cursor()
    assert cursor.execute("SELECT DISTINCT import_id FROM raw_office_action").fetchall() == [
        (summary.import_id,)
    ]
    file_name, content_hash, import_time, loaded, rejected, version = cursor.execute(
        "SELECT file_name, content_hash, import_time, records_loaded, records_rejected, "
        "app_version FROM import_log WHERE import_id = ?",
        [summary.import_id],
    ).fetchone()
    assert file_name == "office_actions_20.jsonl"
    assert content_hash == hashlib.sha256(FIXTURE.read_bytes()).hexdigest()
    assert import_time == datetime(2026, 10, 28, 15, 30)  # the passed-in time, in UTC
    assert (loaded, rejected) == (20, 0)
    assert version
    line_numbers = cursor.execute(
        "SELECT line_number FROM raw_office_action ORDER BY line_number"
    ).fetchall()
    assert [n for (n,) in line_numbers] == list(range(1, 21))


def test_every_raw_field_equals_the_source_value(database) -> None:
    """BR-no-data-alteration: character for character, including oaText and timestamps."""
    summary = import_file(database, FIXTURE, IMPORT_TIME, no_progress)
    cursor = database.cursor()
    columns = ", ".join(EXPECTED_FIELDS)
    rows = cursor.execute(
        f"SELECT line_number, {columns} FROM raw_office_action WHERE import_id = ? "
        "ORDER BY line_number",
        [summary.import_id],
    ).fetchall()
    records = fixture_records()
    assert len(rows) == len(records)
    for (line_number, *values), record in zip(rows, records, strict=True):
        assert line_number == records.index(record) + 1
        for name, stored in zip(EXPECTED_FIELDS, values, strict=True):
            if name not in record:
                assert stored is None, name
            elif name in JSON_FIELDS:
                assert json.loads(stored) == record[name], name
            elif isinstance(record[name], str):
                assert stored == record[name], name
            else:  # numbers and booleans, as the file wrote them
                assert stored == json.dumps(record[name]), name


# --- 3a: not a supported file, or fields differ ----------------------------------------


@pytest.mark.parametrize("kind", ["csv", "zip"])
def test_a_file_that_is_not_json_lines_is_unsupported(database, tmp_path: Path, kind) -> None:
    if kind == "csv":
        path = tmp_path / "office_actions.csv"
        path.write_text("id,documentCode\nabc,CTNF\n", encoding="utf-8")
    else:
        path = tmp_path / "office_actions.zip"
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.write(FIXTURE, FIXTURE.name)
    with pytest.raises(UnsupportedFileError) as raised:
        import_file(database, path, IMPORT_TIME, no_progress)
    assert path.name in raised.value.message
    assert counts(database) == NOTHING_STORED


def test_a_file_missing_a_required_field_is_refused_and_the_field_named(
    database, tmp_path: Path
) -> None:
    records = fixture_records()
    for record in records:
        del record["submissionDate"]
    path = write_records(tmp_path / "missing.jsonl", records)
    with pytest.raises(LayoutMismatchError) as raised:
        import_file(database, path, IMPORT_TIME, no_progress)
    assert raised.value.missing == ["submissionDate"]
    assert "submissionDate" in raised.value.message
    assert counts(database) == NOTHING_STORED


def test_a_file_with_an_extra_field_is_refused_and_the_field_named(
    database, tmp_path: Path
) -> None:
    records = fixture_records()
    records[3]["examinerTeam"] = "new"
    path = write_records(tmp_path / "extra.jsonl", records)
    with pytest.raises(LayoutMismatchError) as raised:
        import_file(database, path, IMPORT_TIME, no_progress)
    assert raised.value.unexpected == ["examinerTeam"]
    assert counts(database) == NOTHING_STORED


def test_an_extra_field_after_the_layout_sample_still_refuses_the_file(
    database, tmp_path: Path
) -> None:
    """Without this, the field's values would be dropped silently (BR-no-data-alteration)."""
    records = many_records(105)
    records[104]["examinerTeam"] = "new"
    path = write_records(tmp_path / "late_extra.jsonl", records)
    with pytest.raises(LayoutMismatchError) as raised:
        import_file(database, path, IMPORT_TIME, no_progress)
    assert raised.value.unexpected == ["examinerTeam"]
    assert counts(database) == NOTHING_STORED


def test_an_optional_field_absent_from_every_record_is_accepted(database, tmp_path) -> None:
    records = fixture_records()
    for record in records:
        record.pop("nationalClass", None)
    path = write_records(tmp_path / "no_class.jsonl", records)
    assert import_file(database, path, IMPORT_TIME, no_progress).records_loaded == 20


# --- 4a: corrupted or unreadable ------------------------------------------------------


def test_a_file_truncated_mid_line_is_unreadable_and_nothing_is_kept(
    database, tmp_path: Path
) -> None:
    path = truncated_copy(tmp_path / "truncated.jsonl")
    with pytest.raises(UnreadableFileError) as raised:
        import_file(database, path, IMPORT_TIME, no_progress)
    assert raised.value.line_number == 20
    assert "line 20" in raised.value.message
    assert counts(database) == NOTHING_STORED


def test_a_bad_line_after_the_layout_sample_is_found_while_loading(
    database, tmp_path: Path
) -> None:
    path = write_records(tmp_path / "late_bad.jsonl", many_records(110))
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    lines[106] = lines[106][:500] + "\n"
    path.write_text("".join(lines), encoding="utf-8", newline="\n")
    with pytest.raises(UnreadableFileError) as raised:
        import_file(database, path, IMPORT_TIME, no_progress)
    assert raised.value.line_number == 107
    assert counts(database) == NOTHING_STORED


# --- 5a: records that fail a required-field check ---------------------------------------


def test_rejected_records_are_stored_with_reasons_and_the_rest_load(
    database, tmp_path: Path
) -> None:
    records = fixture_records()
    del records[2]["groupArtUnitNumber"]
    del records[9]["groupArtUnitNumber"]
    records[14]["groupArtUnitNumber"] = 12345
    path = write_records(tmp_path / "some_bad.jsonl", records)

    summary = import_file(database, path, IMPORT_TIME, no_progress)

    assert (summary.records_loaded, summary.records_rejected) == (17, 3)
    assert summary.records_loaded + summary.records_rejected == len(records)
    assert summary.rejected_by_reason == {
        "missing groupArtUnitNumber": 2,
        "groupArtUnitNumber is not four digits": 1,
    }
    rejected = (
        database.cursor()
        .execute("SELECT line_number, reason, raw_line FROM rejected_record ORDER BY line_number")
        .fetchall()
    )
    source_lines = path.read_text(encoding="utf-8").splitlines()
    assert [(n, reason) for n, reason, _ in rejected] == [
        (3, "missing groupArtUnitNumber"),
        (10, "missing groupArtUnitNumber"),
        (15, "groupArtUnitNumber is not four digits"),
    ]
    assert [raw for _, _, raw in rejected] == [source_lines[2], source_lines[9], source_lines[14]]
    assert counts(database)["raw_office_action"] == 17


def test_an_empty_value_or_a_bad_timestamp_rejects_the_record(database, tmp_path: Path) -> None:
    records = fixture_records()
    records[0]["documentCode"] = ""
    records[1]["submissionDate"] = "last Tuesday"
    path = write_records(tmp_path / "bad_values.jsonl", records)
    summary = import_file(database, path, IMPORT_TIME, no_progress)
    assert summary.rejected_by_reason == {
        "missing documentCode": 1,
        "submissionDate is not a timestamp": 1,
    }


# --- Already imported (DI-no-duplicates) -------------------------------------------------


def test_importing_the_same_file_twice_reports_already_imported(database, tmp_path) -> None:
    first = import_file(database, FIXTURE, IMPORT_TIME, no_progress)
    renamed = shutil.copy(FIXTURE, tmp_path / "renamed.jsonl")
    second = import_file(database, Path(renamed), IMPORT_TIME, no_progress)
    assert second.already_imported is True
    assert second.import_id == first.import_id
    assert counts(database) == {"import_log": 1, "raw_office_action": 20, "rejected_record": 0}


# --- Interrupted (ROB-resume, QS-interrupted-import-resumes) -----------------------------


class Stop(Exception):
    pass


def test_an_import_stopped_before_commit_leaves_the_database_as_it_was(database) -> None:
    def stop_while_storing(fraction: float, message: str) -> None:
        if message.startswith("Storing"):
            raise Stop

    with pytest.raises(Stop):
        import_file(database, FIXTURE, IMPORT_TIME, stop_while_storing)
    assert counts(database) == NOTHING_STORED
    assert import_file(database, FIXTURE, IMPORT_TIME, no_progress).records_loaded == 20


def test_an_import_killed_mid_transaction_can_be_imported_again(tmp_path: Path) -> None:
    data = tmp_path / "data"
    child = f"""
import os, sys
from datetime import datetime, UTC
from pathlib import Path
from patent_intelligence import storage
from patent_intelligence.ingestion import import_file
database = storage.open(Path({str(data)!r}))
def die(fraction, message):
    if message.startswith("Storing"):
        os._exit(3)
import_file(database, Path({str(FIXTURE)!r}), datetime.now(UTC), die)
"""
    source = Path(__file__).parents[2] / "src"
    result = subprocess.run(
        [sys.executable, "-c", child],
        env={**os.environ, "PYTHONPATH": str(source)},
        check=False,
        timeout=120,
    )
    assert result.returncode == 3

    database = storage.open(data)
    try:
        assert counts(database) == NOTHING_STORED
        assert import_file(database, FIXTURE, IMPORT_TIME, no_progress).records_loaded == 20
    finally:
        database.close()


# --- Logging (architecture 8.2.7) --------------------------------------------------------


def test_the_log_has_the_counts_and_no_letter_text_records_or_examiner_numbers(
    database, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    records = fixture_records()
    del records[4]["groupArtUnitNumber"]
    path = write_records(tmp_path / "logged.jsonl", records)
    with caplog.at_level(logging.INFO):
        import_file(database, path, IMPORT_TIME, no_progress)

    assert "19 records loaded, 1 rejected" in caplog.text
    assert "missing groupArtUnitNumber" in caplog.text
    for record in records:
        assert record["examinerEmployeeNumber"] not in caplog.text
        assert record["oaText"][:60] not in caplog.text
        assert record["id"] not in caplog.text


# --- Helpers --------------------------------------------------------------------------


def many_records(count: int) -> list[dict]:
    """The fixture repeated with distinct ids, for files longer than the layout sample."""
    base = fixture_records()
    records = []
    for n in range(count):
        record = dict(base[n % len(base)])
        record["id"] = f"{record['id']}-{n}"
        records.append(record)
    return records


def truncated_copy(path: Path) -> Path:
    content = FIXTURE.read_bytes()
    last_line_start = content.rstrip(b"\n").rfind(b"\n") + 1
    path.write_bytes(content[: last_line_start + 300])
    return path
