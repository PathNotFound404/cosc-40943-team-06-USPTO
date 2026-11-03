"""The Sources view (UC-FEAT-verify-source, docs/design/verification.md Tests)."""

from types import SimpleNamespace

from patent_intelligence import analytics, provenance
from patent_intelligence.provenance import Selection, SourceLookupFailedError
from patent_intelligence.ui.sources_view import SourcesView
from tests.ingestion.conftest import FIXTURE, IMPORT_TIME, fixture_records
from tests.provenance.test_records_for import remove_import


def make_view(database, recreate_answer=False, page_size=200):
    calls = SimpleNamespace(offers=[], recreated=0)

    def offer(parent, message):
        calls.offers.append(message)
        return recreate_answer

    def recreate():
        calls.recreated += 1

    return SourcesView(database, recreate, offer, page_size), calls


def document_codes(database):
    return analytics.run_metric(database, "office-actions-by-document-code", {})


def shown_rows(view) -> list[tuple[str, ...]]:
    return [view.model.row_text(row) for row in range(view.model.rowCount())]


# --- Main flow (steps 1-3) --------------------------------------------------------------


def test_a_bar_lists_its_records_with_the_counted_field_source_file_and_import_date(
    qt_app, staged_database
) -> None:
    view, calls = make_view(staged_database)
    view.show_sources(document_codes(staged_database), Selection("CTFR"))
    # Readable fields, not the record ID; the counted Document Code is not repeated.
    assert view.model.headers == (
        "Application Number",
        "Invention Title",
        "Document Code",
        "Art Unit",
        "Submission Date",
        "Source file",
        "Import date",
    )
    rows = shown_rows(view)
    assert len(rows) == 9
    assert {(row[2], *row[-2:]) for row in rows} == {
        ("CTFR", FIXTURE.name, IMPORT_TIME.strftime("%Y-%m-%d"))
    }
    by_id = {record["id"]: record for record in fixture_records()}
    for record, row in zip(view.model.records, rows, strict=True):
        source = by_id[record.record_id]
        assert row[:2] == (source["patentApplicationNumber"], source.get("inventionTitle", ""))
        assert row[3:5] == (str(source["groupArtUnitNumber"]), source["submissionDate"][:10])
        assert record.record_id not in row
    assert view.total.text().startswith("9 records")
    assert "Office actions by Document Code: CTFR" in view.heading.text()
    assert calls.offers == []


def test_the_whole_chart_lists_every_record_it_counted(qt_app, staged_database) -> None:
    result = analytics.run_metric(staged_database, "rejections-by-technology-center-and-type", {})
    view, _ = make_view(staged_database)
    view.show_sources(result, None)
    assert view.model.rowCount() == result.total
    assert view.model.headers[2:6] == (
        "Technology Center",
        "USPTO rejection tag",
        "Document Code",
        "Art Unit",
    )
    assert ("2800", "No USPTO rejection tag in the source") in {
        row[2:4] for row in shown_rows(view)
    }


# --- 2b: more records than one page -----------------------------------------------------


def test_records_are_read_a_page_at_a_time_with_the_total_shown(qt_app, staged_database) -> None:
    view, _ = make_view(staged_database, page_size=6)
    view.show_sources(document_codes(staged_database), None)
    assert view.model.rowCount() == 6
    assert view.total.text().startswith("20 records")
    while view.model.canFetchMore():
        view.model.fetchMore()
    ids = [record.record_id for record in view.model.records]
    assert len(ids) == len(set(ids)) == 20


# --- 4a: one record in full -------------------------------------------------------------


def test_selecting_a_record_shows_every_stored_field_and_its_source_file(
    qt_app, staged_database
) -> None:
    view, _ = make_view(staged_database)
    view.show_sources(document_codes(staged_database), None)
    view.table.selectRow(3)
    record = view.model.records[3]
    source = next(r for r in fixture_records() if r["id"] == record.record_id)
    fields = view.record_fields()
    assert fields["oaText"] == source["oaText"]
    assert fields["patentApplicationNumber"] == source["patentApplicationNumber"]
    assert set(source) <= set(fields)
    assert fields["id"] == record.record_id  # the record ID is still shown here
    assert FIXTURE.name in view.record_heading.text()
    assert source["patentApplicationNumber"] in view.record_heading.text()
    # The letter text in full, character for character as stored.
    assert view.letter_text.toPlainText() == source["oaText"]
    assert view.letter_text.isReadOnly()


# --- 2a: the source data is unavailable -------------------------------------------------


def test_an_unavailable_source_is_reported_and_recreating_is_offered(
    qt_app, two_weeks_database
) -> None:
    result = document_codes(two_weeks_database)
    remove_import(two_weeks_database, 2)
    view, calls = make_view(two_weeks_database, recreate_answer=True)
    view.show_sources(result, None)
    message = provenance.SourceUnavailableError().message
    assert calls.offers == [message]
    assert view.notices.item(0).text() == message
    assert calls.recreated == 1  # 2a2: create visualizations
    assert view.model is None


def test_declining_to_recreate_lists_nothing_and_creates_nothing(
    qt_app, two_weeks_database
) -> None:
    result = document_codes(two_weeks_database)
    remove_import(two_weeks_database, 2)
    view, calls = make_view(two_weeks_database, recreate_answer=False)
    view.show_sources(result, Selection("CTNF"))
    assert len(calls.offers) == 1
    assert calls.recreated == 0  # 2a2: the use case ends
    assert view.model is None
    assert view.total.text() == ""


# --- Failure handling -------------------------------------------------------------------


def test_a_failed_lookup_is_shown_without_offering_to_recreate(
    qt_app, staged_database, monkeypatch
) -> None:
    def fail(*args):
        raise SourceLookupFailedError()

    monkeypatch.setattr(provenance, "records_for", fail)
    view, calls = make_view(staged_database)
    view.show_sources(document_codes(staged_database), None)
    assert view.notices.item(0).text() == SourceLookupFailedError().message
    assert calls.offers == []
    assert view.model is None


def test_a_source_that_becomes_unavailable_while_scrolling_is_reported(
    qt_app, two_weeks_database
) -> None:
    result = document_codes(two_weeks_database)
    view, calls = make_view(two_weeks_database, page_size=6)
    view.show_sources(result, None)
    model = view.model
    remove_import(two_weeks_database, 2)
    model.fetchMore()
    assert calls.offers == [provenance.SourceUnavailableError().message]
    assert model.rowCount() == 6  # nothing from the changed data was added
    assert not model.canFetchMore()
    assert view.model is None
