"""The expected layout and the per-record checks: the one place that defines "valid" (8.2.5)."""

# Every field of the office action file (SRS 7.2). A field outside this list refuses the file.
EXPECTED_FIELDS = (
    "accessLevelCategory",
    "aiaindicator",
    "applicationDeemedWithdrawnDate",
    "applicationStatusNumber",
    "applicationTypeCategory",
    "cmsIdentifier",
    "cmsLastModifiedTimeStamp",
    "customerNumber",
    "documentActiveIndicator",
    "documentCode",
    "effectiveFilingDate",
    "examinerEmployeeNumber",
    "filingDate",
    "groupArtUnitNumber",
    "id",
    "inventionSubjectMatterCategory",
    "inventionTitle",
    "nationalClass",
    "nationalSubClass",
    "oaText",
    "obsoleteDocumentIdentifier",
    "patentApplicationConfirmationNumber",
    "patentApplicationNumber",
    "rejections",
    "sections",
    "sourceSystemName",
    "submissionDate",
    "systemCreateTimestamp",
    "systemLastModifiedTimestamp",
    "techCenter",
    "workGroup",
)

# Stored as JSON; every other field is stored as the text the file gave.
JSON_FIELDS = frozenset({"rejections", "sections"})

# The fields SRS 7.2 marks Required. The file is refused when one of them is absent from
# every record in the layout sample. Optional fields are left out of records, not sent empty.
REQUIRED_LAYOUT_FIELDS = (
    "id",
    "documentCode",
    "submissionDate",
    "oaText",
    "examinerEmployeeNumber",
    "groupArtUnitNumber",
    "workGroup",
    "techCenter",
    "patentApplicationNumber",
    "filingDate",
    "effectiveFilingDate",
)

# The fields every chart needs; a record without one is rejected (8.2.5).
REQUIRED_RECORD_FIELDS = (
    "id",
    "patentApplicationNumber",
    "groupArtUnitNumber",
    "documentCode",
    "submissionDate",
)


def compare_field_names(field_names: set[str]) -> tuple[list[str], list[str]]:
    """Return the required layout fields that are absent and the fields that are unexpected."""
    missing = [name for name in REQUIRED_LAYOUT_FIELDS if name not in field_names]
    unexpected = sorted(field_names - set(EXPECTED_FIELDS))
    return missing, unexpected


def rejection_reason_sql(line: str) -> str:
    """A DuckDB expression over a JSON text column giving the record's rejection reasons,
    joined with '; ', or '' when the record is valid."""

    def value(field: str) -> str:
        return f"json_extract_string({line}, '$.{field}')"

    checks = [
        f"CASE WHEN coalesce({value(field)}, '') = '' THEN 'missing {field}' END"
        for field in REQUIRED_RECORD_FIELDS
    ]
    checks.append(
        f"CASE WHEN coalesce({value('groupArtUnitNumber')}, '') <> '' "
        f"AND NOT regexp_full_match({value('groupArtUnitNumber')}, '[0-9]{{4}}') "
        "THEN 'groupArtUnitNumber is not four digits' END"
    )
    checks.append(
        f"CASE WHEN coalesce({value('submissionDate')}, '') <> '' "
        f"AND try_cast({value('submissionDate')} AS TIMESTAMPTZ) IS NULL "
        "THEN 'submissionDate is not a timestamp' END"
    )
    return "concat_ws('; ', " + ", ".join(checks) + ")"
