# utils/benchmarking.py
# Comprehensive benchmarking suite for algorithm performance analysis
# Implements integrated benchmarking with real-time metrics (Decision #17)
# Reference: https://pytest-benchmark.readthedocs.io/en/latest/
import time
import statistics
import json
import csv
import os
from typing import Dict, List, Any, Optional, Callable, Tuple
from functools import wraps
import logging
from datetime import datetime
from dataclasses import dataclass, field
from collections import defaultdict
from utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class BenchmarkResult:
    """Container for benchmark results"""
    name: str
    mode: int
    iterations: int
    times: List[float]
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def mean(self) -> float:
        """Mean execution time"""
        return statistics.mean(self.times)

    @property
    def median(self) -> float:
        """Median execution time"""
        return statistics.median(self.times)

    @property
    def std_dev(self) -> float:
        """Standard deviation of execution times"""
        return statistics.stdev(self.times) if len(self.times) > 1 else 0.0

    @property
    def min_time(self) -> float:
        """Minimum execution time"""
        return min(self.times)

    @property
    def max_time(self) -> float:
        """Maximum execution time"""
        return max(self.times)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'name': self.name,
            'mode': self.mode,
            'iterations': self.iterations,
            'mean': self.mean,
            'median': self.median,
            'std_dev': self.std_dev,
            'min': self.min_time,
            'max': self.max_time,
            'times': self.times,
            'metadata': self.metadata,
            'timestamp': datetime.now().isoformat()
        }


class BenchmarkSuite:
    """
    Comprehensive benchmarking suite
    Implements integrated benchmarking with statistical analysis (Decision #17)
    """
    def __init__(self, output_dir: str = "benchmarks"):
        self.output_dir = output_dir
        self.results = defaultdict(list)  # name -> list of BenchmarkResult
        self.enabled = True
        self.min_iterations = 5
        self.max_iterations = 100
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

    def benchmark_function(self, name: str, mode: int = 1,
                          iterations: int = 10) -> Callable:
        """
        Decorator for benchmarking functions
        Automatically times function execution and stores results
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                if not self.enabled:
                    return func(*args, **kwargs)

                # Warm up run (not counted)
                func(*args, **kwargs)

                # Actual benchmark runs
                times = []
                for _ in range(iterations):
                    start = time.perf_counter()
                    result = func(*args, **kwargs)
                    end = time.perf_counter()
                    times.append(end - start)

                # Create and store result
                result_obj = BenchmarkResult(
                    name=name,
                    mode=mode,
                    iterations=iterations,
                    times=times,
                    metadata={
                        'function': func.__name__,
                        'args_count': len(args),
                        'kwargs_count': len(kwargs),
                        'timestamp': datetime.now().isoformat()
                    }
                )
                self.results[name].append(result_obj)
                return result
            return wrapper
        return decorator

    def benchmark_algorithm(self, algorithm_func: Callable,
                           test_cases: List[Dict[str, Any]],
                           name: str, mode: int = 1) -> BenchmarkResult:
        """
        Benchmark algorithm with multiple test cases
        Returns comprehensive benchmark results
        """
        times = []
        metadata = {
            'test_case_count': len(test_cases),
            'algorithm_name': algorithm_func.__name__
        }
        for i, test_case in enumerate(test_cases):
            # Warm up
            algorithm_func(**test_case)
            # Benchmark
            start = time.perf_counter()
            result = algorithm_func(**test_case)
            end = time.perf_counter()
            times.append(end - start)
            # Store per-test-case metadata
            metadata[f'test_case_{i}'] = {
                'size': len(test_case.get('entities', [])),
                'result_size': len(result) if hasattr(result, '__len__') else 1
            }

        return BenchmarkResult(
            name=name,
            mode=mode,
            iterations=len(test_cases),
            times=times,
            metadata=metadata
        )

    def compare_modes(self, name: str, results: List[BenchmarkResult]) -> Dict[str, Any]:
        """
        Compare different modes of the same algorithm
        Returns statistical comparison
        """
        if len(results) < 2:
            raise ValueError("Need at least 2 results to compare")

        comparison = {
            'name': name,
            'mode_comparison': {},
            'best_mode': None,
            'speedup': {}
        }

        # Find best mode by mean time
        best_mode = min(results, key=lambda x: x.mean).mode
        best_mean = min(x.mean for x in results)

        for result in results:
            mode_key = f'mode_{result.mode}'
            comparison['mode_comparison'][mode_key] = {
                'mean': result.mean,
                'median': result.median,
                'std_dev': result.std_dev,
                'min': result.min_time,
                'max': result.max_time,
                'relative_speed': best_mean / result.mean if result.mean > 0 else float('inf')
            }
            if result.mode == best_mode:
                comparison['best_mode'] = result.mode

            # Calculate speedup vs best mode
            if result.mode != best_mode:
                speedup = result.mean / best_mean
                comparison['speedup'][f'mode_{result.mode}_vs_mode_{best_mode}'] = speedup

        return comparison

    def save_results(self, filename: str = None) -> str:
        """
        Save benchmark results to file
        Returns path to saved file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"benchmark_results_{timestamp}.json"

        filepath = os.path.join(self.output_dir, filename)

        # Convert results to serializable format
        serializable_results = {}
        for name, result_list in self.results.items():
            serializable_results[name] = [result.to_dict() for result in result_list]

        with open(filepath, 'w') as f:
            json.dump(serializable_results, f, indent=2)

        logger.info(f"Benchmark results saved to {filepath}")
        return filepath

    def export_csv(self, filename: str = None) -> str:
        """
        Export benchmark results to CSV for analysis
        Returns path to exported file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"benchmark_summary_{timestamp}.csv"

        filepath = os.path.join(self.output_dir, filename)

        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Name', 'Mode', 'Iterations', 'Mean (s)', 'Median (s)',
                             'Std Dev (s)', 'Min (s)', 'Max (s)', 'Timestamp'])
            for name, result_list in self.results.items():
                for result in result_list:
                    writer.writerow([
                        name,
                        result.mode,
                        result.iterations,
                        f"{result.mean:.6f}",
                        f"{result.median:.6f}",
                        f"{result.std_dev:.6f}",
                        f"{result.min_time:.6f}",
                        f"{result.max_time:.6f}",
                        result.metadata.get('timestamp', '')
                    ])

        logger.info(f"Benchmark CSV exported to {filepath}")
        return filepath

    def generate_report(self) -> str:
        """
        Generate human-readable benchmark report
        Returns report content as string
        """
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("BENCHMARK REPORT")
        report_lines.append("=" * 80)
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")

        for name, result_list in self.results.items():
            report_lines.append(f"\nAlgorithm: {name}")
            report_lines.append("-" * 40)

            # Group results by mode
            mode_results = defaultdict(list)
            for result in result_list:
                mode_results[result.mode].append(result)

            for mode, results in sorted(mode_results.items()):
                report_lines.append(f"\n  Mode {mode}:")
                for i, result in enumerate(results):
                    report_lines.append(f"    Run {i+1}:")
                    report_lines.append(f"      Mean: {result.mean:.6f}s")
                    report_lines.append(f"      Median: {result.median:.6f}s")
                    report_lines.append(f"      Std Dev: {result.std_dev:.6f}s")
                    report_lines.append(f"      Range: {result.min_time:.6f}s - {result.max_time:.6f}s")
                    report_lines.append(f"      Iterations: {result.iterations}")

            # Compare modes if multiple exist
            if len(mode_results) > 1:
                report_lines.append("\n  Mode Comparison:")
                best_mode = min(
                    (mode for mode in mode_results.keys()),
                    key=lambda m: statistics.mean(r.mean for r in mode_results[m])
                )
                for mode in sorted(mode_results.keys()):
                    results = mode_results[mode]
                    mean_time = statistics.mean(r.mean for r in results)
                    if mode == best_mode:
                        report_lines.append(f"    Mode {mode}: {mean_time:.6f}s (BEST)")
                    else:
                        best_mean = statistics.mean(r.mean for r in mode_results[best_mode])
                        speedup = best_mean / mean_time
                        report_lines.append(f"    Mode {mode}: {mean_time:.6f}s ({speedup:.2f}x slower)")

        report_lines.append("\n" + "=" * 80)
        return "\n".join(report_lines)

    def enable(self):
        """Enable benchmarking"""
        self.enabled = True

    def disable(self):
        """Disable benchmarking"""
        self.enabled = False

    def clear(self):
        """Clear all benchmark results"""
        self.results.clear()


# Global benchmark suite instance
_global_benchmark_suite = BenchmarkSuite()


def get_benchmark_suite() -> BenchmarkSuite:
    """Get global benchmark suite instance"""
    return _global_benchmark_suite


def benchmark_function(name: str = None, mode: int = 1, iterations: int = 10):
    """
    Global decorator for benchmarking functions
    Uses the global benchmark suite
    """
    def decorator(func):
        nonlocal name
        if name is None:
            name = func.__name__
        @wraps(func)
        def wrapper(*args, **kwargs):
            return _global_benchmark_suite.benchmark_function(
                name, mode, iterations
            )(func)(*args, **kwargs)
        return wrapper
    return decorator
