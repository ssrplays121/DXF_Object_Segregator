"""Cython declaration file for intersection module."""

cdef extern from "geometry_types.h":
    struct Point:
        double x
        double y
        double z

    struct Intersection:
        Point p1
        Point p2
        int line1_id
        int line2_id
