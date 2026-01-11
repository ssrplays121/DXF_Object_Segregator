# ui/hierarchy_sidebar.py
# Hierarchy tree view components with custom delegates
# Implements hierarchical override system for visibility and recolorization (Decision #15)
# Reference: https://doc.qt.io/qt-6/model-view-programming.html
from PyQt6.QtWidgets import (QStyledItemDelegate, QStyleOptionViewItem, QStyle,
                            QWidget, QCheckBox, QPushButton, QColorDialog, QVBoxLayout,
                            QHBoxLayout, QLabel, QFrame)
from PyQt6.QtCore import Qt, QSize, QRect, QModelIndex, pyqtSignal, QAbstractItemModel
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QIcon, QPixmap
from typing import Dict, Any, Optional
from models.object_node import ObjectNode, ObjectTree
import logging
from utils.logging import get_logger

logger = get_logger(__name__)

class HierarchyModel(QAbstractItemModel):
    """
    Model for object hierarchy tree
    Implements hierarchical data model with unique object IDs (Decision #7)
    """
    def __init__(self, object_tree: ObjectTree = None, parent=None):
        super().__init__(parent)
        self.object_tree = object_tree
        self.root_index = QModelIndex()
        # Cache for performance
        self._index_cache = {}
        if object_tree and object_tree.root_id:
            self.root_index = self.createIndex(0, 0, object_tree.root_id)

    def set_object_tree(self, object_tree: ObjectTree):
        """Update model with new object tree"""
        self.beginResetModel()
        self.object_tree = object_tree
        self._index_cache.clear()
        if object_tree and object_tree.root_id:
            self.root_index = self.createIndex(0, 0, object_tree.root_id)
        else:
            self.root_index = QModelIndex()
        self.endResetModel()

    def get_index_by_id(self, node_id: str) -> QModelIndex:
        """Get model index for node ID"""
        if not self.object_tree or node_id not in self.object_tree.nodes:
            return QModelIndex()
        # Simple implementation - in real app would use more efficient caching
        return self._find_index_recursive(self.root_index, node_id)

    def _find_index_recursive(self, parent_index: QModelIndex, target_id: str) -> QModelIndex:
        """Find index recursively (placeholder for efficient implementation)"""
        if not parent_index.isValid():
            return QModelIndex()

        node_id = parent_index.internalPointer()
        if node_id == target_id:
            return parent_index

        # Check children
        for row in range(self.rowCount(parent_index)):
            child_index = self.index(row, 0, parent_index)
            result = self._find_index_recursive(child_index, target_id)
            if result.isValid():
                return result
        return QModelIndex()

    # QAbstractItemModel implementation methods
    def index(self, row: int, column: int, parent: QModelIndex = QModelIndex()) -> QModelIndex:
        """Create model index for given row, column, parent"""
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if not parent.isValid():
            # Root level - only root node
            if self.object_tree and self.object_tree.root_id:
                return self.createIndex(row, column, self.object_tree.root_id)
            return QModelIndex()

        # Get parent node
        parent_id = parent.internalPointer()
        parent_node = self.object_tree.get_node(parent_id)

        # Get child node ID at this row
        child_ids = list(parent_node.children_ids)
        if row < len(child_ids):
            return self.createIndex(row, column, child_ids[row])
        return QModelIndex()

    def parent(self, index: QModelIndex) -> QModelIndex:
        """Get parent index for given index"""
        if not index.isValid():
            return QModelIndex()

        node_id = index.internalPointer()
        node = self.object_tree.get_node(node_id)
        if not node.parent_ids:
            return QModelIndex()  # Root node has no parent

        # For simplicity, use first parent (in real app, handle multiple parents)
        parent_id = next(iter(node.parent_ids), None)
        if not parent_id:
             return QModelIndex()
        parent_node = self.object_tree.get_node(parent_id)

        # Find row of this node in parent's children
        row = 0
        for child_id in parent_node.children_ids:
            if child_id == node_id:
                break
            row += 1
        return self.createIndex(row, 0, parent_id)

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Get number of rows under parent"""
        if not self.object_tree:
            return 0

        if not parent.isValid():
            # Root level - only root node
            return 1 if self.object_tree.root_id else 0

        node_id = parent.internalPointer()
        node = self.object_tree.get_node(node_id)
        return len(node.children_ids)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Number of columns (always 1 for hierarchy)"""
        return 1

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        """Get data for given index and role"""
        if not index.isValid():
            return None

        node_id = index.internalPointer()
        node = self.object_tree.get_node(node_id)

        if role == Qt.ItemDataRole.DisplayRole:
            # Display name for node
            if node.is_root:
                return "Root"
            elif node.metadata.get('name'):
                return node.metadata['name']
            elif len(node.entity_ids) == 1:
                return f"Entity {list(node.entity_ids)[0]}"
            else:
                return f"Object {node.id[:8]}"
        elif role == Qt.ItemDataRole.UserRole:
            # Custom role for node ID
            return node_id
        elif role == Qt.ItemDataRole.DecorationRole:
            # Icon based on node type
            if node.is_root:
                return QIcon(":/icons/root.png")
            elif len(node.entity_ids) == 1:
                return QIcon(":/icons/entity.png")
            else:
                return QIcon(":/icons/object.png")
        return None

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        """Get flags for index"""
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        return super().flags(index) | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable


class VisibilityButton(QPushButton):
    """Custom button for visibility toggle"""
    visibility_changed = pyqtSignal(bool)

    def __init__(self, visible: bool = True, parent=None):
        super().__init__(parent)
        self.visible = visible
        self.setCheckable(True)
        self.setChecked(visible)
        self.setFixedSize(20, 20)
        self.setToolTip("Toggle visibility")
        self.clicked.connect(self.on_clicked)
        self.update_style()

    def on_clicked(self, checked: bool):
        self.visible = checked
        self.update_style()
        self.visibility_changed.emit(checked)

    def update_style(self):
        """Update button style based on visibility state"""
        if self.visible:
            self.setStyleSheet("""
QPushButton {
    background-color: #4CAF50;
    border: none;
    border-radius: 10px;
}
QPushButton:hover {
    background-color: #45a049;
}
QPushButton:pressed {
    background-color: #3d8b40;
}
""")
            # self.setIcon(QIcon(":/icons/visible.png")) # Requires resource file
        else:
            self.setStyleSheet("""
QPushButton {
    background-color: #f44336;
    border: none;
    border-radius: 10px;
}
QPushButton:hover {
    background-color: #e53935;
}
QPushButton:pressed {
    background-color: #d32f2f;
}
""")
            # self.setIcon(QIcon(":/icons/hidden.png")) # Requires resource file

    def sizeHint(self):
        return QSize(20, 20)


class ColorButton(QPushButton):
    """Custom button for color selection"""
    color_changed = pyqtSignal(QColor)

    def __init__(self, color: QColor = None, parent=None):
        super().__init__(parent)
        self.color = color or QColor(255, 255, 255)
        self.setFixedSize(20, 20)
        self.setToolTip("Change color")
        self.clicked.connect(self.on_clicked)
        self.update_style()

    def on_clicked(self):
        color = QColorDialog.getColor(self.color, self, "Select Color")
        if color.isValid():
            self.color = color
            self.update_style()
            self.color_changed.emit(color)

    def update_style(self):
        """Update button style based on color"""
        self.setStyleSheet(f"""
QPushButton {{
    background-color: {self.color.name()};
    border: 1px solid #666;
    border-radius: 10px;
}}
QPushButton:hover {{
    border: 1px solid #000;
}}
""")

    def sizeHint(self):
        return QSize(20, 20)


class HierarchyDelegate(QStyledItemDelegate):
    """
    Custom delegate for hierarchy tree view
    Implements visibility toggle and color override controls (Decision #15)
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.visibility_cache = {}
        self.color_cache = {}

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        """Custom painting for tree items"""
        # Draw default background
        style = option.widget.style() if option.widget else None
        if style:
            style.drawPrimitive(QStyle.PrimitiveElement.PE_PanelItemViewItem, option, painter, option.widget)
        else:
            # Fallback if no widget style
            painter.fillRect(option.rect, option.backgroundBrush)

        # Get node data
        node_id = index.internalPointer()
        model = index.model()
        if not hasattr(model, 'object_tree'):
             # If model doesn't have object_tree, use default painting
            super().paint(painter, option, index)
            return
        node = model.object_tree.get_node(node_id)

        # Draw icon
        icon = index.data(Qt.ItemDataRole.DecorationRole)
        if icon and not icon.isNull():
            icon_rect = QRect(option.rect.left() + 5,
                              option.rect.top() + (option.rect.height() - 16) // 2,
                              16, 16)
            icon.paint(painter, icon_rect)

        # Draw text
        text = index.data(Qt.ItemDataRole.DisplayRole)
        text_rect = QRect(option.rect.left() + 30, option.rect.top(),
                          option.rect.width() - 200, option.rect.height())
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter, str(text))

        # Draw visibility button
        visibility_rect = QRect(option.rect.right() - 80,
                                option.rect.top() + (option.rect.height() - 20) // 2,
                                20, 20)
        self.draw_visibility_button(painter, visibility_rect, node_id)

        # Draw color button
        color_rect = QRect(option.rect.right() - 50,
                           option.rect.top() + (option.rect.height() - 20) // 2,
                           20, 20)
        self.draw_color_button(painter, color_rect, node_id)

    def draw_visibility_button(self, painter: QPainter, rect: QRect, node_id: str):
        """Draw visibility button"""
        visible = self.visibility_cache.get(node_id, True)
        color = QColor(76, 175, 80) if visible else QColor(244, 67, 54)

        # Draw button background
        painter.save()
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(rect)

        # Draw icon
        if visible:
            # Draw eye icon (simplified as X for now)
            painter.setPen(QPen(Qt.GlobalColor.white, 2))
            painter.drawLine(rect.left() + 4, rect.top() + 4,
                             rect.right() - 4, rect.bottom() - 4)
            painter.drawLine(rect.left() + 4, rect.bottom() - 4,
                             rect.right() - 4, rect.top() + 4)
        else:
            # Draw crossed eye icon (simplified as X for now)
            painter.setPen(QPen(Qt.GlobalColor.white, 2))
            painter.drawLine(rect.left() + 4, rect.top() + 4,
                             rect.right() - 4, rect.bottom() - 4)
            painter.drawLine(rect.left() + 4, rect.bottom() - 4,
                             rect.right() - 4, rect.top() + 4)
            # Diagonal cross
            painter.setPen(QPen(Qt.GlobalColor.white, 3))
            painter.drawLine(rect.left(), rect.bottom(),
                             rect.right(), rect.top())

        painter.restore()

    def draw_color_button(self, painter: QPainter, rect: QRect, node_id: str):
        """Draw color button"""
        color = self.color_cache.get(node_id, QColor(255, 255, 255))

        # Draw button background
        painter.save()
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(Qt.GlobalColor.black, 1))
        painter.drawEllipse(rect)
        painter.restore()

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        """Custom size hint"""
        return QSize(super().sizeHint(option, index).width(), 30)

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem,
                     index: QModelIndex) -> QWidget:
        """Create editor widget for item"""
        # Custom editor not needed for this delegate
        return None

    def updateEditorGeometry(self, editor: QWidget, option: QStyleOptionViewItem,
                             index: QModelIndex):
        """Update editor geometry"""
        editor.setGeometry(option.rect)
