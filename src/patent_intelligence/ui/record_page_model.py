"""A table model that reads a selection's source records one page at a time as the table
scrolls (UC-FEAT-verify-source 2b, docs/design/verification.md)."""

from collections.abc import Callable

from PySide6.QtCore import QAbstractTableModel, QModelIndex, QPersistentModelIndex, Qt

from patent_intelligence import provenance
from patent_intelligence.analytics import MetricResult
from patent_intelligence.errors import AppError
from patent_intelligence.provenance import RecordPage, Selection, SourceRecord
from patent_intelligence.storage import Database

PAGE_SIZE = 200
_Index = QModelIndex | QPersistentModelIndex


class RecordPageModel(QAbstractTableModel):
    """Rows for `first_page` and the pages after it. A page that cannot be read stops the
    fetching and is handed to `on_error`, which the view shows (8.2.1)."""

    def __init__(
        self,
        database: Database,
        result: MetricResult,
        selection: Selection | None,
        first_page: RecordPage,
        on_error: Callable[[AppError], None],
        page_size: int = PAGE_SIZE,
    ) -> None:
        super().__init__()
        self._database = database
        self._result = result
        self._selection = selection
        self._on_error = on_error
        self._page_size = page_size
        self.records: list[SourceRecord] = list(first_page.records)
        self.total = first_page.total
        self.headers = (
            "Record ID",
            "Application Number",
            *first_page.counted_fields,
            "Source file",
            "Import date",
        )
        self._failed = False

    def rowCount(self, parent: _Index = QModelIndex()) -> int:  # noqa: B008, N802
        return 0 if parent.isValid() else len(self.records)

    def columnCount(self, parent: _Index = QModelIndex()) -> int:  # noqa: B008, N802
        return 0 if parent.isValid() else len(self.headers)

    def headerData(  # noqa: N802
        self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole
    ) -> str | None:
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self.headers[section]
        return None

    def data(self, index: _Index, role: int = Qt.ItemDataRole.DisplayRole) -> str | None:
        if role != Qt.ItemDataRole.DisplayRole or not index.isValid():
            return None
        return self.row_text(index.row())[index.column()]

    def row_text(self, row: int) -> tuple[str, ...]:
        record = self.records[row]
        metric = self._result.metric
        fields = (metric.category_field, metric.series_field)
        counted = tuple(
            f"No {field} in the source" if value is None else value
            for field, value in zip(fields, record.counted_values, strict=False)
        )
        return (
            record.record_id,
            record.application_number or "",
            *counted,
            record.source_file,
            record.import_date.isoformat(),  # YYYY-MM-DD (8.2.2)
        )

    def canFetchMore(self, parent: _Index = QModelIndex()) -> bool:  # noqa: B008, N802
        return not parent.isValid() and not self._failed and len(self.records) < self.total

    def fetchMore(self, parent: _Index = QModelIndex()) -> None:  # noqa: B008, N802
        if not self.canFetchMore(parent):
            return
        try:
            page = provenance.records_for(
                self._database, self._result, self._selection, len(self.records), self._page_size
            )
        except AppError as error:
            self._failed = True
            self._on_error(error)
            return
        if not page.records:
            self._failed = True
            return
        first = len(self.records)
        self.beginInsertRows(QModelIndex(), first, first + len(page.records) - 1)
        self.records.extend(page.records)
        self.endInsertRows()
