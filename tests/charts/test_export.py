"""Exporting charts to labeled PNG files (UC-FEAT-export-visuals, docs/design/visualization.md
Tests)."""

import importlib
import logging
import os
import struct
import sys
from datetime import date
from io import BytesIO
from pathlib import Path

import pytest
from matplotlib import image

from patent_intelligence import analytics
from patent_intelligence.analytics import run_metric
from patent_intelligence.charts import (
    Decision,
    FolderNotWritableError,
    draw,
    export_charts,
    file_name,
    find_conflicts,
)
from patent_intelligence.charts.export import WIDTH_PIXELS, label_lines, labeled_figure
from tests.ingestion.conftest import FIXTURE, counts

export_module = importlib.import_module("patent_intelligence.charts.export")

GENERATED = date(2026, 11, 3)
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def two_charts(database):
    return [
        draw(run_metric(database, "office-actions-by-document-code", {})),
        draw(run_metric(database, "rejections-by-technology-center-and-type", {})),
    ]


def source_files(database) -> dict[int, str]:
    return {file.import_id: file.file_name for file in analytics.imported_files(database)}


def png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    assert data[:8] == PNG_SIGNATURE
    return struct.unpack(">II", data[16:24])


# --- Main flow (steps 4-6, POST-1, POST-2, FR-CHART-counted-field) ----------------------


def test_exporting_two_charts_writes_two_labeled_pngs(staged_database, folder) -> None:
    charts = two_charts(staged_database)
    files = source_files(staged_database)

    summary = export_charts(charts, folder, {}, GENERATED, files)

    assert summary.failed == ()
    assert summary.saved == tuple(folder / file_name(chart) for chart in charts)
    assert sorted(path.name for path in folder.iterdir()) == sorted(
        ["Office actions by Document Code.png", "Rejection types by Technology Center.png"]
    )
    for path in summary.saved:
        width, height = png_size(path)
        assert width == WIDTH_PIXELS
        assert height > 0


@pytest.mark.parametrize(
    "name", ["office-actions-by-document-code", "rejections-by-technology-center-and-type"]
)
def test_each_image_is_labeled_with_title_source_dates_generation_date_and_counted_field(
    staged_database, folder, name
) -> None:
    chart = draw(run_metric(staged_database, name, {}))
    labeled = labeled_figure(chart, GENERATED, source_files(staged_database))

    # Above the label is the chart as drawn, which names its title and counted field.
    drawn = draw(chart.result).figure
    assert drawn.get_suptitle() == chart.title
    assert drawn.axes[0].get_title(loc="left") == (
        f"Counted field: {chart.result.metric.counted_field}"
    )
    buffer = BytesIO()
    drawn.savefig(buffer, format="png", dpi=labeled.dpi, facecolor=drawn.get_facecolor())
    buffer.seek(0)
    (placed,) = labeled.images
    assert (placed.get_array() == image.imread(buffer, format="png")).all()
    # Below it, the label.
    (label,) = labeled.texts
    assert label.get_text().splitlines() == [
        f"Data source: USPTO weekly office action file {FIXTURE.name}",
        "Date range: Submission Date 2026-10-13 to 2026-10-16",
        "Generated 2026-11-03",  # the date passed in (8.2.2)
    ]
    # The file holds the chart and the label strip, at the export width.
    (path,) = export_charts([chart], folder, {}, GENERATED, source_files(staged_database)).saved
    assert png_size(path) == (WIDTH_PIXELS, round(labeled.get_figheight() * labeled.dpi))
    assert placed.get_array().shape[0] < png_size(path)[1]


def test_a_chart_over_two_imports_names_both_files(two_weeks_database) -> None:
    chart = draw(run_metric(two_weeks_database, "office-actions-by-document-code", {}))
    (source, *_) = label_lines(chart, GENERATED, source_files(two_weeks_database))
    assert source == (
        f"Data source: USPTO weekly office action files {FIXTURE.name}, week_2026-10-25.jsonl"
    )


def test_exporting_leaves_the_chart_on_screen_unchanged(staged_database, folder) -> None:
    (chart, _) = two_charts(staged_database)
    height, texts = chart.figure.get_figheight(), list(chart.figure.texts)
    export_charts([chart], folder, {}, GENERATED, source_files(staged_database))
    assert chart.figure.get_figheight() == height
    assert chart.figure.texts == texts


def test_exporting_changes_no_stored_data(staged_database, folder) -> None:
    before = counts(staged_database)
    export_charts(two_charts(staged_database), folder, {}, GENERATED, {})
    assert counts(staged_database) == before


# --- 4a: the folder is not writable -----------------------------------------------------


def test_a_missing_folder_is_not_writable(staged_database, folder) -> None:
    charts = two_charts(staged_database)
    missing = folder / "missing"
    with pytest.raises(FolderNotWritableError):
        find_conflicts(charts, missing)
    with pytest.raises(FolderNotWritableError):
        export_charts(charts, missing, {}, GENERATED, {})
    assert not missing.exists()


@pytest.mark.skipif(sys.platform == "win32", reason="folder permissions are POSIX modes")
def test_a_read_only_folder_raises_and_no_file_is_written(staged_database, folder) -> None:
    charts = two_charts(staged_database)
    folder = folder / "read-only"
    folder.mkdir()
    folder.chmod(0o500)
    try:
        if os.access(folder, os.W_OK):
            pytest.skip("this user can write to read-only folders")
        with pytest.raises(FolderNotWritableError) as raised:
            find_conflicts(charts, folder)
        assert "Choose a different folder" in raised.value.message
        with pytest.raises(FolderNotWritableError):
            export_charts(charts, folder, {}, GENERATED, {})
        assert list(folder.iterdir()) == []
    finally:
        folder.chmod(0o700)


# --- 5a: a chart fails to export --------------------------------------------------------


def test_when_one_chart_fails_the_others_are_written_and_it_is_listed(
    staged_database, folder, monkeypatch, caplog
) -> None:
    charts = two_charts(staged_database)
    written = folder / "already written.png"
    written.write_bytes(b"kept")
    real_write = export_module._write

    def fail_the_second(chart, path, generated_at, files):
        if chart is charts[1]:
            raise OSError("No space left on device")
        real_write(chart, path, generated_at, files)

    monkeypatch.setattr(export_module, "_write", fail_the_second)
    with caplog.at_level(logging.ERROR):
        summary = export_charts(charts, folder, {}, GENERATED, {})

    assert summary.saved == (folder / file_name(charts[0]),)
    assert [failure.title for failure in summary.failed] == [charts[1].title]
    assert png_size(summary.saved[0])[0] == WIDTH_PIXELS
    assert not (folder / file_name(charts[1])).exists()
    assert written.read_bytes() == b"kept"  # files already there stay
    assert "rejections-by-technology-center-and-type" in caplog.text


def test_a_failed_write_leaves_no_partial_file_and_keeps_the_file_it_was_to_replace(
    staged_database, folder, monkeypatch
) -> None:
    (chart, _) = two_charts(staged_database)
    existing = folder / file_name(chart)
    existing.write_bytes(b"the earlier export")

    def full_disk(*args, **kwargs):
        raise OSError("No space left on device")

    monkeypatch.setattr(type(chart.figure), "savefig", full_disk)
    summary = export_charts([chart], folder, {file_name(chart): Decision.OVERWRITE}, GENERATED, {})

    assert summary.saved == ()
    assert [failure.title for failure in summary.failed] == [chart.title]
    assert existing.read_bytes() == b"the earlier export"
    assert [path.name for path in folder.iterdir()] == [existing.name]


# --- 5b: the file name is taken ---------------------------------------------------------


def test_taken_file_names_are_found(staged_database, folder) -> None:
    charts = two_charts(staged_database)
    (folder / file_name(charts[1])).write_bytes(b"earlier")
    assert find_conflicts(charts, folder) == [file_name(charts[1])]


def test_overwrite_replaces_the_existing_file(staged_database, folder) -> None:
    (chart, _) = two_charts(staged_database)
    existing = folder / file_name(chart)
    existing.write_bytes(b"earlier")

    summary = export_charts([chart], folder, {existing.name: Decision.OVERWRITE}, GENERATED, {})

    assert summary.saved == (existing,)
    assert png_size(existing)[0] == WIDTH_PIXELS
    assert [path.name for path in folder.iterdir()] == [existing.name]


def test_keep_both_keeps_the_existing_file_and_saves_the_new_one_under_another_name(
    staged_database, folder
) -> None:
    (chart, _) = two_charts(staged_database)
    existing = folder / "Office actions by Document Code.png"
    existing.write_bytes(b"earlier")
    (folder / "Office actions by Document Code (2).png").write_bytes(b"earlier too")

    summary = export_charts([chart], folder, {existing.name: Decision.KEEP_BOTH}, GENERATED, {})

    assert summary.saved == (folder / "Office actions by Document Code (3).png",)
    assert existing.read_bytes() == b"earlier"
    assert png_size(summary.saved[0])[0] == WIDTH_PIXELS


def test_a_taken_name_with_no_decision_is_never_overwritten(staged_database, folder) -> None:
    (chart, _) = two_charts(staged_database)
    existing = folder / file_name(chart)
    existing.write_bytes(b"earlier")
    summary = export_charts([chart], folder, {}, GENERATED, {})
    assert existing.read_bytes() == b"earlier"
    assert summary.saved == (folder / "Office actions by Document Code (2).png",)


def test_a_title_is_made_a_safe_file_name(staged_database) -> None:
    chart = draw(
        run_metric(staged_database, "office-actions-by-art-unit", {"technology_center": "3700"})
    )
    assert file_name(chart) == "Office actions by Art Unit, Technology Center 3700.png"
