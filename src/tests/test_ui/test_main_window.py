"""Tests for main window."""

import pytest
from PyQt6.QtWidgets import QApplication


@pytest.fixture(scope="module")
def qapp():
    """Create a QApplication for testing."""
    app = QApplication([])
    yield app
    app.quit()


class TestMainWindow:
    """Test cases for MainWindow."""

    def test_main_window_creation(self, qapp):
        """Test creating the main window."""
        from ui.main_window import MainWindow
        window = MainWindow()
        assert window.windowTitle() == "DXF Object Segregator"
        window.close()

    def test_main_window_components(self, qapp):
        """Test main window components are initialized."""
        from ui.main_window import MainWindow
        window = MainWindow()
        assert window.sidebar is not None
        assert window.canvas is not None
        assert window.toolbar is not None
        assert window.menu_bar is not None
        window.close()
