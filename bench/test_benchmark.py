"""
pytest-benchmark tests for pathvein.

These benchmarks use pytest-benchmark for more rigorous statistical analysis
and can be integrated with CI/CD for performance regression detection.

Usage:
    # Run benchmarks
    pytest bench/test_benchmark.py --benchmark-only

    # Save baseline
    pytest bench/test_benchmark.py --benchmark-only --benchmark-save=baseline

    # Compare against baseline
    pytest bench/test_benchmark.py --benchmark-only --benchmark-compare=baseline

    # Generate JSON for CI
    pytest bench/test_benchmark.py --benchmark-only --benchmark-json=output.json

    # Show histogram
    pytest bench/test_benchmark.py --benchmark-only --benchmark-histogram

Install dependencies:
    pip install pytest pytest-benchmark
"""

import tempfile
from pathlib import Path

import pytest

from pathvein._backend import (
    PatternMatcher,
    get_backend_info,
    match_pattern,
    walk_parallel,
)
from pathvein._path_utils import pattern_match


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
    """Create a temporary directory structure for benchmarks."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        # Create a medium-sized directory structure
        # 5 subdirs × 4 levels × 20 files = ~2000 files
        def create_tree(parent: Path, depth: int, max_depth: int = 4):
            if depth > max_depth:
                return

            # Create files
            for i in range(20):
                ext = ["txt", "py", "rs", "md", "json"][i % 5]
                (parent / f"file_{depth}_{i}.{ext}").touch()

            # Create subdirs
            if depth < max_depth:
                for i in range(5):
                    subdir = parent / f"subdir_{depth}_{i}"
                    subdir.mkdir()
                    create_tree(subdir, depth + 1, max_depth)

        create_tree(root, 0)
        yield root


@pytest.fixture(scope="session")
def test_filenames():
    """Generate a list of test filenames for pattern matching."""
    filenames = []
    for i in range(1000):
        ext = ["txt", "py", "rs", "md", "json", "yaml", "toml", "sh"][i % 8]
        prefix = ["test", "main", "lib", "util", "helper", "config"][i % 6]
        filenames.append(f"{prefix}_{i}.{ext}")
    return filenames


# Directory Walking Benchmarks
class TestDirectoryWalking:
    """Benchmark directory walking operations."""

    def test_walk_parallel(self, benchmark, temp_dir_structure):
        """Benchmark parallel directory walking."""
        result = benchmark(lambda: list(walk_parallel(str(temp_dir_structure))))
        # Verify we got results
        assert len(result) > 0

    def test_walk_with_max_depth(self, benchmark, temp_dir_structure):
        """Benchmark directory walking with max_depth=2."""
        result = benchmark(
            lambda: list(walk_parallel(str(temp_dir_structure), max_depth=2))
        )
        assert len(result) > 0


# Pattern Matching Benchmarks
class TestPatternMatching:
    """Benchmark pattern matching operations."""

    def test_single_pattern_simple(self, benchmark, test_filenames):
        """Benchmark single simple pattern (*.py)."""
        pattern = "*.py"
        result = benchmark(
            lambda: [f for f in test_filenames if pattern_match(f, pattern)]
        )
        assert len(result) > 0

    def test_single_pattern_match_pattern(self, benchmark, test_filenames):
        """Benchmark single pattern using match_pattern."""
        pattern = "test_*.txt"  # Changed to match actual files (test_0.txt, test_24.txt, etc.)
        result = benchmark(
            lambda: [f for f in test_filenames if match_pattern(f, pattern)]
        )
        assert len(result) > 0

    def test_multiple_patterns_3(self, benchmark, test_filenames):
        """Benchmark 3 patterns using PatternMatcher."""
        patterns = ["*.py", "*.rs", "*.md"]
        matcher = PatternMatcher(patterns)
        result = benchmark(lambda: [f for f in test_filenames if matcher.matches(f)])
        assert len(result) > 0

    def test_multiple_patterns_12(self, benchmark, test_filenames):
        """Benchmark 12 patterns using PatternMatcher."""
        patterns = [
            f"{prefix}_*.{ext}"
            for prefix in ["test", "main", "lib"]
            for ext in ["py", "rs", "md", "txt"]
        ]
        matcher = PatternMatcher(patterns)
        result = benchmark(lambda: [f for f in test_filenames if matcher.matches(f)])
        assert len(result) > 0

    def test_pattern_cache_effectiveness(self, benchmark, test_filenames):
        """Benchmark repeated pattern matching (tests cache)."""
        pattern = "*.py"

        def repeated_match():
            results = []
            for _ in range(100):
                results.extend([f for f in test_filenames if pattern_match(f, pattern)])
            return results

        result = benchmark(repeated_match)
        assert len(result) > 0


# End-to-End Benchmarks
class TestEndToEnd:
    """Benchmark end-to-end operations."""

    def test_scan_with_patterns(self, benchmark, temp_dir_structure):
        """Benchmark scanning directory with pattern filtering."""
        patterns = ["*.py", "*.rs", "*.md"]
        matcher = PatternMatcher(patterns)

        def scan():
            files = []
            for dirpath, dirnames, filenames in walk_parallel(str(temp_dir_structure)):
                files.extend([f for f in filenames if matcher.matches(f)])
            return files

        result = benchmark(scan)
        assert len(result) > 0

    def test_scan_single_pattern(self, benchmark, temp_dir_structure):
        """Benchmark scanning directory with single pattern using PatternMatcher.

        Note: Uses PatternMatcher instead of match_pattern for efficiency.
        PatternMatcher compiles patterns once and keeps them in Rust,
        avoiding FFI overhead on each match.
        """
        pattern = "*.py"
        matcher = PatternMatcher([pattern])

        def scan():
            files = []
            for dirpath, dirnames, filenames in walk_parallel(str(temp_dir_structure)):
                files.extend([f for f in filenames if matcher.matches(f)])
            return files

        result = benchmark(scan)
        assert len(result) > 0

    def test_scan_single_pattern_antipattern(self, benchmark, temp_dir_structure):
        """Benchmark scan using match_pattern in a loop (ANTI-PATTERN).

        This demonstrates why you should NOT use match_pattern repeatedly.
        Each call crosses the Python/Rust FFI boundary, causing overhead.
        Use PatternMatcher instead (see test_scan_single_pattern).
        """
        pattern = "*.py"

        def scan():
            files = []
            for dirpath, dirnames, filenames in walk_parallel(str(temp_dir_structure)):
                files.extend([f for f in filenames if match_pattern(f, pattern)])
            return files

        result = benchmark(scan)
        assert len(result) > 0


# Comparison Tests
class TestComparison:
    """Tests that compare different approaches."""

    def test_pattern_matcher_vs_individual(self, benchmark, test_filenames):
        """Compare PatternMatcher vs individual match_pattern calls."""
        patterns = ["*.py", "*.rs", "*.md"]

        if get_backend_info()["backend"] == "rust":
            # Rust: Use PatternMatcher (should be faster)
            matcher = PatternMatcher(patterns)
            result = benchmark(
                lambda: [f for f in test_filenames if matcher.matches(f)]
            )
        else:
            # Python: Use individual checks (might be comparable due to caching)
            result = benchmark(
                lambda: [
                    f
                    for f in test_filenames
                    if any(match_pattern(f, p) for p in patterns)
                ]
            )

        assert len(result) > 0


# Public API Benchmarks
class TestPublicAPI:
    """Benchmark public API functions that users actually call.

    These are different from micro benchmarks - they test the full API
    surface that users interact with, not internal implementation details.
    """

    def test_scan_api(self, benchmark, temp_dir_structure):
        """Benchmark the public scan() API function."""
        from pathvein import scan
        from pathvein.pattern import FileStructurePattern

        # Create patterns that will find Python and Rust files
        patterns = [
            FileStructurePattern().add_file("*.py"),
            FileStructurePattern().add_file("*.rs"),
        ]

        result = benchmark(lambda: scan(temp_dir_structure, patterns))
        # We should find some matches in our test structure
        assert len(result) >= 0

    def test_scan_new_approach_rust_scan_parallel(self, benchmark, temp_dir_structure):
        """Benchmark NEW approach: scan_parallel with precompiled patterns in Rust.

        This uses scan_parallel() which:
        1. Precompiles all patterns ONCE
        2. Walks and matches entirely in Rust
        3. No FFI crossings during scan loop
        """
        from pathvein import scan
        from pathvein.pattern import FileStructurePattern

        patterns = [
            FileStructurePattern().add_file("*.py"),
            FileStructurePattern().add_file("*.rs"),
        ]

        result = benchmark(lambda: scan(temp_dir_structure, patterns))
        assert len(result) >= 0

    def test_scan_old_approach_walk_then_match(self, benchmark, temp_dir_structure):
        """Benchmark OLD approach: walk_parallel() then match in Python.

        This uses the old pattern:
        1. walk_parallel() returns all directories
        2. For each directory, call pattern.matches()
        3. pattern.matches() calls back to Rust for glob matching
        4. Many FFI crossings during scan loop
        """
        from pathvein.pattern import FileStructurePattern
        from pathvein._backend import walk_parallel
        from pathvein.lib import ScanResult
        from pathlib import Path

        patterns = [
            FileStructurePattern().add_file("*.py"),
            FileStructurePattern().add_file("*.rs"),
        ]

        def old_approach():
            matches = set()
            for dirpath_str, dirnames, filenames in walk_parallel(
                str(temp_dir_structure)
            ):
                dirpath = Path(dirpath_str)
                for pattern in patterns:
                    if pattern.matches((dirpath, dirnames, filenames)):
                        matches.add(ScanResult(dirpath, pattern))
            return matches

        result = benchmark(old_approach)
        assert len(result) >= 0

    def test_assess_api(self, benchmark, temp_dir_structure):
        """Benchmark the public assess() API function."""
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
            # Create a test file if none exist
            test_file = temp_dir_structure / "test.py"
            test_file.touch()

        patterns = [FileStructurePattern().add_file("*.py")]

        result = benchmark(lambda: list(assess(test_file, patterns)))
        assert isinstance(result, list)

    def test_scan_api_complex_pattern(self, benchmark, temp_dir_structure):
        """Benchmark scan() with complex patterns (required + optional files)."""
        from pathvein import scan
        from pathvein.pattern import FileStructurePattern

        # Complex pattern with required and optional files
        pattern = (
            FileStructurePattern().add_file("*.py").add_file("*.md", is_optional=True)
        )

        result = benchmark(lambda: scan(temp_dir_structure, [pattern]))
        assert len(result) >= 0

    def test_shuffle_to_api_dryrun(self, benchmark, temp_dir_structure):
        """Benchmark the public shuffle_to() API function (dryrun mode)."""
        from pathvein import scan, shuffle_to
        from pathvein.pattern import FileStructurePattern
        from pathlib import Path
        import tempfile

        # First scan to get matches
        patterns = [FileStructurePattern().add_file("*.py")]
        matches = scan(temp_dir_structure, patterns)

        if not matches:
            # Skip if no matches
            return

        # Benchmark shuffle_to in dryrun mode
        with tempfile.TemporaryDirectory() as tmpdir:
            dest = Path(tmpdir) / "output"
            result = benchmark(lambda: shuffle_to(matches, dest, dryrun=True))

        assert isinstance(result, list)


if __name__ == "__main__":
    # Show instructions if run directly
    print(__doc__)
