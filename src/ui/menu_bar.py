"""Menu bar widget."""

from PyQt6.QtWidgets import QMenuBar, QMenu, QMessageBox
from PyQt6.QtGui import QAction


class MenuBar(QMenuBar):
    """Application menu bar."""

    def __init__(self, parent=None):
        """Initialize the menu bar."""
        super().__init__(parent)
        self.parent = parent

        # File menu
        self.file_menu = self.addMenu("&File")
        self._setup_file_menu()

        # Edit menu
        self.edit_menu = self.addMenu("&Edit")
        self._setup_edit_menu()

        # View menu
        self.view_menu = self.addMenu("&View")
        self._setup_view_menu()

        # Tools menu
        self.tools_menu = self.addMenu("&Tools")
        self._setup_tools_menu()

        # Help menu
        self.help_menu = self.addMenu("&Help")
        self._setup_help_menu()

    def _setup_file_menu(self):
        """Setup File menu."""
        open_action = QAction("&Open", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.parent.open_file)
        self.file_menu.addAction(open_action)

        save_action = QAction("&Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.parent.save_file)
        self.file_menu.addAction(save_action)

        self.file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.parent.close_application)
        self.file_menu.addAction(exit_action)

    def _setup_edit_menu(self):
        """Setup Edit menu."""
        undo_action = QAction("&Undo", self)
        undo_action.setShortcut("Ctrl+Z")
        self.edit_menu.addAction(undo_action)

        redo_action = QAction("&Redo", self)
        redo_action.setShortcut("Ctrl+Y")
        self.edit_menu.addAction(redo_action)

        self.edit_menu.addSeparator()

        settings_action = QAction("&Settings", self)
        settings_action.triggered.connect(lambda: self._show_settings())
        self.edit_menu.addAction(settings_action)

    def _setup_view_menu(self):
        """Setup View menu."""
        zoom_in_action = QAction("Zoom &In", self)
        zoom_in_action.setShortcut("+")
        self.view_menu.addAction(zoom_in_action)

        zoom_out_action = QAction("Zoom &Out", self)
        zoom_out_action.setShortcut("-")
        self.view_menu.addAction(zoom_out_action)

        self.view_menu.addSeparator()

        fit_view_action = QAction("&Fit View", self)
        fit_view_action.setShortcut("F")
        self.view_menu.addAction(fit_view_action)

    def _setup_tools_menu(self):
        """Setup Tools menu."""
        analysis_action = QAction("&Run Analysis", self)
        self.tools_menu.addAction(analysis_action)

        benchmark_action = QAction("&Benchmark", self)
        self.tools_menu.addAction(benchmark_action)

    def _setup_help_menu(self):
        """Setup Help menu."""
        about_action = QAction("&About", self)
        about_action.triggered.connect(lambda: self._show_about())
        self.help_menu.addAction(about_action)

    def _show_settings(self):
        """Show settings dialog."""
        # TODO: Implement settings dialog
        pass

    def _show_about(self):
        """Show about dialog."""
        QMessageBox.information(
            self.parent,
            "About DXF Object Segregator",
            "DXF Object Segregator v0.1.0\n\n"
            "A tool for analyzing and segregating objects in DXF files.\n\n"
            "© 2024 Contributors"
        )
