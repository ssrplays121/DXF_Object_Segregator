"""Toolbar widget."""

from PyQt6.QtWidgets import QToolBar, QSpinBox, QComboBox
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtCore import Qt


class Toolbar(QToolBar):
    """Application toolbar."""

    def __init__(self, parent=None):
        """Initialize the toolbar."""
        super().__init__("Main Toolbar", parent)
        self.setObjectName("MainToolbar")

        # File operations
        self.open_action = QAction("Open", self)
        self.open_action.setShortcut("Ctrl+O")
        self.addAction(self.open_action)

        self.save_action = QAction("Save", self)
        self.save_action.setShortcut("Ctrl+S")
        self.addAction(self.save_action)

        self.addSeparator()

        # View operations
        self.zoom_in_action = QAction("Zoom In", self)
        self.zoom_in_action.setShortcut("+")
        self.addAction(self.zoom_in_action)

        self.zoom_out_action = QAction("Zoom Out", self)
        self.zoom_out_action.setShortcut("-")
        self.addAction(self.zoom_out_action)

        self.fit_view_action = QAction("Fit View", self)
        self.fit_view_action.setShortcut("F")
        self.addAction(self.fit_view_action)

        self.addSeparator()

        # Display options
        self.addWidget(self._create_layer_selector())
        self.addWidget(self._create_entity_type_selector())

    def _create_layer_selector(self) -> QComboBox:
        """Create layer selector combo box."""
        combo = QComboBox()
        combo.addItem("All Layers")
        combo.setMaximumWidth(150)
        return combo

    def _create_entity_type_selector(self) -> QComboBox:
        """Create entity type selector combo box."""
        combo = QComboBox()
        combo.addItem("All Types")
        combo.addItem("Lines")
        combo.addItem("Circles")
        combo.addItem("Arcs")
        combo.addItem("Polygons")
        combo.setMaximumWidth(150)
        return combo
