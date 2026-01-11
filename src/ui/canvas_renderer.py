# ui/canvas_renderer.py
from PyQt6.QtWidgets import QGraphicsScene, QGraphicsLineItem, QGraphicsEllipseItem
from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QPen, QColor, QBrush
from typing import Dict, Any, Optional
import logging
from utils.logging import get_logger

logger = get_logger(__name__)

class CanvasScene(QGraphicsScene):
    """
    Custom QGraphicsScene for rendering DXF entities
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.entity_items = {}  # entity_id -> QGraphicsItem
        self.object_colors = {}  # object_id -> QColor
        self.visibility_states = {}  # object_id -> bool
    
    def add_entity(self, entity: Dict[str, Any], object_id: str):
        """
        Add entity to scene with object-specific styling
        """
        if not entity:
            return
        
        color = self.object_colors.get(object_id, QColor(255, 255, 255))
        visible = self.visibility_states.get(object_id, True)
        
        if entity['type'] == 'LINE':
            line = QGraphicsLineItem(
                entity['start'][0], entity['start'][1],
                entity['end'][0], entity['end'][1]
            )
            pen = QPen(color, 1.0)
            line.setPen(pen)
            line.setVisible(visible)
            self.addItem(line)
            self.entity_items[entity['id']] = line
            
        elif entity['type'] == 'CIRCLE':
            radius = entity['radius']
            circle = QGraphicsEllipseItem(
                entity['center'][0] - radius,
                entity['center'][1] - radius,
                radius * 2,
                radius * 2
            )
            pen = QPen(color, 1.0)
            brush = QBrush(Qt.BrushStyle.NoBrush)
            circle.setPen(pen)
            circle.setBrush(brush)
            circle.setVisible(visible)
            self.addItem(circle)
            self.entity_items[entity['id']] = circle
    
    def set_object_color(self, object_id: str, color: QColor):
        """
        Set color for all entities in an object
        """
        self.object_colors[object_id] = color
        
        # Update existing items
        for entity_id, item in self.entity_items.items():
            # In real implementation, would need mapping from entity to object
            item.setPen(QPen(color, 1.0))
    
    def set_object_visibility(self, object_id: str, visible: bool):
        """
        Set visibility for all entities in an object
        """
        self.visibility_states[object_id] = visible
        
        # Update existing items
        for entity_id, item in self.entity_items.items():
            # In real implementation, would need mapping from entity to object
            item.setVisible(visible)
    
    def clear_entities(self):
        """
        Clear all entities from scene
        """
        for item in self.entity_items.values():
            self.removeItem(item)
        self.entity_items.clear()
