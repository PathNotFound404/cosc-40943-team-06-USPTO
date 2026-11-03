"""The Export view: the charts open in this session, the folder picker, and the
overwrite-or-keep-both question (UC-FEAT-export-visuals, FR-TASK-completion-notice)."""

from collections.abc import Callable
from datetime import date
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import (
    QFileDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from patent_intelligence import analytics
from patent_intelligence.charts import (
    Chart,
    Decision,
    ExportSummary,
    FolderNotWritableError,
    export_charts,
    find_conflicts,
)
from patent_intelligence.storage import Database

# Asks for the folder to save in; None when the user cancels (step 3, 3a).
FolderChooser = Callable[[QWidget], Path | None]
# Asks whether to overwrite a taken file name or keep both; None when the user cancels (5b1).
ConflictQuestion = Callable[[QWidget, str], Decision | None]
# Tells the user the folder cannot be used (4a1).
Alert = Callable[[QWidget, str], None]

_TITLE = "Export visualizations"


def _choose_folder(parent: QWidget) -> Path | None:
    folder = QFileDialog.getExistingDirectory(parent, "Choose where to save the visualizations")
    return Path(folder) if folder else None


def _ask_conflict(parent: QWidget, name: str) -> Decision | None:
    question = QMessageBox(parent)
    question.setWindowTitle(_TITLE)
    question.setText(f"A file named {name} already exists in this folder.")
    overwrite = question.addButton("Overwrite", QMessageBox.ButtonRole.DestructiveRole)
    keep_both = question.addButton("Keep both", QMessageBox.ButtonRole.AcceptRole)
    question.addButton(QMessageBox.StandardButton.Cancel)
    question.setDefaultButton(keep_both)
    question.exec()
    if question.clickedButton() is overwrite:
        return Decision.OVERWRITE
    if question.clickedButton() is keep_both:
        return Decision.KEEP_BOTH
    return None


def _alert(parent: QWidget, message: str) -> None:
    QMessageBox.warning(parent, _TITLE, message)


class ExportView(QWidget):
    def __init__(
        self,
        database: Database,
        charts: Callable[[], list[Chart]],
        choose_folder: FolderChooser = _choose_folder,
        ask_conflict: ConflictQuestion = _ask_conflict,
        alert: Alert = _alert,
        today: Callable[[], date] = date.today,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._database = database
        self._charts = charts
        self._choose_folder = choose_folder
        self._ask_conflict = ask_conflict
        self._alert = alert
        self._today = today
        self._shown: list[Chart] = []

        self.instructions = QLabel("")
        self.choices = QListWidget()
        self.choices.itemChanged.connect(lambda _item: self._enable_export())
        self.export_button = QPushButton("Export…")
        self.export_button.clicked.connect(self.export_selected)
        self.notices = QListWidget()

        layout = QVBoxLayout(self)
        layout.addWidget(self.instructions)
        layout.addWidget(self.choices, stretch=1)
        layout.addWidget(self.export_button)
        layout.addWidget(self.notices, stretch=1)
        self.show_charts()

    def showEvent(self, event: QShowEvent) -> None:
        self.show_charts()
        super().showEvent(event)

    def show_charts(self) -> None:
        """Step 2: list the charts open in this session, all checked."""
        self._shown = list(self._charts())
        self.choices.blockSignals(True)
        self.choices.clear()
        for chart in self._shown:
            item = QListWidgetItem(chart.title)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked)
            self.choices.addItem(item)
        self.choices.blockSignals(False)
        if self._shown:
            self.instructions.setText("Choose the visualizations to export:")
        else:
            self.instructions.setText(
                "No visualizations have been created in this session. "
                "Create them on the Visualizations tab first."
            )
        self._enable_export()

    def selected(self) -> list[Chart]:
        return [
            chart
            for row, chart in enumerate(self._shown)
            if self.choices.item(row).checkState() == Qt.CheckState.Checked
        ]

    def export_selected(self) -> None:
        """Steps 3-6: ask for a folder until one can be written to, ask about each taken file
        name, write the charts, and say what was saved and what failed."""
        charts = self.selected()
        if not charts:
            return
        while True:
            folder = self._choose_folder(self)
            if folder is None:
                return  # 3a: nothing exported
            try:
                conflicts = find_conflicts(charts, folder)
                break
            except FolderNotWritableError as error:
                self._alert(self, error.message)  # 4a1, then back to step 3 (4a2)
        decisions = {}
        for name in conflicts:
            decision = self._ask_conflict(self, name)
            if decision is None:
                return  # 3a: nothing exported
            decisions[name] = decision
        source_files = {
            file.import_id: file.file_name for file in analytics.imported_files(self._database)
        }
        try:
            summary = export_charts(charts, folder, decisions, self._today(), source_files)
        except FolderNotWritableError as error:  # the folder changed after it was checked
            self._alert(self, error.message)
            return
        self._show_summary(folder, summary)

    def _show_summary(self, folder: Path, summary: ExportSummary) -> None:
        """Step 6 and 5a2 (FR-TASK-completion-notice)."""
        if summary.saved:
            count = len(summary.saved)
            self.notices.addItem(
                f"Saved {count} visualization{'' if count == 1 else 's'} in {folder}:"
            )
            for path in summary.saved:
                self.notices.addItem(f"    {path}")
        if summary.failed:
            self.notices.addItem("These visualizations could not be exported:")
            for failure in summary.failed:
                self.notices.addItem(f"    {failure.title}: {failure.reason}")

    def _enable_export(self) -> None:
        self.export_button.setEnabled(bool(self.selected()))
