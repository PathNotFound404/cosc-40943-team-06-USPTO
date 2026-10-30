"""Running metrics over the staged dataset (UC-FEAT-create-visuals steps 2 and 5)."""

import logging
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date

import duckdb

from patent_intelligence.analytics.errors import MetricFailedError, StagedDataMissingError
from patent_intelligence.analytics.metrics import METRICS, Metric
from patent_intelligence.storage import Database

log = logging.getLogger(__name__)

_BY_NAME = {metric.name: metric for metric in METRICS}


@dataclass(frozen=True)
class MetricResult:
    """One metric's counts and what they cover. A category of None is a value the source did
    not give; it is counted, not dropped (BR-no-data-alteration)."""

    metric: Metric
    parameters: Mapping[str, str]
    counts: tuple[tuple[str | None, int], ...]  # largest first
    import_ids: tuple[int, ...]
    earliest_submission: date | None
    latest_submission: date | None
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


def base_query(name: str, parameters: Mapping[str, str]) -> tuple[str, dict[str, str]]:
    """The metric's base query and its parameter values, so Provenance lists exactly the rows
    the chart counted (KD-charts-from-sql). Raises MetricFailedError for an unknown metric or
    parameters that do not match it."""
    metric = _BY_NAME.get(name)
    if metric is None or set(parameters) != set(metric.parameters):
        log.error("No metric %s with parameters %s", name, sorted(parameters))
        raise MetricFailedError(name)
    return metric.base_query, dict(parameters)


def run_metric(database: Database, name: str, parameters: Mapping[str, str]) -> MetricResult:
    """Count the metric's base query by category, in DuckDB. Raises MetricFailedError (5a)."""
    query, values = base_query(name, parameters)
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
    )
    log.info("Ran the metric %s: %d counted in %d categories", name, result.total, len(counts))
    return result
