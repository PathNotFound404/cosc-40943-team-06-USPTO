-- The import log and the raw tables (docs/design/intake.md, Data model).
-- Raw tables are append-only (architecture 8.2.8). Every source field is stored as the
-- text the file gave; typing happens in the staged dataset (BR-no-data-alteration).

CREATE SEQUENCE import_id_sequence START 1;

CREATE TABLE import_log (
    import_id INTEGER PRIMARY KEY,
    file_name TEXT NOT NULL,
    content_hash TEXT NOT NULL UNIQUE,      -- SHA-256 of the whole file (DI-no-duplicates)
    import_time TIMESTAMP NOT NULL,         -- UTC (architecture 8.2.2)
    records_loaded INTEGER NOT NULL,
    records_rejected INTEGER NOT NULL,
    app_version TEXT NOT NULL
);

-- One row per office action, one column per source field in SRS 7.2, named as in the file.
CREATE TABLE raw_office_action (
    import_id INTEGER NOT NULL REFERENCES import_log (import_id),
    line_number BIGINT NOT NULL,
    accessLevelCategory TEXT,
    aiaindicator TEXT,
    applicationDeemedWithdrawnDate TEXT,
    applicationStatusNumber TEXT,
    applicationTypeCategory TEXT,
    cmsIdentifier TEXT,
    cmsLastModifiedTimeStamp TEXT,
    customerNumber TEXT,
    documentActiveIndicator TEXT,
    documentCode TEXT,
    effectiveFilingDate TEXT,
    examinerEmployeeNumber TEXT,
    filingDate TEXT,
    groupArtUnitNumber TEXT,
    id TEXT,
    inventionSubjectMatterCategory TEXT,
    inventionTitle TEXT,
    nationalClass TEXT,
    nationalSubClass TEXT,
    oaText TEXT,
    obsoleteDocumentIdentifier TEXT,
    patentApplicationConfirmationNumber TEXT,
    patentApplicationNumber TEXT,
    rejections JSON,
    sections JSON,
    sourceSystemName TEXT,
    submissionDate TEXT,
    systemCreateTimestamp TEXT,
    systemLastModifiedTimestamp TEXT,
    techCenter TEXT,
    workGroup TEXT,
    PRIMARY KEY (import_id, line_number)
);

-- A record that failed a required-field check, kept as it was with its reason.
-- raw_line may contain letter text, so it is never logged (architecture 8.2.7).
CREATE TABLE rejected_record (
    import_id INTEGER NOT NULL REFERENCES import_log (import_id),
    line_number BIGINT NOT NULL,
    reason TEXT NOT NULL,
    raw_line TEXT NOT NULL,
    PRIMARY KEY (import_id, line_number)
);
