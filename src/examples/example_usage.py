"""Example usage of DXF Object Segregator."""

from core.dxf_processor import DXFProcessor
from core.objects.object_factory import ObjectFactory


def example_load_and_process_dxf():
    """Example: Load and process a DXF file."""
    # Load DXF file
    processor = DXFProcessor("sample_shapes.dxf")
    entities = processor.parse()

    # Create object nodes
    factory = ObjectFactory()
    for i, entity in enumerate(entities):
        node = factory.create_node(
            str(entity['handle']),
            entity['type'],
            entity['data']
        )

    # Get all nodes
    nodes = factory.get_all_nodes()
    print(f"Loaded {len(nodes)} objects from DXF file")


def example_hierarchy_creation():
    """Example: Create and navigate object hierarchy."""
    from core.objects.object_node import ObjectNode

    # Create hierarchy
    root = ObjectNode("root", "ROOT")
    group1 = ObjectNode("group1", "GROUP")
    group2 = ObjectNode("group2", "GROUP")
    line1 = ObjectNode("line1", "LINE")
    line2 = ObjectNode("line2", "LINE")

    # Build hierarchy
    root.add_child(group1)
    root.add_child(group2)
    group1.add_child(line1)
    group2.add_child(line2)

    # Navigate
    print(f"Root path: {root.get_path()}")
    print(f"Line1 path: {line1.get_path()}")


if __name__ == "__main__":
    example_hierarchy_creation()
