#!/usr/bin/env python3
"""
segregation.py - Groups DXF entities into objects based on layer and geometric intersection

This script reads a DXF file, groups entities that intersect each other within the same layer,
and exports the grouped objects to a JSON file with comprehensive error logging.
"""

import ezdxf
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set, Union
import traceback
import sys
import time
from collections import defaultdict, deque
import argparse
from ezdxf.math import Vec3, Vec2, intersection_line_line_2d, distance_point_line_2d
import re


def ensure_coordinate_tuple(coord):
    """
    Ensure coordinate is a proper (x, y) tuple regardless of input format
    """
    # Handle None values
    if coord is None:
        return (0.0, 0.0)

    # Handle float/int values that might be single coordinates
    if isinstance(coord, (int, float)):
        return (float(coord), 0.0)

    # Handle Vec2/Vec3 objects
    if hasattr(coord, 'x') and hasattr(coord, 'y'):
        return (float(coord.x), float(coord.y))

    # Handle tuples/lists
    if isinstance(coord, (tuple, list)):
        if len(coord) == 0:
            return (0.0, 0.0)
        elif len(coord) == 1:
            return (float(coord[0]), 0.0)
        else:
            # Handle nested structures
            if isinstance(coord[0], (tuple, list)) and len(coord[0]) >= 2:
                return (float(coord[0][0]), float(coord[0][1]))
            return (float(coord[0]), float(coord[1]) if len(coord) > 1 else 0.0)

    # Handle dictionary-like objects with 'x' and 'y' keys
    if isinstance(coord, dict):
        if 'x' in coord and 'y' in coord:
            return (float(coord['x']), float(coord['y']))
        elif 'location' in coord:
            return ensure_coordinate_tuple(coord['location'])
        elif 'start' in coord and 'end' in coord:  # Handle line objects
            return ensure_coordinate_tuple(coord['start'])

    # Handle string representations
    try:
        if isinstance(coord, str):
            # Try to parse common coordinate string formats
            coords = re.findall(r'[-+]?\d*\.?\d+', coord)
            if len(coords) >= 2:
                return (float(coords[0]), float(coords[1]))
            elif len(coords) == 1:
                return (float(coords[0]), 0.0)
    except:
        pass

    # Last resort: try to convert to string and extract numbers
    try:
        str_coord = str(coord)
        coords = re.findall(r'[-+]?\d*\.?\d+', str_coord)
        if len(coords) >= 2:
            return (float(coords[0]), float(coords[1]))
        elif len(coords) == 1:
            return (float(coords[0]), 0.0)
    except:
        pass

    # If all else fails, return default coordinates
    print(f"⚠️ WARNING: Could not parse coordinate format: {type(coord)} - {coord}")
    return (0.0, 0.0)


class DXFErrorTracker:
    """Tracks errors and missing values during DXF extraction and processing"""

    def __init__(self):
        self.errors = defaultdict(list)
        self.missing_values = defaultdict(int)
        self.warning_count = 0
        self.error_count = 0
        self.start_time = time.time()

    def add_error(self, context: str, error: Exception, entity_type: str = None, entity_handle: str = None):
        """Record an error with context"""
        error_info = {
            'context': context,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc(limit=2),
            'entity_type': entity_type or 'unknown',
            'entity_handle': entity_handle or 'unknown',
            'timestamp': time.time()
        }
        self.errors[context].append(error_info)
        self.error_count += 1
        print(f"❌ ERROR [{context}]: {str(error)} (Entity: {entity_type}, Handle: {entity_handle})")

    def add_missing_value(self, context: str, attribute: str, entity_type: str = None):
        """Record a missing value"""
        key = f"{context}.{attribute}"
        self.missing_values[key] += 1
        self.warning_count += 1
        # Only print first occurrence to avoid spam
        if self.missing_values[key] == 1:
            print(f"⚠️ WARNING [{context}]: Missing attribute '{attribute}' for {entity_type or 'entity'} - using default")

    def get_summary(self) -> str:
        """Generate a comprehensive error summary"""
        summary = []
        summary.append("\n" + "="*60)
        summary.append("DXF ENTITY SEGREGATION ERROR SUMMARY")
        summary.append("="*60)

        elapsed_time = time.time() - self.start_time
        summary.append(f"⏱️  Processing Time: {elapsed_time:.2f} seconds")

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
                for i, error in enumerate(errors[:3], 1):  # Show first 3 errors per context
                    summary.append(f"    Error #{i}:")
                    summary.append(f"      Type: {error['error_type']}")
                    summary.append(f"      Message: {error['error_message']}")
                    summary.append(f"      Entity: {error['entity_type']} (Handle: {error['entity_handle']})")
                    # Only show first line of traceback to keep it clean
                    tb_lines = error['traceback'].split('\n')
                    if len(tb_lines) > 1:
                        summary.append(f"      Traceback: {tb_lines[1].strip()}")
                if len(errors) > 3:
                    summary.append(f"      ... and {len(errors) - 3} more errors in this context")

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
        if any('intersection' in context.lower() for context in self.errors):
            summary.append("  - Some entities may have complex geometry that requires manual verification")

        summary.append("="*60)
        return "\n".join(summary)

    def has_errors(self) -> bool:
        return self.error_count > 0

    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics for metadata"""
        elapsed_time = time.time() - self.start_time
        return {
            'total_errors': self.error_count,
            'total_warnings': self.warning_count,
            'processing_time_seconds': round(elapsed_time, 2),
            'missing_values_count': sum(self.missing_values.values())
        }


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
            entity_type = getattr(obj, 'dxftype', lambda: 'unknown')() if hasattr(obj, 'dxftype') else 'unknown'
            entity_handle = safe_dxf_getattr(getattr(obj, 'dxf', None), 'handle', 'unknown', error_tracker, context) if hasattr(obj, 'dxf') else 'unknown'
            error_tracker.add_error(f"{context}.{attr_name}", e, entity_type, entity_handle)
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
            entity_type = getattr(dxf_obj, 'dxftype', lambda: 'unknown')() if hasattr(dxf_obj, 'dxftype') else 'unknown'
            entity_handle = safe_getattr(dxf_obj, 'handle', 'unknown', error_tracker, context) if hasattr(dxf_obj, 'handle') else 'unknown'
            error_tracker.add_error(f"{context}.dxf.{attr_name}", e, entity_type, entity_handle)
        return default


def serialize_dxf_value(value):
    """Safely serialize DXF values for JSON, handling modern math types"""
    if isinstance(value, (Vec3, Vec2)):
        return [float(value.x), float(value.y), float(value.z) if hasattr(value, 'z') else 0.0]
    elif isinstance(value, (list, tuple)):
        return [serialize_dxf_value(item) for item in value]
    elif hasattr(value, '__dict__') and not isinstance(value, (int, float, str, bool, type(None), list, dict)):
        try:
            return str(value)
        except:
            return repr(value)
    return value


def extract_entity_geometry(entity, error_tracker: DXFErrorTracker, context: str) -> Dict[str, Any]:
    """
    Extract geometry data from an entity for intersection detection

    Returns a dictionary containing geometry information suitable for intersection calculations
    """
    entity_type = entity.dxftype() if hasattr(entity, 'dxftype') else 'UNKNOWN'
    geometry = {'type': entity_type.lower()}

    try:
        if entity_type == 'LINE':
            start = safe_dxf_getattr(entity.dxf, 'start', Vec3(0, 0, 0), error_tracker, f"{context}.line")
            end = safe_dxf_getattr(entity.dxf, 'end', Vec3(1, 0, 0), error_tracker, f"{context}.line")
            # Use ensure_coordinate_tuple for robust coordinate handling
            geometry.update({
                'start': ensure_coordinate_tuple(start),
                'end': ensure_coordinate_tuple(end)
            })

        elif entity_type == 'CIRCLE':
            center = safe_dxf_getattr(entity.dxf, 'center', Vec3(0, 0, 0), error_tracker, f"{context}.circle")
            radius = safe_dxf_getattr(entity.dxf, 'radius', 1.0, error_tracker, f"{context}.circle")
            geometry.update({
                'center': ensure_coordinate_tuple(center),
                'radius': float(radius) if radius is not None else 1.0
            })

        elif entity_type == 'ARC':
            center = safe_dxf_getattr(entity.dxf, 'center', Vec3(0, 0, 0), error_tracker, f"{context}.arc")
            radius = safe_dxf_getattr(entity.dxf, 'radius', 1.0, error_tracker, f"{context}.arc")
            start_angle = safe_dxf_getattr(entity.dxf, 'start_angle', 0.0, error_tracker, f"{context}.arc")
            end_angle = safe_dxf_getattr(entity.dxf, 'end_angle', 360.0, error_tracker, f"{context}.arc")
            geometry.update({
                'center': ensure_coordinate_tuple(center),
                'radius': float(radius) if radius is not None else 1.0,
                'start_angle': float(start_angle) if start_angle is not None else 0.0,
                'end_angle': float(end_angle) if end_angle is not None else 360.0
            })

        elif entity_type in ['LWPOLYLINE', 'POLYLINE']:
            vertices = []
            closed = False

            if entity_type == 'LWPOLYLINE':
                closed = safe_getattr(entity, 'closed', False, error_tracker, f"{context}.lwpolyline")
                # Extract vertices from LWPOLYLINE
                points = safe_getattr(entity, 'get_points', [], error_tracker, f"{context}.lwpolyline")
                if callable(points):
                    try:
                        points = points()
                    except Exception as e:
                        error_tracker.add_error(f"{context}.lwpolyline.get_points", e, entity_type)
                        points = []

                for point in points:
                    vertices.append(ensure_coordinate_tuple(point))

            elif entity_type == 'POLYLINE':
                closed = safe_getattr(entity, 'is_closed', False, error_tracker, f"{context}.polyline")
                # Extract vertices from POLYLINE
                if hasattr(entity, 'vertices'):
                    for vertex in entity.vertices:
                        if hasattr(vertex, 'dxf') and hasattr(vertex.dxf, 'location'):
                            loc = vertex.dxf.location
                            vertices.append(ensure_coordinate_tuple(loc))

            geometry.update({
                'vertices': vertices,
                'closed': bool(closed)
            })

        elif entity_type == 'POINT':
            location = safe_dxf_getattr(entity.dxf, 'location', Vec3(0, 0, 0), error_tracker, f"{context}.point")
            geometry.update({
                'location': ensure_coordinate_tuple(location)
            })

        elif entity_type == 'TEXT':
            insert = safe_dxf_getattr(entity.dxf, 'insert', Vec3(0, 0, 0), error_tracker, f"{context}.text")
            height = safe_dxf_getattr(entity.dxf, 'height', 1.0, error_tracker, f"{context}.text")
            geometry.update({
                'insert': ensure_coordinate_tuple(insert),
                'height': float(height) if height is not None else 1.0
            })

        # Add bounding box for all entities
        geometry['bbox'] = calculate_entity_bbox(geometry, entity_type)

    except Exception as e:
        error_tracker.add_error(f"{context}.geometry_extraction", e, entity_type)
        geometry['error'] = str(e)

    return geometry


def calculate_entity_bbox(geometry: Dict[str, Any], entity_type: str) -> Dict[str, Any]:
    """
    Calculate bounding box for an entity's geometry

    Returns a dictionary with min/max coordinates for quick intersection testing
    """
    bbox = {'min_x': float('inf'), 'min_y': float('inf'), 'max_x': float('-inf'), 'max_y': float('-inf')}

    try:
        if entity_type == 'LINE':
            if 'start' in geometry and 'end' in geometry:
                start = geometry['start']
                end = geometry['end']
                bbox['min_x'] = min(start[0], end[0])
                bbox['min_y'] = min(start[1], end[1])
                bbox['max_x'] = max(start[0], end[0])
                bbox['max_y'] = max(start[1], end[1])

        elif entity_type in ['CIRCLE', 'ARC']:
            if 'center' in geometry and 'radius' in geometry:
                center = geometry['center']
                radius = geometry['radius']
                bbox['min_x'] = center[0] - radius
                bbox['min_y'] = center[1] - radius
                bbox['max_x'] = center[0] + radius
                bbox['max_y'] = center[1] + radius

        elif entity_type in ['LWPOLYLINE', 'POLYLINE']:
            if 'vertices' in geometry and geometry['vertices']:
                vertices = geometry['vertices']
                bbox['min_x'] = min(v[0] for v in vertices)
                bbox['min_y'] = min(v[1] for v in vertices)
                bbox['max_x'] = max(v[0] for v in vertices)
                bbox['max_y'] = max(v[1] for v in vertices)

        elif entity_type == 'POINT':
            if 'location' in geometry:
                loc = geometry['location']
                bbox['min_x'] = bbox['max_x'] = loc[0]
                bbox['min_y'] = bbox['max_y'] = loc[1]

        elif entity_type == 'TEXT':
            if 'insert' in geometry and 'height' in geometry:
                insert = geometry['insert']
                height = geometry['height']
                # Simple bounding box for text (approximate)
                bbox['min_x'] = insert[0]
                bbox['min_y'] = insert[1]
                bbox['max_x'] = insert[0] + height * 2  # Rough estimate
                bbox['max_y'] = insert[1] + height

    except Exception as e:
        # If bounding box calculation fails, use default values
        bbox = {'min_x': 0, 'min_y': 0, 'max_x': 1, 'max_y': 1}

    return bbox


def bbox_intersect(bbox1: Dict[str, float], bbox2: Dict[str, float]) -> bool:
    """
    Quick bounding box intersection test

    Returns True if bounding boxes overlap, False otherwise
    """
    return not (bbox1['max_x'] < bbox2['min_x'] or
                bbox1['min_x'] > bbox2['max_x'] or
                bbox1['max_y'] < bbox2['min_y'] or
                bbox1['min_y'] > bbox2['max_y'])


def entities_intersect(entity1_geom: Dict[str, Any], entity2_geom: Dict[str, Any],
                      entity1_type: str, entity2_type: str, error_tracker: DXFErrorTracker) -> bool:
    """
    Determine if two entities intersect geometrically

    Uses a two-step approach: first check bounding boxes, then perform detailed geometry intersection
    """
    try:
        # Quick bounding box check first
        if not bbox_intersect(entity1_geom['bbox'], entity2_geom['bbox']):
            return False

        # Get entity types in lowercase for comparison
        type1 = entity1_type.lower()
        type2 = entity2_type.lower()

        # Handle different entity type combinations
        if type1 == 'line' and type2 == 'line':
            return line_line_intersect(entity1_geom, entity2_geom, error_tracker)

        elif (type1 == 'line' and type2 == 'circle') or (type1 == 'circle' and type2 == 'line'):
            line_geom = entity1_geom if type1 == 'line' else entity2_geom
            circle_geom = entity1_geom if type1 == 'circle' else entity2_geom
            return line_circle_intersect(line_geom, circle_geom, error_tracker)

        elif type1 == 'circle' and type2 == 'circle':
            return circle_circle_intersect(entity1_geom, entity2_geom, error_tracker)

        elif (type1 == 'line' and type2 in ['lwpolyline', 'polyline']) or (type1 in ['lwpolyline', 'polyline'] and type2 == 'line'):
            line_geom = entity1_geom if type1 == 'line' else entity2_geom
            poly_geom = entity1_geom if type1 in ['lwpolyline', 'polyline'] else entity2_geom
            return line_polyline_intersect(line_geom, poly_geom, error_tracker)

        elif type1 in ['lwpolyline', 'polyline'] and type2 in ['lwpolyline', 'polyline']:
            return polyline_polyline_intersect(entity1_geom, entity2_geom, error_tracker)

        elif type1 == 'point' or type2 == 'point':
            point_geom = entity1_geom if type1 == 'point' else entity2_geom
            other_geom = entity2_geom if type1 == 'point' else entity1_geom
            other_type = type2 if type1 == 'point' else type1
            return point_entity_intersect(point_geom, other_geom, other_type, error_tracker)

        # Default cases - consider intersecting if bounding boxes overlap
        return True

    except Exception as e:
        error_tracker.add_error(f"intersection_detection.{type1}_{type2}", e, type1, "unknown")
        return False


def line_line_intersect(line1_geom: Dict[str, Any], line2_geom: Dict[str, Any], error_tracker: DXFErrorTracker) -> bool:
    """
    Check if two lines intersect

    Uses ezdxf.math.intersection_line_line_2d for accurate 2D line intersection detection
    """
    try:
        # Get coordinates with fallback values and ensure proper tuple format
        start1 = ensure_coordinate_tuple(line1_geom.get('start', (0.0, 0.0)))
        end1 = ensure_coordinate_tuple(line1_geom.get('end', (1.0, 0.0)))
        start2 = ensure_coordinate_tuple(line2_geom.get('start', (0.0, 0.0)))
        end2 = ensure_coordinate_tuple(line2_geom.get('end', (1.0, 0.0)))

        # Use the ezdxf math function with proper Vec2 objects
        from ezdxf.math import Vec2
        intersection = intersection_line_line_2d(
            Vec2(start1[0], start1[1]),
            Vec2(end1[0], end1[1]),
            Vec2(start2[0], start2[1]),
            Vec2(end2[0], end2[1])
        )

        if intersection is None:
            return False

        # Check if intersection point lies within both line segments
        def point_on_segment(point, start, end):
            """Check if point is on the line segment between start and end"""
            # Use tolerance for floating point comparisons
            min_x = min(start[0], end[0]) - 1e-6
            max_x = max(start[0], end[0]) + 1e-6
            min_y = min(start[1], end[1]) - 1e-6
            max_y = max(start[1], end[1]) + 1e-6

            return (min_x <= point.x <= max_x) and (min_y <= point.y <= max_y)

        return point_on_segment(intersection, start1, end1) and point_on_segment(intersection, start2, end2)

    except Exception as e:
        # Add detailed debugging information
        debug_info = {
            'line1_start': line1_geom.get('start'),
            'line1_end': line1_geom.get('end'),
            'line2_start': line2_geom.get('start'),
            'line2_end': line2_geom.get('end'),
            'types': {
                'start1_type': type(line1_geom.get('start')).__name__ if line1_geom.get('start') is not None else 'None',
                'end1_type': type(line1_geom.get('end')).__name__ if line1_geom.get('end') is not None else 'None',
                'start2_type': type(line2_geom.get('start')).__name__ if line2_geom.get('start') is not None else 'None',
                'end2_type': type(line2_geom.get('end')).__name__ if line2_geom.get('end') is not None else 'None'
            }
        }
        error_tracker.add_error("line_line_intersection", e, "LINE", "unknown")
        return False


def line_circle_intersect(line_geom: Dict[str, Any], circle_geom: Dict[str, Any], error_tracker: DXFErrorTracker) -> bool:
    try:
        start = ensure_coordinate_tuple(line_geom['start'])
        end = ensure_coordinate_tuple(line_geom['end'])
        center = ensure_coordinate_tuple(circle_geom['center'])
        radius = circle_geom['radius']

        from ezdxf.math import Vec2
        distance = distance_point_line_2d(
            Vec2(center[0], center[1]),
            Vec2(start[0], start[1]),
            Vec2(end[0], end[1])
        )

        return distance <= radius + 1e-6
    except Exception as e:
        error_tracker.add_error("line_circle_intersection", e, "LINE/CIRCLE", "unknown")
        return False


def circle_circle_intersect(circle1_geom: Dict[str, Any], circle2_geom: Dict[str, Any], error_tracker: DXFErrorTracker) -> bool:
    try:
        center1 = ensure_coordinate_tuple(circle1_geom['center'])
        center2 = ensure_coordinate_tuple(circle2_geom['center'])
        radius1 = circle1_geom['radius']
        radius2 = circle2_geom['radius']

        dx = center2[0] - center1[0]
        dy = center2[1] - center1[1]
        distance = (dx * dx + dy * dy) ** 0.5

        return abs(radius1 - radius2) <= distance <= (radius1 + radius2) + 1e-6
    except Exception as e:
        error_tracker.add_error("circle_circle_intersection", e, "CIRCLE", "unknown")
        return False


def line_polyline_intersect(line_geom: Dict[str, Any], poly_geom: Dict[str, Any], error_tracker: DXFErrorTracker) -> bool:
    """
    Check if a line intersects with a polyline

    Breaks polyline into individual line segments and checks each one
    """
    try:
        vertices = poly_geom.get('vertices', [])
        if not vertices:
            return False

        # Check intersection with each segment
        for i in range(len(vertices) - 1):
            segment_start = vertices[i]
            segment_end = vertices[i + 1]

            # Create temporary line geometry for this segment
            segment_geom = {
                'start': segment_start,
                'end': segment_end,
                'bbox': {
                    'min_x': min(segment_start[0], segment_end[0]),
                    'min_y': min(segment_start[1], segment_end[1]),
                    'max_x': max(segment_start[0], segment_end[0]),
                    'max_y': max(segment_start[1], segment_end[1])
                }
            }

            if line_line_intersect(line_geom, segment_geom, error_tracker):
                return True

        # If polyline is closed, check the last segment connecting back to first vertex
        if poly_geom.get('closed', False) and len(vertices) > 2:
            segment_start = vertices[-1]
            segment_end = vertices[0]

            segment_geom = {
                'start': segment_start,
                'end': segment_end,
                'bbox': {
                    'min_x': min(segment_start[0], segment_end[0]),
                    'min_y': min(segment_start[1], segment_end[1]),
                    'max_x': max(segment_start[0], segment_end[0]),
                    'max_y': max(segment_start[1], segment_end[1])
                }
            }

            if line_line_intersect(line_geom, segment_geom, error_tracker):
                return True

        return False

    except Exception as e:
        error_tracker.add_error("line_polyline_intersection", e, "LINE/POLYLINE", "unknown")
        return False


def polyline_polyline_intersect(poly1_geom: Dict[str, Any], poly2_geom: Dict[str, Any], error_tracker: DXFErrorTracker) -> bool:
    """
    Check if two polylines intersect

    Checks all segment combinations between the two polylines
    """
    try:
        vertices1 = poly1_geom.get('vertices', [])
        vertices2 = poly2_geom.get('vertices', [])

        if not vertices1 or not vertices2:
            return False

        # Check all segment combinations
        for i in range(len(vertices1) - 1):
            seg1_start = vertices1[i]
            seg1_end = vertices1[i + 1]
            seg1_geom = {
                'start': seg1_start,
                'end': seg1_end,
                'bbox': {
                    'min_x': min(seg1_start[0], seg1_end[0]),
                    'min_y': min(seg1_start[1], seg1_end[1]),
                    'max_x': max(seg1_start[0], seg1_end[0]),
                    'max_y': max(seg1_start[1], seg1_end[1])
                }
            }

            for j in range(len(vertices2) - 1):
                seg2_start = vertices2[j]
                seg2_end = vertices2[j + 1]
                seg2_geom = {
                    'start': seg2_start,
                    'end': seg2_end,
                    'bbox': {
                        'min_x': min(seg2_start[0], seg2_end[0]),
                        'min_y': min(seg2_start[1], seg2_end[1]),
                        'max_x': max(seg2_start[0], seg2_end[0]),
                        'max_y': max(seg2_start[1], seg2_end[1])
                    }
                }

                if line_line_intersect(seg1_geom, seg2_geom, error_tracker):
                    return True

        # Check closing segments if polylines are closed
        if poly1_geom.get('closed', False) and len(vertices1) > 2:
            seg1_start = vertices1[-1]
            seg1_end = vertices1[0]
            seg1_geom = {
                'start': seg1_start,
                'end': seg1_end,
                'bbox': {
                    'min_x': min(seg1_start[0], seg1_end[0]),
                    'min_y': min(seg1_start[1], seg1_end[1]),
                    'max_x': max(seg1_start[0], seg1_end[0]),
                    'max_y': max(seg1_start[1], seg1_end[1])
                }
            }

            for j in range(len(vertices2) - 1):
                seg2_start = vertices2[j]
                seg2_end = vertices2[j + 1]
                seg2_geom = {
                    'start': seg2_start,
                    'end': seg2_end,
                    'bbox': {
                        'min_x': min(seg2_start[0], seg2_end[0]),
                        'min_y': min(seg2_start[1], seg2_end[1]),
                        'max_x': max(seg2_start[0], seg2_end[0]),
                        'max_y': max(seg2_start[1], seg2_end[1])
                    }
                }

                if line_line_intersect(seg1_geom, seg2_geom, error_tracker):
                    return True

        if poly2_geom.get('closed', False) and len(vertices2) > 2:
            seg2_start = vertices2[-1]
            seg2_end = vertices2[0]
            seg2_geom = {
                'start': seg2_start,
                'end': seg2_end,
                'bbox': {
                    'min_x': min(seg2_start[0], seg2_end[0]),
                    'min_y': min(seg2_start[1], seg2_end[1]),
                    'max_x': max(seg2_start[0], seg2_end[0]),
                    'max_y': max(seg2_start[1], seg2_end[1])
                }
            }

            for i in range(len(vertices1) - 1):
                seg1_start = vertices1[i]
                seg1_end = vertices1[i + 1]
                seg1_geom = {
                    'start': seg1_start,
                    'end': seg1_end,
                    'bbox': {
                        'min_x': min(seg1_start[0], seg1_end[0]),
                        'min_y': min(seg1_start[1], seg1_end[1]),
                        'max_x': max(seg1_start[0], seg1_end[0]),
                        'max_y': max(seg1_start[1], seg1_end[1])
                    }
                }

                if line_line_intersect(seg1_geom, seg2_geom, error_tracker):
                    return True

        return False

    except Exception as e:
        error_tracker.add_error("polyline_polyline_intersection", e, "POLYLINE", "unknown")
        return False


def point_entity_intersect(point_geom: Dict[str, Any], entity_geom: Dict[str, Any], entity_type: str, error_tracker: DXFErrorTracker) -> bool:
    """
    Check if a point intersects with another entity

    For lines: check if point is on the line segment
    For circles: check if point is within radius
    For polylines: check if point is on any segment
    """
    try:
        point = ensure_coordinate_tuple(point_geom['location'])

        if entity_type == 'line':
            start = ensure_coordinate_tuple(entity_geom['start'])
            end = ensure_coordinate_tuple(entity_geom['end'])

            # Check if point is on line segment using distance method
            from ezdxf.math import Vec2
            distance_to_line = distance_point_line_2d(
                Vec2(point[0], point[1]),
                Vec2(start[0], start[1]),
                Vec2(end[0], end[1])
            )
            distance_to_start = ((point[0] - start[0]) ** 2 + (point[1] - start[1]) ** 2) ** 0.5
            distance_to_end = ((point[0] - end[0]) ** 2 + (point[1] - end[1]) ** 2) ** 0.5
            line_length = ((end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2) ** 0.5

            # Point is on line segment if:
            # 1. Distance to line is very small
            # 2. Distance to start + distance to end ≈ line length
            return (distance_to_line < 1e-6 and
                   abs((distance_to_start + distance_to_end) - line_length) < 1e-6)

        elif entity_type == 'circle':
            center = ensure_coordinate_tuple(entity_geom['center'])
            radius = entity_geom['radius']
            distance = ((point[0] - center[0]) ** 2 + (point[1] - center[1]) ** 2) ** 0.5
            return abs(distance - radius) < 1e-6

        elif entity_type in ['lwpolyline', 'polyline']:
            vertices = entity_geom.get('vertices', [])
            if not vertices:
                return False

            # Check if point is on any segment
            for i in range(len(vertices) - 1):
                start = vertices[i]
                end = vertices[i + 1]
                from ezdxf.math import Vec2
                distance_to_line = distance_point_line_2d(
                    Vec2(point[0], point[1]),
                    Vec2(start[0], start[1]),
                    Vec2(end[0], end[1])
                )
                distance_to_start = ((point[0] - start[0]) ** 2 + (point[1] - start[1]) ** 2) ** 0.5
                distance_to_end = ((point[0] - end[0]) ** 2 + (point[1] - end[1]) ** 2) ** 0.5
                segment_length = ((end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2) ** 0.5

                if (distance_to_line < 1e-6 and
                    abs((distance_to_start + distance_to_end) - segment_length) < 1e-6):
                    return True

            # Check closing segment if closed polyline
            if entity_geom.get('closed', False) and len(vertices) > 2:
                start = vertices[-1]
                end = vertices[0]
                from ezdxf.math import Vec2
                distance_to_line = distance_point_line_2d(
                    Vec2(point[0], point[1]),
                    Vec2(start[0], start[1]),
                    Vec2(end[0], end[1])
                )
                distance_to_start = ((point[0] - start[0]) ** 2 + (point[1] - start[1]) ** 2) ** 0.5
                distance_to_end = ((point[0] - end[0]) ** 2 + (point[1] - end[1]) ** 2) ** 0.5
                segment_length = ((end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2) ** 0.5

                return (distance_to_line < 1e-6 and
                       abs((distance_to_start + distance_to_end) - segment_length) < 1e-6)

            return False

        else:
            # For other entities, use bounding box approximation
            bbox = entity_geom['bbox']
            return (bbox['min_x'] - 1e-6 <= point[0] <= bbox['max_x'] + 1e-6 and
                    bbox['min_y'] - 1e-6 <= point[1] <= bbox['max_y'] + 1e-6)

    except Exception as e:
        error_tracker.add_error(f"point_{entity_type}_intersection", e, "POINT", "unknown")
        return False


def group_entities_by_layer(entities: List[Any], error_tracker: DXFErrorTracker) -> Dict[str, List[Dict[str, Any]]]:
    """
    Group entities by their layer

    Returns a dictionary mapping layer names to lists of entity data
    """
    layer_groups = defaultdict(list)
    entity_count = 0

    for entity in entities:
        entity_count += 1
        try:
            context = f"entity_{entity_count}"
            entity_type = safe_getattr(entity, 'dxftype', lambda: 'UNKNOWN')() if hasattr(entity, 'dxftype') else 'UNKNOWN'
            layer = safe_dxf_getattr(entity.dxf, 'layer', '0', error_tracker, f"{context}.{entity_type}")
            handle = safe_dxf_getattr(entity.dxf, 'handle', f'entity_{entity_count}', error_tracker, f"{context}.{entity_type}")

            # Extract geometry for intersection detection
            geometry = extract_entity_geometry(entity, error_tracker, f"{context}.{entity_type}")

            entity_data = {
                'type': entity_type,
                'handle': handle,
                'layer': layer,
                'geometry': geometry,
                'attributes': {}
            }

            # Extract attributes
            if hasattr(entity, 'dxf'):
                for attr_name in dir(entity.dxf):
                    if attr_name.startswith('_') or attr_name in ['__class__', '__dict__', '__module__']:
                        continue

                    try:
                        if hasattr(entity.dxf, attr_name):
                            attr_value = getattr(entity.dxf, attr_name)
                            entity_data['attributes'][attr_name] = serialize_dxf_value(attr_value)
                    except Exception as e:
                        error_tracker.add_error(f"{context}.{entity_type}.attribute_{attr_name}", e, entity_type, handle)

            # Special handling for text entities
            if entity_type == 'TEXT':
                text_content = safe_dxf_getattr(entity.dxf, 'text', '', error_tracker, f"{context}.TEXT")
                entity_data['text_content'] = text_content

            layer_groups[layer].append(entity_data)

        except Exception as e:
            entity_type = safe_getattr(entity, 'dxftype', lambda: 'UNKNOWN')() if hasattr(entity, 'dxftype') else 'UNKNOWN'
            handle = safe_dxf_getattr(entity.dxf, 'handle', f'entity_{entity_count}', error_tracker, f"entity_{entity_count}") if hasattr(entity, 'dxf') else f'entity_{entity_count}'
            error_tracker.add_error(f"entity_{entity_count}", e, entity_type, handle)
            continue

    print(f"✅ Grouped {entity_count} entities into {len(layer_groups)} layers")
    return layer_groups


def find_connected_components(entities_data: List[Dict[str, Any]], error_tracker: DXFErrorTracker, layer_name: str) -> List[List[Dict[str, Any]]]:
    """
    Find connected components within a layer using geometric intersection

    Uses BFS to find groups of entities that intersect each other directly or indirectly
    """
    if not entities_data:
        return []

    n = len(entities_data)
    visited = [False] * n
    components = []

    print(f"🔍 Finding connected components in layer '{layer_name}' with {n} entities...")

    for i in range(n):
        if visited[i] or not entities_data[i].get('geometry'):
            continue

        # Start BFS for new component
        component = []
        queue = deque([i])
        visited[i] = True

        while queue:
            current_idx = queue.popleft()
            current_entity = entities_data[current_idx]
            component.append(current_entity)

            # Check intersections with all unvisited entities
            for next_idx in range(n):
                if visited[next_idx] or not entities_data[next_idx].get('geometry'):
                    continue

                next_entity = entities_data[next_idx]

                # Skip if bounding boxes don't overlap (quick check)
                if not bbox_intersect(current_entity['geometry']['bbox'], next_entity['geometry']['bbox']):
                    continue

                # Detailed intersection check
                if entities_intersect(
                    current_entity['geometry'],
                    next_entity['geometry'],
                    current_entity['type'],
                    next_entity['type'],
                    error_tracker
                ):
                    visited[next_idx] = True
                    queue.append(next_idx)

        if component:
            components.append(component)

    print(f"✅ Found {len(components)} connected components in layer '{layer_name}'")
    return components


def create_segregated_json(layer_groups: Dict[str, List[Dict[str, Any]]], error_tracker: DXFErrorTracker,
                          source_file: str) -> Dict[str, Any]:
    """
    Create the final JSON structure with segregated objects

    Each object contains entities that are connected within the same layer
    """
    result = {
        'metadata': {
            'source_file': str(source_file),
            'processing_time': time.time() - error_tracker.start_time,
            'error_summary': error_tracker.get_processing_stats()
        },
        'layers': []
    }

    total_objects = 0
    total_entities = 0

    for layer_name, entities_data in layer_groups.items():
        layer_context = f"layer_{layer_name}"
        print(f"🏗️  Processing layer: '{layer_name}' with {len(entities_data)} entities")

        try:
            # Find connected components (objects) in this layer
            components = find_connected_components(entities_data, error_tracker, layer_name)

            layer_data = {
                'layer_name': layer_name,
                'entity_count': len(entities_data),
                'object_count': len(components),
                'objects': []
            }

            for obj_idx, component in enumerate(components, 1):
                object_id = f"{layer_name}_obj_{obj_idx}"

                # Calculate bounding box for the entire object
                all_points = []
                for entity in component:
                    geom = entity['geometry']
                    bbox = geom.get('bbox', {})
                    if bbox:
                        all_points.extend([
                            (bbox['min_x'], bbox['min_y']),
                            (bbox['max_x'], bbox['max_y'])
                        ])

                if all_points:
                    min_x = min(p[0] for p in all_points)
                    min_y = min(p[1] for p in all_points)
                    max_x = max(p[0] for p in all_points)
                    max_y = max(p[1] for p in all_points)
                    object_bbox = {
                        'min_x': min_x,
                        'min_y': min_y,
                        'max_x': max_x,
                        'max_y': max_y,
                        'width': max_x - min_x,
                        'height': max_y - min_y
                    }
                else:
                    object_bbox = {'min_x': 0, 'min_y': 0, 'max_x': 1, 'max_y': 1, 'width': 1, 'height': 1}

                object_data = {
                    'object_id': object_id,
                    'entity_count': len(component),
                    'entity_types': list(set(entity['type'] for entity in component)),
                    'bounding_box': object_bbox,
                    'entities': []
                }

                # Add all entities to the object
                for entity in component:
                    entity_copy = entity.copy()
                    # Remove geometry from final output to reduce size (keep bbox)
                    if 'geometry' in entity_copy:
                        entity_copy.pop('geometry')
                    object_data['entities'].append(entity_copy)

                layer_data['objects'].append(object_data)
                total_objects += 1
                total_entities += len(component)

            result['layers'].append(layer_data)

        except Exception as e:
            error_tracker.add_error(f"layer_processing.{layer_name}", e, "LAYER", "unknown")
            # Add layer with error information
            result['layers'].append({
                'layer_name': layer_name,
                'entity_count': len(entities_data),
                'object_count': 0,
                'objects': [],
                'error': str(e)
            })

    result['metadata']['summary'] = {
        'total_layers': len(layer_groups),
        'total_objects': total_objects,
        'total_entities': total_entities
    }

    return result


def segregate_dxf_objects(dxf_path: str, json_path: str = None) -> Dict[str, Any]:
    """
    Main function to segregate DXF entities into objects

    Args:
        dxf_path: Path to input DXF file
        json_path: Path to output JSON file (optional)

    Returns:
        Dictionary containing the segregated data
    """
    error_tracker = DXFErrorTracker()
    result = {
        'metadata': {
            'source_file': str(dxf_path),
            'success': False,
            'error_summary': {}
        },
        'layers': []
    }

    try:
        print("="*60)
        print("DXF ENTITY SEGREGATION")
        print("="*60)
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
        except Exception as e:
            error_tracker.add_error("modelspace_loading", e)
            msp = []

        # Group entities by layer
        layer_groups = group_entities_by_layer(msp, error_tracker)

        # Create segregated JSON structure
        result = create_segregated_json(layer_groups, error_tracker, dxf_path)
        result['metadata']['success'] = True

        # Save to JSON file if requested
        if json_path:
            try:
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, default=str)
                print(f"✅ Segregated data saved to: {json_path}")
            except Exception as e:
                error_tracker.add_error("json_save", e)

        # Print summary
        print("="*60)
        print("✨ SEGREGATION COMPLETED!")
        print("="*60)
        print(f"📊 SUMMARY:")
        print(f"   Layers processed: {len(result['layers'])}")
        print(f"   Total objects found: {result['metadata']['summary']['total_objects']}")
        print(f"   Total entities processed: {result['metadata']['summary']['total_entities']}")

        # Print error summary
        print(error_tracker.get_summary())

        return result

    except Exception as e:
        error_tracker.add_error("main_processing", e)
        print(error_tracker.get_summary())
        return {
            'error': f"Critical failure during DXF segregation: {str(e)}",
            'file_path': str(dxf_path),
            'traceback': traceback.format_exc(),
            'metadata': {
                'success': False,
                'error_summary': error_tracker.get_processing_stats()
            }
        }


def main():
    """Main function with command line argument parsing"""
    parser = argparse.ArgumentParser(description='Segregate DXF entities into objects based on layer and geometric intersection')
    parser.add_argument('input_dxf', nargs='?', default='input.dxf',
                      help='Path to input DXF file (default: input.dxf)')
    parser.add_argument('output_json', nargs='?', default='segregated_objects.json',
                      help='Path to output JSON file (default: segregated_objects.json)')
    parser.add_argument('--verbose', '-v', action='store_true',
                      help='Enable verbose output (currently always enabled)')

    args = parser.parse_args()

    input_dxf = args.input_dxf
    output_json = args.output_json

    # Validate input file exists
    if not Path(input_dxf).exists():
        print(f"❌ Error: DXF file not found at {input_dxf}")
        sys.exit(1)

    try:
        # Process the DXF file
        result = segregate_dxf_objects(input_dxf, output_json)

        # Check if processing was successful
        metadata = result.get('metadata', {})
        success = metadata.get('success', False)

        if not success:
            print(f"❌ Processing failed. Check error summary above.")
            sys.exit(1)

        print(f"\n💡 Output JSON file: {output_json}")
        print("This file contains entities grouped into objects based on layer and geometric intersection.")

    except KeyboardInterrupt:
        print("\n🛑 Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"💥 Unexpected error: {str(e)}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
