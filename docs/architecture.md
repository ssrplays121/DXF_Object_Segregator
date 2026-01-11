# Architecture

## Overview

DXF Object Segregator is a Python application for analyzing and segregating objects within DXF (Drawing Exchange Format) files.

## High-Level Architecture

### Core Components

1. **DXF Processor** (`core/dxf_processor.py`)
   - Handles reading and parsing DXF files
   - Extracts entities and metadata

2. **Geometry Modules** (`core/geometry/`)
   - `vertex_sharing`: Identifies vertices shared between objects
   - `intersection`: Computes geometric intersections
   - `containment`: Determines containment relationships
   - `grouping`: Groups related objects
   - `tree_construction`: Builds hierarchical object trees

3. **Object Model** (`core/objects/`)
   - `ObjectNode`: Represents individual objects in the hierarchy
   - `ObjectFactory`: Creates and manages objects

4. **UI Layer** (`ui/`)
   - `MainWindow`: Primary application window
   - `HierarchySidebar`: Displays object hierarchy
   - `CanvasRenderer`: Renders DXF objects
   - `Toolbar`, `MenuBar`: Navigation and tools
   - `Themes`: UI theme management

5. **Utilities** (`utils/`)
   - Logging, error handling, configuration
   - Validators and helper functions
   - Benchmarking utilities

## Performance Considerations

- Cython modules for geometry computations
- Efficient spatial indexing with tree structures
- Lazy loading of DXF file data

## Data Flow

1. User loads DXF file
2. DXF Processor parses entities
3. Geometry modules analyze relationships
4. Object tree is constructed
5. UI renders hierarchy and canvas

## Testing

- Unit tests in `tests/` mirror source structure
- Integration tests for component interactions
- Performance benchmarks in `benchmarks/`
