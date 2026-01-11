"""Cython implementation of hierarchy tree construction."""

from typing import List, Dict, Optional


class TreeNode:
    """Represents a node in the object hierarchy tree."""

    def __init__(self, object_id: int, object_data: Dict = None):
        """
        Initialize a tree node.

        Args:
            object_id: Unique identifier for the object.
            object_data: Additional object data.
        """
        self.object_id = object_id
        self.object_data = object_data or {}
        self.children: List[TreeNode] = []
        self.parent: Optional[TreeNode] = None

    def add_child(self, child: 'TreeNode'):
        """Add a child node."""
        self.children.append(child)
        child.parent = self

    def remove_child(self, child: 'TreeNode'):
        """Remove a child node."""
        if child in self.children:
            self.children.remove(child)
            child.parent = None

    def is_leaf(self) -> bool:
        """Check if node is a leaf."""
        return len(self.children) == 0


def build_tree_from_containment(containment_map: Dict[int, List[int]]) -> TreeNode:
    """
    Build a hierarchy tree from containment relationships.

    Args:
        containment_map: Dictionary mapping object IDs to contained object IDs.

    Returns:
        Root node of the hierarchy tree.
    """
    cdef int root_id = -1
    cdef dict nodes = {}

    # Create all nodes
    for obj_id in containment_map.keys():
        nodes[obj_id] = TreeNode(obj_id)

    # Find root (object not contained in any other)
    all_objects = set(containment_map.keys())
    contained_objects = set()
    for contained_list in containment_map.values():
        contained_objects.update(contained_list)

    root_candidates = all_objects - contained_objects
    if root_candidates:
        root_id = list(root_candidates)[0]
    else:
        root_id = list(all_objects)[0] if all_objects else -1

    root = TreeNode(root_id) if root_id >= 0 else TreeNode(-1)

    # Build tree structure
    for obj_id, contained_ids in containment_map.items():
        if obj_id in nodes:
            for contained_id in contained_ids:
                if contained_id in nodes:
                    nodes[obj_id].add_child(nodes[contained_id])

    return root
