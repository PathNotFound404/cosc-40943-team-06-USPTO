"""The Export view (UC-FEAT-export-visuals, docs/design/visualization.md Tests)."""

import importlib
import os
import sys
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import pytest
from PySide6.QtCore import Qt

from patent_intelligence.analytics import run_metric
from patent_intelligence.app import build_window
from patent_intelligence.charts import Decision, draw, file_name
from patent_intelligence.jobs.runner import JobRunner
from patent_intelligence.ui.export_view import ExportView
from tests.ingestion.conftest import counts
from tests.ui.test_charts_view import all_metrics

export_module = importlib.import_module("patent_intelligence.charts.export")
GENERATED = date(2026, 11, 3)


@pytest.fixture
def folder(tmp_path: Path) -> Path:
    folder = tmp_path / "exports"
    folder.mkdir()
    return folder


def two_charts(database):
    return [
        draw(run_metric(database, "office-actions-by-document-code", {})),
        draw(run_metric(database, "rejections-by-type", {})),
    ]


def make_view(database, charts, folders, decisions=None):
    """An Export view whose questions are answered from `folders` (one per time it asks;
    None cancels) and `decisions` (one per taken file name)."""
    calls = SimpleNamespace(folders_asked=0, conflicts=[], alerts=[])
    folders = list(folders)

    def choose_folder(parent):
        calls.folders_asked += 1
        return folders.pop(0)

    def ask_conflict(parent, name):
        calls.conflicts.append(name)
        return (decisions or {}).get(name)

    def alert(parent, message):
        calls.alerts.append(message)

    view = ExportView(
        database, lambda: charts, choose_folder, ask_conflict, alert, lambda: GENERATED
    )
    return view, calls


def notices(view: ExportView) -> list[str]:
    return [view.notices.item(row).text() for row in range(view.notices.count())]


def listed(view: ExportView) -> list[str]:
    return [view.choices.item(row).text() for row in range(view.choices.count())]


# --- Step 2: the charts open in this session ------------------------------------------


def test_the_export_tab_lists_the_charts_created_in_this_session_all_checked(
    qt_app, staged_database
) -> None:
    runner = JobRunner()
    window = build_window(
        runner, staged_database, choose=all_metrics, choose_weeks=lambda *args: args[-1]
    )
    runner.shutdown()
    charts_view, export_view = window.tabs.widget(1), window.tabs.widget(3)
    assert window.tabs.tabText(3) == "Export"
    assert listed(export_view) == []
    assert not export_view.export_button.isEnabled()

    charts_view.create_visualizations()
    window.tabs.setCurrentWidget(export_view)
    window.show()
    try:
        assert listed(export_view) == [chart.title for chart in charts_view.charts]
        assert export_view.selected() == charts_view.charts
        assert export_view.export_button.isEnabled()
    finally:
        window.close()


def test_export_needs_one_chart_checked_and_writes_only_the_checked(
    qt_app, staged_database, folder
) -> None:
    charts = two_charts(staged_database)
    view, _ = make_view(staged_database, charts, [folder])
    view.choices.item(0).setCheckState(Qt.CheckState.Unchecked)
    assert view.export_button.isEnabled()
    view.choices.item(1).setCheckState(Qt.CheckState.Unchecked)
    assert not view.export_button.isEnabled()
    view.choices.item(1).setCheckState(Qt.CheckState.Checked)

    view.export_selected()

    assert [path.name for path in folder.iterdir()] == [file_name(charts[1])]


# --- Main flow and the notice (steps 3-6, FR-TASK-completion-notice) ------------------


def test_exporting_saves_every_checked_chart_and_lists_each_saved_path(
    qt_app, staged_database, folder
) -> None:
    charts = two_charts(staged_database)
    view, calls = make_view(staged_database, charts, [folder])
    before = counts(staged_database)

    view.export_selected()

    paths = [folder / file_name(chart) for chart in charts]
    assert all(path.is_file() for path in paths)
    assert notices(view) == [
        f"Saved 2 visualizations in {folder}:",
        *(f"    {path}" for path in paths),
    ]
    assert calls.alerts == [] and calls.conflicts == []
    assert counts(staged_database) == before  # exporting changes no stored data


def test_the_notice_lists_each_chart_that_failed(
    qt_app, staged_database, folder, monkeypatch
) -> None:
    charts = two_charts(staged_database)
    real_write = export_module._write

    def fail_the_first(chart, path, generated_at, files):
        if chart is charts[0]:
            raise OSError("No space left on device")
        real_write(chart, path, generated_at, files)

    monkeypatch.setattr(export_module, "_write", fail_the_first)
    view, _ = make_view(staged_database, charts, [folder])

    view.export_selected()

    assert notices(view) == [
        f"Saved 1 visualization in {folder}:",
        f"    {folder / file_name(charts[1])}",
        "These visualizations could not be exported:",
        f"    {charts[0].title}: The file could not be written. "
        "Details were written to the log file.",
    ]


# --- 3a: the user cancels -------------------------------------------------------------


def test_cancelling_the_folder_choice_writes_no_files(qt_app, staged_database, folder) -> None:
    view, calls = make_view(staged_database, two_charts(staged_database), [None])
    view.export_selected()
    assert calls.folders_asked == 1
    assert list(folder.iterdir()) == []
    assert notices(view) == []


def test_cancelling_the_overwrite_question_writes_no_files(qt_app, staged_database, folder) -> None:
    charts = two_charts(staged_database)
    taken = folder / file_name(charts[1])
    taken.write_bytes(b"earlier")
    view, calls = make_view(staged_database, charts, [folder], decisions={})

    view.export_selected()

    assert calls.conflicts == [taken.name]
    assert [path.name for path in folder.iterdir()] == [taken.name]
    assert taken.read_bytes() == b"earlier"
    assert notices(view) == []


# --- 4a: the folder is not writable ---------------------------------------------------


def test_a_folder_that_cannot_be_written_is_refused_and_another_is_asked_for(
    qt_app, staged_database, folder, tmp_path
) -> None:
    missing = tmp_path / "missing"
    view, calls = make_view(staged_database, two_charts(staged_database), [missing, folder])

    view.export_selected()

    assert calls.folders_asked == 2
    (alert,) = calls.alerts
    assert str(missing) in alert and "Choose a different folder" in alert
    assert len(list(folder.iterdir())) == 2


@pytest.mark.skipif(sys.platform == "win32", reason="folder permissions are POSIX modes")
def test_a_read_only_folder_is_refused_and_cancelling_then_writes_nothing(
    qt_app, staged_database, tmp_path
) -> None:
    read_only = tmp_path / "read-only"
    read_only.mkdir()
    read_only.chmod(0o500)
    try:
        if os.access(read_only, os.W_OK):
            pytest.skip("this user can write to read-only folders")
        view, calls = make_view(staged_database, two_charts(staged_database), [read_only, None])
        view.export_selected()
        assert len(calls.alerts) == 1
        assert list(read_only.iterdir()) == []
    finally:
        read_only.chmod(0o700)


# --- 5b: a file with the same name exists ---------------------------------------------


def test_each_taken_file_name_is_asked_about_and_the_decision_is_followed(
    qt_app, staged_database, folder
) -> None:
    charts = two_charts(staged_database)
    first, second = (folder / file_name(chart) for chart in charts)
    first.write_bytes(b"earlier first")
    second.write_bytes(b"earlier second")
    view, calls = make_view(
        staged_database,
        charts,
        [folder],
        decisions={first.name: Decision.OVERWRITE, second.name: Decision.KEEP_BOTH},
    )

    view.export_selected()

    assert calls.conflicts == [first.name, second.name]
    assert first.read_bytes() != b"earlier first"  # overwritten
    assert second.read_bytes() == b"earlier second"  # kept
    kept_both = folder / f"{second.stem} (2).png"
    assert kept_both.is_file()
    assert notices(view)[1:] == [f"    {first}", f"    {kept_both}"]
