import importlib
import logging

import pytest

from patent_intelligence.analytics import METRICS, MetricResult, run_metric
from patent_intelligence.analytics.errors import MetricFailedError
from patent_intelligence.charts import draw, series_colors
from tests.analytics.conftest import EXPECTED_BREAKDOWN, EXPECTED_COUNTS

# The package exports the function `draw`, which hides the module of the same name.
draw_module = importlib.import_module("patent_intelligence.charts.draw")


def texts(chart) -> list[str]:
    axes = chart.figure.axes[0]
    return [
        chart.figure.get_suptitle(),
        axes.get_title(loc="left"),
        axes.get_xlabel(),
        *(label.get_text() for label in axes.get_yticklabels()),
    ]


# --- Main flow (step 6, FR-CHART-counted-field) -----------------------------------------


@pytest.mark.parametrize(("name", "parameters"), list(EXPECTED_COUNTS))
def test_each_chart_names_its_counted_field_and_shows_the_hand_counted_bars(
    staged_database, name, parameters
) -> None:
    chart = draw(run_metric(staged_database, name, dict(parameters)))
    expected = EXPECTED_COUNTS[(name, parameters)]
    shown = texts(chart)
    assert f"Counted field: {chart.result.metric.counted_field}" in shown
    if chart.result.metric.series_field is None:
        assert {bar.category: bar.patch.get_width() for bar in chart.bars} == expected
    else:
        assert {bar.category for bar in chart.bars} == set(expected)


def test_the_art_unit_chart_names_its_technology_center(staged_database) -> None:
    chart = draw(
        run_metric(staged_database, "office-actions-by-art-unit", {"technology_center": "3700"})
    )
    assert chart.title == "Office actions by Art Unit, Technology Center 3700"
    assert texts(chart)[0] == chart.title


def test_a_rejection_entry_with_no_type_is_its_own_labeled_bar(staged_database) -> None:
    chart = draw(run_metric(staged_database, "rejections-by-type", {}))
    assert "No USPTO rejection tag in the source" in texts(chart)
    assert sum(bar.patch.get_width() for bar in chart.bars) == 20


def test_the_largest_bar_is_drawn_at_the_top(staged_database) -> None:
    chart = draw(run_metric(staged_database, "office-actions-by-document-code", {}))
    top, *rest = chart.bars
    assert top.category == "CTNF"
    assert top.patch.get_y() > max(bar.patch.get_y() for bar in rest)


# --- Two-way charts -------------------------------------------------------------------


@pytest.mark.parametrize("name", list(EXPECTED_BREAKDOWN))
def test_each_segment_is_its_share_of_the_technology_center_counted_by_hand(
    staged_database, name
) -> None:
    chart = draw(run_metric(staged_database, name, {}))
    totals = EXPECTED_COUNTS[(name, ())]
    shares = {(bar.category, bar.series): bar.patch.get_width() for bar in chart.bars}
    assert shares == pytest.approx(
        {cell: 100 * count / totals[cell[0]] for cell, count in EXPECTED_BREAKDOWN[name].items()}
    )
    for category in totals:
        in_category = [width for (c, _), width in shares.items() if c == category]
        assert sum(in_category) == pytest.approx(100)


def test_a_two_way_chart_shows_each_categorys_n_and_a_legend_of_series(staged_database) -> None:
    chart = draw(run_metric(staged_database, "rejections-by-technology-center-and-type", {}))
    assert "1600 (n = 8)" in texts(chart)
    (legend,) = chart.figure.legends
    assert [text.get_text() for text in legend.get_texts()] == [
        "101",
        "102",
        "103",
        "112",
        "Other",
        "No USPTO rejection tag in the source",
    ]


def two_way_result(breakdown) -> MetricResult:
    (metric,) = [m for m in METRICS if m.name == "rejections-by-technology-center-and-type"]
    totals: dict = {}
    for category, _, count in breakdown:
        totals[category] = totals.get(category, 0) + count
    return MetricResult(metric, {}, tuple(totals.items()), (1,), None, None, tuple(breakdown))


def test_a_series_keeps_its_color_when_the_counts_change_order() -> None:
    week_one = series_colors(two_way_result([("1600", "101", 9), ("1600", "103", 1)]))
    week_two = series_colors(
        two_way_result([("1600", "101", 1), ("1600", "103", 9), ("1600", "102", 5)])
    )
    assert week_one["101"] == week_two["101"]
    assert week_one["103"] == week_two["103"]


def test_a_missing_series_is_gray_and_an_unlisted_one_gets_its_own_color() -> None:
    colors = series_colors(
        two_way_result([("1600", None, 1), ("1600", "NewType", 2), ("1600", "103", 3)])
    )
    assert colors[None] == "#a3a29c"
    assert len(set(colors.values())) == 3


# --- 5a: drawing fails ------------------------------------------------------------------


def test_a_drawing_failure_is_a_failed_metric(staged_database, monkeypatch, caplog) -> None:
    result = run_metric(staged_database, "office-actions-by-document-code", {})

    def broken(result):
        raise ValueError("bad figure")

    monkeypatch.setattr(draw_module, "_draw", broken)
    with caplog.at_level(logging.ERROR), pytest.raises(MetricFailedError) as raised:
        draw(result)
    assert raised.value.metric_name == "office-actions-by-document-code"
    assert "office-actions-by-document-code" in caplog.text
