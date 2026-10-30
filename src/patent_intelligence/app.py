"""The entry point that PyInstaller packages."""

import logging
import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from patent_intelligence import settings, storage
from patent_intelligence.errors import AppError
from patent_intelligence.jobs.runner import JobRunner
from patent_intelligence.logging_setup import configure_logging
from patent_intelligence.ui.charts_view import ChartsView
from patent_intelligence.ui.import_view import ImportView
from patent_intelligence.ui.main_window import MainWindow

log = logging.getLogger(__name__)


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
    # Drilling into a bar (6a) is wired when Provenance is built (UC-FEAT-verify-source).
    window = MainWindow(ImportView(runner, database), ChartsView(runner, database))
    window.show()
    exit_code = app.exec()
    runner.shutdown(wait=False)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
