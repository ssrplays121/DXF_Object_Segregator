import json
import sys
from pathlib import Path

def convert_to_human_readable(detailed_json_path: str, output_json_path: str = None) -> dict:
    """
    Convert detailed DXF extraction JSON to human-readable format

    Args:
        detailed_json_path: Path to the detailed JSON output from DXF extraction
        output_json_path: Path to save the human-readable JSON (optional)

    Returns:
        Human-readable JSON data as dictionary
    """
    print("=" * 60)
    print("DXF HUMAN-READABLE CONVERTER")
    print("=" * 60)

    # Load the detailed JSON
    try:
        with open(detailed_json_path, 'r', encoding='utf-8') as f:
            detailed_data = json.load(f)
        print(f"✅ Loaded detailed JSON from: {detailed_json_path}")
    except Exception as e:
        print(f"❌ Error loading JSON file: {str(e)}")
        sys.exit(1)

    # Create human-readable structure
    human_readable = {
        "drawing_summary": {},
        "layers": [],
        "entities": []
    }

    # 1. Process layers (simplified)
    if 'layers' in detailed_data:
        human_readable['layers'] = process_layers(detailed_data['layers'])
        print(f"🎨 Processed {len(human_readable['layers'])} layers")

    # 2. Process entities (main content)
    if 'modelspace' in detailed_data and 'entities' in detailed_data['modelspace']:
        entities = detailed_data['modelspace']['entities']
        human_readable['entities'] = process_entities(entities)
        print(f"📐 Processed {len(human_readable['entities'])} entities")

    # 3. Create drawing summary
    human_readable['drawing_summary'] = create_drawing_summary(human_readable)

    # 4. Save to file if requested
    if output_json_path:
        try:
            with open(output_json_path, 'w', encoding='utf-8') as f:
                json.dump(human_readable, f, indent=2, ensure_ascii=False)
            print(f"✅ Saved human-readable JSON to: {output_json_path}")
        except Exception as e:
            print(f"❌ Error saving output file: {str(e)}")

    print("=" * 60)
    print("✨ CONVERSION COMPLETED!")
    print("=" * 60)

    return human_readable

def process_layers(detailed_layers: list) -> list:
    """
    Convert detailed layer information to human-readable format

    Args:
        detailed_layers: List of detailed layer data from DXF extraction

    Returns:
        Simplified list of layer information
    """
    simplified_layers = []

    # Common AutoCAD color numbers to names mapping
    color_names = {
        1: "red", 2: "yellow", 3: "green", 4: "cyan",
        5: "blue", 6: "magenta", 7: "white", 8: "black",
        256: "bylayer", 0: "byblock"
    }

    for layer in detailed_layers:
        # Simplify color representation
        color_num = layer.get('color', 7)
        color_name = color_names.get(color_num, f"color_{color_num}")

        # Simplify line type name
        linetype = layer.get('linetype', 'CONTINUOUS').lower().replace('bylayer', 'by_layer')

        simplified_layer = {
            "name": layer.get('name', 'unnamed'),
            "color": color_name,
            "line_type": linetype
        }

        # Only include layers that have actual entities or are meaningful
        if layer.get('name') not in ['Defpoints', '*']:
            simplified_layers.append(simplified_layer)

    return simplified_layers

def process_entities(detailed_entities: list) -> list:
    """
    Convert detailed entity information to human-readable format

    Args:
        detailed_entities: List of detailed entity data from DXF extraction

    Returns:
        Simplified list of entity information
    """
    simplified_entities = []
    entity_counter = 1

    for entity in detailed_entities:
        try:
            entity_type = entity.get('type', '').lower()
            layer = entity.get('layer', '0')

            # Skip entities that are not visually meaningful
            if entity_type in ['insert', 'attrib', 'dimension']:  # Can be expanded based on needs
                continue

            simplified_entity = {
                "id": entity_counter,
                "type": entity_type,
                "layer": layer
            }

            # Process geometry based on entity type
            if entity_type == 'circle' and 'geometry' in entity:
                geom = entity['geometry']
                simplified_entity.update({
                    "center": parse_coordinate(geom.get('center', '(0.0, 0.0, 0.0)')),
                    "radius": round(float(geom.get('radius', 0.0)), 2),
                    "diameter": round(float(geom.get('radius', 0.0)) * 2, 2)
                })

            elif entity_type in ['arc', 'ellipse'] and 'geometry' in entity:
                geom = entity['geometry']
                simplified_entity.update({
                    "center": parse_coordinate(geom.get('center', '(0.0, 0.0, 0.0)')),
                    "start_angle": round(float(geom.get('start_angle', 0.0)), 1),
                    "end_angle": round(float(geom.get('end_angle', 360.0)), 1)
                })

                if entity_type == 'arc':
                    simplified_entity.update({
                        "radius": round(float(geom.get('radius', 0.0)), 2)
                    })
                elif entity_type == 'ellipse':
                    simplified_entity.update({
                        "major_axis": parse_coordinate(geom.get('major_axis', '(1.0, 0.0, 0.0)')),
                        "minor_radius_ratio": round(float(geom.get('ratio', 1.0)), 2)
                    })

            elif entity_type == 'line' and 'geometry' in entity:
                geom = entity['geometry']
                simplified_entity.update({
                    "start_point": parse_coordinate(geom.get('start', '(0.0, 0.0, 0.0)')),
                    "end_point": parse_coordinate(geom.get('end', '(1.0, 0.0, 0.0)'))
                })

            elif entity_type in ['lwpolyline', 'polyline'] and 'geometry' in entity:
                geom = entity['geometry']
                vertices = []

                if 'vertices' in geom and isinstance(geom['vertices'], list):
                    for vertex in geom['vertices']:
                        if isinstance(vertex, dict):
                            vertices.append({
                                "x": round(float(vertex.get('x', 0.0)), 2),
                                "y": round(float(vertex.get('y', 0.0)), 2)
                            })
                        elif isinstance(vertex, (list, tuple)) and len(vertex) >= 2:
                            vertices.append({
                                "x": round(float(vertex[0]), 2),
                                "y": round(float(vertex[1]), 2)
                            })

                simplified_entity.update({
                    "vertices": vertices,
                    "closed": bool(geom.get('closed', False)),
                    "vertex_count": len(vertices)
                })

            elif entity_type == 'text' and 'text_content' in entity:
                simplified_entity.update({
                    "text": entity['text_content'],
                    "insertion_point": parse_coordinate(entity['attributes'].get('insert', '(0.0, 0.0, 0.0)')),
                    "height": round(float(entity['attributes'].get('height', 2.5)), 2)
                })

            # Add to the list if it has meaningful content
            if 'geometry' in entity or 'text_content' in entity or entity_type in ['circle', 'arc', 'ellipse', 'line']:
                simplified_entities.append(simplified_entity)
                entity_counter += 1

        except Exception as e:
            print(f"⚠️ Warning: Could not process entity {entity_counter}: {str(e)}")
            continue

    return simplified_entities

def parse_coordinate(coord_str: str) -> list:
    """
    Parse coordinate string to clean [x, y] format

    Args:
        coord_str: Coordinate string like "(140.0, 50.0, 0.0)"

    Returns:
        List with [x, y] coordinates rounded to 2 decimal places
    """
    try:
        # Clean the string and extract numbers
        cleaned = coord_str.replace('(', '').replace(')', '').replace(',', ' ').strip()
        numbers = [float(x) for x in cleaned.split() if x.strip()]

        # Return only x, y coordinates (ignore z for 2D drawings)
        if len(numbers) >= 2:
            return [round(numbers[0], 2), round(numbers[1], 2)]
        return [0.0, 0.0]
    except:
        return [0.0, 0.0]

def create_drawing_summary(human_readable_data: dict) -> dict:
    """
    Create a summary of the drawing content

    Args:
        human_readable_data: Processed human-readable data

    Returns:
        Summary dictionary
    """
    entities = human_readable_data.get('entities', [])
    layers = human_readable_data.get('layers', [])

    # Count entity types
    entity_types = {}
    for entity in entities:
        etype = entity.get('type', 'unknown')
        entity_types[etype] = entity_types.get(etype, 0) + 1

    # Calculate drawing bounds (simplified)
    all_x = []
    all_y = []

    for entity in entities:
        if 'center' in entity:
            all_x.append(entity['center'][0])
            all_y.append(entity['center'][1])
        if 'start_point' in entity:
            all_x.append(entity['start_point'][0])
            all_y.append(entity['start_point'][1])
            all_x.append(entity['end_point'][0])
            all_y.append(entity['end_point'][1])
        if 'vertices' in entity:
            for vertex in entity['vertices']:
                all_x.append(vertex['x'])
                all_y.append(vertex['y'])

    bounds = {
        "min_x": round(min(all_x), 2) if all_x else 0.0,
        "max_x": round(max(all_x), 2) if all_x else 0.0,
        "min_y": round(min(all_y), 2) if all_y else 0.0,
        "max_y": round(max(all_y), 2) if all_y else 0.0,
        "width": round(max(all_x) - min(all_x), 2) if all_x else 0.0,
        "height": round(max(all_y) - min(all_y), 2) if all_y else 0.0
    } if all_x and all_y else {}

    return {
        "title": "DXF Drawing Content",
        "description": "Human-readable summary of DXF file contents",
        "total_entities": len(entities),
        "entity_counts_by_type": entity_types,
        "total_layers": len(layers),
        "active_layers": [layer['name'] for layer in layers],
        "drawing_bounds": bounds,
        "units": "drawing units"
    }

def print_summary(human_readable_data: dict):
    """
    Print a human-readable summary to console

    Args:
        human_readable_data: Processed human-readable data
    """
    summary = human_readable_data['drawing_summary']
    entities = human_readable_data['entities']
    layers = human_readable_data['layers']

    print("\n" + "=" * 60)
    print("DRAWING SUMMARY")
    print("=" * 60)

    print(f"📊 Total Entities: {summary.get('total_entities', 0)}")
    print(f"🎨 Active Layers: {', '.join(summary.get('active_layers', []))}")

    print("\n📈 Entity Breakdown:")
    for entity_type, count in summary.get('entity_counts_by_type', {}).items():
        print(f"  • {entity_type.capitalize()}: {count}")

    if 'drawing_bounds' in summary and summary['drawing_bounds']:
        bounds = summary['drawing_bounds']
        print(f"\n📏 Drawing Bounds:")
        print(f"  Width: {bounds['width']} units")
        print(f"  Height: {bounds['height']} units")
        print(f"  Area: {round(bounds['width'] * bounds['height'], 2)} square units")

    print("\n🔍 Entity Details:")
    for entity in entities:
        if entity['type'] == 'circle':
            print(f"  ○ Circle on '{entity['layer']}' layer: Center {entity['center']}, Radius {entity['radius']}")
        elif entity['type'] == 'arc':
            print(f"  ⌒ Arc on '{entity['layer']}' layer: Center {entity['center']}, Radius {entity['radius']}, {entity['start_angle']}° to {entity['end_angle']}°")
        elif entity['type'] == 'ellipse':
            print(f"  ◯ Ellipse on '{entity['layer']}' layer: Center {entity['center']}, Major axis ratio {entity['minor_radius_ratio']}")
        elif entity['type'] == 'line':
            print(f"  ─ Line on '{entity['layer']}' layer: From {entity['start_point']} to {entity['end_point']}")

    print("=" * 60)

if __name__ == "__main__":
    import argparse

    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description='Convert DXF JSON to human-readable format')
    parser.add_argument('input_json', nargs='?', default='output_complex.json',
                        help='Path to input JSON file (default: output_complex.json)')
    parser.add_argument('output_json', nargs='?', default='output_simple.json',
                        help='Path to output human-readable JSON file (default: output_simple.json)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Enable verbose output')

    args = parser.parse_args()
    input_json = args.input_json
    output_json = args.output_json

    # Validate input file exists
    if not Path(input_json).exists():
        print(f"❌ Error: Input file not found: {input_json}")
        sys.exit(1)

    try:
        # Convert to human-readable format
        result = convert_to_human_readable(input_json, output_json)

        # Print summary to console
        print_summary(result)

        # Show where to find the output
        print(f"\n💡 Human-readable JSON saved to: {output_json}")
        print("This file contains only the essential visual information in a clean format.")

    except KeyboardInterrupt:
        print("\n🛑 Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"💥 Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
