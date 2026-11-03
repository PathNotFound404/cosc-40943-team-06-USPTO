"""The records behind a chart or one bar of it, and one record in full
(UC-FEAT-verify-source, docs/design/verification.md)."""

import logging
from dataclasses import dataclass
from datetime import date

import duckdb

from patent_intelligence import analytics
from patent_intelligence.analytics import MetricResult
from patent_intelligence.provenance.errors import SourceLookupFailedError, SourceUnavailableError
from patent_intelligence.storage import Database

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class Selection:
    """One bar, or one segment of a two-way bar. A category or series of None is the bar for
    a value the source did not give, not "all"; `series` is ignored for a one-way chart."""

    category: str | None
    series: str | None = None


@dataclass(frozen=True)
class SourceRecord:
    """One counted row: what a reader recognizes the record by, the value of each counted
    field, and where it came from (the use case's "Source display strategy"). `record_id` and
    `import_id` are what `record_detail` takes. A value the source did not give is None."""

    record_id: str
    import_id: int
    application_number: str | None
    invention_title: str | None
    counted_values: tuple[str | None, ...]
    document_code: str | None
    art_unit: str | None
    submission_date: date | None
    source_file: str
    import_date: date


@dataclass(frozen=True)
class RecordPage:
    """One page of a selection's records, the total across every page, and the names of the
    counted fields, in the order of `SourceRecord.counted_values` (FR-CHART-counted-field)."""

    records: tuple[SourceRecord, ...]
    total: int
    counted_fields: tuple[str, ...]


@dataclass(frozen=True)
class RecordDetail:
    """Every stored field of one raw record, as stored, and its source file."""

    record_id: str
    import_id: int
    source_file: str
    import_date: date
    fields: tuple[tuple[str, object], ...]  # in the raw table's column order


def records_for(
    database: Database,
    result: MetricResult,
    selection: Selection | None,
    offset: int,
    limit: int,
) -> RecordPage:
    """The rows `result` counted for `selection` (None for the whole chart), sorted by source
    file, Application Number, Submission Date, then record ID, one page from `offset`. Raises
    SourceUnavailableError when an import the chart counted is gone or the rows no longer add
    up to the chart (2a), and SourceLookupFailedError when the query fails."""
    metric = result.metric
    two_way = metric.series_field is not None
    query, values = analytics.base_query(metric.name, result.parameters, result.weeks)
    # Only the chart's own imports, so a later import does not add to what it counted.
    values["chart_import_ids"] = list(result.import_ids)
    filters = ["list_contains($chart_import_ids::INTEGER[], import_id)"]
    if selection is not None:
        filters.append("category IS NOT DISTINCT FROM $selected_category::VARCHAR")
        values["selected_category"] = selection.category
        if two_way:
            filters.append("series IS NOT DISTINCT FROM $selected_series::VARCHAR")
            values["selected_series"] = selection.series
    selected = f"SELECT * FROM ({query}) WHERE {' AND '.join(filters)}"
    counted = "category, series" if two_way else "category"
    # The use case's sort; the record ID and the rest break ties, so pages never skip or
    # repeat a row (2b).
    order = f"file_name, application_number, submitted, record_id, import_id, {counted}"

    cursor = database.cursor()
    try:
        # One transaction, so the check, the total, and the page read the same data.
        with database.transaction(cursor):
            (present,) = cursor.execute(
                "SELECT count(*) FROM import_log WHERE list_contains($ids::INTEGER[], import_id)",
                {"ids": list(result.import_ids)},
            ).fetchone()
            if present != len(result.import_ids):
                log.warning(
                    "The source of %s is gone: an import it counted was removed", metric.name
                )
                raise SourceUnavailableError()
            (total,) = cursor.execute(f"SELECT count(*) FROM ({selected})", values).fetchone()
            if total != _charted_value(result, selection):
                log.warning("The source of %s no longer adds up to the chart", metric.name)
                raise SourceUnavailableError()
            rows = cursor.execute(
                f"""
                WITH page AS (
                    SELECT s.*, o.application_number, o.document_code, o.art_unit,
                        o.submission_date::DATE AS submitted, i.file_name,
                        i.import_time::DATE AS imported
                    FROM ({selected}) AS s
                    JOIN import_log AS i ON i.import_id = s.import_id
                    LEFT JOIN staged_office_action AS o ON o.record_id = s.record_id
                ),
                one_page AS (
                    SELECT * FROM page ORDER BY {order} LIMIT $page_limit OFFSET $page_offset
                ),
                titles AS (
                    SELECT r.id AS title_id, r.import_id AS title_import, r.inventionTitle
                    FROM raw_office_action AS r
                    WHERE r.id IN (SELECT record_id FROM one_page)
                    QUALIFY row_number() OVER (
                        PARTITION BY r.id, r.import_id ORDER BY {_CHOSEN_COPY_ORDER}
                    ) = 1
                )
                SELECT record_id, import_id, application_number, inventionTitle, document_code,
                    art_unit, submitted, file_name, imported, {counted}
                FROM one_page
                LEFT JOIN titles
                    ON title_id = one_page.record_id AND title_import = one_page.import_id
                ORDER BY {order}
                """,
                {**values, "page_limit": limit, "page_offset": offset},
            ).fetchall()
    except duckdb.Error as error:
        log.exception("The source records of %s could not be read", metric.name)
        raise SourceLookupFailedError() from error
    finally:
        cursor.close()

    counted_fields = (metric.category_field,)
    if two_way:
        counted_fields += (metric.series_field,)
    records = tuple(
        SourceRecord(
            record_id,
            import_id,
            application_number,
            title,
            tuple(counted_values),
            document_code,
            art_unit,
            submitted,
            file,
            imported,
        )
        for (
            record_id,
            import_id,
            application_number,
            title,
            document_code,
            art_unit,
            submitted,
            file,
            imported,
            *counted_values,
        ) in rows
    )
    log.info("Listed %d of %d source records of %s", len(records), total, metric.name)
    return RecordPage(records, total, counted_fields)


def _charted_value(result: MetricResult, selection: Selection | None) -> int:
    """What the chart shows for `selection`: the bar, the segment, or the whole chart."""
    if selection is None:
        return result.total
    if result.metric.series_field is None:
        return dict(result.counts).get(selection.category, 0)
    segments = {(category, series): count for category, series, count in result.breakdown}
    return segments.get((selection.category, selection.series), 0)


# When one import holds a record twice, the copy the staged dataset chose
# (docs/design/intake.md, duplicate records).
_CHOSEN_COPY_ORDER = """
    try_cast(r.systemLastModifiedTimestamp AS TIMESTAMP) DESC NULLS LAST, r.line_number DESC
"""


def record_detail(database: Database, record_id: str, import_id: int) -> RecordDetail:
    """Every stored field of the raw record `record_id` from import `import_id`, as stored
    (4a; BR-no-data-alteration). Raises SourceUnavailableError when it is not stored, and
    SourceLookupFailedError when the query fails."""
    cursor = database.cursor()
    try:
        cursor.execute(
            f"""
            SELECT r.*, i.file_name AS source_file, i.import_time::DATE AS import_date
            FROM raw_office_action AS r JOIN import_log AS i USING (import_id)
            WHERE r.id = $record_id AND r.import_id = $import_id
            ORDER BY {_CHOSEN_COPY_ORDER}
            LIMIT 1
            """,
            {"record_id": record_id, "import_id": import_id},
        )
        names = [column[0] for column in cursor.description]
        row = cursor.fetchone()
    except duckdb.Error as error:
        log.exception("A source record could not be read")
        raise SourceLookupFailedError() from error
    finally:
        cursor.close()
    if row is None:
        log.warning("A source record asked for is not stored")
        raise SourceUnavailableError()
    stored = dict(zip(names, row, strict=True))
    source_file, import_date = stored.pop("source_file"), stored.pop("import_date")
    return RecordDetail(record_id, import_id, source_file, import_date, tuple(stored.items()))
