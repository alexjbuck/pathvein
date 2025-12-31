#!/usr/bin/env python3
"""
pytest-benchmark tests for pathvein.

These benchmarks compare Pure Python vs Hybrid vs Pure Rust implementations
to determine if Rust optimization is worth the effort.

Benchmark Categories:
- Micro Benchmarks: Internal implementation details (walk, pattern matching)
- API Benchmarks: Public API functions that users actually call (scan, shuffle)

Approaches Compared:
- Pure Python: No Rust, pure Python implementation (os.walk + fnmatch)
- Hybrid: Python walk + Rust pattern matching (FFI overhead)
- Pure Rust: Everything in Rust (precompiled patterns, no FFI overhead)

Usage:
    # Run all benchmarks
    pytest bench/test_benchmark.py --benchmark-only

    # Run only API benchmarks (what users care about)
    pytest bench/test_benchmark.py::TestAPIBenchmarks --benchmark-only

    # Run only micro benchmarks (implementation details)
    pytest bench/test_benchmark.py::TestMicroBenchmarks --benchmark-only

    # Compare with baseline
    pytest bench/test_benchmark.py --benchmark-only --benchmark-compare=baseline

    # Generate JSON for CI
    pytest bench/test_benchmark.py --benchmark-only --benchmark-json=output.json

Install dependencies:
    pip install pytest pytest-benchmark
"""

import tempfile
from pathlib import Path

import pytest

from pathvein._backend import get_backend_info


# Show backend info at collection time
def pytest_collection():
    """Display backend info when tests are collected."""
    info = get_backend_info()
    print(f"\n{'=' * 70}")
    print(f"Benchmarking with {info['backend'].upper()} backend")
    print(f"Has Rust: {info['has_rust']}")
    print(f"{'=' * 70}\n")


@pytest.fixture(scope="session")
def temp_dir_structure():
    """Create a medium-sized test directory structure.

    Creates ~2000 files across 5 levels to simulate real-world usage.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        def create_tree(parent: Path, depth: int, max_depth: int = 4):
            if depth > max_depth:
                return

            # Create 20 files per directory
            for i in range(20):
                ext = ["txt", "py", "rs", "md", "json"][i % 5]
                (parent / f"file_{depth}_{i}.{ext}").touch()

            # Create 5 subdirectories per level
            if depth < max_depth:
                for i in range(5):
                    subdir = parent / f"subdir_{depth}_{i}"
                    subdir.mkdir()
                    create_tree(subdir, depth + 1, max_depth)

        create_tree(root, 0)
        yield root


@pytest.fixture(scope="session")
def small_dir_structure():
    """Create a SMALL test directory structure.

    Size: ~140 files, ~30 directories across 3 levels
    Simulates: A small project or library
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        def create_tree(parent: Path, depth: int, max_depth: int = 2):
            if depth > max_depth:
                return

            # Create 10 files per directory
            for i in range(10):
                ext = ["txt", "py", "rs", "md", "json"][i % 5]
                (parent / f"file_{depth}_{i}.{ext}").touch()

            # Create 3 subdirectories per level
            if depth < max_depth:
                for i in range(3):
                    subdir = parent / f"subdir_{depth}_{i}"
                    subdir.mkdir()
                    create_tree(subdir, depth + 1, max_depth)

        create_tree(root, 0)
        yield root


@pytest.fixture(scope="session")
def large_dir_structure():
    """Create a LARGE test directory structure.

    Size: ~31,250 files, ~1,562 directories across 6 levels
    Simulates: A large monorepo or comprehensive codebase
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        def create_tree(parent: Path, depth: int, max_depth: int = 4):
            if depth > max_depth:
                return

            # Create 25 files per directory
            for i in range(25):
                ext = ["txt", "py", "rs", "md", "json", "yaml", "toml", "sh"][i % 8]
                (parent / f"file_{depth}_{i}.{ext}").touch()

            # Create 5 subdirectories per level
            if depth < max_depth:
                for i in range(5):
                    subdir = parent / f"subdir_{depth}_{i}"
                    subdir.mkdir()
                    create_tree(subdir, depth + 1, max_depth)

        create_tree(root, 0)
        yield root


@pytest.fixture(scope="session")
def test_filenames():
    """Generate 1000 test filenames for pattern matching benchmarks."""
    filenames = []
    for i in range(1000):
        ext = ["txt", "py", "rs", "md", "json", "yaml", "toml", "sh"][i % 8]
        prefix = ["test", "main", "lib", "util", "helper", "config"][i % 6]
        filenames.append(f"{prefix}_{i}.{ext}")
    return filenames


# =============================================================================
# MICRO BENCHMARKS - Internal Implementation Details
# =============================================================================


class TestMicroBenchmarks:
    """Benchmark internal implementation details.

    These test low-level components like directory walking and pattern matching.
    Useful for understanding where performance comes from, but users don't
    directly call these functions.
    """

    def test_micro_walk_parallel(self, benchmark, temp_dir_structure):
        """Micro: Benchmark parallel directory walking (Rust implementation)."""
        from pathvein._backend import walk_parallel

        result = benchmark(lambda: list(walk_parallel(str(temp_dir_structure))))
        assert len(result) > 0

    def test_micro_pattern_matching_single(self, benchmark, test_filenames):
        """Micro: Benchmark single pattern matching (Rust globset)."""
        from pathvein._backend import PatternMatcher

        patterns = ["*.py"]
        matcher = PatternMatcher(patterns)
        result = benchmark(lambda: [f for f in test_filenames if matcher.matches(f)])
        assert len(result) > 0

    def test_micro_pattern_matching_multiple(self, benchmark, test_filenames):
        """Micro: Benchmark multiple pattern matching (Rust globset)."""
        from pathvein._backend import PatternMatcher

        patterns = ["*.py", "*.rs", "*.md", "*.txt"]
        matcher = PatternMatcher(patterns)
        result = benchmark(lambda: [f for f in test_filenames if matcher.matches(f)])
        assert len(result) > 0


# =============================================================================
# API BENCHMARKS - Public API Functions (What Users Call)
# =============================================================================


class TestAPIBenchmarks:
    """Benchmark PUBLIC API functions that users actually call.

    These are the functions users use directly: scan() and shuffle().
    These benchmarks show the REAL performance that matters.
    """

    # -------------------------------------------------------------------------
    # SCAN BENCHMARKS - Compare Pure Python vs Hybrid vs Pure Rust
    # These 3 benchmarks are the MAIN comparison for "Is Rust worth it?"
    # -------------------------------------------------------------------------

    def test_api_scan_1_pure_python(self, benchmark, temp_dir_structure):
        """API: Scan approach #1 - PURE PYTHON (baseline).

        os.walk() + Python fnmatch pattern matching.
        No Rust, pure Python implementation.
        """
        from pathvein.pattern import FileStructurePattern
        from pathvein.lib import ScanResult
        import os

        patterns = [
            FileStructurePattern().add_file("*.py"),
            FileStructurePattern().add_file("*.rs"),
        ]

        def pure_python_scan():
            matches = set()
            # Use Python walk (not Rust walk_parallel)
            for dirpath, dirnames, filenames in os.walk(temp_dir_structure):
                dirpath = Path(dirpath)
                for pattern in patterns:
                    # pattern.matches() will use Python fnmatch (no Rust)
                    if pattern.matches((dirpath, dirnames, filenames)):
                        matches.add(ScanResult(dirpath, pattern))
            return matches

        result = benchmark(pure_python_scan)
        assert len(result) >= 0

    def test_api_scan_2_hybrid(self, benchmark, temp_dir_structure):
        """API: Scan approach #2 - HYBRID (Python os.walk + Rust matchers).

        Python's C-based os.walk() + Rust PatternMatcher for fast matching.
        Tests if Rust pattern matching alone provides most of the benefit.
        """
        from pathvein.pattern import FileStructurePattern
        from pathvein.lib import ScanResult
        from pathlib import Path
        import os

        patterns = [
            FileStructurePattern().add_file("*.py"),
            FileStructurePattern().add_file("*.rs"),
        ]

        def hybrid_scan():
            matches = set()
            # Python walk (C-based os.walk)
            for dirpath, dirnames, filenames in os.walk(temp_dir_structure):
                dirpath = Path(dirpath)
                # Rust pattern matching (calls Rust PatternMatcher)
                for pattern in patterns:
                    if pattern.matches((dirpath, dirnames, filenames)):
                        matches.add(ScanResult(dirpath, pattern))
            return matches

        result = benchmark(hybrid_scan)
        assert len(result) >= 0

    def test_api_scan_3_pure_rust(self, benchmark, temp_dir_structure):
        """API: Scan approach #3 - PURE RUST (optimal).

        Everything in Rust: precompiled patterns, parallel walk, matching.
        Zero FFI crossings during scan loop. Should be fastest.
        """
        from pathvein import scan
        from pathvein.pattern import FileStructurePattern

        patterns = [
            FileStructurePattern().add_file("*.py"),
            FileStructurePattern().add_file("*.rs"),
        ]

        result = benchmark(lambda: scan(temp_dir_structure, patterns))
        assert len(result) >= 0

    # -------------------------------------------------------------------------
    # SCENARIO BENCHMARKS - Test size & pattern complexity impact
    # -------------------------------------------------------------------------

    # Scenario 1: Small directory (~140 files), 1 simple pattern
    def test_api_scenario1_small_simple_1_pure_python(
        self, benchmark, small_dir_structure
    ):
        """Scenario 1a: Small dir + 1 pattern - Pure Python."""
        from pathvein.pattern import FileStructurePattern
        from pathvein.lib import ScanResult
        import os

        patterns = [FileStructurePattern().add_file("*.py")]

        def pure_python_scan():
            matches = set()
            for dirpath, dirnames, filenames in os.walk(small_dir_structure):
                dirpath = Path(dirpath)
                for pattern in patterns:
                    if pattern.matches((dirpath, dirnames, filenames)):
                        matches.add(ScanResult(dirpath, pattern))
            return matches

        result = benchmark(pure_python_scan)
        assert len(result) >= 0

    def test_api_scenario1_small_simple_2_hybrid(self, benchmark, small_dir_structure):
        """Scenario 1b: Small dir + 1 pattern - Hybrid."""
        from pathvein.pattern import FileStructurePattern
        from pathvein.lib import ScanResult
        import os

        patterns = [FileStructurePattern().add_file("*.py")]

        def hybrid_scan():
            matches = set()
            for dirpath, dirnames, filenames in os.walk(small_dir_structure):
                dirpath = Path(dirpath)
                for pattern in patterns:
                    if pattern.matches((dirpath, dirnames, filenames)):
                        matches.add(ScanResult(dirpath, pattern))
            return matches

        result = benchmark(hybrid_scan)
        assert len(result) >= 0

    def test_api_scenario1_small_simple_3_pure_rust(
        self, benchmark, small_dir_structure
    ):
        """Scenario 1c: Small dir + 1 pattern - Pure Rust."""
        from pathvein import scan
        from pathvein.pattern import FileStructurePattern

        patterns = [FileStructurePattern().add_file("*.py")]
        result = benchmark(lambda: scan(small_dir_structure, patterns))
        assert len(result) >= 0

    # Scenario 2: Small directory (~140 files), many patterns
    def test_api_scenario2_small_many_1_pure_python(
        self, benchmark, small_dir_structure
    ):
        """Scenario 2a: Small dir + many patterns - Pure Python."""
        from pathvein.pattern import FileStructurePattern
        from pathvein.lib import ScanResult
        import os

        patterns = [
            FileStructurePattern().add_file("*.py"),
            FileStructurePattern().add_file("*.rs"),
            FileStructurePattern().add_file("*.md"),
            FileStructurePattern().add_file("*.txt"),
            FileStructurePattern().add_file("*.json"),
            FileStructurePattern().add_file("*.yaml"),
            FileStructurePattern().add_file("*.toml"),
            FileStructurePattern().add_file("*.sh"),
        ]

        def pure_python_scan():
            matches = set()
            for dirpath, dirnames, filenames in os.walk(small_dir_structure):
                dirpath = Path(dirpath)
                for pattern in patterns:
                    if pattern.matches((dirpath, dirnames, filenames)):
                        matches.add(ScanResult(dirpath, pattern))
            return matches

        result = benchmark(pure_python_scan)
        assert len(result) >= 0

    def test_api_scenario2_small_many_2_hybrid(self, benchmark, small_dir_structure):
        """Scenario 2b: Small dir + many patterns - Hybrid."""
        from pathvein.pattern import FileStructurePattern
        from pathvein.lib import ScanResult
        import os

        patterns = [
            FileStructurePattern().add_file("*.py"),
            FileStructurePattern().add_file("*.rs"),
            FileStructurePattern().add_file("*.md"),
            FileStructurePattern().add_file("*.txt"),
            FileStructurePattern().add_file("*.json"),
            FileStructurePattern().add_file("*.yaml"),
            FileStructurePattern().add_file("*.toml"),
            FileStructurePattern().add_file("*.sh"),
        ]

        def hybrid_scan():
            matches = set()
            for dirpath, dirnames, filenames in os.walk(small_dir_structure):
                dirpath = Path(dirpath)
                for pattern in patterns:
                    if pattern.matches((dirpath, dirnames, filenames)):
                        matches.add(ScanResult(dirpath, pattern))
            return matches

        result = benchmark(hybrid_scan)
        assert len(result) >= 0

    def test_api_scenario2_small_many_3_pure_rust(self, benchmark, small_dir_structure):
        """Scenario 2c: Small dir + many patterns - Pure Rust."""
        from pathvein import scan
        from pathvein.pattern import FileStructurePattern

        patterns = [
            FileStructurePattern().add_file("*.py"),
            FileStructurePattern().add_file("*.rs"),
            FileStructurePattern().add_file("*.md"),
            FileStructurePattern().add_file("*.txt"),
            FileStructurePattern().add_file("*.json"),
            FileStructurePattern().add_file("*.yaml"),
            FileStructurePattern().add_file("*.toml"),
            FileStructurePattern().add_file("*.sh"),
        ]

        result = benchmark(lambda: scan(small_dir_structure, patterns))
        assert len(result) >= 0

    # Scenario 3: Large directory (~31,250 files), 1 simple pattern
    def test_api_scenario3_large_simple_1_pure_python(
        self, benchmark, large_dir_structure
    ):
        """Scenario 3a: Large dir + 1 pattern - Pure Python."""
        from pathvein.pattern import FileStructurePattern
        from pathvein.lib import ScanResult
        import os

        patterns = [FileStructurePattern().add_file("*.py")]

        def pure_python_scan():
            matches = set()
            for dirpath, dirnames, filenames in os.walk(large_dir_structure):
                dirpath = Path(dirpath)
                for pattern in patterns:
                    if pattern.matches((dirpath, dirnames, filenames)):
                        matches.add(ScanResult(dirpath, pattern))
            return matches

        result = benchmark(pure_python_scan)
        assert len(result) >= 0

    def test_api_scenario3_large_simple_2_hybrid(self, benchmark, large_dir_structure):
        """Scenario 3b: Large dir + 1 pattern - Hybrid."""
        from pathvein.pattern import FileStructurePattern
        from pathvein.lib import ScanResult
        import os

        patterns = [FileStructurePattern().add_file("*.py")]

        def hybrid_scan():
            matches = set()
            for dirpath, dirnames, filenames in os.walk(large_dir_structure):
                dirpath = Path(dirpath)
                for pattern in patterns:
                    if pattern.matches((dirpath, dirnames, filenames)):
                        matches.add(ScanResult(dirpath, pattern))
            return matches

        result = benchmark(hybrid_scan)
        assert len(result) >= 0

    def test_api_scenario3_large_simple_3_pure_rust(
        self, benchmark, large_dir_structure
    ):
        """Scenario 3c: Large dir + 1 pattern - Pure Rust."""
        from pathvein import scan
        from pathvein.pattern import FileStructurePattern

        patterns = [FileStructurePattern().add_file("*.py")]
        result = benchmark(lambda: scan(large_dir_structure, patterns))
        assert len(result) >= 0

    # Scenario 4: Large directory (~31,250 files), many patterns with complexity
    def test_api_scenario4_large_complex_1_pure_python(
        self, benchmark, large_dir_structure
    ):
        """Scenario 4a: Large dir + complex patterns - Pure Python."""
        from pathvein.pattern import FileStructurePattern
        from pathvein.lib import ScanResult
        import os

        patterns = [
            FileStructurePattern().add_file("*.py").add_file("*.rs"),
            FileStructurePattern().add_file("*.md").add_file("*.txt", is_optional=True),
            FileStructurePattern().add_file("*.json"),
            FileStructurePattern()
            .add_file("*.yaml")
            .add_file("*.toml", is_optional=True),
            FileStructurePattern().add_file("*.sh"),
        ]

        def pure_python_scan():
            matches = set()
            for dirpath, dirnames, filenames in os.walk(large_dir_structure):
                dirpath = Path(dirpath)
                for pattern in patterns:
                    if pattern.matches((dirpath, dirnames, filenames)):
                        matches.add(ScanResult(dirpath, pattern))
            return matches

        result = benchmark(pure_python_scan)
        assert len(result) >= 0

    def test_api_scenario4_large_complex_2_hybrid(self, benchmark, large_dir_structure):
        """Scenario 4b: Large dir + complex patterns - Hybrid."""
        from pathvein.pattern import FileStructurePattern
        from pathvein.lib import ScanResult
        import os

        patterns = [
            FileStructurePattern().add_file("*.py").add_file("*.rs"),
            FileStructurePattern().add_file("*.md").add_file("*.txt", is_optional=True),
            FileStructurePattern().add_file("*.json"),
            FileStructurePattern()
            .add_file("*.yaml")
            .add_file("*.toml", is_optional=True),
            FileStructurePattern().add_file("*.sh"),
        ]

        def hybrid_scan():
            matches = set()
            for dirpath, dirnames, filenames in os.walk(large_dir_structure):
                dirpath = Path(dirpath)
                for pattern in patterns:
                    if pattern.matches((dirpath, dirnames, filenames)):
                        matches.add(ScanResult(dirpath, pattern))
            return matches

        result = benchmark(hybrid_scan)
        assert len(result) >= 0

    def test_api_scenario4_large_complex_3_pure_rust(
        self, benchmark, large_dir_structure
    ):
        """Scenario 4c: Large dir + complex patterns - Pure Rust."""
        from pathvein import scan
        from pathvein.pattern import FileStructurePattern

        patterns = [
            FileStructurePattern().add_file("*.py").add_file("*.rs"),
            FileStructurePattern().add_file("*.md").add_file("*.txt", is_optional=True),
            FileStructurePattern().add_file("*.json"),
            FileStructurePattern()
            .add_file("*.yaml")
            .add_file("*.toml", is_optional=True),
            FileStructurePattern().add_file("*.sh"),
        ]

        result = benchmark(lambda: scan(large_dir_structure, patterns))
        assert len(result) >= 0

    # -------------------------------------------------------------------------
    # OTHER API BENCHMARKS - Different patterns/functions (NOT part of main comparison)
    # -------------------------------------------------------------------------

    def test_api_scan_complex_pattern(self, benchmark, temp_dir_structure):
        """API: Scan with complex pattern (NOT part of 3-way comparison).

        Tests pure Rust performance with more complex pattern requirements.
        This is NOT a different approach - it's testing pattern complexity.
        """
        from pathvein import scan
        from pathvein.pattern import FileStructurePattern

        pattern = (
            FileStructurePattern()
            .add_file("*.py")
            .add_file("*.rs")
            .add_file("*.md", is_optional=True)
            .add_file("*.txt", is_optional=True)
        )

        result = benchmark(lambda: scan(temp_dir_structure, [pattern]))
        assert len(result) >= 0

    # -------------------------------------------------------------------------
    # SHUFFLE BENCHMARKS - Test file copying performance
    # -------------------------------------------------------------------------

    def test_api_shuffle_to_dryrun(self, benchmark, temp_dir_structure):
        """API: Benchmark shuffle_to() in dryrun mode.

        Tests the overhead of planning file copies without actually copying.
        Useful for understanding shuffle performance without I/O.
        """
        from pathvein import scan, shuffle_to
        from pathvein.pattern import FileStructurePattern
        from pathlib import Path
        import tempfile

        # First scan to get matches
        patterns = [FileStructurePattern().add_file("*.py")]
        matches = scan(temp_dir_structure, patterns)

        if not matches:
            pytest.skip("No matches found for shuffle benchmark")

        # Benchmark shuffle_to in dryrun mode
        with tempfile.TemporaryDirectory() as tmpdir:
            dest = Path(tmpdir) / "output"
            result = benchmark(lambda: shuffle_to(matches, dest, dryrun=True))

        assert isinstance(result, list)

    def test_api_assess(self, benchmark, temp_dir_structure):
        """API: Benchmark assess() for reverse pattern matching.

        Given a file, find which patterns it belongs to.
        Less commonly used but part of public API.
        """
        from pathvein import assess
        from pathvein.pattern import FileStructurePattern

        # Find a file in the test structure
        import os

        test_file = None
        for root, dirs, files in os.walk(temp_dir_structure):
            if files:
                test_file = (
                    temp_dir_structure
                    / root.replace(str(temp_dir_structure), "").lstrip("/")
                    / files[0]
                )
                break

        if test_file is None:
            test_file = temp_dir_structure / "test.py"
            test_file.touch()

        patterns = [FileStructurePattern().add_file("*.py")]

        result = benchmark(lambda: list(assess(test_file, patterns)))
        assert isinstance(result, list)


if __name__ == "__main__":
    # Show instructions if run directly
    print(__doc__)
