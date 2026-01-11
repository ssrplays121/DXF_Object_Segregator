# User Guide

## Installation

### Requirements
- Python 3.8+
- pip

### Install from Source

```bash
git clone https://github.com/yourusername/DXF_Object_Segregator.git
cd DXF_Object_Segregator
pip install -e .
```

### Install with Development Dependencies

```bash
pip install -e ".[dev]"
```

## Getting Started

### Running the Application

```bash
python -m dxf_object_segregator
```

### Loading a DXF File

1. Launch the application
2. Click File → Open
3. Select your DXF file
4. The object hierarchy will be displayed in the left sidebar

## Features

### Object Hierarchy
- View objects organized in a tree structure
- Expand/collapse nodes to explore relationships
- Identify parent-child relationships

### Visual Analysis
- Zoom in/out on the canvas
- Pan across the drawing
- Highlight objects on selection

### Geometric Analysis
- Analyze vertex sharing between objects
- Detect intersections
- Determine containment relationships
- Group related objects

### Export Options
- Export hierarchy to JSON
- Export analysis results
- Save filtered views

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+O   | Open File |
| Ctrl+S   | Save |
| Ctrl+Q   | Quit |
| Ctrl+Z   | Undo |
| Ctrl+Y   | Redo |
| +        | Zoom In |
| -        | Zoom Out |
| F        | Fit View |

## Settings

Access settings via Edit → Settings to customize:
- Theme (Light/Dark)
- Default file locations
- Analysis parameters
- UI preferences
