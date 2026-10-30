"""The metric registry: each metric is a named base query over the staged views
(KD-charts-from-sql, docs/design/visualization.md, Release 1.0 metrics).

A base query returns one row per counted item: `record_id`, `category`, `import_id`, and
`submission_date`, and for a two-way metric also `series`, the second field each category is
split by. Analytics counts its rows and Provenance lists them, from the same text.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Metric:
    name: str
    title: str
    counts: str  # what one row is, as the chart's axis names it
    category_field: str
    base_query: str  # named parameters are written $name
    parameters: tuple[str, ...] = ()
    series_field: str | None = None
    # Known series values, in the fixed order their colors follow from week to week.
    series_order: tuple[str, ...] = ()

    @property
    def counted_field(self) -> str:
        """The field the figures were counted from, shown on every chart
        (FR-CHART-counted-field)."""
        if self.series_field is None:
            return self.category_field
        return f"{self.series_field}, by {self.category_field}"


TECHNOLOGY_CENTER = "technology_center"

_OFFICE_ACTIONS = "Office actions"
# The USPTO rejection types the sample gives (docs/design/visualization.md, Release 1.0 metrics).
_REJECTION_TYPES = ("101", "102", "103", "112", "DoublePatent", "Other")

METRICS = (
    Metric(
        name="office-actions-by-document-code",
        title="Office actions by Document Code",
        counts=_OFFICE_ACTIONS,
        category_field="Document Code",
        base_query="""
            SELECT record_id, document_code AS category, import_id, submission_date
            FROM staged_office_action
        """,
    ),
    Metric(
        name="office-actions-by-technology-center",
        title="Office actions by Technology Center",
        counts=_OFFICE_ACTIONS,
        category_field="Technology Center",
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
        category_field="USPTO rejection tag",
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
        category_field="Art Unit",
        base_query="""
            SELECT record_id, art_unit AS category, import_id, submission_date
            FROM staged_office_action
            WHERE technology_center = $technology_center
        """,
        parameters=(TECHNOLOGY_CENTER,),
    ),
    Metric(
        name="rejections-by-technology-center-and-type",
        title="Rejection types by Technology Center",
        counts="Rejection entries",
        category_field="Technology Center",
        series_field="USPTO rejection tag",
        series_order=_REJECTION_TYPES,
        base_query="""
            SELECT r.record_id, o.technology_center AS category, r.rejection_type AS series,
                r.import_id, o.submission_date
            FROM staged_rejection AS r
            JOIN staged_office_action AS o USING (record_id)
        """,
    ),
    # The CTFR share of each Technology Center is its final rejection share.
    Metric(
        name="office-actions-by-technology-center-and-document-code",
        title="Document Codes by Technology Center",
        counts=_OFFICE_ACTIONS,
        category_field="Technology Center",
        series_field="Document Code",
        series_order=("CTNF", "CTFR"),
        base_query="""
            SELECT record_id, technology_center AS category, document_code AS series, import_id,
                submission_date
            FROM staged_office_action
        """,
    ),
)
