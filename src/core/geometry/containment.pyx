"""Cython implementation of containment detection."""

import numpy as np
cimport numpy as np


def check_point_in_polygon(double x, double y, polygon_vertices: list) -> bool:
    """
    Check if a point is inside a polygon.

    Args:
        x: X coordinate of the point.
        y: Y coordinate of the point.
        polygon_vertices: List of (x, y) tuples representing polygon vertices.

    Returns:
        True if point is inside polygon, False otherwise.
    """
    cdef int num_vertices = len(polygon_vertices)
    cdef int inside = 0
    cdef int i, j
    cdef double xi, yi, xj, yj

    for i in range(num_vertices):
        j = (i + 1) % num_vertices
        xi, yi = polygon_vertices[i]
        xj, yj = polygon_vertices[j]

        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            inside = 1 - inside

    return inside == 1


def find_contained_objects(container_vertices: list, object_vertices: list) -> bool:
    """
    Check if an object is contained within another.

    Args:
        container_vertices: Vertices of the container polygon.
        object_vertices: Vertices of the object.

    Returns:
        True if object is contained, False otherwise.
    """
    for vertex in object_vertices:
        if not check_point_in_polygon(vertex[0], vertex[1], container_vertices):
            return False
    return True
