#!/usr/bin/env python3
"""
Benchmark comparing Python-only vs Rust-backed implementations of pathvein.

This script benchmarks the key operations that have Rust acceleration:
- Directory walking (walk_parallel)
- Pattern matching (PatternMatcher)
- End-to-end file scanning

Run this script twice to compare:
1. With Rust backend: Normal installation
2. Pure Python: Install from sdist in environment without Rust compiler
"""

import argparse
import json
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Any

# Import pathvein
try:
    from pathvein._backend import (
        get_backend_info,
        walk_parallel,
        PatternMatcher,
        match_pattern,
    )
    from pathvein._path_utils import pattern_match
except ImportError as e:
    print(f"Error importing pathvein: {e}")
    print("Make sure pathvein is installed in your environment")
    sys.exit(1)


class BenchmarkResults:
    """Store and format benchmark results."""

    def __init__(self):
        self.backend_info = get_backend_info()
        self.results: List[Dict[str, Any]] = []

    def add_result(
        self,
        operation: str,
        scenario: str,
        duration: float,
        items_processed: int = 0,
        **kwargs,
    ):
        """Add a benchmark result."""
        result = {
            "operation": operation,
            "scenario": scenario,
            "duration_seconds": duration,
            "items_processed": items_processed,
            **kwargs,
        }
        if items_processed > 0:
            result["items_per_second"] = items_processed / duration
        self.results.append(result)

    def print_summary(self):
        """Print formatted benchmark results."""
        print("\n" + "=" * 80)
        print("BENCHMARK RESULTS")
        print("=" * 80)
        print(f"\nBackend: {self.backend_info['backend']}")
        print(f"Has Rust: {self.backend_info['has_rust']}")
        print(f"Python Version: {sys.version.split()[0]}")
        print("=" * 80)

        # Group by operation
        operations = {}
        for result in self.results:
            op = result["operation"]
            if op not in operations:
                operations[op] = []
            operations[op].append(result)

        # Print each operation group
        for operation, results in operations.items():
            print(f"\n{operation}")
            print("-" * 80)
            for r in results:
                scenario = r["scenario"]
                duration = r["duration_seconds"]
                print(f"  {scenario:40s} {duration:8.4f}s", end="")

                if r.get("items_processed", 0) > 0:
                    rate = r["items_per_second"]
                    print(f"  ({rate:10.0f} items/s)", end="")

                # Print any extra info
                extra = {
                    k: v
                    for k, v in r.items()
                    if k
                    not in [
                        "operation",
                        "scenario",
                        "duration_seconds",
                        "items_processed",
                        "items_per_second",
                    ]
                }
                if extra:
                    print(f"  {extra}", end="")
                print()

        print("\n" + "=" * 80)

    def save_json(self, filepath: str):
        """Save results as JSON for comparison."""
        data = {
            "backend_info": self.backend_info,
            "python_version": sys.version,
            "results": self.results,
        }
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        print(f"\nResults saved to: {filepath}")


def create_test_tree(root: Path, depth: int, files_per_dir: int, dirs_per_level: int):
    """Create a test directory tree."""

    def create_level(parent: Path, current_depth: int):
        if current_depth > depth:
            return

        # Create files
        for i in range(files_per_dir):
            ext = ["txt", "py", "rs", "md", "json"][i % 5]
            (parent / f"file_{i}.{ext}").touch()

        # Create subdirectories
        if current_depth < depth:
            for i in range(dirs_per_level):
                subdir = parent / f"dir_{current_depth}_{i}"
                subdir.mkdir()
                create_level(subdir, current_depth + 1)

    root.mkdir(parents=True, exist_ok=True)
    create_level(root, 1)


def benchmark_directory_walking(results: BenchmarkResults, test_root: Path):
    """Benchmark directory walking operations."""
    print("\n[1/4] Benchmarking directory walking...")

    # Small tree
    small_tree = test_root / "small"
    create_test_tree(small_tree, depth=2, files_per_dir=10, dirs_per_level=3)

    start = time.time()
    entries = list(walk_parallel(str(small_tree)))
    duration = time.time() - start
    total_items = sum(len(files) + len(dirs) for _, dirs, files in entries)
    results.add_result(
        "Directory Walking", "Small tree (2 levels, ~100 files)", duration, total_items
    )

    # Medium tree
    medium_tree = test_root / "medium"
    create_test_tree(medium_tree, depth=3, files_per_dir=20, dirs_per_level=4)

    start = time.time()
    entries = list(walk_parallel(str(medium_tree)))
    duration = time.time() - start
    total_items = sum(len(files) + len(dirs) for _, dirs, files in entries)
    results.add_result(
        "Directory Walking",
        "Medium tree (3 levels, ~1000 files)",
        duration,
        total_items,
    )

    # Large tree
    large_tree = test_root / "large"
    create_test_tree(large_tree, depth=4, files_per_dir=25, dirs_per_level=5)

    start = time.time()
    entries = list(walk_parallel(str(large_tree)))
    duration = time.time() - start
    total_items = sum(len(files) + len(dirs) for _, dirs, files in entries)
    results.add_result(
        "Directory Walking",
        "Large tree (4 levels, ~10000 files)",
        duration,
        total_items,
    )


def benchmark_pattern_matching(results: BenchmarkResults, test_root: Path):
    """Benchmark pattern matching operations."""
    print("[2/4] Benchmarking pattern matching...")

    # Create test files
    test_dir = test_root / "patterns"
    test_dir.mkdir(exist_ok=True)

    # Create diverse filenames
    filenames = []
    for i in range(1000):
        ext = ["txt", "py", "rs", "md", "json", "yaml", "toml", "sh"][i % 8]
        prefix = ["test", "main", "lib", "util", "helper", "config"][i % 6]
        filenames.append(f"{prefix}_{i}.{ext}")

    for filename in filenames:
        (test_dir / filename).touch()

    # Single pattern matching - simple
    pattern = "*.py"
    start = time.time()
    matches = [f for f in filenames if pattern_match(f, pattern)]
    duration = time.time() - start
    results.add_result(
        "Pattern Matching",
        "Single pattern, simple (*.py)",
        duration,
        len(matches),
        total_files=len(filenames),
    )

    # Single pattern matching - complex (using PatternMatcher)
    pattern = "test_*.py"
    start = time.time()
    matches = [f for f in filenames if match_pattern(f, pattern)]
    duration = time.time() - start
    results.add_result(
        "Pattern Matching",
        "Single pattern, complex (test_*.py)",
        duration,
        len(matches),
        total_files=len(filenames),
    )

    # Multiple patterns - few
    patterns = ["*.py", "*.rs", "*.md"]
    matcher = PatternMatcher(patterns)
    start = time.time()
    matches = [f for f in filenames if matcher.matches(f)]
    duration = time.time() - start
    results.add_result(
        "Pattern Matching",
        "Multiple patterns, 3 patterns",
        duration,
        len(matches),
        total_files=len(filenames),
    )

    # Multiple patterns - many
    patterns = [
        f"{prefix}_*.{ext}"
        for prefix in ["test", "main", "lib"]
        for ext in ["py", "rs", "md", "txt"]
    ]
    matcher = PatternMatcher(patterns)
    start = time.time()
    matches = [f for f in filenames if matcher.matches(f)]
    duration = time.time() - start
    results.add_result(
        "Pattern Matching",
        f"Multiple patterns, {len(patterns)} patterns",
        duration,
        len(matches),
        total_files=len(filenames),
    )

    # Repeated matching (tests cache effectiveness)
    pattern = "*.py"
    start = time.time()
    for _ in range(100):
        matches = [f for f in filenames if pattern_match(f, pattern)]
    duration = time.time() - start
    results.add_result(
        "Pattern Matching",
        "Repeated matching (100x, cache test)",
        duration,
        len(matches) * 100,
    )


def benchmark_scan_operations(results: BenchmarkResults, test_root: Path):
    """Benchmark end-to-end scan operations (walk + filter)."""
    print("[3/4] Benchmarking end-to-end scan...")

    # Small scan - walk + filter by patterns
    small_tree = test_root / "small"
    patterns = ["*.py", "*.txt"]
    matcher = PatternMatcher(patterns)

    start = time.time()
    files = []
    for dirpath, dirnames, filenames in walk_parallel(str(small_tree)):
        files.extend([f for f in filenames if matcher.matches(f)])
    duration = time.time() - start
    results.add_result(
        "End-to-End Scan", "Small tree, 2 patterns", duration, len(files)
    )

    # Medium scan
    medium_tree = test_root / "medium"
    patterns = ["*.py", "*.rs", "*.md"]
    matcher = PatternMatcher(patterns)

    start = time.time()
    files = []
    for dirpath, dirnames, filenames in walk_parallel(str(medium_tree)):
        files.extend([f for f in filenames if matcher.matches(f)])
    duration = time.time() - start
    results.add_result(
        "End-to-End Scan", "Medium tree, 3 patterns", duration, len(files)
    )

    # Large scan
    large_tree = test_root / "large"
    patterns = ["*.py", "*.txt", "*.rs", "*.md", "*.json"]
    matcher = PatternMatcher(patterns)

    start = time.time()
    files = []
    for dirpath, dirnames, filenames in walk_parallel(str(large_tree)):
        files.extend([f for f in filenames if matcher.matches(f)])
    duration = time.time() - start
    results.add_result(
        "End-to-End Scan", "Large tree, 5 patterns", duration, len(files)
    )

    # Complex pattern scan
    patterns = ["test_*.py", "lib_*.rs", "*.md"]
    matcher = PatternMatcher(patterns)

    start = time.time()
    files = []
    for dirpath, dirnames, filenames in walk_parallel(str(large_tree)):
        files.extend([f for f in filenames if matcher.matches(f)])
    duration = time.time() - start
    results.add_result(
        "End-to-End Scan", "Large tree, complex patterns", duration, len(files)
    )


def benchmark_real_world(results: BenchmarkResults):
    """Benchmark on the actual pathvein repository."""
    print("[4/4] Benchmarking on real repository...")

    repo_root = Path(__file__).parent.parent

    # Scan Python files
    matcher = PatternMatcher(["*.py"])
    start = time.time()
    files = []
    for dirpath, dirnames, filenames in walk_parallel(str(repo_root)):
        files.extend([f for f in filenames if matcher.matches(f)])
    duration = time.time() - start
    results.add_result(
        "Real Repository", "Scan Python files (*.py)", duration, len(files)
    )

    # Scan Rust files
    matcher = PatternMatcher(["*.rs"])
    start = time.time()
    files = []
    for dirpath, dirnames, filenames in walk_parallel(str(repo_root)):
        files.extend([f for f in filenames if matcher.matches(f)])
    duration = time.time() - start
    results.add_result(
        "Real Repository", "Scan Rust files (*.rs)", duration, len(files)
    )

    # Scan all source files
    matcher = PatternMatcher(["*.py", "*.rs", "*.toml", "*.md"])
    start = time.time()
    files = []
    for dirpath, dirnames, filenames in walk_parallel(str(repo_root)):
        files.extend([f for f in filenames if matcher.matches(f)])
    duration = time.time() - start
    results.add_result("Real Repository", "Scan all source files", duration, len(files))

    # Scan Python excluding tests (simple filter)
    matcher = PatternMatcher(["*.py"])
    test_matcher = PatternMatcher(["test_*.py"])
    start = time.time()
    files = []
    for dirpath, dirnames, filenames in walk_parallel(str(repo_root)):
        # Exclude tests directory
        if "tests" in dirpath or ".venv" in dirpath:
            continue
        files.extend(
            [f for f in filenames if matcher.matches(f) and not test_matcher.matches(f)]
        )
    duration = time.time() - start
    results.add_result(
        "Real Repository", "Scan Python excluding tests", duration, len(files)
    )


def compare_results(python_json: str, rust_json: str):
    """Compare two benchmark JSON files and show speedups."""
    with open(python_json) as f:
        python_data = json.load(f)
    with open(rust_json) as f:
        rust_data = json.load(f)

    print("\n" + "=" * 80)
    print("PERFORMANCE COMPARISON: Rust vs Python")
    print("=" * 80)
    print(f"\nPython Backend: {python_data['backend_info']['backend']}")
    print(f"Rust Backend: {rust_data['backend_info']['backend']}")
    print("=" * 80)

    # Create lookup for rust results
    rust_lookup = {}
    for r in rust_data["results"]:
        key = (r["operation"], r["scenario"])
        rust_lookup[key] = r

    # Compare each python result
    for py_result in python_data["results"]:
        key = (py_result["operation"], py_result["scenario"])
        rust_result = rust_lookup.get(key)

        if not rust_result:
            continue

        py_time = py_result["duration_seconds"]
        rust_time = rust_result["duration_seconds"]
        speedup = py_time / rust_time

        print(f"\n{py_result['operation']} - {py_result['scenario']}")
        print(f"  Python: {py_time:.4f}s")
        print(f"  Rust:   {rust_time:.4f}s")
        print(f"  Speedup: {speedup:.2f}x {'faster' if speedup > 1 else 'slower'}")

    print("\n" + "=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark pathvein Python vs Rust implementations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run benchmarks with current backend
  python benchmark_backends.py

  # Save results to specific file
  python benchmark_backends.py -o rust_results.json

  # Compare two result files
  python benchmark_backends.py --compare python_results.json rust_results.json

Setup for comparison:
  1. Run with Rust backend (normal install):
     python benchmark_backends.py -o rust_results.json

  2. Create venv without Rust and install from sdist:
     python -m venv venv_python
     source venv_python/bin/activate
     pip install --no-binary pathvein pathvein  # Force sdist build

  3. Run with Python backend:
     python benchmark_backends.py -o python_results.json

  4. Compare results:
     python benchmark_backends.py --compare python_results.json rust_results.json
        """,
    )
    parser.add_argument("-o", "--output", help="Output JSON file for results")
    parser.add_argument(
        "--compare",
        nargs=2,
        metavar=("FILE1", "FILE2"),
        help="Compare two benchmark result JSON files",
    )
    parser.add_argument(
        "--skip-real", action="store_true", help="Skip real repository benchmarks"
    )

    args = parser.parse_args()

    # Compare mode
    if args.compare:
        compare_results(args.compare[0], args.compare[1])
        return

    # Run benchmarks
    print("=" * 80)
    print("PATHVEIN BACKEND BENCHMARK")
    print("=" * 80)

    backend_info = get_backend_info()
    print(f"\nBackend: {backend_info['backend']}")
    print(f"Has Rust: {backend_info['has_rust']}")

    results = BenchmarkResults()

    # Create temp directory for test data
    with tempfile.TemporaryDirectory() as tmpdir:
        test_root = Path(tmpdir)

        print(f"\nTest data directory: {test_root}")
        print("=" * 80)

        # Run benchmarks
        benchmark_directory_walking(results, test_root)
        benchmark_pattern_matching(results, test_root)
        benchmark_scan_operations(results, test_root)

    if not args.skip_real:
        benchmark_real_world(results)

    # Print results
    results.print_summary()

    # Save JSON if requested
    if args.output:
        results.save_json(args.output)
    else:
        # Auto-generate filename based on backend
        backend_name = "rust" if backend_info["has_rust"] else "python"
        filename = f"benchmark_results_{backend_name}.json"
        results.save_json(filename)


if __name__ == "__main__":
    main()
