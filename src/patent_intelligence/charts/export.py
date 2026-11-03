"""Writing charts to labeled PNG files (UC-FEAT-export-visuals steps 4-6, INT-export).

Each chart is drawn again from its result, so the figure on screen is never changed, and its
label is drawn into the image below the chart, where it survives being copied into a post."""

import logging
import os
import re
import tempfile
import textwrap
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from enum import Enum
from io import BytesIO
from pathlib import Path

from matplotlib import image
from matplotlib.figure import Figure

from patent_intelligence.charts.draw import Chart, draw
from patent_intelligence.charts.errors import FolderNotWritableError

log = logging.getLogger(__name__)

# Sized for a LinkedIn post (INT-export): a fixed width, and the height the chart needs.
WIDTH_PIXELS = 1200
_LABEL_LINE_INCHES = 0.2
_LABEL_PADDING_INCHES = 0.25
_LABEL_WRAP = 110  # characters per label line
_TEXT_SECONDARY = "#52514e"
# Characters a file name may not hold on macOS or Windows.
_NOT_IN_FILE_NAMES = re.compile(r'[<>:"/\\|?*]')


class Decision(Enum):
    """What to do when a chart's file name is already taken in the folder (5b1)."""

    OVERWRITE = "overwrite"
    KEEP_BOTH = "keep both"


@dataclass(frozen=True)
class ExportFailure:
    title: str
    reason: str


@dataclass(frozen=True)
class ExportSummary:
    """Each file saved, and each chart that could not be (step 6, 5a2)."""

    saved: tuple[Path, ...]
    failed: tuple[ExportFailure, ...]


def file_name(chart: Chart) -> str:
    """The chart's file name: its title, as a PNG."""
    return _NOT_IN_FILE_NAMES.sub("-", chart.title) + ".png"


def find_conflicts(charts: Sequence[Chart], folder: Path) -> list[str]:
    """The charts' file names already taken in `folder` (5b). Raises FolderNotWritableError
    when the folder cannot be written to (4a)."""
    _check_writable(folder)
    return [name for name in map(file_name, charts) if (folder / name).exists()]


def export_charts(
    charts: Sequence[Chart],
    folder: Path,
    decisions: Mapping[str, Decision],
    generated_at: date,
    source_files: Mapping[int, str],
) -> ExportSummary:
    """Write each chart to `folder` as a labeled PNG (step 5). A taken file name is replaced
    or kept by its decision; with none, it is kept. A chart that fails is listed in the
    summary and the rest are still written (5a); files already written stay. `source_files`
    names the weekly file of each import ID, for the label's data source. Raises
    FolderNotWritableError before writing anything (4a)."""
    _check_writable(folder)
    saved: list[Path] = []
    failed: list[ExportFailure] = []
    for chart in charts:
        name = file_name(chart)
        path = folder / name
        if path.exists() and decisions.get(name) is not Decision.OVERWRITE:
            path = _free_path(path)
        try:
            _write(chart, path, generated_at, source_files)
        except Exception:
            log.exception("Exporting the visualization %s failed", chart.result.metric.name)
            failed.append(
                ExportFailure(
                    chart.title,
                    "The file could not be written. Details were written to the log file.",
                )
            )
            continue
        saved.append(path)
    log.info("Exported %d visualizations; %d failed", len(saved), len(failed))
    return ExportSummary(tuple(saved), tuple(failed))


def label_lines(chart: Chart, generated_at: date, source_files: Mapping[int, str]) -> list[str]:
    """The label drawn below the chart: data source, date range, and generation date. The
    title and counted field are already on the chart (FR-CHART-counted-field)."""
    result = chart.result
    files = [source_files.get(import_id, f"import {import_id}") for import_id in result.import_ids]
    source = "Data source: USPTO weekly office action "
    source += ("file " if len(files) == 1 else "files ") + ", ".join(files)
    if not files:
        source = "Data source: no USPTO weekly office action file holds records for this chart"
    if result.earliest_submission is None:
        dates = "Date range: no Submission Date in the source"
    else:
        dates = (
            f"Date range: Submission Date {result.earliest_submission} "
            f"to {result.latest_submission}"
        )
    return [
        *textwrap.wrap(source, _LABEL_WRAP),
        dates,
        f"Generated {generated_at.isoformat()}",
    ]


def labeled_figure(chart: Chart, generated_at: date, source_files: Mapping[int, str]) -> Figure:
    """A new figure: the chart drawn again from its result, as pixels, with its label in a
    strip below it, so the chart's own layout (a two-way legend included) never overlaps the
    label."""
    drawn = draw(chart.result).figure
    dpi = WIDTH_PIXELS / drawn.get_figwidth()
    buffer = BytesIO()
    drawn.savefig(buffer, format="png", dpi=dpi, facecolor=drawn.get_facecolor())
    buffer.seek(0)
    pixels = image.imread(buffer, format="png")
    lines = label_lines(chart, generated_at, source_files)
    label_pixels = round(dpi * (_LABEL_PADDING_INCHES + _LABEL_LINE_INCHES * len(lines)))
    height_pixels = pixels.shape[0] + label_pixels
    figure = Figure(
        figsize=(WIDTH_PIXELS / dpi, height_pixels / dpi), dpi=dpi, facecolor=drawn.get_facecolor()
    )
    figure.figimage(pixels, xo=0, yo=label_pixels, origin="upper")
    figure.text(
        0.02,
        (dpi * _LABEL_PADDING_INCHES / 2) / height_pixels,
        "\n".join(lines),
        ha="left",
        va="bottom",
        color=_TEXT_SECONDARY,
        fontsize=9,
        linespacing=1.5,
    )
    return figure


def _write(chart: Chart, path: Path, generated_at: date, source_files: Mapping[int, str]) -> None:
    """Write to a temporary file and move it into place, so a failed write never leaves a
    partial file or destroys the file it was to replace."""
    figure = labeled_figure(chart, generated_at, source_files)
    handle, temporary = tempfile.mkstemp(dir=path.parent, suffix=".png.partial")
    os.close(handle)
    try:
        figure.savefig(
            temporary,
            format="png",
            dpi=figure.dpi,  # the dpi the chart's pixels were placed at
            facecolor=figure.get_facecolor(),
        )
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def _free_path(path: Path) -> Path:
    """Keep both: the next name not taken, numbered as macOS Finder does."""
    number = 2
    while (candidate := path.with_name(f"{path.stem} ({number}){path.suffix}")).exists():
        number += 1
    return candidate


def _check_writable(folder: Path) -> None:
    """4a: the folder exists and a file can be written in it. A disk with no space left
    fails this write; one that fills part way through fails that chart (5a)."""
    if not folder.is_dir():
        raise FolderNotWritableError(folder)
    try:
        with tempfile.TemporaryFile(dir=folder) as probe:
            probe.write(b"\0")
            probe.flush()
    except OSError as error:
        raise FolderNotWritableError(folder) from error
