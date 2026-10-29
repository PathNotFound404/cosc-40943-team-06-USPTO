"""Storage: the only component that opens the DuckDB file (architecture 8.2.3, 8.2.8)."""

from patent_intelligence.storage.database import Database, StorageError, open

__all__ = ["Database", "StorageError", "open"]
