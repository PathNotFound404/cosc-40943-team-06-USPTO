"""The Visualizations view: the weeks every chart counts, the metric chooser, and one tab per
chart (UC-FEAT-create-visuals)."""

from collections.abc import Callable
from datetime import date, timedelta

from matplotlib.backend_bases import PickEvent
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from patent_intelligence import analytics
from patent_intelligence.analytics import (
    ALL_WEEKS,
    TECHNOLOGY_CENTER,
    ImportedFile,
    Metric,
    SubmissionWeek,
    Weeks,
)
from patent_intelligence.analytics.errors import MetricFailedError, StagedDataMissingError
from patent_intelligence.charts import Bar, Chart, draw
from patent_intelligence.jobs.cleaning_job import CleaningJob
from patent_intelligence.jobs.runner import JobRunner
from patent_intelligence.storage import Database

Choice = tuple[Metric, dict[str, str]]
# Asks which weeks to chart, starting from the weeks charted now; None when the user cancels
# (steps 3-4, 4a).
WeeksChooser = Callable[[QWidget, list[ImportedFile], list[SubmissionWeek], Weeks], Weeks | None]
# Asks which metrics to create; None when the user cancels (steps 3-4, 4a).
Chooser = Callable[[QWidget, tuple[Metric, ...], list[str]], list[Choice] | None]
# Asks whether to clean the data now; True to clean (2a1-2a2).
CleaningOffer = Callable[[QWidget, str], bool]
# Shows the records behind a bar or segment: chart, category, series (6a, verification.md).
DrillDown = Callable[[Chart, str | None, str | None], None]
# Shows the records behind a whole chart (UC-FEAT-verify-source step 1, verification.md).
ViewSource = Callable[[Chart], None]


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


class WeekFilter(QWidget):
    """Which weeks are counted: all imported data, the chosen imported files, or the chosen
    calendar weeks of Submission Date. A new list of choices starts all checked. `changed` is
    emitted on every change; the choice is complete when at least one box is checked."""

    ALL, IMPORTED_FILES, CALENDAR_WEEKS = range(3)
    changed = Signal()

    def __init__(
        self,
        files: list[ImportedFile],
        weeks: list[SubmissionWeek],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._files = files
        self._weeks = weeks
        self._keys: list[int | date | None] = []

        self.mode = QComboBox()
        self.mode.addItems(
            ["All imported data", "Imported files", "Calendar weeks of Submission Date"]
        )
        self.choices = QListWidget()
        self.choices.setMaximumHeight(110)
        self.mode.currentIndexChanged.connect(lambda _index: self._fill())
        self.choices.itemChanged.connect(lambda _item: self.changed.emit())

        top = QHBoxLayout()
        top.addWidget(QLabel("Weeks counted:"))
        top.addWidget(self.mode, stretch=1)
        self.top = top
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(top)
        layout.addWidget(self.choices)
        self._fill()

    def weeks(self) -> Weeks:
        chosen = frozenset(
            key
            for row, key in enumerate(self._keys)
            if self.choices.item(row).checkState() == Qt.CheckState.Checked
        )
        if self.mode.currentIndex() == self.IMPORTED_FILES:
            return Weeks(import_ids=chosen)
        if self.mode.currentIndex() == self.CALENDAR_WEEKS:
            return Weeks(submission_weeks=chosen)
        return ALL_WEEKS

    def is_complete(self) -> bool:
        return self.mode.currentIndex() == self.ALL or any(
            self.choices.item(row).checkState() == Qt.CheckState.Checked
            for row in range(self.choices.count())
        )

    def show_weeks(
        self, files: list[ImportedFile], weeks: list[SubmissionWeek], current: Weeks
    ) -> None:
        """Offer these choices, with `current` checked."""
        self._files, self._weeks = files, weeks
        if current.import_ids is not None:
            mode, chosen = self.IMPORTED_FILES, current.import_ids
        elif current.submission_weeks is not None:
            mode, chosen = self.CALENDAR_WEEKS, current.submission_weeks
        else:
            mode, chosen = self.ALL, frozenset()
        self.mode.blockSignals(True)
        self.mode.setCurrentIndex(mode)
        self.mode.blockSignals(False)
        self._fill(chosen if mode != self.ALL else None)

    def _fill(self, chosen: frozenset | None = None) -> None:
        self.choices.blockSignals(True)
        self.choices.clear()
        if self.mode.currentIndex() == self.IMPORTED_FILES:
            entries = [(file.import_id, imported_file_label(file)) for file in self._files]
        elif self.mode.currentIndex() == self.CALENDAR_WEEKS:
            entries = [(week.monday, submission_week_label(week)) for week in self._weeks]
        else:
            entries = []
        self._keys = [key for key, _ in entries]
        for key, label in entries:
            item = QListWidgetItem(label)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            checked = chosen is None or key in chosen
            item.setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)
            self.choices.addItem(item)
        self.choices.blockSignals(False)
        self.choices.setVisible(bool(entries))
        self.changed.emit()


def _office_actions(count: int) -> str:
    return f"{count:,} office action" + ("" if count == 1 else "s")


def imported_file_label(file: ImportedFile) -> str:
    label = f"{file.file_name}, imported {file.import_time:%Y-%m-%d} ("
    label += _office_actions(file.office_actions)
    if file.earliest_submission is not None:
        label += f", submitted {file.earliest_submission} to {file.latest_submission}"
    return label + ")"


def submission_week_label(week: SubmissionWeek) -> str:
    if week.monday is None:
        return f"No Submission Date in the source ({_office_actions(week.office_actions)})"
    sunday = week.monday + timedelta(days=6)
    return f"{week.monday} to {sunday} ({_office_actions(week.office_actions)})"


class WeekChooser(QDialog):
    """The first question when creating visualizations: which data every chart counts
    (step 3). OK needs at least one box checked."""

    def __init__(
        self,
        files: list[ImportedFile],
        weeks: list[SubmissionWeek],
        current: Weeks,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Create visualizations")
        self.week_filter = WeekFilter(files, weeks)
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        ok = self.buttons.button(QDialogButtonBox.StandardButton.Ok)
        self.week_filter.changed.connect(lambda: ok.setEnabled(self.week_filter.is_complete()))
        self.week_filter.show_weeks(files, weeks, current)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Choose the imported data to chart:"))
        layout.addWidget(self.week_filter)
        layout.addWidget(self.buttons)

    @staticmethod
    def choose(
        parent: QWidget, files: list[ImportedFile], weeks: list[SubmissionWeek], current: Weeks
    ) -> Weeks | None:
        dialog = WeekChooser(files, weeks, current, parent)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return None
        return dialog.week_filter.weeks()


class ChartPage(QWidget):
    """One chart's tab. A chart that takes a Technology Center has a drop-down to change it
    on the tab (6b). With `on_view_source`, a button shows the chart's source records
    (UC-FEAT-verify-source step 1)."""

    def __init__(
        self,
        chart: Chart,
        technology_centers: list[str],
        on_technology_center: Callable[[ChartPage, str], None],
        on_view_source: Callable[[ChartPage], None] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        layout = QVBoxLayout(self)
        self.view_source: QPushButton | None = None
        if on_view_source is not None:
            self.view_source = QPushButton("View source records")
            self.view_source.clicked.connect(lambda: on_view_source(self))
            row = QHBoxLayout()
            row.addWidget(self.view_source)
            row.addStretch(1)
            layout.addLayout(row)
        self.technology_center: QComboBox | None = None
        if TECHNOLOGY_CENTER in chart.result.metric.parameters:
            self.technology_center = QComboBox()
            self.technology_center.addItems(technology_centers)
            self.technology_center.setCurrentText(chart.result.parameters[TECHNOLOGY_CENTER])
            self.technology_center.currentTextChanged.connect(
                lambda value: on_technology_center(self, value)
            )
            row = QHBoxLayout()
            row.addWidget(QLabel("Technology Center:"))
            row.addWidget(self.technology_center)
            row.addStretch(1)
            layout.addLayout(row)
        layout.addWidget(self.scroll, stretch=1)


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
        choose_weeks: WeeksChooser = WeekChooser.choose,
        view_source: ViewSource | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._view_source = view_source
        self._runner = runner
        self._database = database
        self._choose = choose
        self._choose_weeks = choose_weeks
        self._offer_cleaning = offer_cleaning
        self._drill_down = drill_down
        # The charts created in this session, staged for export (step 7). Kept in memory only
        # (architecture section 7).
        self.charts: list[Chart] = []
        # The weeks every chart counts (6b).
        self.weeks = ALL_WEEKS

        self.create_button = QPushButton("Create visualizations")
        self.create_button.clicked.connect(self.create_visualizations)
        self.notices = QListWidget()
        self.notices.setMaximumHeight(90)
        self.week_filter = WeekFilter([], [])
        self.apply_weeks = QPushButton("Apply to all visualizations")
        self.apply_weeks.clicked.connect(self.change_weeks)
        self.week_filter.changed.connect(
            lambda: self.apply_weeks.setEnabled(self.week_filter.is_complete())
        )
        self.week_filter.top.addWidget(self.apply_weeks)
        self.week_filter.hide()  # until there are charts to recount
        self.tabs = QTabWidget()

        layout = QVBoxLayout(self)
        layout.addWidget(self.create_button)
        layout.addWidget(self.notices)
        layout.addWidget(self.week_filter)
        layout.addWidget(self.tabs, stretch=1)

    def create_visualizations(self) -> None:
        """Steps 1-7: confirm the data is staged, ask which weeks and then which metrics, run
        and draw each, and bring the charts already shown to the same weeks."""
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

        files = analytics.imported_files(self._database)
        weeks = analytics.submission_weeks(self._database)
        chosen_weeks = self._choose_weeks(self, files, weeks, self.weeks)
        if chosen_weeks is None:
            return
        technology_centers = analytics.technology_centers(self._database)
        choices = self._choose(self, metrics, technology_centers)
        if not choices:
            return

        self.weeks = chosen_weeks
        self.week_filter.show_weeks(files, weeks, chosen_weeks)
        self.week_filter.show()
        failed = []
        first_index = None
        for metric, parameters in choices:
            try:
                chart = self._count(metric.name, parameters)
            except MetricFailedError:
                failed.append(metric.title)  # logged by Analytics or Charts (5a1)
                continue
            index = self._show(chart, technology_centers)
            first_index = index if first_index is None else first_index
        if first_index is not None:
            self.tabs.setCurrentIndex(first_index)
        if failed:
            self.notices.addItem(
                f"These visualizations could not be created: {', '.join(failed)}. "
                "Details were written to the log file."
            )
        self._recount_all()

    def change_weeks(self) -> None:
        """6b: count every chart again over the weeks chosen above the tabs."""
        self.weeks = self.week_filter.weeks()
        self._recount_all()

    def on_bar_selected(self, chart: Chart, bar: Bar) -> None:
        """6a: hand the chart and the selected bar or segment to Provenance."""
        if self._drill_down is not None:
            self._drill_down(chart, bar.category, bar.series)

    def view_chart_source(self, page: ChartPage) -> None:
        """UC-FEAT-verify-source step 1: hand the tab's chart, as counted now, to Provenance."""
        if self._view_source is not None:
            self._view_source(self.charts[self.tabs.indexOf(page)])

    def page(self, index: int) -> ChartPage:
        return self.tabs.widget(index)

    def _count(self, name: str, parameters: dict[str, str]) -> Chart:
        return draw(analytics.run_metric(self._database, name, parameters, self.weeks))

    def _show(self, chart: Chart, technology_centers: list[str]) -> int:
        """Show `chart` on its own tab. A chart of the same metric replaces the one already
        shown, so the session holds the newest of each; the Technology Center is changed on
        the tab rather than opening another."""
        on_view_source = self.view_chart_source if self._view_source is not None else None
        page = ChartPage(chart, technology_centers, self._change_technology_center, on_view_source)
        self._set_chart(page, chart)
        for index, shown in enumerate(self.charts):
            if shown.result.metric.name == chart.result.metric.name:
                self.charts[index] = chart
                replaced = self.tabs.widget(index)
                self.tabs.removeTab(index)
                replaced.deleteLater()
                self.tabs.insertTab(index, page, chart.title)
                return index
        self.charts.append(chart)
        return self.tabs.addTab(page, chart.title)

    def _recount_all(self) -> None:
        """Count again each chart that does not count `self.weeks`. A chart that fails keeps
        what it showed, and the user is told it still counts the weeks before (5a)."""
        failed = []
        for index, shown in enumerate(self.charts):
            if shown.result.weeks == self.weeks:
                continue
            try:
                chart = self._count(shown.result.metric.name, dict(shown.result.parameters))
            except MetricFailedError:
                failed.append(shown.title)
                continue
            self.charts[index] = chart
            self._set_chart(self.page(index), chart)
        if failed:
            self.notices.addItem(
                f"These visualizations could not be counted for the chosen weeks and still "
                f"show the weeks they counted before: {', '.join(failed)}. "
                "Details were written to the log file."
            )

    def _change_technology_center(self, page: ChartPage, technology_center: str) -> None:
        """6b: redraw the tab's chart for another Technology Center, over the same weeks."""
        index = self.tabs.indexOf(page)
        shown = self.charts[index]
        parameters = {**shown.result.parameters, TECHNOLOGY_CENTER: technology_center}
        try:
            chart = self._count(shown.result.metric.name, parameters)
        except MetricFailedError:
            self.notices.addItem(
                f"{shown.result.metric.title} could not be counted for Technology Center "
                f"{technology_center}. Details were written to the log file."
            )
            page.technology_center.blockSignals(True)
            page.technology_center.setCurrentText(shown.result.parameters[TECHNOLOGY_CENTER])
            page.technology_center.blockSignals(False)
            return
        self.charts[index] = chart
        self._set_chart(page, chart)
        self.tabs.setTabText(index, chart.title)

    def _set_chart(self, page: ChartPage, chart: Chart) -> None:
        canvas = FigureCanvasQTAgg(chart.figure)
        figure = chart.figure
        canvas.setMinimumHeight(round(figure.get_figheight() * figure.dpi))
        if self._drill_down is not None:
            canvas.mpl_connect("pick_event", lambda event: self._on_pick(chart, event))
        page.scroll.setWidget(canvas)  # the scroll area deletes the canvas it held

    def _on_pick(self, chart: Chart, event: PickEvent) -> None:
        for bar in chart.bars:
            if bar.patch is event.artist:
                self.on_bar_selected(chart, bar)
                return
