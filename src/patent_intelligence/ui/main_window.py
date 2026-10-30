"""The main window and its view tabs (UI-main-views). Release 1.0 views are added as their
use cases are built: Import, then Visualizations. How the chart tabs map onto Weekly Overview,
Art Units, and Trends waits on wireframes (OI-18)."""

from PySide6.QtWidgets import QMainWindow, QTabWidget, QWidget

from patent_intelligence.settings import APP_NAME


class MainWindow(QMainWindow):
    def __init__(self, import_view: QWidget, charts_view: QWidget | None = None) -> None:
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(900, 600)
        self.tabs = QTabWidget()
        self.tabs.addTab(import_view, "Import")
        if charts_view is not None:
            self.tabs.addTab(charts_view, "Visualizations")
        self.setCentralWidget(self.tabs)
