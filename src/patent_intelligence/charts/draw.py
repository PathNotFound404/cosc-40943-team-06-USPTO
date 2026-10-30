"""Drawing a metric result as a chart (UC-FEAT-create-visuals step 6)."""

import logging
from dataclasses import dataclass

from matplotlib.figure import Figure
from matplotlib.patches import Rectangle

from patent_intelligence.analytics import TECHNOLOGY_CENTER, MetricResult
from patent_intelligence.analytics.errors import MetricFailedError

log = logging.getLogger(__name__)

# One series, so one hue and no legend; text stays in text colors, never the bar color.
_BAR = "#2a78d6"
_SURFACE = "#fcfcfb"
_TEXT = "#0b0b0b"
_TEXT_SECONDARY = "#52514e"
_GRID = "#e4e3df"


@dataclass(eq=False)
class Chart:
    """A drawn metric: the figure, and the result that is its identity (metric, parameters,
    import IDs, counted field, date range). `bars` pairs each bar with its category."""

    result: MetricResult
    figure: Figure
    bars: tuple[tuple[Rectangle, str | None], ...]

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
        return f"No {result.metric.counted_field} in the source"
    return category


def draw(result: MetricResult) -> Chart:
    """Draw `result` as horizontal bars, largest first, naming the counted field on the chart
    (FR-CHART-counted-field). A drawing failure raises MetricFailedError (5a)."""
    try:
        return _draw(result)
    except Exception as error:
        log.exception("Drawing the metric %s failed", result.metric.name)
        raise MetricFailedError(result.metric.name) from error


def _draw(result: MetricResult) -> Chart:
    labels = [category_label(result, category) for category, _ in result.counts]
    values = [count for _, count in result.counts]
    figure = Figure(figsize=(8, max(3.0, 1.6 + 0.32 * len(values))), layout="constrained")
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
    positions = list(range(len(values)))[::-1]  # largest at the top
    container = axes.barh(positions, values, height=0.6, color=_BAR, picker=True)
    axes.bar_label(container, padding=3, color=_TEXT_SECONDARY, fontsize=9)
    axes.set_yticks(positions, labels, color=_TEXT, fontsize=9)
    axes.set_xlabel(result.metric.counts, color=_TEXT_SECONDARY, fontsize=9)
    axes.tick_params(axis="x", colors=_TEXT_SECONDARY, labelsize=9)
    axes.tick_params(axis="y", length=0)
    axes.grid(axis="x", color=_GRID, linewidth=0.8)
    axes.set_axisbelow(True)
    axes.margins(x=0.06)
    for side in ("top", "right", "left"):
        axes.spines[side].set_visible(False)
    axes.spines["bottom"].set_color(_GRID)
    if not values:
        axes.text(
            0.5,
            0.5,
            f"No {result.metric.counts.lower()} to count",
            ha="center",
            transform=axes.transAxes,
            color=_TEXT_SECONDARY,
        )

    bars = tuple(zip(container.patches, (category for category, _ in result.counts), strict=True))
    return Chart(result, figure, bars)
