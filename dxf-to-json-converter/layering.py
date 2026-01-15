# layering.py
import ezdxf
import json
from pathlib import Path
import traceback
import sys
import os
import argparse
from collections import defaultdict
from ezdxf.math import Vec3, Vec2, UCS, Matrix44

class DXFErrorTracker:
    """Tracks errors and missing values during DXF processing"""

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
        summary.append("DXF LAYER SPLITTING ERROR SUMMARY")
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
    """Safely serialize DXF values for logging"""
    if isinstance(value, (Vec3, Vec2, UCS, Matrix44)):
        return str(value)
    elif hasattr(value, '__dict__') and not isinstance(value, (int, float, str, bool, type(None), list, dict)):
        try:
            return str(value)
        except:
            return repr(value)
    return value

def split_dxf_by_layers(input_dxf_path: str, output_dir: str = None) -> Dict[str, Any]:
    """
    Split a DXF file by layers, creating separate DXF files for each layer

    Args:
        input_dxf_path: Path to the input DXF file
        output_dir: Directory to store the output layer files (optional)

    Returns:
        Dictionary containing processing results and error information
    """
    error_tracker = DXFErrorTracker()
    result = {
        'processing_metadata': {
            'source_file': str(input_dxf_path),
            'success': False,
            'errors': [],
            'warnings': [],
            'output_directory': None,
            'layers_processed': []
        }
    }

    try:
        input_path = Path(input_dxf_path)
        if not input_path.exists():
            error_tracker.add_error("file_validation", FileNotFoundError(f"File not found: {input_dxf_path}"))
            return {
                'error': f"File not found: {input_dxf_path}",
                'success': False
            }

        print(f"🔍 Reading DXF file: {input_dxf_path}")

        # Try to read the file with recovery mode for corrupted files
        try:
            doc = ezdxf.readfile(input_dxf_path)
        except (IOError, ezdxf.DXFStructureError) as e:
            error_tracker.add_error("file_reading", e)
            print("🔄 Attempting recovery mode...")
            try:
                from ezdxf import recover
                doc, auditor = recover.readfile(input_dxf_path)
                if auditor.has_errors:
                    print(f"⚡ Recovery fixed {len(auditor.errors)} errors")
            except Exception as recovery_error:
                error_tracker.add_error("recovery_mode", recovery_error)
                return {
                    'error': f"Failed to read DXF file: {str(recovery_error)}",
                    'file_path': str(input_dxf_path),
                    'error_details': traceback.format_exc()
                }

        print(f"✅ Successfully loaded DXF file (version: {getattr(doc, 'dxfversion', 'unknown')})")

        # Determine output directory
        if output_dir is None:
            # Create folder named after input file (without extension)
            base_name = input_path.stem
            output_dir = Path.cwd() / base_name
        else:
            output_dir = Path(output_dir)

        # Create output directory if it doesn't exist
        output_dir.mkdir(exist_ok=True, parents=True)
        result['processing_metadata']['output_directory'] = str(output_dir)
        print(f"📁 Output directory: {output_dir}")

        # Get all layers from the document
        layers = []
        try:
            if hasattr(doc, 'layers'):
                print(f"🎨 Found {len(doc.layers)} layers")
                for layer in doc.layers:
                    layer_name = safe_dxf_getattr(layer.dxf, 'name', 'unnamed', error_tracker, 'layer_processing')
                    layers.append(layer_name)
            else:
                # Fallback: extract layers from entities
                layer_names = set()
                for entity in doc.modelspace():
                    layer = safe_dxf_getattr(entity.dxf, 'layer', '0', error_tracker, 'entity')
                    layer_names.add(layer)
                layers = list(layer_names)
                print(f"🎨 Found {len(layers)} layers from entities")
        except Exception as e:
            error_tracker.add_error("layer_extraction", e)
            layers = ['0']  # Default layer

        # Remove special/internal layers
        layers = [layer for layer in layers if not layer.startswith('*') and layer.lower() not in ['defpoints', 'viewport']]

        print(f"📋 Processing layers: {', '.join(layers)}")

        # Process each layer
        processed_layers = []
        total_entities = 0
        layer_entity_counts = {}

        for layer_name in layers:
            layer_context = f"layer_{layer_name}"
            print(f"\n🔄 Processing layer: '{layer_name}'")

            try:
                # Create a new DXF document for this layer
                layer_doc = ezdxf.new(doc.dxfversion)

                # Copy necessary resources from original document
                _copy_layer_resources(doc, layer_doc, layer_name, error_tracker)

                # Get modelspace of the new document
                layer_msp = layer_doc.modelspace()

                # Filter entities from the original document that belong to this layer
                entities_on_layer = []
                for entity in doc.modelspace():
                    entity_layer = safe_dxf_getattr(entity.dxf, 'layer', '0', error_tracker, f"entity_in_{layer_name}")
                    if entity_layer == layer_name:
                        entities_on_layer.append(entity)

                entity_count = len(entities_on_layer)
                layer_entity_counts[layer_name] = entity_count
                total_entities += entity_count

                if entity_count == 0:
                    print(f"ℹ️  Layer '{layer_name}' has no entities - skipping")
                    continue

                print(f"  📐 Found {entity_count} entities on layer '{layer_name}'")

                # Copy entities to the new document
                _copy_entities(entities_on_layer, layer_msp, error_tracker, layer_context)

                # Save the layer DXF file
                safe_layer_name = "".join(c for c in layer_name if c.isalnum() or c in ('-', '_')).strip()
                if not safe_layer_name:
                    safe_layer_name = f"layer_{len(processed_layers) + 1}"

                output_file = output_dir / f"{safe_layer_name}.dxf"
                layer_doc.saveas(output_file)
                print(f"✅ Created: {output_file}")

                processed_layers.append({
                    'layer_name': layer_name,
                    'output_file': str(output_file),
                    'entity_count': entity_count
                })

            except Exception as e:
                error_tracker.add_error(f"layer_processing_{layer_name}", e)
                print(f"❌ Failed to process layer '{layer_name}': {str(e)}")

        # Get paperspace layouts and process them by layers
        try:
            layout_names = list(doc.layout_names())
            if len(layout_names) > 1:  # More than just Model space
                print(f"\n📐 Processing layouts: {', '.join([ln for ln in layout_names if ln != 'Model'])}")

                for layout_name in layout_names:
                    if layout_name == 'Model':
                        continue

                    layout_context = f"layout_{layout_name}"
                    print(f"\n🔄 Processing layout: '{layout_name}'")

                    try:
                        layout = doc.layout(layout_name)
                        # Group entities by layer in this layout
                        layout_entities_by_layer = defaultdict(list)

                        for entity in layout:
                            entity_layer = safe_dxf_getattr(entity.dxf, 'layer', '0', error_tracker, layout_context)
                            layout_entities_by_layer[entity_layer].append(entity)

                        # Process each layer that has entities in this layout
                        for layer_name, entities in layout_entities_by_layer.items():
                            if not entities:
                                continue

                            layer_context = f"layout_{layout_name}_layer_{layer_name}"
                            print(f"  📐 Layout '{layout_name}' has {len(entities)} entities on layer '{layer_name}'")

                            # Create or get the layer document
                            layer_doc = None
                            layer_file = None

                            # Check if we already created a file for this layer
                            for processed in processed_layers:
                                if processed['layer_name'] == layer_name:
                                    try:
                                        layer_doc = ezdxf.readfile(processed['output_file'])
                                        layer_file = Path(processed['output_file'])
                                    except Exception as e:
                                        error_tracker.add_error(f"layout_layer_read_{layer_name}", e)
                                    break

                            # If no existing file, create a new one
                            if layer_doc is None:
                                layer_doc = ezdxf.new(doc.dxfversion)
                                _copy_layer_resources(doc, layer_doc, layer_name, error_tracker)

                            # Copy entities to the layout
                            if hasattr(layer_doc, 'layouts'):
                                # Create a new layout if it doesn't exist
                                new_layout_name = f"{layout_name}"
                                if new_layout_name not in layer_doc.layout_names():
                                    layer_doc.layouts.new(new_layout_name)

                                target_layout = layer_doc.layout(new_layout_name)
                                _copy_entities(entities, target_layout, error_tracker, layer_context)

                            # Save the updated layer file
                            if layer_file is None:
                                safe_layer_name = "".join(c for c in layer_name if c.isalnum() or c in ('-', '_')).strip()
                                if not safe_layer_name:
                                    safe_layer_name = f"layer_{len(processed_layers) + 1}"

                                layer_file = output_dir / f"{safe_layer_name}.dxf"

                            layer_doc.saveas(layer_file)

                            # Update processed layers list
                            if not any(p['layer_name'] == layer_name for p in processed_layers):
                                processed_layers.append({
                                    'layer_name': layer_name,
                                    'output_file': str(layer_file),
                                    'entity_count': len(entities)
                                })

                    except Exception as e:
                        error_tracker.add_error(f"layout_processing_{layout_name}", e)
                        print(f"❌ Failed to process layout '{layout_name}': {str(e)}")

        except Exception as e:
            error_tracker.add_error("layout_processing", e)

        # Compile results
        result = {
            'processing_metadata': {
                'source_file': str(input_dxf_path),
                'success': True,
                'output_directory': str(output_dir),
                'layers_processed': processed_layers,
                'total_layers': len(layers),
                'total_entities': total_entities,
                'layer_entity_counts': layer_entity_counts,
                'error_summary': {
                    'total_errors': error_tracker.error_count,
                    'total_warnings': error_tracker.warning_count,
                    'missing_values_count': sum(error_tracker.missing_values.values())
                }
            }
        }

        # Print error summary
        print(error_tracker.get_summary())

        # Add error summary to result
        result['processing_metadata']['error_details'] = {
            'error_count': error_tracker.error_count,
            'warning_count': error_tracker.warning_count,
            'missing_values_summary': dict(error_tracker.missing_values),
            'has_errors': error_tracker.has_errors()
        }

        return result

    except Exception as e:
        error_tracker.add_error("main_processing", e)
        print(error_tracker.get_summary())
        return {
            'error': f"Critical failure during DXF processing: {str(e)}",
            'file_path': str(input_dxf_path),
            'traceback': traceback.format_exc(),
            'processing_metadata': {
                'error_summary': {
                    'total_errors': error_tracker.error_count,
                    'total_warnings': error_tracker.warning_count
                }
            }
        }

def _copy_layer_resources(source_doc, target_doc, layer_name, error_tracker):
    """Copy necessary resources for a specific layer to the target document"""
    try:
        # Copy the specific layer definition
        if hasattr(source_doc, 'layers') and layer_name in source_doc.layers:
            source_layer = source_doc.layers.get(layer_name)
            if source_layer and hasattr(target_doc, 'layers'):
                target_doc.layers.new(
                    name=layer_name,
                    dxfattribs={
                        'color': safe_dxf_getattr(source_layer.dxf, 'color', 7, error_tracker, 'layer_copy'),
                        'linetype': safe_dxf_getattr(source_layer.dxf, 'linetype', 'Continuous', error_tracker, 'layer_copy')
                    }
                )

        # Copy used linetypes
        if hasattr(source_doc, 'linetypes'):
            used_linetypes = set()
            for entity in source_doc.modelspace():
                if safe_dxf_getattr(entity.dxf, 'layer', '0', error_tracker, 'linetype_check') == layer_name:
                    linetype = safe_dxf_getattr(entity.dxf, 'linetype', 'Continuous', error_tracker, 'linetype_check')
                    used_linetypes.add(linetype)

            for linetype_name in used_linetypes:
                if linetype_name in source_doc.linetypes and linetype_name not in target_doc.linetypes:
                    try:
                        source_ltype = source_doc.linetypes.get(linetype_name)
                        target_doc.linetypes.new(
                            name=linetype_name,
                            dxfattribs={
                                'description': safe_dxf_getattr(source_ltype.dxf, 'description', '', error_tracker, 'linetype_copy'),
                                # Pattern handling needs special care
                            }
                        )
                    except Exception as e:
                        error_tracker.add_error(f"linetype_copy_{linetype_name}", e)

        # Copy text styles
        if hasattr(source_doc, 'styles'):
            used_styles = set()
            for entity in source_doc.modelspace():
                if safe_dxf_getattr(entity.dxf, 'layer', '0', error_tracker, 'style_check') == layer_name:
                    if hasattr(entity, 'dxftype') and entity.dxftype() == 'TEXT':
                        style = safe_dxf_getattr(entity.dxf, 'style', 'Standard', error_tracker, 'style_check')
                        used_styles.add(style)

            for style_name in used_styles:
                if style_name in source_doc.styles and style_name not in target_doc.styles:
                    try:
                        source_style = source_doc.styles.get(style_name)
                        target_doc.styles.new(
                            name=style_name,
                            dxfattribs={
                                'font': safe_dxf_getattr(source_style.dxf, 'font', 'txt', error_tracker, 'style_copy')
                            }
                        )
                    except Exception as e:
                        error_tracker.add_error(f"style_copy_{style_name}", e)

    except Exception as e:
        error_tracker.add_error("resource_copy", e)

def _copy_entities(source_entities, target_space, error_tracker, context):
    """Copy entities from source to target space with error handling"""
    for entity in source_entities:
        try:
            entity_type = safe_getattr(entity, 'dxftype', 'UNKNOWN', error_tracker, context)
            dxfattribs = {}

            # Copy basic DXF attributes
            if hasattr(entity, 'dxf'):
                for attr in ['layer', 'color', 'linetype', 'thickness', 'lineweight']:
                    if hasattr(entity.dxf, attr):
                        dxfattribs[attr] = getattr(entity.dxf, attr)

            # Handle specific entity types with their special requirements
            if entity_type == 'LINE':
                target_space.add_line(
                    safe_dxf_getattr(entity.dxf, 'start', (0, 0, 0), error_tracker, f"{context}.line"),
                    safe_dxf_getattr(entity.dxf, 'end', (1, 0, 0), error_tracker, f"{context}.line"),
                    dxfattribs=dxfattribs
                )
            elif entity_type == 'CIRCLE':
                target_space.add_circle(
                    safe_dxf_getattr(entity.dxf, 'center', (0, 0, 0), error_tracker, f"{context}.circle"),
                    safe_dxf_getattr(entity.dxf, 'radius', 1.0, error_tracker, f"{context}.circle"),
                    dxfattribs=dxfattribs
                )
            elif entity_type == 'ARC':
                target_space.add_arc(
                    safe_dxf_getattr(entity.dxf, 'center', (0, 0, 0), error_tracker, f"{context}.arc"),
                    safe_dxf_getattr(entity.dxf, 'radius', 1.0, error_tracker, f"{context}.arc"),
                    safe_dxf_getattr(entity.dxf, 'start_angle', 0, error_tracker, f"{context}.arc"),
                    safe_dxf_getattr(entity.dxf, 'end_angle', 360, error_tracker, f"{context}.arc"),
                    dxfattribs=dxfattribs
                )
            elif entity_type == 'TEXT':
                target_space.add_text(
                    safe_dxf_getattr(entity.dxf, 'text', 'Text', error_tracker, f"{context}.text"),
                    dxfattribs={
                        **dxfattribs,
                        'insert': safe_dxf_getattr(entity.dxf, 'insert', (0, 0, 0), error_tracker, f"{context}.text"),
                        'height': safe_dxf_getattr(entity.dxf, 'height', 1.0, error_tracker, f"{context}.text")
                    }
                )
            else:
                # Try to copy generic entities
                try:
                    target_space.add_entity(entity.copy())
                except Exception as copy_error:
                    error_tracker.add_error(f"{context}.generic_copy", copy_error, entity_type)

        except Exception as e:
            error_tracker.add_error(f"{context}.entity_copy", e, entity_type)

def dxf_to_layer_files(input_dxf: str, output_dir: str = None) -> dict:
    """
    Main function to split DXF file by layers

    Args:
        input_dxf: Path to input DXF file
        output_dir: Optional output directory (defaults to folder named after input file)

    Returns:
        Dictionary containing processing results
    """
    print("="*60)
    print("DXF LAYER SPLITTER")
    print("="*60)

    # Process the DXF file
    print("🚀 Starting DXF layer splitting...")
    result = split_dxf_by_layers(input_dxf, output_dir)

    print("="*60)
    print("✨ PROCESSING COMPLETED!")
    print("="*60)

    # Print summary
    metadata = result.get('processing_metadata', {})
    if metadata.get('success', False):
        print(f"\n📈 PROCESSING SUMMARY:")
        print(f"✅ Success: {metadata.get('success', False)}")
        print(f"📁 Source file: {metadata.get('source_file', 'unknown')}")
        print(f"📁 Output directory: {metadata.get('output_directory', 'unknown')}")

        error_details = metadata.get('error_details', {})
        print(f"❌ Total errors: {error_details.get('error_count', 0)}")
        print(f"⚠️ Total warnings: {error_details.get('warning_count', 0)}")

        layers_processed = metadata.get('layers_processed', [])
        print(f"\n📋 LAYERS PROCESSED ({len(layers_processed)}):")
        for layer_info in layers_processed:
            print(f"  • {layer_info['layer_name']}: {layer_info['entity_count']} entities → {Path(layer_info['output_file']).name}")

        if not layers_processed:
            print("  ⚠️ No layers were processed successfully")
    else:
        print(f"\n❌ PROCESSING FAILED:")
        if 'error' in result:
            print(f"  Error: {result['error']}")

    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Split DXF file by layers')
    parser.add_argument('input_dxf', nargs='?', default='input.dxf',
                        help='Path to input DXF file (default: input.dxf)')
    parser.add_argument('--output-dir', '-o', help='Output directory (default: folder named after input file)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')

    args = parser.parse_args()
    input_dxf = args.input_dxf
    output_dir = args.output_dir

    # Validate input file exists
    if not Path(input_dxf).exists():
        print(f"❌ Error: DXF file not found at {input_dxf}")
        sys.exit(1)

    try:
        # Process the DXF file
        result = dxf_to_layer_files(input_dxf, output_dir)

        # Check if processing was successful
        metadata = result.get('processing_metadata', {})
        success = metadata.get('success', False)

        if not success:
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n🛑 Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"💥 Unexpected error: {str(e)}")
        traceback.print_exc()
        sys.exit(1)
