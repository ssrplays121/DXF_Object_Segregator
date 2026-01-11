"""Cython declaration file for containment module."""

cdef extern from "containment_c.h":
    int point_in_polygon(double x, double y, double* polygon_x,
                         double* polygon_y, int num_points)
