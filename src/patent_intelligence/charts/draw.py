"""Drawing a metric result as a chart (UC-FEAT-create-visuals step 6)."""

import logging
from dataclasses import dataclass

from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle

from patent_intelligence.analytics import TECHNOLOGY_CENTER, MetricResult
from patent_intelligence.analytics.errors import MetricFailedError

log = logging.getLogger(__name__)

# A one-way chart is one series: one hue and no legend. Text stays in text colors, never a
# series color.
_BAR = "#2a78d6"
_SURFACE = "#fcfcfb"
_TEXT = "#0b0b0b"
_TEXT_SECONDARY = "#52514e"
_GRID = "#e4e3df"
# Two-way series colors, in this fixed order (validated for adjacent segments); a value the
# source did not give is gray.
_SERIES_COLORS = (
    "#2a78d6",
    "#eb6834",
    "#1baf7a",
    "#eda100",
    "#e87ba4",
    "#008300",
    "#6250d6",
    "#e34948",
)
_MISSING = "#a3a29c"
# A segment narrower than this share (%) is too small to hold its label.
_LABELED_SHARE = 8


@dataclass(frozen=True)
class Bar:
    """One bar, or one segment of a two-way bar, and what it shows."""

    patch: Rectangle
    category: str | None
    series: str | None = None


@dataclass(eq=False)
class Chart:
    """A drawn metric: the figure, and the result that is its identity (metric, parameters,
    import IDs, counted field, date range)."""

    result: MetricResult
    figure: Figure
    bars: tuple[Bar, ...]

    @property
    def title(self) -> str:
        return chart_title(self.result)


def chart_title(result: MetricResult) -> str:
    title = result.metric.title
    if technology_center := result.parameters.get(TECHNOLOGY_CENTER):
        title += f", Technology Center {technology_center}"
    return title


def category_label(result: MetricResult, category: str | None) -> str:
    """The bar's label; a value the source did not give is named as such, not hidden."""
    if category is None:
        return f"No {result.metric.category_field} in the source"
    return category


def series_label(result: MetricResult, series: str | None) -> str:
    if series is None:
        return f"No {result.metric.series_field} in the source"
    return series


def series_colors(result: MetricResult) -> dict[str | None, str]:
    """Each series' color. Known values keep their place in the metric's order whatever their
    counts; values not listed follow, sorted. More values than colors is a drawing failure
    rather than two series sharing a color."""
    present = {series for _, series, _ in result.breakdown}
    known = list(result.metric.series_order)
    ordered = known + sorted(value for value in present if value is not None and value not in known)
    if len(ordered) > len(_SERIES_COLORS):
        raise ValueError(f"{len(ordered)} series values; at most {len(_SERIES_COLORS)} are drawn")
    colors: dict[str | None, str] = {
        value: _SERIES_COLORS[index] for index, value in enumerate(ordered) if value in present
    }
    if None in present:
        colors[None] = _MISSING
    return colors


def draw(result: MetricResult) -> Chart:
    """Draw `result`, naming the counted field on the chart (FR-CHART-counted-field): one-way
    metrics as horizontal bars, two-way metrics as 100% stacked bars. Largest category first.
    A drawing failure raises MetricFailedError (5a)."""
    try:
        if result.metric.series_field is None:
            return _draw(result)
        return _draw_two_way(result)
    except Exception as error:
        log.exception("Drawing the metric %s failed", result.metric.name)
        raise MetricFailedError(result.metric.name) from error


def _figure(result: MetricResult, rows: int) -> tuple[Figure, Axes]:
    figure = Figure(figsize=(8, max(3.0, 1.6 + 0.32 * rows)), layout="constrained")
    figure.set_facecolor(_SURFACE)
    axes = figure.add_subplot()
    axes.set_facecolor(_SURFACE)
    figure.suptitle(chart_title(result), color=_TEXT, fontsize=13, x=0.02, ha="left")
    axes.set_title(
        f"Counted field: {result.metric.counted_field}",
        color=_TEXT_SECONDARY,
        fontsize=10,
        loc="left",
    )
    axes.tick_params(axis="x", colors=_TEXT_SECONDARY, labelsize=9)
    axes.tick_params(axis="y", length=0)
    axes.grid(axis="x", color=_GRID, linewidth=0.8)
    axes.set_axisbelow(True)
    for side in ("top", "right", "left"):
        axes.spines[side].set_visible(False)
    axes.spines["bottom"].set_color(_GRID)
    if not result.counts:
        axes.text(
            0.5,
            0.5,
            f"No {result.metric.counts.lower()} to count",
            ha="center",
            transform=axes.transAxes,
            color=_TEXT_SECONDARY,
        )
    return figure, axes


def _draw(result: MetricResult) -> Chart:
    figure, axes = _figure(result, len(result.counts))
    labels = [category_label(result, category) for category, _ in result.counts]
    values = [count for _, count in result.counts]
    positions = list(range(len(values)))[::-1]  # largest at the top
    container = axes.barh(positions, values, height=0.6, color=_BAR, picker=True)
    axes.bar_label(container, padding=3, color=_TEXT_SECONDARY, fontsize=9)
    axes.set_yticks(positions, labels, color=_TEXT, fontsize=9)
    axes.set_xlabel(result.metric.counts, color=_TEXT_SECONDARY, fontsize=9)
    axes.margins(x=0.06)
    bars = tuple(
        Bar(patch, category)
        for patch, (category, _) in zip(container.patches, result.counts, strict=True)
    )
    return Chart(result, figure, bars)


def _draw_two_way(result: MetricResult) -> Chart:
    figure, axes = _figure(result, len(result.counts))
    totals = dict(result.counts)
    # Largest at the top.
    position = {category: len(totals) - 1 - row for row, (category, _) in enumerate(result.counts)}
    by_cell = {(category, series): count for category, series, count in result.breakdown}
    colors = series_colors(result)
    left = dict.fromkeys(totals, 0.0)
    bars = []
    for series, color in colors.items():
        for category in totals:
            count = by_cell.get((category, series))
            if not count:
                continue
            share = 100 * count / totals[category]
            (patch,) = axes.barh(
                position[category],
                share,
                left=left[category],
                height=0.6,
                color=color,
                edgecolor=_SURFACE,
                linewidth=1,
                picker=True,
                label=series_label(result, series),
            ).patches
            if share >= _LABELED_SHARE:
                axes.text(
                    left[category] + share / 2,
                    position[category],
                    f"{share:.0f}%",
                    ha="center",
                    va="center",
                    color=_TEXT,
                    fontsize=8,
                )
            left[category] += share
            bars.append(Bar(patch, category, series))
    axes.set_yticks(
        list(position.values()),
        [f"{category_label(result, category)} (n = {totals[category]:,})" for category in totals],
        color=_TEXT,
        fontsize=9,
    )
    axes.set_xlim(0, 100)
    axes.set_xlabel(
        f"Share of {result.metric.counts.lower()} in each {result.metric.category_field} (%)",
        color=_TEXT_SECONDARY,
        fontsize=9,
    )
    # One legend entry per series, in color order.
    handles, labels = axes.get_legend_handles_labels()
    unique = dict(zip(labels, handles, strict=True))
    figure.legend(
        unique.values(),
        unique.keys(),
        loc="outside lower center",
        ncols=min(len(unique), 4),
        frameon=False,
        fontsize=9,
        labelcolor=_TEXT,
    )
    return Chart(result, figure, tuple(bars))
