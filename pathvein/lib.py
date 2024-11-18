import re
import pickle
import typer
import logging
from dataclasses import dataclass
from enum import StrEnum, auto
from pprint import pformat
from pathlib import Path
from typing import Annotated, Self, Any

from .requirements import (
    FileStructureRequirement,
    REMUS_REQUIREMENTS,
    IVER_REQUIREMENTS,
)

logger = logging.getLogger(__name__)

context_settings = {
    "help_option_names": ["-h", "--help"],
}

cli = typer.Typer(context_settings=context_settings)


class VehicleType(StrEnum):
    IVER3 = auto()
    IVER4 = auto()
    REMUS = auto()
    UNKNOWN = auto()


@dataclass
class Mission:
    path: Path
    structure: FileStructureRequirement

    @property
    def vehicle_type(self: Self) -> VehicleType:
        iver3_pattern = (r"iver3", r"iver-3", r"iver_3")
        iver4_pattern = (r"iver4", r"iver-4", r"iver_4")
        remus_pattern = (r"remus", r"remus", r"remus")

        input = self.path.as_posix().lower()

        if any(len(re.findall(pattern, input)) > 0 for pattern in iver3_pattern):
            return VehicleType.IVER3
        if any(len(re.findall(pattern, input)) > 0 for pattern in iver4_pattern):
            return VehicleType.IVER4
        if any(len(re.findall(pattern, input)) > 0 for pattern in remus_pattern):
            return VehicleType.REMUS
        return VehicleType.UNKNOWN

    @property
    def vehicle_id(self: Self) -> str:
        pattern = r"\d{3,}"
        matches = re.findall(pattern, self.path.as_posix())
        id = matches[-1]
        return f"{id}"

    @property
    def name(self: Self) -> str:
        return self.path.name

    def __repr__(self: Self) -> str:
        return f"{self.path}"

    def __key(self: Self):
        return (self.path, self.vehicle_type, self.vehicle_id, self.name)

    def __hash__(self: Self):
        return hash(self.__key())

    def __eq__(self: Self, other: Any):
        if isinstance(other, Mission):
            return self.__key() == other.__key()
        return NotImplemented


def set_logger_level(verbosity: int, default: int = logging.ERROR) -> None:
    """
    Set the logger level based on the level of verbosity

    level = default - 10*verbosity

    verbosity = # of -v flags passed

    default = 30 = logging.ERROR

    level with -v   = 30 = logging.WARNING
    level with -vv  = 20 = logging.INFO
    level with -vvv = 10 = logging.DEBUG
    """
    logger.setLevel(default - 10 * verbosity)


@cli.command()
def scan(
    directory: Path,
    output: Path = Path("scan.pkl"),
    verbose: Annotated[int, typer.Option("--verbose", "-v", count=True)] = 0,
) -> set[Mission]:
    """Recursively scan a directory path for mission-like directory structures"""

    logger.info("Beginning scan of %s", directory)

    # Resolve to real paths to ensure that things like .exist() and .is_dir() work correctly
    directory = directory.resolve()

    mission_structures = [IVER_REQUIREMENTS, REMUS_REQUIREMENTS]

    for structure in mission_structures:
        logger.debug(
            "Scanning for directories that match mission structure: %s", structure
        )

    candidates = set()
    for dirpath, dirnames, filenames in directory.walk():
        logger.debug("Path.walk: (%s, %s, %s)", dirpath, dirnames, filenames)
        for structure in mission_structures:
            if structure.matches((dirpath, dirnames, filenames)):
                candidates.add((dirpath, structure))

    logger.debug("Candidate mission directories: %s", candidates)

    missions = {Mission(path, structure) for (path, structure) in candidates}

    logger.info("Finished scan of %s, found: %s", directory, pformat(missions))

    logger.info("Found %s missions", len(missions))

    with output.open("wb") as handle:
        pickle.dump(missions, handle)

    return missions


@cli.command()
def shuffle(
    source: Path,
    destination: Path,
    overwrite: bool = False,
    dryrun: bool = False,
    verbose: Annotated[int, typer.Option("--verbose", "-v", count=True)] = 0,
) -> None:
    """Recursively scan a source path for mission-like directory structures and copy them to the destination."""
    missions = scan(source, verbose=verbose)

    logger.info("Beginning shuffle organization of %s to %s", source, destination)

    # Resolve to real paths to ensure that things like .exist() and .is_dir() work correctly
    source = source.resolve()
    destination = destination.resolve()

    # Side effect time!
    copied_count = 0
    for mission in missions:
        destination_path = (
            destination / mission.vehicle_type / mission.vehicle_id / mission.name
        )
        # Copy the file structure that matches the mission_structure from the mission path to the destination path
        try:
            mission.structure.copy(mission.path, destination_path, dryrun=dryrun)
            logger.debug("%s copied to %s", mission, destination_path)
            copied_count += 1
        except FileExistsError:
            logger.error(
                "Destination folder exists already: %s. Overwrite is disabled, skipping: %s",
                destination_path,
                mission.path.name,
            )

    logger.info("Finished shuffle organization of %s to %s", source, destination)
    logger.info("Copied %s missions", copied_count)


def main():
    logging.basicConfig(
        level=logging.NOTSET,
        format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
        datefmt="%m-%d %H:%M",
        handlers=[logging.FileHandler("/tmp/organizer.log"), logging.StreamHandler()],
    )
    cli()


if __name__ == "__main__":
    main()
