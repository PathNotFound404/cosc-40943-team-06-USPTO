from pathlib import Path

import pytest

from patent_intelligence import storage
from patent_intelligence.cleaning import StagedSummary, staging
from patent_intelligence.cleaning.errors import CleaningFailedError, NoRawDataError
from patent_intelligence.jobs import import_job
from patent_intelligence.jobs.import_job import ImportJob
from tests.ingestion.conftest import (
    FIXTURE,
    IMPORT_TIME,
    counts,
    fixture_records,
    no_progress,
    write_records,
)


@pytest.fixture
def database(tmp_path: Path):
    database = storage.open(tmp_path / "data")
    yield database
    database.close()


def staged_count(database) -> int:
    return database.cursor().execute("SELECT count(*) FROM staged_office_action").fetchone()[0]


# --- Trigger: cleaning starts when the import finishes -----------------------------------


def test_a_finished_import_is_cleaned_and_staged_in_the_same_job(database) -> None:
    result = ImportJob(database, FIXTURE, IMPORT_TIME).run(no_progress)

    assert result.import_summary.records_loaded == 20
    assert result.staged_summary == StagedSummary(office_actions_staged=20, rejections_staged=20)
    assert result.cleaning_error is None
    assert staged_count(database) == 20


def test_an_already_imported_file_is_not_cleaned_again(
    database, monkeypatch: pytest.MonkeyPatch
) -> None:
    ImportJob(database, FIXTURE, IMPORT_TIME).run(no_progress)
    cleaned = []
    monkeypatch.setattr(import_job, "build_staged_dataset", cleaned.append)

    result = ImportJob(database, FIXTURE, IMPORT_TIME).run(no_progress)

    assert result.import_summary.already_imported
    assert result.staged_summary is None and result.cleaning_error is None
    assert cleaned == []


# --- Cleaning fails after a committed import (1a, 2a) ------------------------------------


def test_a_file_whose_records_are_all_rejected_has_no_data_to_clean(
    database, tmp_path: Path
) -> None:
    records = fixture_records()
    for record in records:
        record["groupArtUnitNumber"] = 28930
    path = write_records(tmp_path / "all-rejected.jsonl", records)

    result = ImportJob(database, path, IMPORT_TIME).run(no_progress)

    assert result.import_summary.records_rejected == 20
    assert isinstance(result.cleaning_error, NoRawDataError)
    assert counts(database)["rejected_record"] == 20


def test_a_cleaning_failure_keeps_the_import_and_reports_both(
    database, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(staging, "STAGED_VIEWS", {"staged_office_action": "SELECT no_such_column"})

    result = ImportJob(database, FIXTURE, IMPORT_TIME).run(no_progress)

    assert result.import_summary.records_loaded == 20
    assert isinstance(result.cleaning_error, CleaningFailedError)
    assert result.staged_summary is None
    assert counts(database)["raw_office_action"] == 20
