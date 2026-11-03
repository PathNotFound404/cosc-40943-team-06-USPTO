"""Choosing the weeks a chart counts (UC-FEAT-create-visuals 6b)."""

from datetime import date

import pytest

from patent_intelligence.analytics import (
    ALL_WEEKS,
    METRICS,
    ImportedFile,
    SubmissionWeek,
    Weeks,
    base_query,
    imported_files,
    run_metric,
    submission_weeks,
)
from patent_intelligence.cleaning.staging import STAGED_VIEWS
from tests.analytics.conftest import (
    SECOND_IMPORT_TIME,
    TWO_WEEK_DOCUMENT_CODES,
    WEEK_1,
    WEEK_2,
    WEEK_2_REJECTIONS,
)
from tests.ingestion.conftest import IMPORT_TIME

CHOICES = {
    "all": ALL_WEEKS,
    "import 1": Weeks(import_ids=frozenset({1})),
    "import 2": Weeks(import_ids=frozenset({2})),
    "week 1": Weeks(submission_weeks=frozenset({WEEK_1})),
    "week 2": Weeks(submission_weeks=frozenset({WEEK_2})),
}


def parameters_for(metric) -> dict[str, str]:
    # 1600 has office actions in both imports and both weeks.
    return {"technology_center": "1600"} if metric.parameters else {}


def test_each_import_is_listed_with_the_office_actions_staged_from_it(
    two_weeks_database,
) -> None:
    assert imported_files(two_weeks_database) == [
        ImportedFile(
            1,
            "office_actions_20.jsonl",
            IMPORT_TIME.replace(tzinfo=None),
            19,
            date(2026, 10, 13),
            date(2026, 10, 16),
        ),
        ImportedFile(
            2,
            "week_2026-10-25.jsonl",
            SECOND_IMPORT_TIME.replace(tzinfo=None),
            6,
            date(2026, 10, 15),
            date(2026, 10, 23),
        ),
    ]


def test_each_calendar_week_of_submission_date_is_listed_monday_first(
    two_weeks_database,
) -> None:
    assert submission_weeks(two_weeks_database) == [
        SubmissionWeek(WEEK_1, 20),
        SubmissionWeek(WEEK_2, 5),
    ]


@pytest.mark.parametrize("choice", list(CHOICES))
def test_a_chart_counts_only_the_chosen_weeks(two_weeks_database, choice) -> None:
    result = run_metric(two_weeks_database, "office-actions-by-document-code", {}, CHOICES[choice])
    assert dict(result.counts) == TWO_WEEK_DOCUMENT_CODES[choice]
    assert result.weeks == CHOICES[choice]


def test_several_imports_or_weeks_can_be_chosen_together(two_weeks_database) -> None:
    for weeks in (
        Weeks(import_ids=frozenset({1, 2})),
        Weeks(submission_weeks=frozenset({WEEK_1, WEEK_2})),
    ):
        result = run_metric(two_weeks_database, "office-actions-by-document-code", {}, weeks)
        assert dict(result.counts) == TWO_WEEK_DOCUMENT_CODES["all"]


def test_what_a_chart_covers_follows_the_chosen_weeks(two_weeks_database) -> None:
    result = run_metric(
        two_weeks_database, "office-actions-by-document-code", {}, CHOICES["week 2"]
    )
    assert result.import_ids == (2,)
    assert (result.earliest_submission, result.latest_submission) == (
        date(2026, 10, 20),
        date(2026, 10, 23),
    )


def test_rejection_entries_are_chosen_by_their_office_action_week(two_weeks_database) -> None:
    result = run_metric(two_weeks_database, "rejections-by-type", {}, CHOICES["week 2"])
    assert dict(result.counts) == WEEK_2_REJECTIONS


@pytest.mark.parametrize("metric", METRICS, ids=lambda metric: metric.name)
@pytest.mark.parametrize("choice", ["import 2", "week 1"])
def test_the_base_query_lists_exactly_what_the_chart_counted(
    two_weeks_database, metric, choice
) -> None:
    weeks = CHOICES[choice]
    result = run_metric(two_weeks_database, metric.name, parameters_for(metric), weeks)
    query, values = base_query(metric.name, parameters_for(metric), weeks)
    cursor = two_weeks_database.cursor()
    (rows,) = cursor.execute(f"SELECT count(*) FROM ({query})", values).fetchone()
    assert result.total == rows
    assert rows < run_metric(two_weeks_database, metric.name, parameters_for(metric)).total


def test_office_actions_with_no_submission_date_can_be_chosen_not_dropped(
    two_weeks_database,
) -> None:
    # Ingestion refuses a missing Submission Date, but the staged view leaves one it cannot
    # read empty; stand one in for that.
    cursor = two_weeks_database.cursor()
    cursor.execute(
        "CREATE OR REPLACE VIEW staged_office_action AS SELECT * REPLACE ("
        "CASE WHEN record_id LIKE '%-week-2' THEN NULL ELSE submission_date END "
        f"AS submission_date) FROM ({STAGED_VIEWS['staged_office_action']})"
    )
    assert submission_weeks(two_weeks_database) == [
        SubmissionWeek(WEEK_1, 20),
        SubmissionWeek(None, 5),
    ]
    undated = run_metric(
        two_weeks_database,
        "office-actions-by-document-code",
        {},
        Weeks(submission_weeks=frozenset({None})),
    )
    assert dict(undated.counts) == TWO_WEEK_DOCUMENT_CODES["week 2"]
    first_week = run_metric(
        two_weeks_database, "office-actions-by-document-code", {}, CHOICES["week 1"]
    )
    assert dict(first_week.counts) == TWO_WEEK_DOCUMENT_CODES["week 1"]


def test_weeks_are_chosen_one_way_at_a_time() -> None:
    with pytest.raises(ValueError, match="not both"):
        Weeks(import_ids=frozenset({1}), submission_weeks=frozenset({WEEK_1}))
