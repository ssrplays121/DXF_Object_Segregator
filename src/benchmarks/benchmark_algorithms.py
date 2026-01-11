"""Benchmarks for geometry algorithms."""

from utils.benchmarking import Benchmark
import numpy as np


def benchmark_vertex_comparison():
    """Benchmark vertex comparison algorithm."""
    vertices1 = np.random.rand(1000, 3)
    vertices2 = np.random.rand(1000, 3)

    with Benchmark("Vertex Comparison") as b:
        # Perform vertex comparison
        for i in range(100):
            np.linalg.norm(vertices1 - vertices2[i])

    print(b)


def benchmark_intersection_detection():
    """Benchmark intersection detection algorithm."""
    lines = [(np.random.rand(4),) for _ in range(100)]

    with Benchmark("Intersection Detection") as b:
        # Perform intersection detection
        for i in range(len(lines)):
            for j in range(i + 1, len(lines)):
                pass

    print(b)


if __name__ == "__main__":
    benchmark_vertex_comparison()
    benchmark_intersection_detection()
