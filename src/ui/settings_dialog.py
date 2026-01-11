"""Settings dialog."""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QCheckBox, QSpinBox, QComboBox, QPushButton)


class SettingsDialog(QDialog):
    """Settings dialog for application configuration."""

    def __init__(self, parent=None):
        """Initialize the settings dialog."""
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setGeometry(200, 200, 400, 300)

        layout = QVBoxLayout()

        # Theme settings
        theme_label = QLabel("Theme:")
        theme_combo = QComboBox()
        theme_combo.addItem("Light")
        theme_combo.addItem("Dark")
        layout.addWidget(theme_label)
        layout.addWidget(theme_combo)

        layout.addSpacing(20)

        # Grid settings
        grid_label = QLabel("Grid Settings:")
        grid_size_label = QLabel("Grid Size:")
        grid_size_spinbox = QSpinBox()
        grid_size_spinbox.setMinimum(10)
        grid_size_spinbox.setMaximum(500)
        grid_size_spinbox.setValue(50)

        layout.addWidget(grid_label)
        layout.addWidget(grid_size_label)
        layout.addWidget(grid_size_spinbox)

        layout.addSpacing(20)

        # Analysis settings
        analysis_label = QLabel("Analysis Settings:")
        vertex_tolerance_label = QLabel("Vertex Tolerance:")
        vertex_tolerance_spinbox = QSpinBox()
        vertex_tolerance_spinbox.setMinimum(1)
        vertex_tolerance_spinbox.setMaximum(1000)
        vertex_tolerance_spinbox.setValue(100)

        layout.addWidget(analysis_label)
        layout.addWidget(vertex_tolerance_label)
        layout.addWidget(vertex_tolerance_spinbox)

        layout.addStretch()

        # Buttons
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)
