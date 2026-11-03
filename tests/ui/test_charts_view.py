import logging
from types import SimpleNamespace

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialogButtonBox

from patent_intelligence import analytics
from patent_intelligence.analytics import ALL_WEEKS, METRICS, Weeks, base_query
from patent_intelligence.analytics.errors import MetricFailedError, StagedDataMissingError
from patent_intelligence.jobs.cleaning_job import CleaningJob
from patent_intelligence.jobs.runner import JobRunner
from patent_intelligence.ui.charts_view import ChartsView, MetricChooser, WeekChooser, WeekFilter
from patent_intelligence.ui.import_view import ImportView
from patent_intelligence.ui.main_window import MainWindow
from tests.analytics.conftest import TWO_WEEK_DOCUMENT_CODES, WEEK_1, WEEK_2
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

    def keep_weeks(parent, files, weeks, current):
        return current

    view = ChartsView(calls.runner, database, choose, offer, drill_down, keep_weeks)
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


# --- 6b: choosing the weeks every chart counts, and the Technology Center on its tab ------


WEEK_CHOICES = {
    "all": ALL_WEEKS,
    "import 2": Weeks(import_ids=frozenset({2})),
    "week 1": Weeks(submission_weeks=frozenset({WEEK_1})),
    "week 2": Weeks(submission_weeks=frozenset({WEEK_2})),
}


def only(*names: str):
    """A chooser that picks these metrics, the Art Unit metric for Technology Center 1600."""
    return lambda parent, metrics, centers: [
        (metric, {"technology_center": "1600"} if metric.parameters else {})
        for metric in metrics
        if metric.name in names
    ]


def weeks_view(database, weeks=ALL_WEEKS, choose=None, drill_down=None):
    asked = []

    def choose_weeks(parent, files, offered_weeks, current):
        asked.append(("weeks", files, offered_weeks, current))
        return weeks

    def choose_metrics(parent, metrics, centers):
        asked.append(("metrics",))
        return (choose or all_metrics)(parent, metrics, centers)

    view = ChartsView(
        Runner(), database, choose_metrics, lambda *args: False, drill_down, choose_weeks
    )
    return view, asked


def check(week_filter, mode: int, unchecked_rows: tuple[int, ...] = ()) -> None:
    week_filter.mode.setCurrentIndex(mode)
    for row in unchecked_rows:
        week_filter.choices.item(row).setCheckState(Qt.CheckState.Unchecked)


def choice_labels(week_filter) -> list[str]:
    choices = week_filter.choices
    return [choices.item(row).text() for row in range(choices.count())]


def checked_rows(week_filter) -> list[int]:
    choices = week_filter.choices
    return [
        row
        for row in range(choices.count())
        if choices.item(row).checkState() == Qt.CheckState.Checked
    ]


def document_codes(view) -> dict:
    (chart,) = [c for c in view.charts if c.result.metric.name == "office-actions-by-document-code"]
    return dict(chart.result.counts)


def test_creating_asks_for_the_weeks_before_the_visualizations(qt_app, two_weeks_database) -> None:
    view, asked = weeks_view(two_weeks_database)
    view.create_visualizations()
    assert [step[0] for step in asked] == ["weeks", "metrics"]
    _, files, weeks, current = asked[0]
    assert [file.import_id for file in files] == [1, 2]
    assert [week.monday for week in weeks] == [WEEK_1, WEEK_2]
    assert current == ALL_WEEKS


def test_cancelling_the_weeks_question_creates_nothing(qt_app, two_weeks_database) -> None:
    view, asked = weeks_view(two_weeks_database, weeks=None)
    view.create_visualizations()
    assert [step[0] for step in asked] == ["weeks"]
    assert view.charts == []
    assert view.tabs.count() == 0


def test_cancelling_the_visualizations_keeps_the_weeks_charted_before(
    qt_app, two_weeks_database
) -> None:
    view, _ = weeks_view(two_weeks_database, weeks=WEEK_CHOICES["week 2"], choose=lambda *a: None)
    view.create_visualizations()
    assert view.weeks == ALL_WEEKS
    assert view.week_filter.isHidden()


@pytest.mark.parametrize("choice", list(WEEK_CHOICES))
def test_the_weeks_chosen_first_are_counted_by_every_chart(
    qt_app, two_weeks_database, choice
) -> None:
    view, _ = weeks_view(two_weeks_database, weeks=WEEK_CHOICES[choice])
    view.create_visualizations()
    assert len(view.charts) == len(METRICS)
    assert all(chart.result.weeks == WEEK_CHOICES[choice] for chart in view.charts)
    assert document_codes(view) == TWO_WEEK_DOCUMENT_CODES[choice]
    assert not view.week_filter.isHidden()
    assert view.week_filter.weeks() == WEEK_CHOICES[choice]


def test_the_weeks_question_lists_the_files_and_weeks_all_checked(
    qt_app, two_weeks_database
) -> None:
    files = analytics.imported_files(two_weeks_database)
    weeks = analytics.submission_weeks(two_weeks_database)
    dialog = WeekChooser(files, weeks, ALL_WEEKS)
    week_filter = dialog.week_filter
    assert week_filter.mode.currentText() == "All imported data"
    assert week_filter.choices.isHidden()

    check(week_filter, WeekFilter.IMPORTED_FILES)
    assert choice_labels(week_filter) == [
        "office_actions_20.jsonl, imported 2026-10-28 "
        "(19 office actions, submitted 2026-10-13 to 2026-10-16)",
        "week_2026-10-25.jsonl, imported 2026-11-04 "
        "(6 office actions, submitted 2026-10-15 to 2026-10-23)",
    ]
    assert checked_rows(week_filter) == [0, 1]
    check(week_filter, WeekFilter.CALENDAR_WEEKS)
    assert choice_labels(week_filter) == [
        "2026-10-12 to 2026-10-18 (20 office actions)",
        "2026-10-19 to 2026-10-25 (5 office actions)",
    ]
    assert checked_rows(week_filter) == [0, 1]


def test_the_weeks_question_starts_at_the_weeks_charted_now(qt_app, two_weeks_database) -> None:
    files = analytics.imported_files(two_weeks_database)
    weeks = analytics.submission_weeks(two_weeks_database)
    dialog = WeekChooser(files, weeks, WEEK_CHOICES["week 2"])
    assert dialog.week_filter.mode.currentIndex() == WeekFilter.CALENDAR_WEEKS
    assert checked_rows(dialog.week_filter) == [1]
    assert dialog.week_filter.weeks() == WEEK_CHOICES["week 2"]


def test_ok_and_apply_need_at_least_one_box_checked(qt_app, two_weeks_database) -> None:
    files = analytics.imported_files(two_weeks_database)
    weeks = analytics.submission_weeks(two_weeks_database)
    dialog = WeekChooser(files, weeks, ALL_WEEKS)
    ok = dialog.buttons.button(QDialogButtonBox.StandardButton.Ok)
    check(dialog.week_filter, WeekFilter.IMPORTED_FILES, (0, 1))
    assert not ok.isEnabled()
    dialog.week_filter.choices.item(0).setCheckState(Qt.CheckState.Checked)
    assert ok.isEnabled()

    view, _ = weeks_view(two_weeks_database)
    view.create_visualizations()
    check(view.week_filter, WeekFilter.CALENDAR_WEEKS, (0, 1))
    assert not view.apply_weeks.isEnabled()
    check(view.week_filter, WeekFilter.ALL)
    assert view.apply_weeks.isEnabled()


@pytest.mark.parametrize(
    ("mode", "unchecked", "expected"),
    [
        (WeekFilter.IMPORTED_FILES, (0,), "import 2"),
        (WeekFilter.CALENDAR_WEEKS, (0,), "week 2"),
        (WeekFilter.CALENDAR_WEEKS, (1,), "week 1"),
        (WeekFilter.ALL, (), "all"),
    ],
)
def test_changing_the_weeks_above_the_tabs_recounts_every_chart(
    qt_app, two_weeks_database, mode, unchecked, expected
) -> None:
    view, _ = weeks_view(two_weeks_database, weeks=WEEK_CHOICES["import 2"])
    view.create_visualizations()
    titles = tab_titles(view)

    check(view.week_filter, mode, unchecked)
    view.apply_weeks.click()

    assert all(chart.result.weeks == WEEK_CHOICES[expected] for chart in view.charts)
    assert document_codes(view) == TWO_WEEK_DOCUMENT_CODES[expected]
    for index, chart in enumerate(view.charts):
        assert view.page(index).scroll.widget().figure is chart.figure
    assert tab_titles(view) == titles
    assert notices(view) == []


def test_charts_created_later_bring_those_shown_to_the_same_weeks(
    qt_app, two_weeks_database
) -> None:
    view, _ = weeks_view(two_weeks_database, choose=only("office-actions-by-document-code"))
    view.create_visualizations()
    assert document_codes(view) == TWO_WEEK_DOCUMENT_CODES["all"]

    later, _ = weeks_view(two_weeks_database, weeks=WEEK_CHOICES["week 2"])
    view._choose_weeks = later._choose_weeks
    view._choose = only("office-actions-by-technology-center")
    view.create_visualizations()

    assert [chart.result.weeks for chart in view.charts] == [WEEK_CHOICES["week 2"]] * 2
    assert document_codes(view) == TWO_WEEK_DOCUMENT_CODES["week 2"]


def test_if_recounting_fails_a_chart_keeps_what_it_showed_and_the_user_is_told(
    qt_app, two_weeks_database, monkeypatch
) -> None:
    view, _ = weeks_view(two_weeks_database, choose=only("office-actions-by-document-code"))
    view.create_visualizations()
    shown = view.charts[0]

    def fail(database, name, parameters, weeks):
        raise MetricFailedError(name)

    monkeypatch.setattr(analytics, "run_metric", fail)
    check(view.week_filter, WeekFilter.CALENDAR_WEEKS, (0,))
    view.apply_weeks.click()

    assert view.charts == [shown]
    assert view.page(0).scroll.widget().figure is shown.figure
    assert notices(view) == [
        "These visualizations could not be counted for the chosen weeks and still show the "
        "weeks they counted before: Office actions by Document Code. "
        "Details were written to the log file."
    ]


def test_drilling_down_after_choosing_weeks_lists_only_those_weeks_records(
    qt_app, two_weeks_database
) -> None:
    selected = []
    view, _ = weeks_view(
        two_weeks_database,
        weeks=WEEK_CHOICES["import 2"],
        choose=only("office-actions-by-document-code"),
        drill_down=lambda chart, category, series: selected.append((chart, category)),
    )
    view.create_visualizations()
    check(view.week_filter, WeekFilter.CALENDAR_WEEKS, (0,))
    view.apply_weeks.click()
    chart = view.charts[0]
    bar = chart.bars[0]

    # Through the redrawn canvas, so its drill-down is wired.
    view.page(0).scroll.widget().callbacks.process("pick_event", SimpleNamespace(artist=bar.patch))

    assert selected == [(chart, bar.category)]
    query, values = base_query(chart.result.metric.name, {}, chart.result.weeks)
    values["category"] = bar.category
    (records,) = (
        two_weeks_database.cursor()
        .execute(f"SELECT count(*) FROM ({query}) WHERE category = $category", values)
        .fetchone()
    )
    assert records == dict(chart.result.counts)[bar.category] == 3


def art_unit_view(database, weeks=ALL_WEEKS):
    view, _ = weeks_view(
        database,
        weeks=weeks,
        choose=only("office-actions-by-document-code", "office-actions-by-art-unit"),
    )
    view.create_visualizations()
    return view, 1  # the Art Unit tab's index


def test_only_the_art_unit_tab_offers_the_technology_centers(qt_app, two_weeks_database) -> None:
    view, art_unit = art_unit_view(two_weeks_database)
    assert view.page(0).technology_center is None
    combo = view.page(art_unit).technology_center
    assert [combo.itemText(i) for i in range(combo.count())] == analytics.technology_centers(
        two_weeks_database
    )
    assert combo.currentText() == "1600"


def test_changing_the_technology_center_on_the_tab_redraws_it_over_the_same_weeks(
    qt_app, two_weeks_database
) -> None:
    view, art_unit = art_unit_view(two_weeks_database, weeks=WEEK_CHOICES["week 1"])
    other = view.charts[0]

    view.page(art_unit).technology_center.setCurrentText("3700")

    chart = view.charts[art_unit]
    assert chart.result.parameters == {"technology_center": "3700"}
    assert chart.result.weeks == WEEK_CHOICES["week 1"]
    expected = analytics.run_metric(
        two_weeks_database,
        "office-actions-by-art-unit",
        {"technology_center": "3700"},
        WEEK_CHOICES["week 1"],
    )
    assert chart.result.counts == expected.counts
    assert view.page(art_unit).scroll.widget().figure is chart.figure
    assert view.tabs.tabText(art_unit) == "Office actions by Art Unit, Technology Center 3700"
    assert view.charts[0] is other


def test_if_a_technology_center_cannot_be_counted_the_tab_keeps_its_chart(
    qt_app, two_weeks_database, monkeypatch
) -> None:
    view, art_unit = art_unit_view(two_weeks_database)
    shown = view.charts[art_unit]

    def fail(database, name, parameters, weeks):
        raise MetricFailedError(name)

    monkeypatch.setattr(analytics, "run_metric", fail)
    view.page(art_unit).technology_center.setCurrentText("3700")

    assert view.charts[art_unit] is shown
    assert view.page(art_unit).technology_center.currentText() == "1600"
    assert notices(view) == [
        "Office actions by Art Unit could not be counted for Technology Center 3700. "
        "Details were written to the log file."
    ]


def test_creating_the_art_unit_chart_again_replaces_its_one_tab(qt_app, two_weeks_database) -> None:
    view, art_unit = art_unit_view(two_weeks_database)
    view.page(art_unit).technology_center.setCurrentText("3700")
    view._choose = only("office-actions-by-art-unit")
    view.create_visualizations()
    assert view.tabs.count() == len(view.charts) == 2
    assert view.charts[art_unit].result.parameters == {"technology_center": "1600"}
    assert view.page(art_unit).technology_center.currentText() == "1600"
