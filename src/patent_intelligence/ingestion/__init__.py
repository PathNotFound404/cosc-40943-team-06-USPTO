"""Ingestion: reads a weekly file, checks it, and loads its records unchanged."""

from patent_intelligence.ingestion.importer import ImportSummary, import_file

__all__ = ["ImportSummary", "import_file"]
