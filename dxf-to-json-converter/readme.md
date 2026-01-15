# DXF Processing Toolkit
## Overview
A comprehensive suite of Python scripts for processing DXF files with multiple capabilities:

- **convert.py**: Extracts complete DXF data to detailed JSON
- **simplify.py**: Converts detailed JSON to human-readable format
- **layering.py**: Splits DXF files by layers into separate files
- **segregation.py**: Groups DXF entities into objects based on layer and geometric intersection

## Dependencies
- Python 3.10+
- ezdxf==1.4.3
- fonttools, numpy, pyparsing, typing-extensions
- Additional dependencies for geometric operations

## Setup
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

## Usage

### 1. Convert DXF to detailed JSON:
```bash
python convert.py [input.dxf] [output_complex.json]
```
Default: `input.dxf` → `output_complex.json`

### 2. Simplify to human-readable JSON:
```bash
python simplify.py [output_complex.json] [output_simple.json]
```
Default: `output_complex.json` → `output_simple.json`

### 3. Split DXF by layers:
```bash
python layering.py [input.dxf] [--output-dir output_folder]
```
Default: Creates folder named after input file containing one DXF file per layer

### 4. Group entities into objects:
```bash
python segregation.py [input.dxf] [output_objects.json]
```
Default: `input.dxf` → `segregated_objects.json`

## Output Files
- **output_complex.json**: Complete DXF data with all entities, layers, and technical details
- **output_simple.json**: Clean, human-readable format showing only visual content and essential properties
- **[layer_name].dxf**: Individual DXF files for each layer (created by layering.py)
- **output_objects.json**: Hierarchical JSON with entities grouped into meaningful objects based on geometric connections

## Script Descriptions

### convert.py
Extracts all DXF information including:
- Entity geometry and attributes
- Layer definitions and properties
- Block definitions and insertions
- Text styles and linetypes
- Layout information (model space and paper space)
- Comprehensive error tracking and recovery

### simplify.py
Converts complex DXF JSON into a clean, human-readable format:
- Filters out technical/internal entities
- Simplifies coordinate representations
- Groups entities by type and layer
- Provides drawing summary with bounds and entity counts
- Removes redundant technical details for easier analysis

### layering.py
Splits DXF files into separate files by layer:
- Creates individual DXF files for each layer
- Preserves layer properties (color, linetype, etc.)
- Handles both model space and layout entities
- Copies necessary resources (styles, linetypes) to each file
- Intelligent layer name sanitization for file naming
- Comprehensive error handling for corrupted files

### segregation.py
Groups entities into meaningful objects based on:
- Layer-based segregation (entities only group within same layer)
- Geometric intersection detection (lines, circles, polylines)
- Connected component analysis using BFS algorithm
- Object bounding box calculation
- Hierarchical JSON output with object metadata
- Robust coordinate normalization for different DXF formats

## Example Workflows

### Basic DXF to Human-Readable JSON:
```bash
python convert.py drawing.dxf detailed.json
python simplify.py detailed.json readable.json
```

### Layer-Based Processing:
```bash
# Split drawing into layers
python layering.py building_plan.dxf --output-dir building_layers

# Process each layer separately
python convert.py building_layers/Walls.dxf walls.json
python convert.py building_layers/Dimensions.dxf dimensions.json
```

### Object Detection Workflow:
```bash
# Extract objects from DXF
python segregation.py mechanical_part.dxf parts.json

# Convert to human-readable format
python simplify.py parts.json parts_readable.json
```

### Comprehensive Analysis Pipeline:
```bash
# 1. Split by layers
python layering.py architectural_plan.dxf --output-dir plan_layers

# 2. Process each layer to extract objects
python segregation.py plan_layers/Walls.dxf walls_objects.json
python segregation.py plan_layers/Doors.dxf doors_objects.json
python segregation.py plan_layers/Windows.dxf windows_objects.json

# 3. Create human-readable summaries
python simplify.py walls_objects.json walls_summary.json
python simplify.py doors_objects.json doors_summary.json
python simplify.py windows_objects.json windows_summary.json
```

## Error Handling
All scripts include comprehensive error handling:
- Automatic DXF file recovery for corrupted files
- Detailed error logs with context and entity information
- Warning tracking for missing attributes
- Summary reports with actionable recommendations
- Graceful degradation when processing complex drawings

## Notes
- For large DXF files, segregation.py may take longer due to geometric calculations
- Layer names containing special characters are automatically sanitized for file naming
- All scripts support DXF versions from R12 to 2018 (AC1032)
- Recovery mode is automatically activated for corrupted files

This toolkit provides a complete solution for DXF file analysis, conversion, and processing, suitable for CAD automation, BIM workflows, and geometric analysis applications.
