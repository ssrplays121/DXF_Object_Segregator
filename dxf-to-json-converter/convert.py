import ezdxf
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import traceback
import sys
from collections import defaultdict
from ezdxf.math import Vec3, Vec2, UCS, Matrix44  # Modern math classes

class DXFErrorTracker:
    """Tracks errors and missing values during DXF extraction"""

    def __init__(self):
        self.errors = defaultdict(list)
        self.missing_values = defaultdict(int)
        self.warning_count = 0
        self.error_count = 0

    def add_error(self, context: str, error: Exception, entity_type: str = None):
        """Record an error with context"""
        error_info = {
            'context': context,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc(limit=2),
            'entity_type': entity_type or 'unknown'
        }
        self.errors[context].append(error_info)
        self.error_count += 1
        print(f"❌ ERROR [{context}]: {str(error)}")

    def add_missing_value(self, context: str, attribute: str):
        """Record a missing value"""
        key = f"{context}.{attribute}"
        self.missing_values[key] += 1
        self.warning_count += 1
        # Only print first occurrence to avoid spam
        if self.missing_values[key] == 1:
            print(f"⚠️ WARNING [{context}]: Missing attribute '{attribute}' - using None")

    def get_summary(self) -> str:
        """Generate a comprehensive error summary"""
        summary = []
        summary.append("\n" + "="*60)
        summary.append("DXF EXTRACTION ERROR SUMMARY")
        summary.append("="*60)

        if self.error_count == 0 and self.warning_count == 0:
            summary.append("✅ No errors or warnings encountered!")
            return "\n".join(summary)

        summary.append(f"📊 TOTAL ISSUES: {self.error_count + self.warning_count}")
        summary.append(f"   ❌ Errors: {self.error_count}")
        summary.append(f"   ⚠️ Warnings: {self.warning_count}")

        if self.error_count > 0:
            summary.append("\n🔴 ERROR DETAILS:")
            for context, errors in self.errors.items():
                summary.append(f"  Context: {context}")
                for i, error in enumerate(errors, 1):
                    summary.append(f"    Error #{i}:")
                    summary.append(f"      Type: {error['error_type']}")
                    summary.append(f"      Message: {error['error_message']}")
                    summary.append(f"      Entity: {error['entity_type']}")
                    # Only show first line of traceback to keep it clean
                    tb_lines = error['traceback'].split('\n')
                    if len(tb_lines) > 1:
                        summary.append(f"      Traceback: {tb_lines[1].strip()}")

        if self.warning_count > 0:
            summary.append("\n🟡 MISSING VALUES SUMMARY:")
            sorted_missing = sorted(self.missing_values.items(), key=lambda x: x[1], reverse=True)
            for i, (key, count) in enumerate(sorted_missing[:10], 1):  # Show top 10
                summary.append(f"  {i}. {key}: {count} occurrences")
            if len(sorted_missing) > 10:
                summary.append(f"  ... and {len(sorted_missing) - 10} more missing value types")

        summary.append("\n💡 RECOMMENDATIONS:")
        if self.error_count > 0:
            summary.append("  - Check DXF file integrity using ezdxf audit/recover")
            summary.append("  - Consider using recovery mode for corrupted files")
        if self.warning_count > 100:
            summary.append("  - Many missing attributes detected - file may be from non-standard CAD software")

        summary.append("="*60)
        return "\n".join(summary)

    def has_errors(self) -> bool:
        return self.error_count > 0

def safe_getattr(obj, attr_name, default=None, error_tracker=None, context=""):
    """Safely get attribute with error tracking"""
    try:
        if hasattr(obj, attr_name):
            return getattr(obj, attr_name)
        else:
            if error_tracker:
                error_tracker.add_missing_value(context, attr_name)
            return default
    except Exception as e:
        if error_tracker:
            error_tracker.add_error(f"{context}.{attr_name}", e)
        return default

def safe_dxf_getattr(dxf_obj, attr_name, default=None, error_tracker=None, context=""):
    """Safely get DXF attribute with error tracking"""
    try:
        if hasattr(dxf_obj, attr_name):
            return getattr(dxf_obj, attr_name)
        else:
            if error_tracker:
                error_tracker.add_missing_value(f"{context}.dxf", attr_name)
            return default
    except Exception as e:
        if error_tracker:
            error_tracker.add_error(f"{context}.dxf.{attr_name}", e)
        return default

def serialize_dxf_value(value):
    """Safely serialize DXF values for JSON, handling modern math types"""
    if isinstance(value, (Vec3, Vec2, UCS, Matrix44)):
        return str(value)
    elif hasattr(value, '__dict__') and not isinstance(value, (int, float, str, bool, type(None), list, dict)):
        try:
            return str(value)
        except:
            return repr(value)
    return value

def extract_dxf_entities(entities, error_tracker: DXFErrorTracker) -> List[Dict[str, Any]]:
    """
    Extract all information from DXF entities with comprehensive error handling

    Args:
        entities: Iterable of DXF entities
        error_tracker: Error tracking object

    Returns:
        List of dictionaries containing entity data
    """
    entity_data = []
    entity_count = 0

    for entity in entities:
        entity_count += 1
        try:
            # Get entity type safely
            entity_type = entity.dxftype() if hasattr(entity, 'dxftype') else 'UNKNOWN'
            context = f"entity_{entity_count}_{entity_type}"

            # Get basic entity information with safe attribute access
            handle = safe_dxf_getattr(entity.dxf, 'handle', None, error_tracker, context)
            layer = safe_dxf_getattr(entity.dxf, 'layer', '0', error_tracker, context)

            entity_info = {
                'type': entity_type,
                'handle': handle,
                'layer': layer,
                'attributes': {}
            }

            # Extract all DXF attributes from the dxf namespace
            if hasattr(entity, 'dxf'):
                for attr_name in dir(entity.dxf):
                    if attr_name.startswith('_') or attr_name in ['__class__', '__dict__', '__module__']:
                        continue  # Skip private attributes and special methods

                    try:
                        if hasattr(entity.dxf, attr_name):
                            attr_value = getattr(entity.dxf, attr_name)
                            # Serialize the value for JSON
                            entity_info['attributes'][attr_name] = serialize_dxf_value(attr_value)
                    except Exception as e:
                        error_tracker.add_error(f"{context}.attribute_{attr_name}", e, entity_type)
                        entity_info['attributes'][attr_name] = None

            # Special handling for text entities
            if entity_type == 'TEXT':
                text_content = safe_dxf_getattr(entity.dxf, 'text', '', error_tracker, context)
                entity_info['text_content'] = text_content

            # Special handling for insert entities (blocks with attributes)
            if entity_type == 'INSERT':
                entity_info['block_attributes'] = []
                if hasattr(entity, 'attribs'):
                    for i, attrib in enumerate(entity.attribs):
                        attrib_context = f"{context}.attrib_{i}"
                        try:
                            tag = safe_dxf_getattr(attrib.dxf, 'tag', '', error_tracker, attrib_context)
                            text = safe_dxf_getattr(attrib.dxf, 'text', '', error_tracker, attrib_context)
                            position = safe_dxf_getattr(attrib.dxf, 'insert', None, error_tracker, attrib_context)

                            entity_info['block_attributes'].append({
                                'tag': tag,
                                'text': text,
                                'position': serialize_dxf_value(position)
                            })
                        except Exception as e:
                            error_tracker.add_error(attrib_context, e, entity_type)
                            entity_info['block_attributes'].append({
                                'tag': None,
                                'text': None,
                                'position': None,
                                'error': str(e)
                            })

            # Handle geometry data for different entity types
            if entity_type in ['LINE', 'CIRCLE', 'ARC', 'ELLIPSE', 'LWPOLYLINE', 'POLYLINE', 'SPLINE', 'POINT']:
                entity_info['geometry'] = extract_geometry_data(entity, error_tracker, context)

            entity_data.append(entity_info)

        except Exception as e:
            entity_type = getattr(entity, 'dxftype', lambda: 'UNKNOWN')() if hasattr(entity, 'dxftype') else 'UNKNOWN'
            error_tracker.add_error(f"entity_{entity_count}", e, entity_type)
            entity_data.append({
                'type': entity_type,
                'error': str(e),
                'traceback': traceback.format_exc(),
                'handle': None,
                'layer': '0',
                'attributes': {},
                'geometry': None
            })

    print(f"✅ Processed {entity_count} entities in {entities.__class__.__name__}")
    return entity_data

def extract_geometry_data(entity, error_tracker: DXFErrorTracker, context: str) -> Dict[str, Any]:
    """
    Extract geometry-specific data from entities with error handling
    """
    geometry = {}
    entity_type = entity.dxftype() if hasattr(entity, 'dxftype') else 'UNKNOWN'

    try:
        if entity_type == 'LINE':
            start = safe_dxf_getattr(entity.dxf, 'start', None, error_tracker, f"{context}.line")
            end = safe_dxf_getattr(entity.dxf, 'end', None, error_tracker, f"{context}.line")
            geometry = {
                'start': serialize_dxf_value(start),
                'end': serialize_dxf_value(end)
            }
        elif entity_type == 'CIRCLE':
            center = safe_dxf_getattr(entity.dxf, 'center', None, error_tracker, f"{context}.circle")
            radius = safe_dxf_getattr(entity.dxf, 'radius', 0.0, error_tracker, f"{context}.circle")
            geometry = {
                'center': serialize_dxf_value(center),
                'radius': float(radius) if radius is not None else 0.0
            }
        elif entity_type == 'ARC':
            center = safe_dxf_getattr(entity.dxf, 'center', None, error_tracker, f"{context}.arc")
            radius = safe_dxf_getattr(entity.dxf, 'radius', 0.0, error_tracker, f"{context}.arc")
            start_angle = safe_dxf_getattr(entity.dxf, 'start_angle', 0.0, error_tracker, f"{context}.arc")
            end_angle = safe_dxf_getattr(entity.dxf, 'end_angle', 360.0, error_tracker, f"{context}.arc")
            geometry = {
                'center': serialize_dxf_value(center),
                'radius': float(radius) if radius is not None else 0.0,
                'start_angle': float(start_angle) if start_angle is not None else 0.0,
                'end_angle': float(end_angle) if end_angle is not None else 360.0
            }
        elif entity_type == 'ELLIPSE':
            center = safe_dxf_getattr(entity.dxf, 'center', None, error_tracker, f"{context}.ellipse")
            major_axis = safe_dxf_getattr(entity.dxf, 'major_axis', None, error_tracker, f"{context}.ellipse")
            ratio = safe_dxf_getattr(entity.dxf, 'ratio', 1.0, error_tracker, f"{context}.ellipse")
            start_param = safe_dxf_getattr(entity.dxf, 'start_param', 0.0, error_tracker, f"{context}.ellipse")
            end_param = safe_dxf_getattr(entity.dxf, 'end_param', 6.28318530718, error_tracker, f"{context}.ellipse")
            geometry = {
                'center': serialize_dxf_value(center),
                'major_axis': serialize_dxf_value(major_axis),
                'ratio': float(ratio) if ratio is not None else 1.0,
                'start_param': float(start_param) if start_param is not None else 0.0,
                'end_param': float(end_param) if end_param is not None else 6.28318530718
            }
        elif entity_type == 'LWPOLYLINE':
            try:
                vertices = []
                if hasattr(entity, 'vertices'):
                    for i, vertex in enumerate(entity.vertices()):
                        # vertex is typically a tuple (x, y[, start_width, end_width, bulge])
                        vertices.append({
                            'x': float(vertex[0]),
                            'y': float(vertex[1]),
                            'start_width': float(vertex[2]) if len(vertex) > 2 else 0.0,
                            'end_width': float(vertex[3]) if len(vertex) > 3 else 0.0,
                            'bulge': float(vertex[4]) if len(vertex) > 4 else 0.0
                        })
                geometry = {
                    'vertices': vertices,
                    'closed': safe_getattr(entity, 'closed', False, error_tracker, f"{context}.lwpolyline")
                }
            except Exception as e:
                error_tracker.add_error(f"{context}.lwpolyline.vertices", e, entity_type)
                geometry = {
                    'vertices': [],
                    'closed': False,
                    'error': str(e)
                }
        elif entity_type == 'POLYLINE':
            try:
                vertices = []
                if hasattr(entity, 'vertices'):
                    for i, vertex in enumerate(entity.vertices):
                        if hasattr(vertex, 'dxf') and hasattr(vertex.dxf, 'location'):
                            loc = vertex.dxf.location
                            vertices.append({
                                'x': float(loc.x) if hasattr(loc, 'x') else 0.0,
                                'y': float(loc.y) if hasattr(loc, 'y') else 0.0,
                                'z': float(loc.z) if hasattr(loc, 'z') else 0.0
                            })
                geometry = {
                    'vertices': vertices,
                    'closed': safe_getattr(entity, 'is_closed', False, error_tracker, f"{context}.polyline")
                }
            except Exception as e:
                error_tracker.add_error(f"{context}.polyline.vertices", e, entity_type)
                geometry = {
                    'vertices': [],
                    'closed': False,
                    'error': str(e)
                }
        elif entity_type == 'POINT':
            location = safe_dxf_getattr(entity.dxf, 'location', None, error_tracker, f"{context}.point")
            geometry = {
                'location': serialize_dxf_value(location)
            }
        elif entity_type == 'SPLINE':
            geometry = {
                'degree': safe_dxf_getattr(entity.dxf, 'degree', 3, error_tracker, f"{context}.spline"),
                'knots': safe_dxf_getattr(entity.dxf, 'knots', [], error_tracker, f"{context}.spline"),
                'control_points': safe_dxf_getattr(entity.dxf, 'control_points', [], error_tracker, f"{context}.spline"),
                'fit_points': safe_dxf_getattr(entity.dxf, 'fit_points', [], error_tracker, f"{context}.spline")
            }
        else:
            geometry = {'type': entity_type, 'raw_data': str(entity)}

        # Serialize all geometry values
        for key, value in geometry.items():
            if not isinstance(value, (int, float, str, bool, type(None), list, dict)):
                geometry[key] = serialize_dxf_value(value)

        return geometry

    except Exception as e:
        error_tracker.add_error(f"{context}.geometry", e, entity_type)
        return {
            'error': str(e),
            'entity_type': entity_type,
            'partial_data': serialize_dxf_value(geometry)
        }

def extract_dxf_complete_info(dxf_path: str) -> Dict[str, Any]:
    """
    Extract complete information from a DXF file with comprehensive error handling

    Args:
        dxf_path: Path to the DXF file

    Returns:
        Dictionary containing all DXF information with error tracking
    """
    error_tracker = DXFErrorTracker()
    result = {
        'extraction_metadata': {
            'source_file': str(dxf_path),
            'success': False,
            'errors': [],
            'warnings': []
        }
    }

    try:
        print(f"🔍 Reading DXF file: {dxf_path}")

        # Try to read the file with recovery mode for corrupted files
        try:
            doc = ezdxf.readfile(dxf_path)
        except (IOError, ezdxf.DXFStructureError) as e:
            error_tracker.add_error("file_reading", e)
            print("🔄 Attempting recovery mode...")
            try:
                from ezdxf import recover
                doc, auditor = recover.readfile(dxf_path)
                if auditor.has_errors:
                    print(f"⚡ Recovery fixed {len(auditor.errors)} errors")
            except Exception as recovery_error:
                error_tracker.add_error("recovery_mode", recovery_error)
                return {
                    'error': f"Failed to read DXF file: {str(recovery_error)}",
                    'file_path': str(dxf_path),
                    'error_details': traceback.format_exc()
                }

        print(f"✅ Successfully loaded DXF file (version: {getattr(doc, 'dxfversion', 'unknown')})")

        # Get the modelspace
        try:
            msp = doc.modelspace()
            print(f"📐 Processing Model Space ({len(msp)} entities)")
            modelspace_entities = extract_dxf_entities(msp, error_tracker)
        except Exception as e:
            error_tracker.add_error("modelspace_loading", e)
            modelspace_entities = []

        # Get paperspace layouts
        layouts = []
        try:
            layout_names = list(doc.layout_names())
            print(f"📋 Found {len(layout_names)} layouts")
            for layout_name in layout_names:
                if layout_name == 'Model':
                    continue
                try:
                    layout = doc.layout(layout_name)
                    print(f"  📄 Processing layout: '{layout_name}' ({len(layout)} entities)")
                    layout_context = f"layout_{layout_name}"
                    layout_entities = extract_dxf_entities(layout, error_tracker)
                    layouts.append({
                        'name': layout_name,
                        'entities': layout_entities
                    })
                except Exception as e:
                    error_tracker.add_error(f"layout_{layout_name}", e)
                    layouts.append({
                        'name': layout_name,
                        'entities': [],
                        'error': str(e)
                    })
        except Exception as e:
            error_tracker.add_error("layouts_loading", e)

        # Extract block definitions
        blocks = []
        try:
            block_names = list(doc.blocks.block_names())
            print(f"🔷 Processing {len(block_names)} blocks")
            for block_name in block_names:
                if block_name.startswith('*'):  # Skip special blocks
                    continue
                try:
                    block = doc.blocks[block_name]
                    context = f"block_{block_name}"

                    base_point = safe_getattr(block, 'base_point', None, error_tracker, context)
                    block_entities = extract_dxf_entities(block, error_tracker)

                    blocks.append({
                        'name': block_name,
                        'base_point': serialize_dxf_value(base_point),
                        'entities': block_entities
                    })
                except Exception as e:
                    error_tracker.add_error(f"block_{block_name}", e)
                    blocks.append({
                        'name': block_name,
                        'base_point': None,
                        'entities': [],
                        'error': str(e)
                    })
        except Exception as e:
            error_tracker.add_error("blocks_loading", e)

        # Extract header variables
        header_vars = {}
        try:
            if hasattr(doc, 'header'):
                for var_name in doc.header.hdrvars:
                    try:
                        value = doc.header.get(var_name)
                        header_vars[var_name] = serialize_dxf_value(value)
                    except Exception as e:
                        error_tracker.add_error(f"header_{var_name}", e)
                        header_vars[var_name] = None
        except Exception as e:
            error_tracker.add_error("header_loading", e)

        # Extract layers
        layers = []
        try:
            if hasattr(doc, 'layers'):
                print(f"🎨 Processing {len(doc.layers)} layers")
                for i, layer in enumerate(doc.layers):
                    context = f"layer_{i}"
                    try:
                        name = safe_dxf_getattr(layer.dxf, 'name', f'layer_{i}', error_tracker, context)
                        color = safe_dxf_getattr(layer.dxf, 'color', 7, error_tracker, context)
                        linetype = safe_dxf_getattr(layer.dxf, 'linetype', 'CONTINUOUS', error_tracker, context)
                        flags = safe_dxf_getattr(layer.dxf, 'flags', 0, error_tracker, context)

                        layers.append({
                            'name': name,
                            'color': color,
                            'linetype': linetype,
                            'flags': flags
                        })
                    except Exception as e:
                        error_tracker.add_error(context, e)
                        layers.append({
                            'name': f'layer_{i}_error',
                            'color': 7,
                            'linetype': 'CONTINUOUS',
                            'flags': 0,
                            'error': str(e)
                        })
        except Exception as e:
            error_tracker.add_error("layers_loading", e)

        # Extract linetypes
        linetypes = []
        try:
            if hasattr(doc, 'linetypes'):
                print(f"styleType Processing {len(doc.linetypes)} linetypes")
                for i, linetype in enumerate(doc.linetypes):
                    context = f"linetype_{i}"
                    try:
                        name = safe_dxf_getattr(linetype.dxf, 'name', f'linetype_{i}', error_tracker, context)
                        description = safe_dxf_getattr(linetype.dxf, 'description', '', error_tracker, context)
                        pattern = safe_getattr(linetype, 'pattern_tags', None, error_tracker, context)

                        linetypes.append({
                            'name': name,
                            'description': description,
                            'pattern': str(pattern) if pattern else None
                        })
                    except Exception as e:
                        error_tracker.add_error(context, e)
                        linetypes.append({
                            'name': f'linetype_{i}_error',
                            'description': 'error',
                            'pattern': None,
                            'error': str(e)
                        })
        except Exception as e:
            error_tracker.add_error("linetypes_loading", e)

        # Extract text styles
        text_styles = []
        try:
            if hasattr(doc, 'styles'):
                print(f"🔤 Processing {len(doc.styles)} text styles")
                for i, style in enumerate(doc.styles):
                    context = f"style_{i}"
                    try:
                        name = safe_dxf_getattr(style.dxf, 'name', f'style_{i}', error_tracker, context)
                        font = safe_dxf_getattr(style.dxf, 'font', 'standard', error_tracker, context)
                        height = safe_dxf_getattr(style.dxf, 'height', 0.0, error_tracker, context)
                        width = safe_dxf_getattr(style.dxf, 'width', 1.0, error_tracker, context)

                        text_styles.append({
                            'name': name,
                            'font': font,
                            'height': float(height) if height is not None else 0.0,
                            'width': float(width) if width is not None else 1.0
                        })
                    except Exception as e:
                        error_tracker.add_error(context, e)
                        text_styles.append({
                            'name': f'style_{i}_error',
                            'font': 'error',
                            'height': 0.0,
                            'width': 1.0,
                            'error': str(e)
                        })
        except Exception as e:
            error_tracker.add_error("styles_loading", e)

        # Compile complete DXF information
        result = {
            'extraction_metadata': {
                'source_file': str(dxf_path),
                'success': True,
                'processing_time': None,  # Could add timing if needed
                'error_summary': {
                    'total_errors': error_tracker.error_count,
                    'total_warnings': error_tracker.warning_count,
                    'missing_values_count': sum(error_tracker.missing_values.values())
                }
            },
            'file_info': {
                'path': str(dxf_path),
                'version': getattr(doc, 'dxfversion', 'unknown'),
                'acad_version': getattr(doc, 'acad_release', 'unknown'),
                'encoding': getattr(doc, 'encoding', 'unknown')
            },
            'header': header_vars,
            'layers': layers,
            'linetypes': linetypes,
            'text_styles': text_styles,
            'blocks': blocks,
            'modelspace': {
                'name': 'Model',
                'entities': modelspace_entities
            },
            'paperspace_layouts': layouts,
            'errors_and_warnings': {
                'errors': dict(error_tracker.errors),
                'missing_values': dict(error_tracker.missing_values)
            }
        }

        # Print error summary
        print(error_tracker.get_summary())

        # Add error summary to result for JSON output
        result['extraction_metadata']['error_details'] = {
            'error_count': error_tracker.error_count,
            'warning_count': error_tracker.warning_count,
            'missing_values_summary': dict(error_tracker.missing_values),
            'has_errors': error_tracker.has_errors()
        }

        return result

    except Exception as e:
        error_tracker.add_error("main_extraction", e)
        print(error_tracker.get_summary())
        return {
            'error': f"Critical failure during DXF extraction: {str(e)}",
            'file_path': str(dxf_path),
            'traceback': traceback.format_exc(),
            'error_summary': {
                'total_errors': error_tracker.error_count,
                'total_warnings': error_tracker.warning_count
            }
        }

def dxf_to_json(dxf_path: str, json_path: str = None) -> str:
    """
    Convert DXF file to JSON format with comprehensive error reporting

    Args:
        dxf_path: Path to input DXF file
        json_path: Path to output JSON file (optional)

    Returns:
        JSON string containing the DXF data
    """
    print("="*60)
    print("DXF TO JSON CONVERTER")
    print("="*60)

    # Extract complete DXF information
    print("🚀 Starting DXF extraction...")
    dxf_data = extract_dxf_complete_info(dxf_path)

    print("💾 Converting to JSON...")
    # Convert to JSON string with indentation for readability
    json_str = json.dumps(dxf_data, indent=2, default=str)

    # Save to file if path is provided
    if json_path:
        try:
            with open(json_path, 'w', encoding='utf-8') as f:
                f.write(json_str)
            print(f"✅ DXF data successfully exported to {json_path}")
        except Exception as e:
            print(f"❌ Error saving JSON file: {str(e)}")
            traceback.print_exc()

    print("="*60)
    print("✨ EXTRACTION COMPLETED!")
    print("="*60)

    return json_str

if __name__ == "__main__":
    import argparse

    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description='Convert DXF file to JSON format')
    parser.add_argument('input_dxf', nargs='?', default='input.dxf',
                        help='Path to input DXF file (default: input.dxf)')
    parser.add_argument('output_json', nargs='?', default='output_complex.json',
                        help='Path to output JSON file (default: output_complex.json)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Enable verbose output')

    args = parser.parse_args()
    input_dxf = args.input_dxf
    output_json = args.output_json

    if not Path(input_dxf).exists():
        print(f"❌ Error: DXF file not found at {input_dxf}")
        sys.exit(1)

    try:
        # Convert DXF to JSON
        result = dxf_to_json(input_dxf, output_json)

        # Print summary from the JSON data
        try:
            data = json.loads(result)
            metadata = data.get('extraction_metadata', {})

            print(f"\n📈 EXTRACTION SUMMARY:")
            print(f"✅ Success: {metadata.get('success', False)}")
            print(f"📁 Source file: {metadata.get('source_file', 'unknown')}")

            if metadata.get('success'):
                error_details = metadata.get('error_details', {})
                print(f"❌ Total errors: {error_details.get('error_count', 0)}")
                print(f"⚠️ Total warnings: {error_details.get('warning_count', 0)}")
                print(f"❓ Missing values: {error_details.get('missing_values_count', 0)}")

                if 'file_info' in data:
                    print(f"\n📋 FILE INFO:")
                    print(f"  Version: {data['file_info'].get('version', 'unknown')}")
                    print(f"  ACAD Version: {data['file_info'].get('acad_version', 'unknown')}")

                if 'modelspace' in data:
                    entity_count = len(data['modelspace'].get('entities', []))
                    print(f"📐 Modelspace entities: {entity_count}")

                if 'blocks' in data:
                    print(f"🔷 Blocks: {len(data['blocks'])}")

                if 'layers' in data:
                    print(f"🎨 Layers: {len(data['layers'])}")

        except json.JSONDecodeError as e:
            print(f"❌ Error parsing JSON result: {str(e)}")

    except KeyboardInterrupt:
        print("\n🛑 Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"💥 Unexpected error: {str(e)}")
        traceback.print_exc()
        sys.exit(1)
