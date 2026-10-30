import importlib
import logging

import pytest

from patent_intelligence.analytics import run_metric
from patent_intelligence.analytics.errors import MetricFailedError
from patent_intelligence.charts import draw
from tests.analytics.conftest import EXPECTED_COUNTS

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
    assert {category: bar.get_width() for bar, category in chart.bars} == expected


def test_the_art_unit_chart_names_its_technology_center(staged_database) -> None:
    chart = draw(
        run_metric(staged_database, "office-actions-by-art-unit", {"technology_center": "3700"})
    )
    assert chart.title == "Office actions by Art Unit, Technology Center 3700"
    assert texts(chart)[0] == chart.title


def test_a_rejection_entry_with_no_type_is_its_own_labeled_bar(staged_database) -> None:
    chart = draw(run_metric(staged_database, "rejections-by-type", {}))
    assert "No USPTO rejection tag in the source" in texts(chart)
    assert sum(bar.get_width() for bar, _ in chart.bars) == 20


def test_the_largest_bar_is_drawn_at_the_top(staged_database) -> None:
    chart = draw(run_metric(staged_database, "office-actions-by-document-code", {}))
    (top_bar, top_category), *_ = chart.bars
    assert top_category == "CTNF"
    assert top_bar.get_y() > max(bar.get_y() for bar, _ in chart.bars[1:])


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
