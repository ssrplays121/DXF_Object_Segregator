# DXF to JSON Converter

## Overview
Two scripts to convert DXF files to human-readable JSON:

- **convert.py**: Extracts complete DXF data to detailed JSON
- **simplify.py**: Converts detailed JSON to human-readable format

## Dependencies
- Python 3.10+
- ezdxf==1.4.3
- fonttools, numpy, pyparsing, typing-extensions

## Setup
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

## Usage

### Convert DXF to detailed JSON:
```bash
python convert.py [input.dxf] [output_complex.json]
```
Default: `input.dxf` → `output_complex.json`

### Simplify to human-readable JSON:
```bash
python simplify.py [output_complex.json] [output_simple.json]
```
Default: `output_complex.json` → `output_simple.json`

## Output
- **output_complex.json**: Complete DXF data with all entities, layers, and technical details
- **output_simple.json**: Clean, human-readable format showing only visual content and essential properties

## Example Workflow
```bash
python convert.py input.dxf output_complex.json
python simplify.py output_complex.json output_simple.json
```
