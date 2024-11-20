import logging
from pathlib import Path
from typing import Iterable, NamedTuple
from .pattern import FileStructurePattern

logger = logging.getLogger(__name__)

ScanResult = NamedTuple(
    "ScanResult", [("source", Path), ("pattern", FileStructurePattern)]
)


def scan(
    source: Path,
    pattern_spec_paths: Iterable[Path],
) -> set[ScanResult]:
    """Recursively scan a directory path for directory structures that match the requirements"""

    logger.info("Beginning scan of %s", source.as_posix())

    # Resolve to real paths to ensure that things like .exist() and .is_dir() work correctly
    source = source.resolve()

    requirements = [FileStructurePattern.load_json(path) for path in pattern_spec_paths]

    for structure in requirements:
        logger.debug("Scanning for paths that match structure: %s", structure)

    matches = set()
    for dirpath, dirnames, filenames in source.walk():
        logger.debug("Path.walk: (%s, %s, %s)", dirpath, dirnames, filenames)
        for structure in requirements:
            if structure.matches((dirpath, dirnames, filenames)):
                logger.debug("Matched structure %s in %s", structure, dirpath)
                matches.add(ScanResult(dirpath, structure))

    logger.debug("Matching paths: %s", matches)

    return matches


ShuffleResult = NamedTuple("ShuffleResult", [("source", Path), ("destination", Path)])


def shuffle(
    source: Path,
    destination: Path,
    pattern_spec_paths: Iterable[Path],
    overwrite: bool = False,
    dryrun: bool = False,
) -> list[ShuffleResult]:
    """Recursively scan a source path for pattern-spec directory structures and copy them to the destination."""
    matches = scan(source, pattern_spec_paths)

    logger.info("Beginning shuffle organization of %s to %s", source, destination)

    # Resolve to real paths to ensure that things like .exist() and .is_dir() work correctly
    source = source.resolve()
    destination = destination.resolve()

    # Side effect time!
    copied = []
    for path, pattern in matches:
        destination_path = destination / path.name
        try:
            pattern.copy(path, destination_path, overwrite=overwrite, dryrun=dryrun)
            logger.debug("%s copied to %s", path, destination_path)
            copied.append(ShuffleResult(path, destination_path))
        except FileExistsError:
            logger.error(
                "Destination folder exists already: %s. Skipping: %s",
                destination_path,
                path.name,
            )

    logger.info("Finished shuffle organization of %s to %s", source, destination)
    logger.info("Copied %s missions", len(copied))
    return copied
