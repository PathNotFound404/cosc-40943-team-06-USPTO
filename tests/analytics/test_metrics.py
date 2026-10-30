import logging
from datetime import date

import pytest

from patent_intelligence.analytics import (
    METRICS,
    base_query,
    list_metrics,
    run_metric,
    technology_centers,
)
from patent_intelligence.analytics.errors import MetricFailedError, StagedDataMissingError
from tests.analytics.conftest import EXPECTED_BREAKDOWN, EXPECTED_COUNTS
from tests.ingestion.conftest import counts


def parameters_for(metric) -> dict[str, str]:
    return {"technology_center": "3700"} if metric.parameters else {}


# --- Main flow (steps 2 and 5) --------------------------------------------------------


@pytest.mark.parametrize(("name", "parameters"), list(EXPECTED_COUNTS))
def test_each_metric_counts_what_was_counted_by_hand(staged_database, name, parameters) -> None:
    result = run_metric(staged_database, name, dict(parameters))
    assert dict(result.counts) == EXPECTED_COUNTS[(name, parameters)]
    assert result.import_ids == (1,)
    # Technology Center 3700's office actions start a day later than the whole fixture's.
    earliest = date(2026, 10, 14) if parameters else date(2026, 10, 13)
    assert (result.earliest_submission, result.latest_submission) == (earliest, date(2026, 10, 16))


def test_every_metric_in_the_registry_has_a_hand_counted_test() -> None:
    assert {name for name, _ in EXPECTED_COUNTS} == {metric.name for metric in METRICS}


def test_counts_are_largest_first_with_a_missing_value_last(staged_database) -> None:
    result = run_metric(staged_database, "rejections-by-type", {})
    values = [count for _, count in result.counts]
    assert values == sorted(values, reverse=True)
    assert result.counts[-1] == (None, 1)


@pytest.mark.parametrize("metric", METRICS, ids=lambda metric: metric.name)
def test_the_counts_sum_to_the_rows_the_base_query_returns(staged_database, metric) -> None:
    result = run_metric(staged_database, metric.name, parameters_for(metric))
    query, values = base_query(metric.name, parameters_for(metric))
    (rows,) = staged_database.cursor().execute(f"SELECT count(*) FROM ({query})", values).fetchone()
    assert result.total == rows > 0


def test_list_metrics_returns_the_registry_when_the_data_is_staged(staged_database) -> None:
    assert list_metrics(staged_database) == METRICS


def test_the_technology_centers_are_those_staged_in_order(staged_database) -> None:
    assert technology_centers(staged_database) == [
        "1600",
        "1700",
        "2600",
        "2800",
        "2900",
        "3600",
        "3700",
        "3900",
    ]


# --- Two-way metrics -----------------------------------------------------------------


@pytest.mark.parametrize("name", list(EXPECTED_BREAKDOWN))
def test_each_two_way_metric_counts_each_category_and_series_as_counted_by_hand(
    staged_database, name
) -> None:
    result = run_metric(staged_database, name, {})
    breakdown = {(category, series): count for category, series, count in result.breakdown}
    assert breakdown == EXPECTED_BREAKDOWN[name]
    query, values = base_query(name, {})
    (rows,) = staged_database.cursor().execute(f"SELECT count(*) FROM ({query})", values).fetchone()
    assert sum(breakdown.values()) == result.total == rows


@pytest.mark.parametrize("name", list(EXPECTED_BREAKDOWN))
def test_the_base_query_filtered_to_a_segment_returns_that_segments_count(
    staged_database, name
) -> None:
    result = run_metric(staged_database, name, {})
    query, values = base_query(name, {})
    cursor = staged_database.cursor()
    for category, series, count in result.breakdown:
        records = cursor.execute(
            f"SELECT record_id FROM ({query}) WHERE category IS NOT DISTINCT FROM $category "
            "AND series IS NOT DISTINCT FROM $series",
            {**values, "category": category, "series": series},
        ).fetchall()
        assert len(records) == count, (category, series)


def test_one_way_metrics_have_no_breakdown(staged_database) -> None:
    assert run_metric(staged_database, "office-actions-by-document-code", {}).breakdown == ()


def test_the_counted_field_of_a_two_way_metric_names_both_fields() -> None:
    (metric,) = [m for m in METRICS if m.name == "rejections-by-technology-center-and-type"]
    assert metric.counted_field == "USPTO rejection tag, by Technology Center"


# --- No type in the source (BR-no-data-alteration) ------------------------------------


def test_a_rejection_entry_with_no_type_is_counted_and_the_bars_sum_to_the_entries(
    staged_database,
) -> None:
    result = run_metric(staged_database, "rejections-by-type", {})
    (staged_entries,) = (
        staged_database.cursor().execute("SELECT count(*) FROM staged_rejection").fetchone()
    )
    assert dict(result.counts)[None] == 1
    assert result.total == staged_entries == 20


# --- 2a: data is not staged -------------------------------------------------------------


def test_with_no_staged_views_list_metrics_refuses(database) -> None:
    with pytest.raises(StagedDataMissingError):
        list_metrics(database)


def test_with_empty_staged_views_list_metrics_refuses(database) -> None:
    cursor = database.cursor()
    cursor.execute("CREATE VIEW staged_office_action AS SELECT 1 AS record_id WHERE false")
    cursor.execute("CREATE VIEW staged_rejection AS SELECT 1 AS record_id WHERE false")
    with pytest.raises(StagedDataMissingError):
        list_metrics(database)


# --- 5a: a metric fails -----------------------------------------------------------------


def test_a_failing_metric_raises_and_logs_its_name(staged_database, caplog) -> None:
    staged_database.cursor().execute("CREATE OR REPLACE VIEW staged_rejection AS SELECT 1 AS x")
    with caplog.at_level(logging.ERROR), pytest.raises(MetricFailedError) as raised:
        run_metric(staged_database, "rejections-by-type", {})
    assert raised.value.metric_name == "rejections-by-type"
    assert "rejections-by-type" in caplog.text
    assert "Traceback" not in raised.value.message


def test_the_other_metrics_still_run_after_one_fails(staged_database) -> None:
    staged_database.cursor().execute("CREATE OR REPLACE VIEW staged_rejection AS SELECT 1 AS x")
    result = run_metric(staged_database, "office-actions-by-document-code", {})
    assert result.total == 20


@pytest.mark.parametrize(
    ("name", "parameters"),
    [
        ("no-such-metric", {}),
        ("office-actions-by-art-unit", {}),
        ("office-actions-by-document-code", {"technology_center": "3700"}),
    ],
)
def test_an_unknown_metric_or_wrong_parameters_fail(name, parameters) -> None:
    with pytest.raises(MetricFailedError):
        base_query(name, parameters)


# --- 6a: each bar traces to its records (QS-chart-traces-to-records) --------------------


@pytest.mark.parametrize("metric", METRICS, ids=lambda metric: metric.name)
def test_the_base_query_filtered_to_a_bar_returns_that_bars_count(staged_database, metric) -> None:
    result = run_metric(staged_database, metric.name, parameters_for(metric))
    query, values = base_query(metric.name, parameters_for(metric))
    cursor = staged_database.cursor()
    for category, count in result.counts:
        records = cursor.execute(
            f"SELECT record_id FROM ({query}) WHERE category IS NOT DISTINCT FROM $category",
            {**values, "category": category},
        ).fetchall()
        assert len(records) == count, category


# --- Logging (architecture 8.2.7) and no data altered (BR-no-data-alteration) -----------


def test_running_metrics_logs_names_and_counts_only(staged_database, caplog) -> None:
    with caplog.at_level(logging.DEBUG):
        for metric in METRICS:
            run_metric(staged_database, metric.name, parameters_for(metric))
    assert "office-actions-by-document-code" in caplog.text
    assert "TEST-EXAMINER" not in caplog.text


def test_running_metrics_leaves_raw_and_staged_rows_unchanged(staged_database) -> None:
    def staged_rows() -> tuple:
        cursor = staged_database.cursor()
        return tuple(
            cursor.execute(f"SELECT count(*) FROM {view}").fetchone()[0]
            for view in ("staged_office_action", "staged_rejection")
        )

    before = (counts(staged_database), staged_rows())
    for metric in METRICS:
        run_metric(staged_database, metric.name, parameters_for(metric))
    assert (counts(staged_database), staged_rows()) == before
