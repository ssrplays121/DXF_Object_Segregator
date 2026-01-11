"""Factory for creating and managing object nodes."""

from typing import Dict, Any
from .object_node import ObjectNode


class ObjectFactory:
    """Factory for creating object nodes."""

    def __init__(self):
        """Initialize the factory."""
        self.nodes: Dict[str, ObjectNode] = {}

    def create_node(self, object_id: str, entity_type: str,
                    data: Dict[str, Any] = None) -> ObjectNode:
        """
        Create a new object node.

        Args:
            object_id: Unique identifier for the object.
            entity_type: Type of the entity.
            data: Additional object data.

        Returns:
            Created ObjectNode instance.
        """
        if object_id in self.nodes:
            return self.nodes[object_id]

        node = ObjectNode(object_id, entity_type, data)
        self.nodes[object_id] = node
        return node

    def get_node(self, object_id: str) -> ObjectNode:
        """Get an existing node by ID."""
        return self.nodes.get(object_id)

    def remove_node(self, object_id: str):
        """Remove a node."""
        if object_id in self.nodes:
            del self.nodes[object_id]

    def clear(self):
        """Clear all nodes."""
        self.nodes.clear()

    def get_all_nodes(self) -> Dict[str, ObjectNode]:
        """Get all nodes."""
        return self.nodes.copy()
