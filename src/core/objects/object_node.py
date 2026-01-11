"""Object node representation for the hierarchy."""

from typing import List, Dict, Any, Optional


class ObjectNode:
    """Represents a node in the object hierarchy."""

    def __init__(self, object_id: str, entity_type: str, data: Dict[str, Any] = None):
        """
        Initialize an object node.

        Args:
            object_id: Unique identifier for the object.
            entity_type: Type of the entity (e.g., 'LINE', 'CIRCLE').
            data: Additional object data.
        """
        self.object_id = object_id
        self.entity_type = entity_type
        self.data = data or {}
        self.children: List[ObjectNode] = []
        self.parent: Optional[ObjectNode] = None
        self.visible = True
        self.selected = False

    def add_child(self, child: 'ObjectNode'):
        """Add a child node."""
        self.children.append(child)
        child.parent = self

    def remove_child(self, child: 'ObjectNode'):
        """Remove a child node."""
        if child in self.children:
            self.children.remove(child)
            child.parent = None

    def get_all_descendants(self) -> List['ObjectNode']:
        """Get all descendant nodes."""
        descendants = []
        for child in self.children:
            descendants.append(child)
            descendants.extend(child.get_all_descendants())
        return descendants

    def get_path(self) -> List[str]:
        """Get the path from root to this node."""
        path = [self.object_id]
        current = self.parent
        while current is not None:
            path.insert(0, current.object_id)
            current = current.parent
        return path

    def is_leaf(self) -> bool:
        """Check if node is a leaf."""
        return len(self.children) == 0

    def set_visible(self, visible: bool):
        """Set visibility of this node and all descendants."""
        self.visible = visible
        for child in self.children:
            child.set_visible(visible)

    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary representation."""
        return {
            'id': self.object_id,
            'type': self.entity_type,
            'visible': self.visible,
            'selected': self.selected,
            'data': self.data,
            'children': [child.to_dict() for child in self.children]
        }
