"""The metric registry: each metric is a named base query over the staged views
(KD-charts-from-sql, docs/design/visualization.md, Release 1.0 metrics).

A base query returns one row per counted item: `record_id`, `category`, `import_id`, and
`submission_date`. Analytics counts its rows and Provenance lists them, from the same text.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Metric:
    name: str
    title: str
    counts: str  # what one row is, as the chart's axis names it
    counted_field: str  # shown on every chart (FR-CHART-counted-field)
    base_query: str  # named parameters are written $name
    parameters: tuple[str, ...] = ()


TECHNOLOGY_CENTER = "technology_center"

_OFFICE_ACTIONS = "Office actions"

METRICS = (
    Metric(
        name="office-actions-by-document-code",
        title="Office actions by Document Code",
        counts=_OFFICE_ACTIONS,
        counted_field="Document Code",
        base_query="""
            SELECT record_id, document_code AS category, import_id, submission_date
            FROM staged_office_action
        """,
    ),
    Metric(
        name="office-actions-by-technology-center",
        title="Office actions by Technology Center",
        counts=_OFFICE_ACTIONS,
        counted_field="Technology Center",
        base_query="""
            SELECT record_id, technology_center AS category, import_id, submission_date
            FROM staged_office_action
        """,
    ),
    # Counts rejection entries, not office actions; an entry with no type is its own
    # category rather than dropped (BR-no-data-alteration).
    Metric(
        name="rejections-by-type",
        title="Rejections by type",
        counts="Rejection entries",
        counted_field="USPTO rejection tag",
        base_query="""
            SELECT r.record_id, r.rejection_type AS category, r.import_id, o.submission_date
            FROM staged_rejection AS r
            JOIN staged_office_action AS o USING (record_id)
        """,
    ),
    Metric(
        name="office-actions-by-art-unit",
        title="Office actions by Art Unit",
        counts=_OFFICE_ACTIONS,
        counted_field="Art Unit",
        base_query="""
            SELECT record_id, art_unit AS category, import_id, submission_date
            FROM staged_office_action
            WHERE technology_center = $technology_center
        """,
        parameters=(TECHNOLOGY_CENTER,),
    ),
)
