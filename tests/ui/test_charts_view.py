import logging
from types import SimpleNamespace

import pytest

from patent_intelligence import analytics
from patent_intelligence.analytics import METRICS, base_query
from patent_intelligence.analytics.errors import StagedDataMissingError
from patent_intelligence.jobs.cleaning_job import CleaningJob
from patent_intelligence.jobs.runner import JobRunner
from patent_intelligence.ui.charts_view import ChartsView, MetricChooser
from patent_intelligence.ui.import_view import ImportView
from patent_intelligence.ui.main_window import MainWindow
from tests.ingestion.conftest import counts


class Runner:
    """Records submitted jobs instead of running them."""

    def __init__(self) -> None:
        self.jobs: list = []

    def submit(self, job) -> None:
        self.jobs.append(job)


def all_metrics(parent, metrics, technology_centers):
    return [
        (metric, {"technology_center": "3700"} if metric.parameters else {}) for metric in metrics
    ]


def make_view(database, choose=all_metrics, offer_cleaning=None, drill_down=None):
    calls = SimpleNamespace(offers=[], runner=Runner())

    def offer(parent, message):
        calls.offers.append(message)
        return offer_cleaning

    view = ChartsView(calls.runner, database, choose, offer, drill_down)
    return view, calls


def tab_titles(view: ChartsView) -> list[str]:
    return [view.tabs.tabText(index) for index in range(view.tabs.count())]


def notices(view: ChartsView) -> list[str]:
    return [view.notices.item(row).text() for row in range(view.notices.count())]


# --- Main flow (steps 1-7) --------------------------------------------------------------


def test_creating_all_visualizations_shows_one_tab_per_metric(qt_app, staged_database) -> None:
    view, _ = make_view(staged_database)
    view.create_visualizations()
    assert tab_titles(view) == [chart.title for chart in view.charts]
    assert [chart.result.metric for chart in view.charts] == list(METRICS)
    assert "Office actions by Art Unit, Technology Center 3700" in tab_titles(view)
    assert notices(view) == []


def test_the_chooser_offers_every_metric_checked(qt_app) -> None:
    chooser = MetricChooser(METRICS, ["1600", "3700"])
    assert [checkbox.text() for checkbox in chooser.checkboxes] == [m.title for m in METRICS]
    assert all(checkbox.isChecked() for checkbox in chooser.checkboxes)
    assert chooser.choices()[3] == (METRICS[3], {"technology_center": "1600"})


def test_the_chooser_returns_only_the_checked_metrics_and_the_chosen_center(qt_app) -> None:
    chooser = MetricChooser(METRICS, ["1600", "3700"])
    for checkbox in chooser.checkboxes[:3]:
        checkbox.setChecked(False)
    chooser.technology_center.setCurrentText("3700")
    assert chooser.choices() == [
        (METRICS[3], {"technology_center": "3700"}),
        *((metric, {}) for metric in METRICS[4:]),
    ]


def test_with_no_technology_centers_the_art_unit_metric_cannot_be_chosen(qt_app) -> None:
    chooser = MetricChooser(METRICS, [])
    assert not chooser.checkboxes[3].isEnabled()
    assert METRICS[3] not in [metric for metric, _ in chooser.choices()]


# --- 2a: data is not staged -------------------------------------------------------------


def test_with_nothing_staged_the_view_says_so_and_offers_cleaning(qt_app, database) -> None:
    chooser_calls = []
    view, calls = make_view(
        database,
        choose=lambda *args: chooser_calls.append(args),
        offer_cleaning=True,
    )
    view.create_visualizations()
    message = StagedDataMissingError().message
    assert calls.offers == [message]
    assert notices(view)[0] == message
    assert [type(job) for job in calls.runner.jobs] == [CleaningJob]
    assert chooser_calls == []
    assert view.tabs.count() == 0


def test_declining_to_clean_creates_nothing_and_cleans_nothing(qt_app, database) -> None:
    view, calls = make_view(database, offer_cleaning=False)
    view.create_visualizations()
    assert calls.runner.jobs == []
    assert view.tabs.count() == 0
    assert view.charts == []


# --- 4a: the user cancels ---------------------------------------------------------------


def test_cancelling_the_chooser_creates_no_tabs_and_runs_no_query(
    qt_app, staged_database, monkeypatch
) -> None:
    def no_query(*args):
        raise AssertionError("a metric ran after the chooser was cancelled")

    monkeypatch.setattr(analytics, "run_metric", no_query)
    view, _ = make_view(staged_database, choose=lambda *args: None)
    view.create_visualizations()
    assert view.tabs.count() == 0
    assert view.charts == []


# --- 5a: a metric fails ----------------------------------------------------------------


def test_when_metrics_fail_the_rest_are_drawn_and_the_failures_listed(
    qt_app, staged_database, caplog
) -> None:
    staged_database.cursor().execute("CREATE OR REPLACE VIEW staged_rejection AS SELECT 1 AS x")
    view, _ = make_view(staged_database)
    with caplog.at_level(logging.ERROR):
        view.create_visualizations()

    assert tab_titles(view) == [
        "Office actions by Document Code",
        "Office actions by Technology Center",
        "Office actions by Art Unit, Technology Center 3700",
        "Document Codes by Technology Center",
    ]
    assert notices(view) == [
        "These visualizations could not be created: Rejections by type, "
        "Rejection types by Technology Center. Details were written to the log file."
    ]
    assert "rejections-by-type" in caplog.text
    assert "rejections-by-technology-center-and-type" in caplog.text


# --- 6a: drilling down ------------------------------------------------------------------


@pytest.mark.parametrize(
    "name", ["office-actions-by-document-code", "rejections-by-technology-center-and-type"]
)
def test_selecting_a_bar_hands_its_chart_and_category_to_provenance(
    qt_app, staged_database, name
) -> None:
    selected = []
    view, _ = make_view(
        staged_database,
        drill_down=lambda chart, category, series: selected.append((chart, category, series)),
    )
    view.create_visualizations()
    (chart,) = [chart for chart in view.charts if chart.result.metric.name == name]
    bar = chart.bars[0]

    view._on_pick(chart, SimpleNamespace(artist=bar.patch))

    assert selected == [(chart, bar.category, bar.series)]
    # The records Provenance will list are the bar's own (QS-chart-traces-to-records).
    query, values = base_query(name, dict(chart.result.parameters))
    where = "category IS NOT DISTINCT FROM $category"
    values["category"] = bar.category
    if chart.result.metric.series_field is None:
        expected = dict(chart.result.counts)[bar.category]
    else:
        where += " AND series IS NOT DISTINCT FROM $series"
        values["series"] = bar.series
        expected = {(c, s): n for c, s, n in chart.result.breakdown}[(bar.category, bar.series)]
    cursor = staged_database.cursor()
    (records,) = cursor.execute(f"SELECT count(*) FROM ({query}) WHERE {where}", values).fetchone()
    assert records == expected


# --- Step 7: staged for export ----------------------------------------------------------


def test_every_chart_created_in_the_session_is_kept_and_a_recreated_one_replaced(
    qt_app, staged_database
) -> None:
    choice = [all_metrics(None, METRICS, [])[0]]
    view, _ = make_view(staged_database, choose=lambda *args: choice)
    view.create_visualizations()
    first = view.charts[0]

    view._choose = all_metrics
    view.create_visualizations()

    assert len(view.charts) == len(METRICS) == view.tabs.count()
    assert view.charts[0] is not first
    assert tab_titles(view) == [chart.title for chart in view.charts]


# --- No data altered (BR-no-data-alteration) and smoke ---------------------------------


def test_creating_visualizations_leaves_raw_and_staged_rows_unchanged(
    qt_app, staged_database
) -> None:
    def staged_rows() -> tuple:
        cursor = staged_database.cursor()
        return tuple(
            cursor.execute(f"SELECT count(*) FROM {view}").fetchone()[0]
            for view in ("staged_office_action", "staged_rejection")
        )

    before = (counts(staged_database), staged_rows())
    view, _ = make_view(staged_database)
    view.create_visualizations()
    assert (counts(staged_database), staged_rows()) == before


def test_the_main_window_has_the_visualizations_view(qt_app, database) -> None:
    runner = JobRunner()
    view = ChartsView(runner, database)
    window = MainWindow(ImportView(runner, database), view)
    runner.shutdown()
    assert [window.tabs.tabText(index) for index in range(window.tabs.count())] == [
        "Import",
        "Visualizations",
    ]
