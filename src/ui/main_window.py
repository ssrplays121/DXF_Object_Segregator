# ui/main_window.py
# Main application window with MVC architecture
# Implements document-centric workflow (Decision #28)
# Reference: https://www.riverbankcomputing.com/static/Docs/PyQt6/
from PyQt6.QtWidgets import (QMainWindow, QSplitter, QDockWidget, QTreeView,
                            QGraphicsView, QGraphicsScene, QStatusBar, QProgressBar,
                            QMessageBox, QFileDialog, QMenu, QToolBar, QLabel)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, pyqtSlot, QThread, QObject
from PyQt6.QtGui import QAction, QIcon, QColor
from typing import Dict, Any, Optional
import time
import logging
from models.object_node import ObjectTree
from engine.dxf_processor import DXFProcessor
from ui.hierarchy_sidebar import HierarchyModel, HierarchyDelegate
from ui.canvas_renderer import CanvasScene
from utils.logging import get_logger
from utils.error_handling import DXFProcessingError, GeometricError
from utils.benchmarking import benchmark_function
import json # Added for saving project

logger = get_logger(__name__)

class ProcessingWorker(QObject):
    """
    Worker class for background DXF processing
    Runs in separate thread to keep UI responsive (Decision #24)
    """
    finished = pyqtSignal(ObjectTree, float)  # tree, processing_time
    error = pyqtSignal(str, str)  # error_type, error_message
    progress = pyqtSignal(int, str)  # progress_percent, status_message

    def __init__(self, dxf_path: str, config: Dict[str, Any]):
        super().__init__()
        self.dxf_path = dxf_path
        self.config = config

    @pyqtSlot()
    def process_dxf(self):
        """Background processing of DXF file"""
        try:
            start_time = time.perf_counter()
            processor = DXFProcessor(config=self.config)
            # Process DXF file
            object_tree = processor.process_dxf(self.dxf_path)
            elapsed = time.perf_counter() - start_time
            self.finished.emit(object_tree, elapsed)
        except DXFProcessingError as e:
            self.error.emit("DXF Processing Error", str(e))
        except GeometricError as e:
            self.error.emit("Geometric Error", str(e))
        except Exception as e:
            self.error.emit("Unexpected Error", str(e))

class MainWindow(QMainWindow):
    """
    Main application window implementing document-centric workflow (Decision #28)
    Follows MVC pattern with clear separation of concerns (Decision #14)
    """
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__()
        self.config = config or {}
        self.current_file = None
        self.object_tree = None
        self.hierarchy_model = None
        self.canvas_scene = None
        self.processing_thread = None
        self.worker = None
        self._entity_cache = {} # Added for entity access

        # Initialize UI components
        self.setup_ui()
        self.setup_actions()
        self.setup_toolbar()
        self.setup_statusbar()
        self.setup_connections()

        # Set window properties
        self.setWindowTitle("DXF Object Segregator")
        self.setWindowState(Qt.WindowState.WindowMaximized)
        self.setMinimumSize(800, 600)
        logger.info("Main window initialized successfully")

    def setup_ui(self):
        """Initialize main UI components"""
        # Central widget with splitter
        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left sidebar: Hierarchy tree
        self.hierarchy_dock = QDockWidget("Object Hierarchy", self)
        self.hierarchy_dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable |
                                      QDockWidget.DockWidgetFeature.DockWidgetFloatable)
        self.hierarchy_view = QTreeView()
        self.hierarchy_view.setHeaderHidden(True)
        self.hierarchy_view.setItemDelegate(HierarchyDelegate())
        self.hierarchy_dock.setWidget(self.hierarchy_view)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.hierarchy_dock)

        # Right side: Canvas view
        self.canvas_view = QGraphicsView()
        self.canvas_view.setRenderHint(QGraphicsView.RenderHint.Antialiasing)
        self.canvas_view.setRenderHint(QGraphicsView.RenderHint.SmoothPixmapTransform)
        self.canvas_view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.canvas_view.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)

        # Create scene
        self.canvas_scene = CanvasScene()
        self.canvas_view.setScene(self.canvas_scene)

        # Set central widget
        self.setCentralWidget(self.canvas_view)

    def setup_actions(self):
        """Create menu actions"""
        # File menu
        self.file_menu = self.menuBar().addMenu("&File")
        self.open_action = QAction("&Open DXF...", self)
        self.open_action.setShortcut("Ctrl+O")
        self.open_action.triggered.connect(self.open_dxf_file)
        self.save_action = QAction("&Save Project...", self)
        self.save_action.setShortcut("Ctrl+S")
        self.save_action.setEnabled(False)
        self.save_action.triggered.connect(self.save_project)
        self.exit_action = QAction("E&xit", self)
        self.exit_action.setShortcut("Ctrl+Q")
        self.exit_action.triggered.connect(self.close)
        self.file_menu.addAction(self.open_action)
        self.file_menu.addAction(self.save_action)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.exit_action)

        # View menu
        self.view_menu = self.menuBar().addMenu("&View")
        self.zoom_in_action = QAction("Zoom &In", self)
        self.zoom_in_action.setShortcut("Ctrl++")
        self.zoom_in_action.triggered.connect(lambda: self.canvas_view.scale(1.2, 1.2))
        self.zoom_out_action = QAction("Zoom &Out", self)
        self.zoom_out_action.setShortcut("Ctrl+-")
        self.zoom_out_action.triggered.connect(lambda: self.canvas_view.scale(0.8, 0.8))
        self.fit_view_action = QAction("&Fit View", self)
        self.fit_view_action.setShortcut("Ctrl+F")
        self.fit_view_action.triggered.connect(self.fit_view_to_scene)
        self.view_menu.addAction(self.zoom_in_action)
        self.view_menu.addAction(self.zoom_out_action)
        self.view_menu.addAction(self.fit_view_action)

        # Help menu
        self.help_menu = self.menuBar().addMenu("&Help")
        self.about_action = QAction("&About", self)
        self.about_action.triggered.connect(self.show_about_dialog)
        self.help_menu.addAction(self.about_action)

    def setup_toolbar(self):
        """Create toolbar with common actions"""
        self.toolbar = QToolBar("Main Toolbar")
        self.toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(self.toolbar)
        self.toolbar.addAction(self.open_action)
        self.toolbar.addAction(self.save_action)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.zoom_in_action)
        self.toolbar.addAction(self.zoom_out_action)
        self.toolbar.addAction(self.fit_view_action)

    def setup_statusbar(self):
        """Create status bar with progress indicator"""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setVisible(False)
        self.statusbar.addPermanentWidget(self.progress_bar)
        self.status_label = QLabel("Ready")
        self.statusbar.addWidget(self.status_label)

    def setup_connections(self):
        """Setup signal/slot connections"""
        # Connect hierarchy view to canvas updates
        self.hierarchy_view.expanded.connect(self.on_hierarchy_expanded)
        self.hierarchy_view.collapsed.connect(self.on_hierarchy_collapsed)
        # Additional connections would be set up here...

    def open_dxf_file(self):
        """Open DXF file dialog and start processing"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open DXF File", "", "DXF Files (*.dxf);;All Files (*.*)"
        )
        if not file_path:
            return

        self.current_file = file_path
        self.setWindowTitle(f"DXF Object Segregator - {file_path}")
        self.status_label.setText(f"Loading: {file_path}")

        # Start background processing
        self.start_processing_thread(file_path)

    def start_processing_thread(self, dxf_path: str):
        """Start background thread for DXF processing"""
        if self.processing_thread and self.processing_thread.isRunning():
            self.processing_thread.quit()
            self.processing_thread.wait()

        self.processing_thread = QThread()
        self.worker = ProcessingWorker(dxf_path, self.config)

        # Move worker to thread
        self.worker.moveToThread(self.processing_thread)

        # Connect signals
        self.processing_thread.started.connect(self.worker.process_dxf)
        self.worker.finished.connect(self.on_processing_finished)
        self.worker.error.connect(self.on_processing_error)
        self.worker.progress.connect(self.on_processing_progress)
        self.processing_thread.finished.connect(self.worker.deleteLater)

        # Show progress bar
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(100)

        # Start thread
        self.processing_thread.start()
        logger.info(f"Started background processing thread for {dxf_path}")

    @pyqtSlot(ObjectTree, float)
    def on_processing_finished(self, object_tree: ObjectTree, processing_time: float):
        """Handle completed DXF processing"""
        self.processing_thread.quit()
        self.processing_thread.wait()
        self.object_tree = object_tree
        self.progress_bar.setVisible(False)

        # Update UI with results
        self.update_hierarchy_view()
        self.update_canvas_view()
        self.save_action.setEnabled(True)

        # Show completion message
        self.status_label.setText(f"Processing completed in {processing_time:.2f}s")
        QMessageBox.information(
            self,
            "Processing Complete",
            f"Successfully processed {len(object_tree.nodes)} objects in {processing_time:.2f} seconds"
        )
        logger.info(f"Processing completed successfully in {processing_time:.2f}s")

    @pyqtSlot(str, str)
    def on_processing_error(self, error_type: str, error_message: str):
        """Handle processing errors"""
        self.processing_thread.quit()
        self.processing_thread.wait()
        self.progress_bar.setVisible(False)

        # Show error message
        QMessageBox.critical(
            self,
            f"{error_type} - Processing Failed",
            error_message
        )
        self.status_label.setText(f"Error: {error_type}")
        logger.error(f"{error_type}: {error_message}")

    @pyqtSlot(int, str)
    def on_processing_progress(self, progress: int, message: str):
        """Update progress bar and status"""
        self.progress_bar.setValue(progress)
        self.status_label.setText(message)

    def update_hierarchy_view(self):
        """Update hierarchy tree view with object tree"""
        if not self.object_tree:
            return
        self.hierarchy_model = HierarchyModel(self.object_tree)
        self.hierarchy_view.setModel(self.hierarchy_model)
        # Expand root node by default
        if self.object_tree.root_id:
            root_index = self.hierarchy_model.get_index_by_id(self.object_tree.root_id)
            if root_index.isValid():
                self.hierarchy_view.expand(root_index)

    def update_canvas_view(self):
        """Update canvas with rendered entities"""
        if not self.object_tree or not self.canvas_scene:
            return

        # Clear existing scene
        self.canvas_scene.clear()

        # Render entities with default colors
        for node_id, node in self.object_tree.nodes.items():
            if node.entity_ids:
                for entity_id in node.entity_ids:
                    entity = self._get_entity_by_id(entity_id)
                    if entity:
                        self.canvas_scene.add_entity(entity, node_id)

        # Fit view to scene contents
        self.fit_view_to_scene()

    def fit_view_to_scene(self):
        """Fit view to scene contents"""
        if not self.canvas_scene or not self.canvas_scene.items():
            return
        scene_rect = self.canvas_scene.itemsBoundingRect()
        if not scene_rect.isEmpty():
            self.canvas_view.fitInView(scene_rect, Qt.AspectRatioMode.KeepAspectRatio)

    def _get_entity_by_id(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get entity data by ID (placeholder for actual implementation)"""
        # In a real implementation, this would access the entity data
        # from the DXF processor or a shared data model
        # For now, it uses the internal cache populated after processing
        return self._entity_cache.get(entity_id)

    def _update_entity_cache(self, entities: Dict[str, Any]):
        """Update internal entity cache for UI access"""
        self._entity_cache = entities
        logger.debug(f"Updated entity cache with {len(entities)} entities")

    def save_project(self):
        """Save project to file"""
        if not self.object_tree:
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Project", "", "JSON Files (*.json);;All Files (*.*)"
        )
        if not file_path:
            return
        try:
            # Serialize object tree to JSON (Decision #16)
            tree_data = self.object_tree.to_dict()
            with open(file_path, 'w') as f:
                json.dump(tree_data, f, indent=2)
            self.status_label.setText(f"Project saved to: {file_path}")
            logger.info(f"Project saved successfully to {file_path}")
        except Exception as e:
            QMessageBox.critical(
                self,
                "Save Failed",
                f"Failed to save project: {str(e)}"
            )
            logger.error(f"Save failed: {str(e)}")

    def show_about_dialog(self):
        """Show about dialog"""
        about_text = """
<h2>DXF Object Segregator</h2>
<p>Version 0.1.0</p>
<p>A tool for segregating DXF entities into hierarchical objects</p>
<p><b>Features:</b></p>
<ul>
<li>Multiple algorithm modes for vertex sharing and intersection detection</li>
<li>Hybrid containment testing (bounding box + geometric)</li>
<li>Benchmarking suite for algorithm comparison</li>
<li>Hierarchical color and visibility overrides</li>
<li>Multi-platform native installers</li>
</ul>
<p><b>Architecture:</b></p>
<ul>
<li>Cython for performance-critical geometric algorithms</li>
<li>Strict layer separation with MVC UI</li>
<li>Document-centric workflow</li>
<li>Structured logging and error handling</li>
</ul>
"""
        QMessageBox.about(self, "About DXF Object Segregator", about_text)

    def closeEvent(self, event):
        """Handle window close event"""
        if self.processing_thread and self.processing_thread.isRunning():
            reply = QMessageBox.question(
                self,
                "Processing in Progress",
                "DXF processing is still running. Are you sure you want to quit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return

        # Clean up threads
        if self.processing_thread:
            self.processing_thread.quit()
            self.processing_thread.wait()
        event.accept()
        logger.info("Application closed successfully")
