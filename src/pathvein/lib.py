"""
Core library functionality for Pathvein.

This module provides the main functionality for scanning directories, assessing file patterns,
and shuffling (copying) files based on pattern matches. It includes the core data structures
(ScanResult, ShuffleInput, ShuffleResult) and functions (scan, assess, shuffle) that power
the pattern matching and file organization capabilities.
"""

import logging
from pathlib import Path
from typing import Callable, Generator, Iterable, List, NamedTuple, Set

from ._path_utils import iterdir, walk
from .pattern import FileStructurePattern

logger = logging.getLogger(__name__)


# In order to support back to python 3.8 we need to declare these as NamedTuple subclasses
# instead of using the new-type style definition with "ScanResult = NamedTuple(...)" format.


class ScanResult(NamedTuple):
    """
    source: Path
    pattern: FileStructurePattern
    """

    source: Path
    pattern: FileStructurePattern


class ShuffleInput(NamedTuple):
    """
    source: Path
    destination: Path
    pattern: FileStructurePattern
    """

    source: Path
    destination: Path
    pattern: FileStructurePattern


class ShuffleResult(NamedTuple):
    """
    source: Path
    destination: Path
    pattern: FileStructurePattern
    """

    source: Path
    destination: Path
    pattern: FileStructurePattern


def assess(
    file: Path,
    patterns: Iterable[FileStructurePattern],
) -> Generator[ScanResult, None, None]:
    """Assess which patterns a file belongs to and find the pattern root directories.

    Given a file path, this function determines which patterns it could belong to
    by working backwards from the file to find candidate root directories, then
    validating that those roots actually match the pattern.

    This is useful for:
    - Reverse engineering: Given a file, what pattern does it belong to?
    - Validation: Does this file belong to a known pattern?
    - Discovery: What's the root directory of the pattern containing this file?

    Args:
        file: Path to a file to assess
        patterns: Patterns to check against

    Yields:
        ScanResult objects with the root directory and matched pattern

    Example:
        >>> patterns = [pattern1, pattern2]
        >>> for result in assess(Path("data/exp1/results.csv"), patterns):
        ...     print(f"File belongs to pattern at: {result.source}")
    """
    logger.debug("Assessing %s for patterns %s", file, patterns)
    for pattern in patterns:
        logger.debug("Assessing %s for pattern %s", file, pattern)
        roots = pattern.parents_of(file)
        logger.debug("Candidate root directories found: %s", roots)
        if len(roots) > 0:
            for root in roots:
                if pattern.matches(iterdir(root)):
                    logger.debug("Yielding root %s", root)
                    yield ScanResult(root, pattern)


def scan(
    source: Path,
    patterns: Iterable[FileStructurePattern],
) -> Set[ScanResult]:
    """Recursively scan a directory path for directory structures that match the requirements"""

    logger.info("Beginning scan of %s", source.as_posix())

    # Resolve to real paths to ensure that things like .exist() and .is_dir() work correctly
    source = source.resolve()

    # Consume the iterable into a list so we can reuse it
    pattern_list = list(patterns)

    for pattern in pattern_list:
        logger.debug("Scanning for paths that match structure: %s", pattern)

    matches = set()

    for dirpath, dirnames, filenames in walk(source):
        logger.debug("Walk: (%s, %s, %s)", dirpath, dirnames, filenames)
        for pattern in pattern_list:
            if pattern.matches((dirpath, dirnames, filenames)):
                logger.debug("Matched structure %s in %s", pattern, dirpath)
                matches.add(ScanResult(dirpath, pattern))

    logger.debug("Matching paths: %s", matches)

    return matches


def shuffle(
    shuffle_def: Iterable[ShuffleInput],
    overwrite: bool = False,
    dryrun: bool = False,
    use_threading: bool = False,
    max_workers: int = 4,
) -> List[ShuffleResult]:
    """
    Recursively scan a source path for pattern-spec directory structures and copy them to their destination

    ShuffleInput.source will be copied to ShuffleInput.destination, not _into_ it.
    The direct children of ShuffleInput.source will be direct children of ShuffleInput.destination

    Args:
        shuffle_def: Iterable of ShuffleInput defining source->destination mappings
        overwrite: Whether to overwrite existing files (default: False)
        dryrun: If True, don't actually copy files (default: False)
        use_threading: If True, use parallel file copying (default: False)
        max_workers: Number of worker threads for parallel copying (default: 4)
    """

    # Side effect time!
    copied = []
    for source, destination, pattern in shuffle_def:
        try:
            if use_threading:
                pattern.threaded_copy(
                    source,
                    destination,
                    overwrite=overwrite,
                    dryrun=dryrun,
                    max_workers=max_workers,
                )
            else:
                pattern.copy(source, destination, overwrite=overwrite, dryrun=dryrun)
            logger.debug("%s copied to %s", source, destination)
            copied.append(ShuffleResult(source, destination, pattern))
        except FileExistsError:
            logger.error(
                "Destination folder already exists: %s. Skipping: %s",
                destination,
                source.name,
            )
    logger.info("Copied %s directories", len(copied))
    return copied


def shuffle_to(
    matches: Iterable[ScanResult],
    destination: Path,
    overwrite: bool = False,
    dryrun: bool = False,
    use_threading: bool = False,
    max_workers: int = 4,
) -> List[ShuffleResult]:
    """
    Recursively scan a source path for pattern-spec directory structures and copy them into a single destination

    Each match will be copied into a flat structure at `destination / match.source.name`

    Args:
        matches: Iterable of ScanResult from scan()
        destination: Root destination directory
        overwrite: Whether to overwrite existing files (default: False)
        dryrun: If True, don't actually copy files (default: False)
        use_threading: If True, use parallel file copying (default: False)
        max_workers: Number of worker threads for parallel copying (default: 4)
    """

    shuffle_def = map(
        lambda match: ShuffleInput(
            match.source, destination / match.source.name, match.pattern
        ),
        matches,
    )
    return shuffle(
        shuffle_def,
        overwrite=overwrite,
        dryrun=dryrun,
        use_threading=use_threading,
        max_workers=max_workers,
    )


def shuffle_with(
    matches: Iterable[ScanResult],
    destination_fn: Callable[[ScanResult], Path],
    overwrite: bool = False,
    dryrun: bool = False,
    use_threading: bool = False,
    max_workers: int = 4,
) -> List[ShuffleResult]:
    """
    Recursively scan a source path for pattern-spec directory structures and copy them to computed destinations

    Provide a function that takes a ScanResult and returns a destination Path for that result. This allows for
    expressive control over the destination of each match.

    Args:
        matches: Iterable of ScanResult from scan()
        destination_fn: Function that computes destination path from ScanResult
        overwrite: Whether to overwrite existing files (default: False)
        dryrun: If True, don't actually copy files (default: False)
        use_threading: If True, use parallel file copying (default: False)
        max_workers: Number of worker threads for parallel copying (default: 4)
    """

    shuffle_def = map(
        lambda scan_result: ShuffleInput(
            scan_result.source, destination_fn(scan_result), scan_result.pattern
        ),
        matches,
    )
    return shuffle(
        shuffle_def,
        overwrite=overwrite,
        dryrun=dryrun,
        use_threading=use_threading,
        max_workers=max_workers,
    )
