"""The main window and its view tabs (UI-main-views). Release 1.0 views are added as their
use cases are built; this slice adds Import."""

from PySide6.QtWidgets import QMainWindow, QTabWidget, QWidget

from patent_intelligence.settings import APP_NAME


class MainWindow(QMainWindow):
    def __init__(self, import_view: QWidget) -> None:
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(900, 600)
        self.tabs = QTabWidget()
        self.tabs.addTab(import_view, "Import")
        self.setCentralWidget(self.tabs)
