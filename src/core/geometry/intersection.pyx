"""Cython implementation of intersection detection."""

import numpy as np
cimport numpy as np
from typing import List, Tuple


def find_line_intersections(line_segments: List[Tuple], tolerance: float = 1e-6):
    """
    Find intersections between line segments.

    Args:
        line_segments: List of line segment endpoints [(x1, y1, x2, y2), ...].
        tolerance: Tolerance for intersection detection.

    Returns:
        List of intersection points.
    """
    cdef int num_lines = len(line_segments)
    intersections = []

    for i in range(num_lines):
        for j in range(i + 1, num_lines):
            intersection = _line_intersection(
                line_segments[i],
                line_segments[j],
                tolerance
            )
            if intersection is not None:
                intersections.append({
                    'line1': i,
                    'line2': j,
                    'point': intersection
                })

    return intersections


cdef tuple _line_intersection(tuple line1, tuple line2, double tolerance):
    """Find intersection point of two line segments."""
    cdef double x1, y1, x2, y2, x3, y3, x4, y4
    cdef double denom, t, u, ix, iy

    x1, y1, x2, y2 = line1
    x3, y3, x4, y4 = line2

    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)

    if abs(denom) < tolerance:
        return None

    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
    u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom

    if 0 <= t <= 1 and 0 <= u <= 1:
        ix = x1 + t * (x2 - x1)
        iy = y1 + t * (y2 - y1)
        return (ix, iy)

    return None
