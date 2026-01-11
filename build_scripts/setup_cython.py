"""Setup Cython modules."""

import os
import sys
from setuptools import setup
from setuptools.extension import Extension
from Cython.Build import cythonize
import numpy as np


def get_extensions():
    """Get list of Cython extensions to build."""
    extensions = [
        Extension(
            "dxf_object_segregator.core.geometry.vertex_sharing",
            ["src/core/geometry/vertex_sharing.pyx"],
            include_dirs=[np.get_include()],
            language="c"
        ),
        Extension(
            "dxf_object_segregator.core.geometry.intersection",
            ["src/core/geometry/intersection.pyx"],
            include_dirs=[np.get_include()],
            language="c"
        ),
        Extension(
            "dxf_object_segregator.core.geometry.containment",
            ["src/core/geometry/containment.pyx"],
            include_dirs=[np.get_include()],
            language="c"
        ),
        Extension(
            "dxf_object_segregator.core.geometry.grouping",
            ["src/core/geometry/grouping.pyx"],
            include_dirs=[np.get_include()],
            language="c"
        ),
        Extension(
            "dxf_object_segregator.core.geometry.tree_construction",
            ["src/core/geometry/tree_construction.pyx"],
            include_dirs=[np.get_include()],
            language="c"
        ),
    ]
    return cythonize(extensions, language_level="3")


if __name__ == "__main__":
    extensions = get_extensions()
    print(f"Building {len(extensions)} Cython extensions...")
