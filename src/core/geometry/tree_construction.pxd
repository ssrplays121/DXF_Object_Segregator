"""Cython declaration file for tree construction module."""

cdef extern from "tree_construction_c.h":
    struct TreeNode:
        int object_id
        TreeNode** children
        int num_children
