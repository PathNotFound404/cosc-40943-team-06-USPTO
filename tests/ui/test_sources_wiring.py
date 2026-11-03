"""The chart tabs open the Sources view (UC-FEAT-verify-source step 1, UC-FEAT-create-visuals
6a, docs/design/verification.md Tests)."""

from types import SimpleNamespace

import pytest

from patent_intelligence.app import build_window
from patent_intelligence.jobs.runner import JobRunner
from patent_intelligence.ui.sources_view import SourcesView
from tests.provenance.test_records_for import remove_import
from tests.ui.test_charts_view import all_metrics


def keep_weeks(parent, files, weeks, current):
    return current


def window_with_charts(database):
    runner = JobRunner()
    window = build_window(runner, database, choose=all_metrics, choose_weeks=keep_weeks)
    runner.shutdown()  # nothing in these tests runs a job
    charts_view, sources_view = window.tabs.widget(1), window.tabs.widget(2)
    assert isinstance(sources_view, SourcesView)
    assert window.tabs.tabText(2) == "Sources"
    charts_view.create_visualizations()
    return window, charts_view, sources_view


def chart_named(charts_view, name):
    (chart,) = [chart for chart in charts_view.charts if chart.result.metric.name == name]
    return chart


@pytest.mark.parametrize("name", ["rejections-by-type", "rejections-by-technology-center-and-type"])
def test_clicking_a_bar_opens_the_sources_view_with_that_bars_records(
    qt_app, staged_database, name
) -> None:
    window, charts_view, sources_view = window_with_charts(staged_database)
    chart = chart_named(charts_view, name)
    for bar in chart.bars:
        charts_view._on_pick(chart, SimpleNamespace(artist=bar.patch))
        assert window.tabs.currentWidget() is sources_view
        if chart.result.metric.series_field is None:
            value = dict(chart.result.counts)[bar.category]
            expected = (bar.category,)
        else:
            breakdown = {(c, s): n for c, s, n in chart.result.breakdown}
            value = breakdown[(bar.category, bar.series)]
            expected = (bar.category, bar.series)
        assert sources_view.model.total == value == sources_view.model.rowCount()
        assert {record.counted_values for record in sources_view.model.records} == {expected}


def test_view_source_records_on_a_chart_tab_lists_the_whole_chart(qt_app, staged_database) -> None:
    window, charts_view, sources_view = window_with_charts(staged_database)
    index = next(
        index
        for index, chart in enumerate(charts_view.charts)
        if chart.result.metric.name == "office-actions-by-art-unit"
    )
    charts_view.page(index).view_source.click()
    assert window.tabs.currentWidget() is sources_view
    assert sources_view.model.total == charts_view.charts[index].result.total == 5
    assert "Technology Center 3700" in sources_view.heading.text()


def test_recreating_after_2a_returns_to_creating_visualizations(
    qt_app, two_weeks_database, monkeypatch
) -> None:
    window, charts_view, sources_view = window_with_charts(two_weeks_database)
    chart = charts_view.charts[0]
    remove_import(two_weeks_database, 2)
    created = []
    monkeypatch.setattr(charts_view, "create_visualizations", lambda: created.append(True))
    monkeypatch.setattr(sources_view, "_offer_recreate", lambda parent, message: True)
    charts_view.page(0).view_source.click()
    assert created == [True]
    assert window.tabs.currentWidget() is charts_view
    assert sources_view.model is None
    assert chart is charts_view.charts[0]
