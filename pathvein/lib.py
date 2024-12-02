import logging
from pathlib import Path
from typing import Callable, Iterable, List, NamedTuple, Set

from ._path_utils import walk
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
    shuffle_def: Set[ShuffleInput],
    overwrite: bool = False,
    dryrun: bool = False,
) -> List[ShuffleResult]:
    """
    Recursively scan a source path for pattern-spec directory structures and copy them to their destination

    ShuffleInput.source will be copied to ShuffleInput.destination, not _into_ it.
    The direct children of ShuffleInput.source will be direct children of ShuffleInput.destination
    """

    # Side effect time!
    copied = []
    for source, destination, pattern in shuffle_def:
        try:
            pattern.copy(source, destination, overwrite=overwrite, dryrun=dryrun)
            logger.debug("%s copied to %s", source, destination)
            copied.append(ShuffleResult(source, destination, pattern))
        except FileExistsError:
            logger.error(
                "Destination folder already exists: %s. Skipping: %s",
                destination,
                source.name,
            )
    logger.info("Copied %s missions", len(copied))
    return copied


def shuffle_to(
    matches: Set[ScanResult],
    destination: Path,
    overwrite: bool = False,
    dryrun: bool = False,
) -> List[ShuffleResult]:
    """
    Recursively scan a source path for pattern-spec directory structures and copy them into a single destination_fn

    Each match will be copied into a flat structure at `destination / match.source.name`
    """

    shuffle_def = set(
        map(
            lambda match: ShuffleInput(
                match.source, destination / match.source.name, match.pattern
            ),
            matches,
        )
    )
    return shuffle(shuffle_def, overwrite=overwrite, dryrun=dryrun)


def shuffle_with(
    matches: Set[ScanResult],
    destination_fn: Callable[[ScanResult], Path],
    overwrite: bool = False,
    dryrun: bool = False,
) -> List[ShuffleResult]:
    """
    Recursively scan a source path for pattern-spec directory structures and copy them to the destination_fn

    Provide a function that takes a ScanResult and returns a destination Path for that result. This allows for
    expressive control over the destination of each match.
    """

    shuffle_def = set(
        map(
            lambda scan_result: ShuffleInput(
                scan_result.source, destination_fn(scan_result), scan_result.pattern
            ),
            matches,
        )
    )
    return shuffle(shuffle_def, overwrite=overwrite, dryrun=dryrun)
