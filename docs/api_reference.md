# API Reference

## Core Module

### DXF Processor

```python
from dxf_object_segregator.core.dxf_processor import DXFProcessor

processor = DXFProcessor(filepath)
entities = processor.parse()
```

## Geometry Module

### Vertex Sharing

```python
from dxf_object_segregator.core.geometry.vertex_sharing import analyze_vertex_sharing

shared_vertices = analyze_vertex_sharing(entities)
```

### Intersection

```python
from dxf_object_segregator.core.geometry.intersection import compute_intersections

intersections = compute_intersections(entities)
```

### Containment

```python
from dxf_object_segregator.core.geometry.containment import check_containment

containment_map = check_containment(entities)
```

### Grouping

```python
from dxf_object_segregator.core.geometry.grouping import group_objects

groups = group_objects(entities)
```

### Tree Construction

```python
from dxf_object_segregator.core.geometry.tree_construction import build_hierarchy

hierarchy = build_hierarchy(entities)
```

## Object Model

### ObjectNode

```python
from dxf_object_segregator.core.objects.object_node import ObjectNode

node = ObjectNode(entity)
node.add_child(child_node)
```

### ObjectFactory

```python
from dxf_object_segregator.core.objects.object_factory import ObjectFactory

factory = ObjectFactory()
node = factory.create_node(entity)
```

## UI Module

### Main Window

```python
from dxf_object_segregator.ui.main_window import MainWindow

window = MainWindow()
window.show()
```

## Configuration

```python
from dxf_object_segregator.utils.configuration import Config

config = Config.load('config.json')
```
