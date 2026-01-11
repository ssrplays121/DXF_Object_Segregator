"""Dark theme for the application."""


def get_dark_stylesheet() -> str:
    """Get the dark theme stylesheet."""
    return """
    QMainWindow {
        background-color: #2d2d2d;
        color: #ffffff;
    }
    
    QWidget {
        background-color: #2d2d2d;
        color: #ffffff;
    }
    
    QToolBar {
        background-color: #3d3d3d;
        border-bottom: 1px solid #1d1d1d;
    }
    
    QPushButton {
        background-color: #007acc;
        color: #ffffff;
        border: none;
        border-radius: 4px;
        padding: 5px 15px;
    }
    
    QPushButton:hover {
        background-color: #005a9e;
    }
    
    QTreeWidget {
        background-color: #3d3d3d;
        color: #ffffff;
        border: 1px solid #1d1d1d;
    }
    
    QMenuBar {
        background-color: #3d3d3d;
        color: #ffffff;
    }
    
    QMenu {
        background-color: #3d3d3d;
        color: #ffffff;
    }
    """
