"""
Backend selection for pathvein.

This module automatically imports the Rust-accelerated backend if available,
otherwise falls back to pure Python implementations.
"""

import logging
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

# Try to import Rust extension
HAS_RUST_BACKEND = False
try:
    from pathvein import _pathvein_rs  # type: ignore

    HAS_RUST_BACKEND = True
    logger.debug("Rust backend loaded successfully")
except ImportError:
    logger.debug("Rust backend not available, using pure Python implementation")
    _pathvein_rs = None


def walk_parallel(
    path: str, max_depth: Optional[int] = None, follow_links: bool = False
) -> List[Tuple[str, List[str], List[str]]]:
    """
    Walk directory tree in parallel.

    Uses Rust backend if available (5-10x faster), otherwise falls back
    to Python implementation.

    Args:
        path: Root directory to walk
        max_depth: Optional maximum depth to traverse
        follow_links: Whether to follow symbolic links

    Returns:
        List of (path, dirnames, filenames) tuples
    """
    if HAS_RUST_BACKEND and _pathvein_rs is not None:
        # Use Rust backend
        entries = _pathvein_rs.walk_parallel(path, max_depth, follow_links)
        return [(e.path, e.dirnames, e.filenames) for e in entries]
    else:
        # Fall back to Python implementation
        import os

        results = []
        for dirpath, dirnames, filenames in os.walk(path, followlinks=follow_links):
            if max_depth is not None:
                depth = dirpath[len(path) :].count(os.sep)
                if depth >= max_depth:
                    dirnames[:] = []  # Don't recurse deeper
            results.append((dirpath, dirnames, filenames))
        return results


def scan_parallel(
    path: str, patterns, max_depth: Optional[int] = None, follow_links: bool = False
):
    """
    Scan directory tree for pattern matches in Rust.

    This is a streaming implementation that walks AND matches in Rust,
    avoiding the overhead of returning all data to Python and then
    matching it. Instead, we walk in Rust, call back to Python pattern
    matchers, and return only matches.

    Args:
        path: Root directory to scan
        patterns: List of FileStructurePattern objects to match against
        max_depth: Optional maximum depth to traverse
        follow_links: Whether to follow symbolic links

    Returns:
        List of (path, pattern) tuples for directories that matched
    """
    if HAS_RUST_BACKEND and _pathvein_rs is not None:
        from pathlib import Path as PathType

        # Use Rust backend - walk and match in one pass
        results = _pathvein_rs.scan_parallel(path, patterns, max_depth, follow_links)
        # Convert results back to (Path, pattern) tuples
        return [(PathType(r.path), patterns[r.pattern_index]) for r in results]
    else:
        # Fall back to Python implementation
        from pathlib import Path as PathType

        results = []
        for dirpath_str, dirnames, filenames in walk_parallel(
            path, max_depth, follow_links
        ):
            dirpath = PathType(dirpath_str)
            for pattern in patterns:
                if pattern.matches((dirpath, dirnames, filenames)):
                    results.append((dirpath, pattern))
        return results


class PatternMatcher:
    """
    High-performance glob pattern matcher.

    Uses Rust backend if available (3-5x faster), otherwise falls back
    to Python fnmatch.
    """

    def __init__(self, patterns: List[str]):
        """
        Create a pattern matcher.

        Args:
            patterns: List of glob patterns
        """
        self.patterns = patterns

        if HAS_RUST_BACKEND and _pathvein_rs is not None:
            # Use Rust backend
            try:
                self._rust_matcher = _pathvein_rs.PatternMatcher(patterns)
                self._backend = "rust"
            except ValueError as e:
                # Invalid glob pattern, fall back to Python
                logger.debug(
                    "Invalid pattern in %s, falling back to Python: %s", patterns, e
                )
                from pathvein._path_utils import compile_pattern

                self._compiled_patterns = [compile_pattern(p) for p in patterns]
                self._backend = "python"
        else:
            # Fall back to Python
            from pathvein._path_utils import compile_pattern

            self._compiled_patterns = [compile_pattern(p) for p in patterns]
            self._backend = "python"

    def matches(self, path: str) -> bool:
        """Check if path matches any pattern."""
        if self._backend == "rust":
            return self._rust_matcher.matches(path)
        else:
            return any(p.match(path) for p in self._compiled_patterns)

    def matching_patterns(self, path: str) -> List[str]:
        """Return list of patterns that match the path."""
        if self._backend == "rust":
            return self._rust_matcher.matching_patterns(path)
        else:
            return [
                self.patterns[i]
                for i, p in enumerate(self._compiled_patterns)
                if p.match(path)
            ]

    def matches_all(self, path: str) -> bool:
        """Check if path matches ALL patterns."""
        if self._backend == "rust":
            return self._rust_matcher.matches_all(path)
        else:
            return all(p.match(path) for p in self._compiled_patterns)

    def __repr__(self) -> str:
        return f"PatternMatcher({len(self.patterns)} patterns, backend={self._backend})"

    def __len__(self) -> int:
        return len(self.patterns)


def match_pattern(path: str, pattern: str) -> bool:
    """
    Match a single path against a single pattern.

    Uses Rust backend if available, otherwise Python fnmatch.

    Args:
        path: File or directory name to match
        pattern: Glob pattern

    Returns:
        True if path matches pattern
    """
    if HAS_RUST_BACKEND and _pathvein_rs is not None:
        try:
            return _pathvein_rs.match_pattern(path, pattern)
        except ValueError as e:
            # Invalid glob pattern, fall back to Python
            logger.debug("Invalid pattern '%s', falling back to Python: %s", pattern, e)
            from pathvein._path_utils import pattern_match

            return pattern_match(path, pattern)
    else:
        from pathvein._path_utils import pattern_match

        return pattern_match(path, pattern)


def get_backend_info() -> dict:
    """
    Get information about the current backend.

    Returns:
        Dictionary with backend information:
        - has_rust: Whether Rust backend is available
        - backend: "rust" or "python"
        - features: List of available features
    """
    return {
        "has_rust": HAS_RUST_BACKEND,
        "backend": "rust" if HAS_RUST_BACKEND else "python",
        "features": [
            "parallel_walk" if HAS_RUST_BACKEND else None,
            "fast_pattern_matching" if HAS_RUST_BACKEND else None,
        ],
    }
