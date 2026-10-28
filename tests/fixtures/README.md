# Test fixtures

`office_actions_20.jsonl` holds 20 records cut from the sample weekly file
(`bdr_oa_bulkdata_weekly_2026-10-18.json`, git-ignored), chosen to cover five different field
sets: records without `sections`, `customerNumber`, or `inventionTitle`, a rejection entry with
no type, a reissue, a design application, and a work group that differs from its art unit.

Changed from the source, to keep the fixture small and free of identifiable people:

- `examinerEmployeeNumber`, at the top level and inside `sections`, is a placeholder
  (`TEST-EXAMINER-00` and so on), never a real examiner number (`DI-identifiable-people`).
- `oaText` is cut to about 1,500 characters around its first non-ASCII character, and each text
  in `sections` to 400 characters.

Files for the extensions (missing fields, truncated lines, rejected records) are derived from
this one inside the tests, so only this file is committed (architecture 8.2.10).
