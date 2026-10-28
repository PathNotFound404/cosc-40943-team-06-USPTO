from pathlib import Path

import pytest

from patent_intelligence import storage
from patent_intelligence.ingestion import ImportSummary
from patent_intelligence.ingestion.errors import UnreadableFileError
from patent_intelligence.jobs.runner import JobRunner
from patent_intelligence.ui.import_view import ImportView
from patent_intelligence.ui.main_window import MainWindow
from tests.conftest import wait_until
from tests.ingestion.conftest import FIXTURE, IMPORT_TIME, counts, fixture_records, write_records


@pytest.fixture
def view(qt_app, tmp_path: Path):
    database = storage.open(tmp_path / "data")
    runner = JobRunner()
    view = ImportView(runner, database, clock=lambda: IMPORT_TIME)
    yield view, runner, database
    runner.shutdown()
    database.close()


def notices(view: ImportView) -> list[str]:
    return [view.notices.item(row).text() for row in range(view.notices.count())]


# --- Notice (FR-TASK-completion-notice) ------------------------------------------------


def test_the_completion_notice_shows_records_loaded_and_rejected(view) -> None:
    import_view, runner, _ = view
    runner.finished.emit(ImportSummary(1, "week.json", 8664, 3, {"missing groupArtUnitNumber": 3}))
    wait_until(lambda: import_view.notices.count() == 1)
    assert notices(import_view) == [
        "week.json imported: 8,664 records loaded, 3 rejected. "
        "Rejected because of missing groupArtUnitNumber: 3."
    ]


def test_an_already_imported_file_says_nothing_changed(view) -> None:
    import_view, runner, _ = view
    runner.finished.emit(ImportSummary(1, "week.json", 0, 0, already_imported=True))
    wait_until(lambda: import_view.notices.count() == 1)
    assert notices(import_view) == ["week.json has already been imported. Nothing was changed."]


def test_a_failure_shows_the_error_message_and_no_stack_trace(view) -> None:
    import_view, runner, _ = view
    error = UnreadableFileError("week.json", 20)
    runner.failed.emit(error)
    wait_until(lambda: import_view.notices.count() == 1)
    assert notices(import_view) == [error.message]
    assert "Traceback" not in notices(import_view)[0]


def test_dropping_a_folder_imports_nothing_and_says_so(view, tmp_path: Path) -> None:
    import_view, _, database = view
    import_view.on_files_dropped([tmp_path])
    assert "Nothing to import" in notices(import_view)[0]
    assert counts(database)["import_log"] == 0


# --- Several files (ROB-bad-input, QS-corrupt-file-reported) ---------------------------


def test_several_files_import_in_order_and_a_bad_one_is_reported_and_skipped(
    view, tmp_path: Path
) -> None:
    import_view, _, database = view
    records = fixture_records()
    first = FIXTURE
    content = FIXTURE.read_bytes()
    second = tmp_path / "truncated.jsonl"
    second.write_bytes(content[: content.rstrip(b"\n").rfind(b"\n") + 300])
    for record in records:
        record["id"] += "-third"
    third = write_records(tmp_path / "third.jsonl", records)

    import_view.on_files_dropped([first, second, third])
    wait_until(lambda: import_view.notices.count() == 3)

    shown = notices(import_view)
    assert shown[0] == "office_actions_20.jsonl imported: 20 records loaded, 0 rejected."
    assert shown[1].startswith("truncated.jsonl could not be read: line 20")
    assert shown[2] == "third.jsonl imported: 20 records loaded, 0 rejected."
    assert counts(database) == {"import_log": 2, "raw_office_action": 40, "rejected_record": 0}
    stored_files = database.cursor().execute("SELECT file_name FROM import_log").fetchall()
    assert ("truncated.jsonl",) not in stored_files
    assert import_view.progress_bar.value() == 100


# --- Smoke ----------------------------------------------------------------------------


def test_the_main_window_has_the_import_view(view) -> None:
    import_view, _, _ = view
    window = MainWindow(import_view)
    assert window.tabs.tabText(0) == "Import"
    assert import_view.acceptDrops()
