"""The Visualizations view: the metric chooser and one tab per chart (UC-FEAT-create-visuals)."""

from collections.abc import Callable

from matplotlib.backend_bases import PickEvent
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from patent_intelligence import analytics
from patent_intelligence.analytics import TECHNOLOGY_CENTER, Metric
from patent_intelligence.analytics.errors import MetricFailedError, StagedDataMissingError
from patent_intelligence.charts import Bar, Chart, draw
from patent_intelligence.jobs.cleaning_job import CleaningJob
from patent_intelligence.jobs.runner import JobRunner
from patent_intelligence.storage import Database

Choice = tuple[Metric, dict[str, str]]
# Asks which metrics to create; None when the user cancels (steps 3-4, 4a).
Chooser = Callable[[QWidget, tuple[Metric, ...], list[str]], list[Choice] | None]
# Asks whether to clean the data now; True to clean (2a1-2a2).
CleaningOffer = Callable[[QWidget, str], bool]
# Shows the records behind a bar or segment: chart, category, series (6a, verification.md).
DrillDown = Callable[[Chart, str | None, str | None], None]


class MetricChooser(QDialog):
    """Every metric, checked by default (step 3); the Art Unit metric also takes a Technology
    Center, starting at the first staged."""

    def __init__(
        self,
        metrics: tuple[Metric, ...],
        technology_centers: list[str],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Create visualizations")
        self._metrics = metrics
        self.checkboxes: list[QCheckBox] = []
        self.technology_center = QComboBox()
        self.technology_center.addItems(technology_centers)

        layout = QGridLayout(self)
        layout.addWidget(QLabel("Choose the visualizations to create:"), 0, 0, 1, 2)
        for row, metric in enumerate(metrics, start=1):
            checkbox = QCheckBox(metric.title)
            checkbox.setChecked(True)
            self.checkboxes.append(checkbox)
            layout.addWidget(checkbox, row, 0)
            if TECHNOLOGY_CENTER in metric.parameters:
                layout.addWidget(self.technology_center, row, 1)
                if not technology_centers:
                    checkbox.setChecked(False)
                    checkbox.setEnabled(False)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons, len(metrics) + 1, 0, 1, 2)

    def choices(self) -> list[Choice]:
        return [
            (metric, self._parameters(metric))
            for metric, checkbox in zip(self._metrics, self.checkboxes, strict=True)
            if checkbox.isChecked()
        ]

    def _parameters(self, metric: Metric) -> dict[str, str]:
        if TECHNOLOGY_CENTER in metric.parameters:
            return {TECHNOLOGY_CENTER: self.technology_center.currentText()}
        return {}

    @staticmethod
    def choose(
        parent: QWidget, metrics: tuple[Metric, ...], technology_centers: list[str]
    ) -> list[Choice] | None:
        dialog = MetricChooser(metrics, technology_centers, parent)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return None
        return dialog.choices()


def _ask_to_clean(parent: QWidget, message: str) -> bool:
    answer = QMessageBox.question(
        parent,
        "Create visualizations",
        f"{message}\n\nClean the imported data now?",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
    )
    return answer == QMessageBox.StandardButton.Yes


class ChartsView(QWidget):
    def __init__(
        self,
        runner: JobRunner,
        database: Database,
        choose: Chooser = MetricChooser.choose,
        offer_cleaning: CleaningOffer = _ask_to_clean,
        drill_down: DrillDown | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._runner = runner
        self._database = database
        self._choose = choose
        self._offer_cleaning = offer_cleaning
        self._drill_down = drill_down
        # The charts created in this session, staged for export (step 7). Kept in memory only
        # (architecture section 7).
        self.charts: list[Chart] = []

        self.create_button = QPushButton("Create visualizations")
        self.create_button.clicked.connect(self.create_visualizations)
        self.notices = QListWidget()
        self.notices.setMaximumHeight(90)
        self.tabs = QTabWidget()

        layout = QVBoxLayout(self)
        layout.addWidget(self.create_button)
        layout.addWidget(self.notices)
        layout.addWidget(self.tabs, stretch=1)

    def create_visualizations(self) -> None:
        """Steps 1-7: confirm the data is staged, ask which metrics, then run and draw each."""
        try:
            metrics = analytics.list_metrics(self._database)
        except StagedDataMissingError as error:
            self.notices.addItem(error.message)
            if self._offer_cleaning(self, error.message):
                self._runner.submit(CleaningJob(self._database))
                self.notices.addItem(
                    "Cleaning the imported data; its progress is shown on the Import tab. "
                    "Create visualizations again when it is ready."
                )
            return

        choices = self._choose(self, metrics, analytics.technology_centers(self._database))
        if not choices:
            return

        failed = []
        first_index = None
        for metric, parameters in choices:
            try:
                chart = draw(analytics.run_metric(self._database, metric.name, parameters))
            except MetricFailedError:
                failed.append(metric.title)  # logged by Analytics or Charts (5a1)
                continue
            index = self._show(chart)
            first_index = index if first_index is None else first_index
        if first_index is not None:
            self.tabs.setCurrentIndex(first_index)
        if failed:
            self.notices.addItem(
                f"These visualizations could not be created: {', '.join(failed)}. "
                "Details were written to the log file."
            )

    def on_bar_selected(self, chart: Chart, bar: Bar) -> None:
        """6a: hand the chart and the selected bar or segment to Provenance."""
        if self._drill_down is not None:
            self._drill_down(chart, bar.category, bar.series)

    def _show(self, chart: Chart) -> int:
        """Show `chart` on its own tab. A chart of the same metric and parameters replaces the
        one already shown, so the session holds the newest of each."""
        canvas = FigureCanvasQTAgg(chart.figure)
        figure = chart.figure
        canvas.setMinimumHeight(round(figure.get_figheight() * figure.dpi))
        if self._drill_down is not None:
            canvas.mpl_connect("pick_event", lambda event: self._on_pick(chart, event))
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(canvas)

        for index, shown in enumerate(self.charts):
            if _same_chart(shown, chart):
                self.charts[index] = chart
                replaced = self.tabs.widget(index)
                self.tabs.removeTab(index)
                replaced.deleteLater()
                self.tabs.insertTab(index, scroll, chart.title)
                return index
        self.charts.append(chart)
        return self.tabs.addTab(scroll, chart.title)

    def _on_pick(self, chart: Chart, event: PickEvent) -> None:
        for bar in chart.bars:
            if bar.patch is event.artist:
                self.on_bar_selected(chart, bar)
                return


def _same_chart(one: Chart, other: Chart) -> bool:
    return (one.result.metric.name, dict(one.result.parameters)) == (
        other.result.metric.name,
        dict(other.result.parameters),
    )
