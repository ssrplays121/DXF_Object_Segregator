"""Tests for object node module."""

import pytest
from core.objects.object_node import ObjectNode


class TestObjectNode:
    """Test cases for ObjectNode."""

    def test_node_creation(self):
        """Test creating an object node."""
        node = ObjectNode("obj1", "LINE", {"data": "test"})
        assert node.object_id == "obj1"
        assert node.entity_type == "LINE"
        assert node.visible is True
        assert node.selected is False

    def test_node_add_child(self):
        """Test adding child nodes."""
        parent = ObjectNode("parent", "GROUP")
        child = ObjectNode("child", "LINE")
        parent.add_child(child)
        assert child in parent.children
        assert child.parent == parent

    def test_node_remove_child(self):
        """Test removing child nodes."""
        parent = ObjectNode("parent", "GROUP")
        child = ObjectNode("child", "LINE")
        parent.add_child(child)
        parent.remove_child(child)
        assert child not in parent.children
        assert child.parent is None

    def test_node_is_leaf(self):
        """Test leaf node detection."""
        parent = ObjectNode("parent", "GROUP")
        child = ObjectNode("child", "LINE")
        assert parent.is_leaf() is True
        parent.add_child(child)
        assert parent.is_leaf() is False

    def test_node_get_path(self):
        """Test getting node path."""
        root = ObjectNode("root", "ROOT")
        child = ObjectNode("child", "GROUP")
        grandchild = ObjectNode("grandchild", "LINE")
        root.add_child(child)
        child.add_child(grandchild)
        path = grandchild.get_path()
        assert path == ["root", "child", "grandchild"]
