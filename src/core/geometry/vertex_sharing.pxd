# core/geometry/vertex_sharing.pxd
# Cython header file for vertex sharing detection algorithms
# Contains declarations for C-level functions and data structures
# Reference: https://cython.readthedocs.io/en/latest/src/userguide/language_basics.html
from libcpp.vector cimport vector
from libcpp.unordered_map cimport unordered_map
from libcpp.pair cimport pair
from libcpp cimport bool
from libc.math cimport fabs

# C-level data structures for geometric entities
ctypedef struct Point2D:
    double x
    double y

ctypedef struct LineSegment:
    Point2D start
    Point2D end
    size_t entity_id  # Reference to original DXF entity

ctypedef struct Circle:
    Point2D center
    double radius
    size_t entity_id

ctypedef union EntityGeometry:
    LineSegment line
    Circle circle
# Add other entity types as needed

ctypedef enum EntityType:
    LINE = 0
    CIRCLE = 1
    ARC = 2
    POLYLINE = 3
    SPLINE = 4

ctypedef struct Entity:
    EntityType type
    EntityGeometry geometry
    size_t id
    bint processed

# Spatial grid cell for vertex sharing detection
ctypedef struct GridCell:
    vector[size_t] entity_indices  # Indices into entities array
    bint processed

# Main algorithm interface
cdef class VertexSharingDetector:
    cdef:
        vector[Entity] entities
        double tolerance  # 1% tolerance (Decision #2)
        size_t grid_width
        size_t grid_height
        vector[GridCell] grid
        unordered_map[size_t, vector[size_t]] shared_vertex_groups
        bint use_parallel  # OpenMP parallelization flag

    cpdef object detect_shared_vertices(self, int mode=1) except *

    cdef void _mode1_spatial_hash(self) nogil
    cdef void _mode2_kd_tree(self) nogil
    cdef void _mode3_brute_force(self) nogil

    # Helper functions
    cdef double _calculate_max_dimension(self) nogil
    cdef void _add_entity_to_grid(self, size_t entity_idx, double x, double y) nogil
    cdef bint _entities_share_vertex(self, size_t idx1, size_t idx2) nogil
    cdef bint _points_are_close(self, double x1, double y1, double x2, double y2) nogil

# External C functions for performance-critical operations
cdef extern from "vertex_sharing_c.h":
    void spatial_hash_detection(
        Entity* entities,
        size_t num_entities,
        double tolerance,
        size_t* output_groups,
        size_t* group_sizes,
        size_t max_groups
    ) nogil
