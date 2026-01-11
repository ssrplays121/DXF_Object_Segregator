"""About dialog."""

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt


class AboutDialog(QDialog):
    """About dialog displaying application information."""

    def __init__(self, parent=None):
        """Initialize the about dialog."""
        super().__init__(parent)
        self.setWindowTitle("About DXF Object Segregator")
        self.setGeometry(200, 200, 400, 300)

        layout = QVBoxLayout()

        title = QLabel("<h2>DXF Object Segregator</h2>")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        version = QLabel("<p><b>Version:</b> 0.1.0</p>")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version)

        description = QLabel(
            "<p>A tool for analyzing and segregating objects in DXF files.</p>"
            "<p><b>Features:</b></p>"
            "<ul>"
            "<li>Object hierarchy visualization</li>"
            "<li>Geometric analysis</li>"
            "<li>Vertex sharing detection</li>"
            "<li>Intersection detection</li>"
            "<li>Containment analysis</li>"
            "</ul>"
        )
        layout.addWidget(description)

        copyright_text = QLabel(
            "<p>© 2024 DXF Object Segregator Contributors</p>"
            "<p>Licensed under the MIT License</p>"
        )
        copyright_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(copyright_text)

        layout.addStretch()

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)

        self.setLayout(layout)
