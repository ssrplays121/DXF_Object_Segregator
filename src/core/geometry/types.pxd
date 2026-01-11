"""Shared type definitions for geometry modules."""

cdef struct Point:
    double x
    double y
    double z

cdef struct BoundingBox:
    double min_x
    double min_y
    double max_x
    double max_y
