"""Provenance over a staged fixture (UC-FEAT-verify-source, docs/design/verification.md Tests).
The oracle is the chart itself: the records listed are the records it counted."""

import json
import logging
from pathlib import Path

import pytest

from patent_intelligence import analytics
from patent_intelligence.analytics import METRICS, MetricResult
from patent_intelligence.cleaning import build_staged_dataset
from patent_intelligence.ingestion import import_file
from patent_intelligence.provenance import (
    Selection,
    SourceLookupFailedError,
    SourceUnavailableError,
    record_detail,
    records_for,
)
from tests.analytics.conftest import SECOND_IMPORT_TIME
from tests.ingestion.conftest import (
    FIXTURE,
    IMPORT_TIME,
    counts,
    fixture_records,
    no_progress,
    write_records,
)

ALL_ROWS = 10_000


def parameters(metric) -> dict[str, str]:
    return {"technology_center": "3700"} if metric.parameters else {}


def chart(database, metric) -> MetricResult:
    return analytics.run_metric(database, metric.name, parameters(metric))


def selections(result: MetricResult) -> list[tuple[Selection, int]]:
    """Every bar of a one-way chart, or every segment of a two-way chart, with its value."""
    if result.metric.series_field is None:
        return [(Selection(category), count) for category, count in result.counts]
    return [(Selection(category, series), count) for category, series, count in result.breakdown]


def every_record(database, result, selection) -> list:
    return list(records_for(database, result, selection, 0, ALL_ROWS).records)


# --- Main flow --------------------------------------------------------------------------


@pytest.mark.parametrize("metric", METRICS, ids=lambda metric: metric.name)
def test_every_bar_lists_as_many_records_as_its_value_each_with_its_source(
    staged_database, metric
) -> None:
    result = chart(staged_database, metric)
    bars = selections(result)
    assert bars
    for selection, value in [*bars, (None, result.total)]:
        page = records_for(staged_database, result, selection, 0, ALL_ROWS)
        assert page.total == value
        assert len(page.records) == value
        for record in page.records:
            assert record.source_file == FIXTURE.name
            assert record.import_date == IMPORT_TIME.date()
            assert record.application_number
            if selection is not None:
                expected = (selection.category,)
                if metric.series_field is not None:
                    expected += (selection.series,)
                assert record.counted_values == expected


def test_rows_are_sorted_by_source_file_application_number_and_submission_date(
    two_weeks_database,
) -> None:
    result = chart(two_weeks_database, METRICS[0])
    records = every_record(two_weeks_database, result, None)
    assert len({record.source_file for record in records}) == 2
    keys = [(r.source_file, r.application_number, r.submission_date, r.record_id) for r in records]
    assert keys == sorted(keys)


@pytest.mark.parametrize("metric", METRICS, ids=lambda metric: metric.name)
def test_each_row_shows_the_records_own_readable_fields(staged_database, metric) -> None:
    by_id = {record["id"]: record for record in fixture_records()}
    for row in every_record(staged_database, chart(staged_database, metric), None):
        source = by_id[row.record_id]
        assert row.application_number == source["patentApplicationNumber"]
        assert row.invention_title == source.get("inventionTitle")  # one has none
        assert row.document_code == source["documentCode"]
        assert row.art_unit == str(source["groupArtUnitNumber"])
        assert row.submission_date.isoformat() == source["submissionDate"][:10]


def test_the_bar_for_a_value_the_source_did_not_give_lists_only_its_own_records(
    staged_database,
) -> None:
    result = analytics.run_metric(staged_database, "rejections-by-type", {})
    records = every_record(staged_database, result, Selection(None))
    assert len(records) == 1 < result.total
    assert records[0].counted_values == (None,)


def test_each_row_shows_the_field_the_chart_counted(staged_database) -> None:
    one_way = chart(staged_database, METRICS[0])
    page = records_for(staged_database, one_way, Selection("CTFR"), 0, ALL_ROWS)
    assert page.counted_fields == (one_way.metric.counted_field,) == ("Document Code",)
    assert {record.counted_values for record in page.records} == {("CTFR",)}

    two_way = analytics.run_metric(staged_database, "rejections-by-technology-center-and-type", {})
    page = records_for(staged_database, two_way, Selection("1600", "112"), 0, ALL_ROWS)
    assert page.counted_fields == ("Technology Center", "USPTO rejection tag")
    assert {record.counted_values for record in page.records} == {("1600", "112")}


def test_a_chart_of_chosen_weeks_lists_only_those_weeks(two_weeks_database) -> None:
    result = analytics.run_metric(
        two_weeks_database,
        "office-actions-by-document-code",
        {},
        analytics.Weeks(import_ids=frozenset({2})),
    )
    records = every_record(two_weeks_database, result, None)
    assert len(records) == result.total == 6
    assert {record.source_file for record in records} == {"week_2026-10-25.jsonl"}
    assert {record.import_date for record in records} == {SECOND_IMPORT_TIME.date()}


# --- Read only (POST-2) -----------------------------------------------------------------


def staged_counts(database) -> dict[str, int]:
    cursor = database.cursor()
    return {
        **counts(database),
        **{
            view: cursor.execute(f"SELECT count(*) FROM {view}").fetchone()[0]
            for view in ("staged_office_action", "staged_rejection")
        },
    }


def test_viewing_sources_changes_no_table(staged_database) -> None:
    before = staged_counts(staged_database)
    for metric in METRICS:
        result = chart(staged_database, metric)
        for selection, _ in [*selections(result), (None, 0)]:
            for record in every_record(staged_database, result, selection):
                record_detail(staged_database, record.record_id, record.import_id)
    assert staged_counts(staged_database) == before


# --- 2a: the source data is unavailable -------------------------------------------------


def remove_import(database, import_id: int) -> None:
    """Stands in for deleting a dataset (DI-disposal), which no use case describes yet."""
    cursor = database.cursor()
    for table in ("raw_office_action", "rejected_record", "import_log"):
        cursor.execute(f"DELETE FROM {table} WHERE import_id = ?", [import_id])
    build_staged_dataset(database)


def test_after_an_import_behind_a_chart_is_removed_nothing_is_listed(two_weeks_database) -> None:
    result = chart(two_weeks_database, METRICS[0])
    assert result.import_ids == (1, 2)
    remove_import(two_weeks_database, 2)
    for selection in (None, Selection("CTNF")):
        with pytest.raises(SourceUnavailableError):
            records_for(two_weeks_database, result, selection, 0, ALL_ROWS)


def import_later(database, folder: Path, records: list[dict]) -> None:
    path = write_records(folder / "later.jsonl", records)
    import_file(database, path, SECOND_IMPORT_TIME, no_progress)
    build_staged_dataset(database)


def test_a_chart_whose_records_a_later_import_superseded_is_refused(
    staged_database, tmp_path
) -> None:
    result = chart(staged_database, METRICS[0])
    newer = dict(fixture_records()[5])
    newer["systemLastModifiedTimestamp"] = "2026-10-25T00:00:00.000Z"
    import_later(staged_database, tmp_path, [newer])
    with pytest.raises(SourceUnavailableError):
        records_for(staged_database, result, None, 0, ALL_ROWS)
    with pytest.raises(SourceUnavailableError):
        records_for(staged_database, result, Selection(newer["documentCode"]), 0, ALL_ROWS)


def test_a_later_import_that_supersedes_nothing_leaves_the_chart_listable(
    staged_database, tmp_path
) -> None:
    result = chart(staged_database, METRICS[0])
    new = dict(fixture_records()[0])
    new["id"] = "a-record-imported-later"
    import_later(staged_database, tmp_path, [new])
    page = records_for(staged_database, result, None, 0, ALL_ROWS)
    assert page.total == result.total == 20
    assert {record.source_file for record in page.records} == {FIXTURE.name}


# --- 2b: more records than one page -----------------------------------------------------


def test_pages_hold_one_page_each_and_together_every_row_once(staged_database) -> None:
    result = chart(staged_database, METRICS[0])
    first = records_for(staged_database, result, None, 0, 6)
    assert len(first.records) == 6
    assert first.total == 20
    paged = []
    for offset in range(0, 24, 6):
        page = records_for(staged_database, result, None, offset, 6)
        assert page.total == 20
        paged.extend(page.records)
    assert len(paged) == 20
    assert len({record.record_id for record in paged}) == 20
    assert paged == every_record(staged_database, result, None)


# --- 4a: one record in full -------------------------------------------------------------


def stored_text(value) -> str:
    """How Ingestion stores a JSON value that is not text: as its JSON text."""
    return json.dumps(value)


@pytest.mark.parametrize("index", range(20))
def test_one_record_shows_every_stored_field_as_in_the_file(staged_database, index) -> None:
    source = fixture_records()[index]
    detail = record_detail(staged_database, source["id"], 1)
    assert detail.source_file == FIXTURE.name
    assert detail.import_date == IMPORT_TIME.date()
    fields = dict(detail.fields)
    assert fields["import_id"] == 1
    for name, value in source.items():
        if isinstance(value, str):
            assert fields[name] == value, name  # character for character
        elif isinstance(value, (list, dict)):
            assert json.loads(fields[name]) == value, name
        else:
            assert fields[name] == stored_text(value), name
    absent = set(fields) - set(source) - {"import_id", "line_number"}
    assert all(fields[name] is None for name in absent)


def test_a_record_that_is_not_stored_is_unavailable(staged_database) -> None:
    with pytest.raises(SourceUnavailableError):
        record_detail(staged_database, "no-such-record", 1)
    with pytest.raises(SourceUnavailableError):
        record_detail(staged_database, fixture_records()[0]["id"], 99)


def test_when_an_import_holds_a_record_twice_the_chosen_copy_is_shown(database, tmp_path) -> None:
    older, newer = dict(fixture_records()[0]), dict(fixture_records()[0])
    newer["systemLastModifiedTimestamp"] = "2099-01-01T00:00:00.000Z"
    newer["oaText"] = "the newer copy"
    path = write_records(tmp_path / "twice.jsonl", [newer, older])
    import_file(database, path, IMPORT_TIME, no_progress)
    build_staged_dataset(database)
    assert dict(record_detail(database, newer["id"], 1).fields)["oaText"] == "the newer copy"
    result = analytics.run_metric(database, "office-actions-by-document-code", {})
    (row,) = every_record(database, result, None)  # listed once, not once per copy
    assert row.record_id == newer["id"]


# --- Failure handling and logging (8.2.7) -----------------------------------------------


def test_a_failing_query_raises_and_logs_no_record(staged_database, monkeypatch, caplog) -> None:
    result = chart(staged_database, METRICS[0])
    monkeypatch.setattr(analytics, "base_query", lambda *args: ("SELECT * FROM no_such_view", {}))
    with caplog.at_level(logging.INFO), pytest.raises(SourceLookupFailedError):
        records_for(staged_database, result, None, 0, ALL_ROWS)
    assert METRICS[0].name in caplog.text


def test_listing_and_opening_records_logs_no_record_content(staged_database, caplog) -> None:
    result = chart(staged_database, METRICS[0])
    with caplog.at_level(logging.DEBUG):
        records = every_record(staged_database, result, None)
        for record in records:
            record_detail(staged_database, record.record_id, record.import_id)
    for source in fixture_records():
        for value in (
            source["id"],
            source["patentApplicationNumber"],
            source["examinerEmployeeNumber"],
            source["oaText"][:40],
        ):
            assert value not in caplog.text
