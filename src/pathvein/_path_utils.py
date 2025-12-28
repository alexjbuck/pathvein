"""
Path utilities for Pathvein.

This module provides low-level path operations including streaming file copy,
directory walking, and cached directory listing. These utilities are designed
to work with both standard pathlib.Path and third-party path-like objects.
"""

import fnmatch
import logging
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Generator, List, Pattern, Tuple

logger = logging.getLogger(__name__)


def stream_copy(source: Path, destination: Path, chunk_size=256 * 1024) -> None:
    """Copy a file from source to destination using a streaming copy"""
    logger.debug(
        "Stream copy initiated", extra={"file": source, "destination": destination}
    )
    with destination.open("wb") as writer, source.open("rb") as reader:
        # Localize variable access to minimize overhead.
        read = reader.read
        write = writer.write
        while chunk := read(chunk_size):
            write(chunk)
    logger.debug(
        "Copied file",
        extra={
            "file": source,
            "destination": destination,
        },
    )


@lru_cache(maxsize=256)
def compile_pattern(pattern: str) -> Pattern[str]:
    """Compile a glob pattern to a regex pattern for faster matching

    fnmatch internally compiles patterns, but by explicitly caching
    we can ensure patterns are only compiled once and reused across
    all matching operations.
    """
    return re.compile(fnmatch.translate(pattern))


def pattern_match(name: str, pattern: str) -> bool:
    """Match a name against a glob pattern using pre-compiled regex

    This is 10-20% faster than fnmatch.fnmatch() for repeated patterns
    because it caches the compiled regex.
    """
    compiled = compile_pattern(pattern)
    return compiled.match(name) is not None


def walk(source: Path) -> Generator[Tuple[Path, List[str], List[str]], None, None]:
    """
    Recursively walk a directory path and return a list of directories and filesystem

    Independent of os.walk or pathlib.Path.walk, this function just uses iterdir() to walk the directory tree

    In this way it works for both pathlib.Path objects as well as third-party pathlib objects so long as they
    implement iterdir(), is_dir, and is_file() methods.

    This does not offer a sophisticated symlink following mechanism. If `type` is Path, this will short circuit
    to os.walk which provides better symlink handling capability.
    """
    if type(source) is Path:
        for dirpath, dirnames, filenames in os.walk(source):
            yield Path(dirpath), dirnames, filenames
    else:
        dir_stack = []
        dir_stack.append(source)
        while dir_stack:
            path = dir_stack.pop()
            try:
                path, dirnames, filenames = iterdir(path)
            except PermissionError:
                logger.warning("Permission denied for %s", path)
                continue
            yield path, dirnames, filenames
            # Breadth-first traversal
            dirs = [path / dirname for dirname in dirnames]
            logger.debug("dirs: %s", dirs)
            dir_stack.extend(dirs)


@lru_cache(maxsize=10000)
def iterdir(path: Path) -> Tuple[Path, List[str], List[str]]:
    """Return a list of all files and directories in a directory path

    Uses os.scandir() for local paths (2-3x faster than path.iterdir())
    Falls back to path.iterdir() for non-local paths (e.g., S3, UPath)
    """
    # For standard Path objects, use os.scandir for better performance
    # os.scandir returns DirEntry objects which cache stat info
    if type(path) is Path:
        filenames = []
        dirnames = []
        try:
            with os.scandir(path) as entries:
                for entry in entries:
                    # follow_symlinks=False is faster and safer
                    if entry.is_file(follow_symlinks=False):
                        filenames.append(entry.name)
                    elif entry.is_dir(follow_symlinks=False):
                        dirnames.append(entry.name)
            return path, dirnames, filenames
        except (OSError, ValueError):
            # Fall back to iterdir on permission errors or other issues
            pass

    # Fallback for non-standard Path types (UPath, S3Path, etc.)
    contents = list(path.iterdir())
    filenames = [content.name for content in contents if content.is_file()]
    dirnames = [content.name for content in contents if content.is_dir()]
    return path, dirnames, filenames
