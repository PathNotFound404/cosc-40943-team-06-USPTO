"""The Sources view: the records behind a chart or one bar of it, and one record in full
(UC-FEAT-verify-source, docs/design/verification.md)."""

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QLabel,
    QListWidget,
    QMessageBox,
    QSplitter,
    QTableView,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from patent_intelligence import provenance
from patent_intelligence.analytics import MetricResult
from patent_intelligence.charts import category_label, chart_title, series_label
from patent_intelligence.errors import AppError
from patent_intelligence.provenance import Selection, SourceUnavailableError
from patent_intelligence.storage import Database
from patent_intelligence.ui.record_page_model import PAGE_SIZE, RecordPageModel

# Asks whether to create the visualization again; True to create it (2a1-2a2).
RecreateOffer = Callable[[QWidget, str], bool]


def _ask_to_recreate(parent: QWidget, message: str) -> bool:
    answer = QMessageBox.question(
        parent,
        "View source records",
        f"{message}\n\nCreate visualizations now?",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
    )
    return answer == QMessageBox.StandardButton.Yes


def selection_label(result: MetricResult, selection: Selection | None) -> str:
    """What was selected, as the chart names it."""
    title = chart_title(result)
    if selection is None:
        return title
    label = category_label(result, selection.category)
    if result.metric.series_field is not None:
        label += f", {series_label(result, selection.series)}"
    return f"{title}: {label}"


class SourcesView(QWidget):
    def __init__(
        self,
        database: Database,
        recreate: Callable[[], None],
        offer_recreate: RecreateOffer = _ask_to_recreate,
        page_size: int = PAGE_SIZE,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._database = database
        self._recreate = recreate
        self._offer_recreate = offer_recreate
        self._page_size = page_size
        self.model: RecordPageModel | None = None

        self.heading = QLabel("Select a visualization or one of its bars to see its source.")
        self.heading.setWordWrap(True)
        self.total = QLabel()
        self.notices = QListWidget()
        self.notices.setMaximumHeight(70)
        self.notices.hide()
        self.table = QTableView()
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        self.record_heading = QLabel()
        self.record_heading.setWordWrap(True)
        self.record = QTableWidget(0, 2)
        self.record.setHorizontalHeaderLabels(["Field", "Stored value"])
        self.record.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.record.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.record.setWordWrap(True)
        detail = QWidget()
        detail_layout = QVBoxLayout(detail)
        detail_layout.setContentsMargins(0, 0, 0, 0)
        detail_layout.addWidget(self.record_heading)
        detail_layout.addWidget(self.record)

        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(self.table)
        splitter.addWidget(detail)
        layout = QVBoxLayout(self)
        layout.addWidget(self.heading)
        layout.addWidget(self.total)
        layout.addWidget(self.notices)
        layout.addWidget(splitter, stretch=1)

    def show_sources(self, result: MetricResult, selection: Selection | None) -> None:
        """Steps 1-3: list the records `result` counted for `selection` (None for the whole
        chart), one page at a time, with the total (2b1). 2a: say the source is unavailable
        and offer to create the visualization again."""
        self._clear()
        self.heading.setText(f"Source records of {selection_label(result, selection)}")
        try:
            first = provenance.records_for(self._database, result, selection, 0, self._page_size)
        except AppError as error:
            self._show_error(error)
            return
        self.model = RecordPageModel(
            self._database, result, selection, first, self._show_error, self._page_size
        )
        self.table.setModel(self.model)
        self.table.selectionModel().currentRowChanged.connect(
            lambda current, _previous: self.on_record_selected(current.row())
        )
        noun = "record" if first.total == 1 else "records"
        self.total.setText(f"{first.total:,} {noun}, sorted by source file, then record ID")

    def on_record_selected(self, row: int) -> None:
        """4a: every stored field of the record in `row`, as stored, and its source file."""
        if self.model is None or not 0 <= row < len(self.model.records):
            return
        chosen = self.model.records[row]
        try:
            detail = provenance.record_detail(self._database, chosen.record_id, chosen.import_id)
        except AppError as error:
            self._show_error(error)
            return
        self.record_heading.setText(
            f"Record {detail.record_id}, from {detail.source_file}, "
            f"imported {detail.import_date.isoformat()}"
        )
        self.record.setRowCount(len(detail.fields))
        for index, (name, value) in enumerate(detail.fields):
            self.record.setItem(index, 0, QTableWidgetItem(name))
            self.record.setItem(index, 1, QTableWidgetItem("" if value is None else str(value)))

    def record_fields(self) -> dict[str, str]:
        """The single-record panel as shown, field name to value."""
        return {
            self.record.item(row, 0).text(): self.record.item(row, 1).text()
            for row in range(self.record.rowCount())
        }

    def _clear(self) -> None:
        self.model = None
        self.table.setModel(None)
        self.total.clear()
        self.notices.clear()
        self.notices.hide()
        self.record_heading.clear()
        self.record.setRowCount(0)

    def _show_error(self, error: AppError) -> None:
        """The one place this view's actions show a failure (8.2.1)."""
        self.notices.addItem(error.message)
        self.notices.show()
        if isinstance(error, SourceUnavailableError):
            self._clear_records()
            if self._offer_recreate(self, error.message):
                self._recreate()

    def _clear_records(self) -> None:
        self.model = None
        self.table.setModel(None)
        self.total.clear()
        self.record.setRowCount(0)
        self.record_heading.clear()
