"""Light theme for the application."""


def get_light_stylesheet() -> str:
    """Get the light theme stylesheet."""
    return """
    QMainWindow {
        background-color: #ffffff;
        color: #000000;
    }
    
    QWidget {
        background-color: #ffffff;
        color: #000000;
    }
    
    QToolBar {
        background-color: #f0f0f0;
        border-bottom: 1px solid #cccccc;
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
        background-color: #ffffff;
        color: #000000;
        border: 1px solid #cccccc;
    }
    
    QMenuBar {
        background-color: #f0f0f0;
        color: #000000;
    }
    
    QMenu {
        background-color: #ffffff;
        color: #000000;
    }
    """
