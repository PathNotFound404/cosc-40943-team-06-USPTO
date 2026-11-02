"""Running metrics over the staged dataset (UC-FEAT-create-visuals steps 2, 5, and 6b)."""

import logging
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date, datetime

import duckdb

from patent_intelligence.analytics.errors import MetricFailedError, StagedDataMissingError
from patent_intelligence.analytics.metrics import METRICS, Metric
from patent_intelligence.storage import Database

log = logging.getLogger(__name__)

_BY_NAME = {metric.name: metric for metric in METRICS}


@dataclass(frozen=True)
class Weeks:
    """Which weeks a chart counts (6b): every staged office action (both None), those staged
    from the chosen imports, or those submitted in the chosen calendar weeks. A week is named
    by its Monday; None in `submission_weeks` stands for the office actions whose Submission
    Date the source did not give, which can be chosen like a week rather than being dropped
    (BR-no-data-alteration)."""

    import_ids: frozenset[int] | None = None
    submission_weeks: frozenset[date | None] | None = None

    def __post_init__(self) -> None:
        if self.import_ids is not None and self.submission_weeks is not None:
            raise ValueError("Weeks are chosen by imported file or by calendar week, not both")


ALL_WEEKS = Weeks()


@dataclass(frozen=True)
class ImportedFile:
    """One import that can be chosen, with the staged office actions taken from it."""

    import_id: int
    file_name: str
    import_time: datetime
    office_actions: int
    earliest_submission: date | None
    latest_submission: date | None


@dataclass(frozen=True)
class SubmissionWeek:
    """One calendar week of Submission Date, Monday to Sunday; `monday` is None for the
    office actions with no Submission Date in the source."""

    monday: date | None
    office_actions: int


@dataclass(frozen=True)
class MetricResult:
    """One metric's counts and what they cover. A category or series of None is a value the
    source did not give; it is counted, not dropped (BR-no-data-alteration). `breakdown` is
    set only for a two-way metric: the count per category and series."""

    metric: Metric
    parameters: Mapping[str, str]
    counts: tuple[tuple[str | None, int], ...]  # largest first
    import_ids: tuple[int, ...]
    earliest_submission: date | None
    latest_submission: date | None
    breakdown: tuple[tuple[str | None, str | None, int], ...] = ()
    weeks: Weeks = ALL_WEEKS
    total: int = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "total", sum(count for _, count in self.counts))


def list_metrics(database: Database) -> tuple[Metric, ...]:
    """The metrics that can be charted. Raises StagedDataMissingError when the staged views
    are missing or hold no office actions (2a)."""
    cursor = database.cursor()
    try:
        (views,) = cursor.execute(
            "SELECT count(*) FROM duckdb_views() "
            "WHERE view_name IN ('staged_office_action', 'staged_rejection')"
        ).fetchone()
        if views < 2:
            raise StagedDataMissingError()
        (office_actions,) = cursor.execute("SELECT count(*) FROM staged_office_action").fetchone()
    except duckdb.Error as error:
        log.exception("The staged dataset could not be read")
        raise StagedDataMissingError() from error
    finally:
        cursor.close()
    if office_actions == 0:
        raise StagedDataMissingError()
    return METRICS


def technology_centers(database: Database) -> list[str]:
    """The Technology Centers in the staged dataset, for the Art Unit metric's parameter."""
    cursor = database.cursor()
    try:
        rows = cursor.execute(
            "SELECT DISTINCT technology_center FROM staged_office_action "
            "WHERE technology_center IS NOT NULL ORDER BY technology_center"
        ).fetchall()
    finally:
        cursor.close()
    return [technology_center for (technology_center,) in rows]


# The Monday of a Submission Date's calendar week (DuckDB's weeks are ISO weeks).
_WEEK = "date_trunc('week', submission_date)::DATE"


def imported_files(database: Database) -> list[ImportedFile]:
    """Every import, oldest first, with the staged office actions taken from it (6b). An
    import whose records were all superseded by a later copy has none."""
    cursor = database.cursor()
    try:
        rows = cursor.execute(
            """
            SELECT i.import_id, i.file_name, i.import_time, count(o.record_id),
                min(o.submission_date)::DATE, max(o.submission_date)::DATE
            FROM import_log AS i LEFT JOIN staged_office_action AS o USING (import_id)
            GROUP BY i.import_id, i.file_name, i.import_time
            ORDER BY i.import_id
            """
        ).fetchall()
    finally:
        cursor.close()
    return [ImportedFile(*row) for row in rows]


def submission_weeks(database: Database) -> list[SubmissionWeek]:
    """The calendar weeks of Submission Date in the staged dataset, oldest first, then the
    office actions with no Submission Date, if there are any (6b)."""
    cursor = database.cursor()
    try:
        rows = cursor.execute(
            f"""
            SELECT {_WEEK} AS monday, count(*) FROM staged_office_action
            GROUP BY monday ORDER BY monday NULLS LAST
            """
        ).fetchall()
    finally:
        cursor.close()
    return [SubmissionWeek(monday, office_actions) for monday, office_actions in rows]


def base_query(
    name: str, parameters: Mapping[str, str], weeks: Weeks = ALL_WEEKS
) -> tuple[str, dict[str, object]]:
    """The metric's base query limited to `weeks`, and its parameter values, so Provenance
    lists exactly the rows the chart counted (KD-charts-from-sql). Raises MetricFailedError
    for an unknown metric or parameters that do not match it."""
    metric = _BY_NAME.get(name)
    if metric is None or set(parameters) != set(metric.parameters):
        log.error("No metric %s with parameters %s", name, sorted(parameters))
        raise MetricFailedError(name)
    query: str = metric.base_query
    values: dict[str, object] = dict(parameters)
    if weeks.import_ids is not None:
        query = f"""
            SELECT * FROM ({query})
            WHERE list_contains($chosen_import_ids::INTEGER[], import_id)
        """
        values["chosen_import_ids"] = sorted(weeks.import_ids)
    elif weeks.submission_weeks is not None:
        query = f"""
            SELECT * FROM ({query})
            WHERE list_contains($chosen_weeks::DATE[], {_WEEK})
                OR ($no_submission_date_chosen AND submission_date IS NULL)
        """
        values["chosen_weeks"] = sorted(week for week in weeks.submission_weeks if week)
        values["no_submission_date_chosen"] = None in weeks.submission_weeks
    return query, values


def run_metric(
    database: Database, name: str, parameters: Mapping[str, str], weeks: Weeks = ALL_WEEKS
) -> MetricResult:
    """Count the metric's base query over `weeks` by category, in DuckDB. Raises
    MetricFailedError (5a)."""
    query, values = base_query(name, parameters, weeks)
    cursor = database.cursor()
    try:
        # One transaction, so the counts and what they cover come from the same staged data
        # even if an import rebuilds it meanwhile.
        with database.transaction(cursor):
            counts = cursor.execute(
                f"""
                SELECT category, count(*) AS counted FROM ({query})
                GROUP BY category ORDER BY counted DESC, category NULLS LAST
                """,
                values,
            ).fetchall()
            breakdown = []
            if _BY_NAME[name].series_field is not None:
                breakdown = cursor.execute(
                    f"""
                    SELECT category, series, count(*) FROM ({query})
                    GROUP BY category, series ORDER BY category NULLS LAST, series NULLS LAST
                    """,
                    values,
                ).fetchall()
            import_ids, earliest, latest = cursor.execute(
                f"""
                SELECT list(DISTINCT import_id ORDER BY import_id),
                    min(submission_date)::DATE, max(submission_date)::DATE
                FROM ({query})
                """,
                values,
            ).fetchone()
    except duckdb.Error as error:
        log.exception("The metric %s failed", name)
        raise MetricFailedError(name) from error
    finally:
        cursor.close()
    result = MetricResult(
        _BY_NAME[name],
        dict(parameters),
        tuple((category, count) for category, count in counts),
        tuple(import_ids or ()),
        earliest,
        latest,
        tuple(breakdown),
        weeks,
    )
    log.info("Ran the metric %s: %d counted in %d categories", name, result.total, len(counts))
    return result
