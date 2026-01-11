# models/object_node.py
# Data structures for object tree representation
# Implements unique ID system and dual parent references
# Reference: https://docs.python.org/3/library/dataclasses.html
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Any
import json
from uuid import uuid4

@dataclass
class BoundingBox:
    """
    Axis-aligned bounding box for spatial containment testing
    Used in hybrid containment approach (Decision #4)
    """
    min_x: float
    min_y: float
    max_x: float
    max_y: float

    def contains_point(self, x: float, y: float) -> bool:
        """Check if point is within bounding box"""
        return (self.min_x <= x <= self.max_x and
                self.min_y <= y <= self.max_y)

    def intersects(self, other: 'BoundingBox') -> bool:
        """Check if two bounding boxes intersect"""
        return not (self.max_x < other.min_x or
                    self.min_x > other.max_x or
                    self.max_y < other.min_y or
                    self.min_y > other.max_y)

    def union(self, other: 'BoundingBox') -> 'BoundingBox':
        """Create bounding box that contains both boxes"""
        return BoundingBox(
            min_x=min(self.min_x, other.min_x),
            min_y=min(self.min_y, other.min_y),
            max_x=max(self.max_x, other.max_x),
            max_y=max(self.max_y, other.max_y)
        )

@dataclass
class ObjectNode:
    """
    Node in the object tree hierarchy
    Implements unique ID system and dual parent references (Decision #6, #7)
    Attributes:
        id: Unique identifier for this object (UUID4)
        parent_ids: Set of parent object IDs (dual references - Decision #6)
        children_ids: Set of child object IDs
        entity_ids: Set of DXF entity IDs contained in this object
        bounding_box: Bounding box for spatial containment testing
        is_root: Flag indicating if this is the root node
        meta Additional information about this object
    """
    id: str = field(default_factory=lambda: str(uuid4()))
    parent_ids: Set[str] = field(default_factory=set)
    children_ids: Set[str] = field(default_factory=set)
    entity_ids: Set[str] = field(default_factory=set)
    bounding_box: Optional[BoundingBox] = None
    is_root: bool = False
    meta Dict[str, Any] = field(default_factory=dict) # Fixed typo: meta -> metadata

    def add_parent(self, parent_id: str) -> None:
        """Add parent reference with validation"""
        if parent_id == self.id:
            raise ValueError("Object cannot be parent of itself")
        self.parent_ids.add(parent_id)

    def add_child(self, child_id: str) -> None:
        """Add child reference with validation"""
        if child_id == self.id:
            raise ValueError("Object cannot be child of itself")
        self.children_ids.add(child_id)

    def add_entity(self, entity_id: str) -> None:
        """Add DXF entity to this object"""
        self.entity_ids.add(entity_id)

    def calculate_bounding_box(self, entities: Dict[str, Dict[str, Any]]) -> None:
        """
        Calculate bounding box from contained entities
        Uses ezdxf default settings for curve flattening (Decision #5)
        """
        if not self.entity_ids:
            self.bounding_box = None
            return

        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')

        for entity_id in self.entity_ids:
            entity = entities.get(entity_id)
            if not entity:
                continue
            # Get entity bounds based on type
            if entity['type'] == 'LINE':
                points = [entity['start'], entity['end']]
            elif entity['type'] == 'CIRCLE':
                # Approximate circle bounds using 4 points
                cx, cy = entity['center']
                r = entity['radius']
                points = [
                    (cx - r, cy), (cx + r, cy),
                    (cx, cy - r), (cx, cy + r)
                ]
            elif entity['type'] == 'POLYLINE':
                points = entity['points']
            else:
                # Default to entity's bounding box if available
                if 'bbox' in entity:
                    points = [
                        (entity['bbox']['min_x'], entity['bbox']['min_y']),
                        (entity['bbox']['max_x'], entity['bbox']['max_y'])
                    ]
                else:
                    continue

            for x, y in points:
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)

        if min_x == float('inf'):  # No valid points found
            self.bounding_box = None
        else:
            self.bounding_box = BoundingBox(min_x, min_y, max_x, max_y)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization (Decision #16)"""
        return {
            'id': self.id,
            'parent_ids': list(self.parent_ids),
            'children_ids': list(self.children_ids),
            'entity_ids': list(self.entity_ids),
            'bounding_box': self.bounding_box.__dict__ if self.bounding_box else None,
            'is_root': self.is_root,
            'metadata': self.metadata # Fixed typo: meta -> metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ObjectNode':
        """Create from dictionary (JSON deserialization)"""
        node = cls()
        node.id = data['id']
        node.parent_ids = set(data['parent_ids'])
        node.children_ids = set(data['children_ids'])
        node.entity_ids = set(data['entity_ids'])
        node.is_root = data['is_root']
        node.metadata = data['metadata'] # Fixed typo: meta -> metadata
        if data['bounding_box']:
            bbox_data = data['bounding_box']
            node.bounding_box = BoundingBox(
                bbox_data['min_x'], bbox_data['min_y'],
                bbox_data['max_x'], bbox_data['max_y']
            )
        return node

@dataclass
class ObjectTree:
    """
    Complete object tree structure
    Contains all nodes and provides tree operations
    """
    nodes: Dict[str, ObjectNode] = field(default_factory=dict)
    root_id: Optional[str] = None

    def add_node(self, node: ObjectNode) -> None:
        """Add node to tree with ID validation"""
        if node.id in self.nodes:
            raise ValueError(f"Node with ID {node.id} already exists")
        self.nodes[node.id] = node
        if node.is_root:
            self.root_id = node.id

    def get_node(self, node_id: str) -> ObjectNode:
        """Get node by ID with error handling"""
        if node_id not in self.nodes:
            raise KeyError(f"Node with ID {node_id} not found")
        return self.nodes[node_id]

    def get_children(self, node_id: str) -> List[ObjectNode]:
        """Get all child nodes of a parent"""
        node = self.get_node(node_id)
        return [self.get_node(child_id) for child_id in node.children_ids]

    def get_parents(self, node_id: str) -> List[ObjectNode]:
        """Get all parent nodes of a child (dual references - Decision #6)"""
        node = self.get_node(node_id)
        return [self.get_node(parent_id) for parent_id in node.parent_ids]

    def to_dict(self) -> Dict[str, Any]:
        """Convert entire tree to dictionary for serialization"""
        return {
            'root_id': self.root_id,
            'nodes': {node_id: node.to_dict() for node_id, node in self.nodes.items()}
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ObjectTree':
        """Create tree from dictionary (deserialization)"""
        tree = cls()
        tree.root_id = data['root_id']
        # First create all nodes without relationships
        for node_id, node_data in data['nodes'].items():
            node = ObjectNode.from_dict(node_data)
            tree.nodes[node_id] = node
        # Then establish relationships
        for node_id, node_data in data['nodes'].items():
            node = tree.nodes[node_id]
            # Parents and children are already stored as IDs in the node data
            # The tree structure is implicitly defined by the parent_ids/children_ids in each node
        return tree
