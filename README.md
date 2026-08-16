DXF Object Segregator
=====================

A powerful tool for analyzing and segregating objects in DXF (Drawing Exchange Format) files.
Initially built as part of an internship that did not pan out and this code was never utilized.

Features
--------
- Object hierarchy visualization
- Geometric analysis (vertex sharing, intersections, containment)
- Interactive canvas with zoom and pan
- Cython-optimized geometry algorithms
- Comprehensive test suite
- Benchmarking utilities

Installation
------------

From source:

```bash
git clone https://github.com/yourusername/DXF_Object_Segregator.git
cd DXF_Object_Segregator
pip install -e .
```

With development dependencies:

```bash
pip install -e ".[dev]"
```

Usage
-----

Launch the GUI:

```bash
python -m dxf_object_segregator
```

Or use as a library:

```python
from dxf_object_segregator.core.dxf_processor import DXFProcessor

processor = DXFProcessor('your_file.dxf')
entities = processor.parse()
```

Documentation
-------------

- [Architecture](docs/architecture.md) - System design and components
- [API Reference](docs/api_reference.md) - API documentation
- [User Guide](docs/user_guide.md) - How to use the application

License
-------

MIT License - See LICENSE file for details

Contributing
------------

Contributions are welcome! Please feel free to submit a Pull Request.

Author
------

DXF Object Segregator Contributors
