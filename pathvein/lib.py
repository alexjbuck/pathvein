from dataclasses import dataclass
import logging
import os
from pathlib import Path
from typing import Callable, Generator, Iterable, List, NamedTuple, Set, Tuple

from upath import UPath

from .pattern import FileStructurePattern

logger = logging.getLogger(__name__)


# In order to support back to python 3.8 we need to declare these as NamedTuple subclasses
# instead of using the new-type style definition with "ScanResult = NamedTuple(...)" format.


class ScanResult(NamedTuple):
    source: Path
    pattern: FileStructurePattern


class ShuffleInput(NamedTuple):
    source: Path
    destination: Path
    pattern: FileStructurePattern


class ShuffleResult(NamedTuple):
    source: Path
    destination: Path
    pattern: FileStructurePattern


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
            contents = list(path.iterdir())
            filenames = [content.name for content in contents if content.is_file()]
            dirs = [content for content in contents if content.is_dir()]
            dirnames = [dir.name for dir in dirs]
            yield path, dirnames, filenames
            # Breadth-first traversal
            logger.debug("dirs: %s", dirs)
            dir_stack.extend(dirs)


def scan(
    source: Path,
    patterns: Iterable[FileStructurePattern],
) -> Set[ScanResult]:
    """Recursively scan a directory path for directory structures that match the requirements"""

    logger.info("Beginning scan of %s", source.as_posix())

    # Resolve to real paths to ensure that things like .exist() and .is_dir() work correctly
    source = source.resolve()

    for pattern in patterns:
        logger.debug("Scanning for paths that match structure: %s", pattern)

    matches = set()

    for dirpath, dirnames, filenames in walk(source):
        logger.debug("Path.walk: (%s, %s, %s)", dirpath, dirnames, filenames)
        # Expclicitly ensure walk results are the correct types
        dirpath = UPath(dirpath)
        dirnames = list(dirnames)
        filenames = list(filenames)
        for pattern in patterns:
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
