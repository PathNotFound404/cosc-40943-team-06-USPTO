"""The entry point that PyInstaller packages."""

import logging
import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from patent_intelligence import settings, storage
from patent_intelligence.analytics import MetricResult
from patent_intelligence.errors import AppError
from patent_intelligence.jobs.runner import JobRunner
from patent_intelligence.logging_setup import configure_logging
from patent_intelligence.provenance import Selection
from patent_intelligence.storage import Database
from patent_intelligence.ui.charts_view import ChartsView
from patent_intelligence.ui.export_view import ExportView
from patent_intelligence.ui.import_view import ImportView
from patent_intelligence.ui.main_window import MainWindow
from patent_intelligence.ui.sources_view import SourcesView

log = logging.getLogger(__name__)


def build_window(runner: JobRunner, database: Database, **chart_options) -> MainWindow:
    """The main window with its views wired together: a chart tab's "View source records"
    and a click on a bar open the Sources view (UC-FEAT-verify-source step 1,
    UC-FEAT-create-visuals 6a), 2a2 goes back to creating visualizations, and the Export
    view lists the charts created in this session (UC-FEAT-export-visuals step 2).
    `chart_options` are passed to ChartsView, for tests."""

    def show_sources(result: MetricResult, selection: Selection | None) -> None:
        window.tabs.setCurrentWidget(sources_view)
        sources_view.show_sources(result, selection)

    def recreate() -> None:
        window.tabs.setCurrentWidget(charts_view)
        charts_view.create_visualizations()

    sources_view = SourcesView(database, recreate)
    charts_view = ChartsView(
        runner,
        database,
        drill_down=lambda chart, category, series: show_sources(
            chart.result, Selection(category, series)
        ),
        view_source=lambda chart: show_sources(chart.result, None),
        **chart_options,
    )
    export_view = ExportView(database, lambda: charts_view.charts)
    window = MainWindow(ImportView(runner, database), charts_view, sources_view, export_view)
    return window


def main() -> int:
    app = QApplication(sys.argv)
    data_folder = settings.data_folder()
    try:
        try:
            configure_logging(data_folder)
        except OSError as error:
            raise AppError(f"The data folder {data_folder} could not be written to.") from error
        database = storage.open(data_folder)
    except AppError as error:
        log.exception("Start-up failed")
        QMessageBox.critical(None, settings.APP_NAME, error.message)
        return 1

    runner = JobRunner()
    window = build_window(runner, database)
    window.show()
    exit_code = app.exec()
    runner.shutdown(wait=False)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
