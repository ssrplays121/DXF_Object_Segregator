"""Cython declaration file for grouping module."""

cdef extern from "grouping_c.h":
    struct Group:
        int* object_ids
        int count
