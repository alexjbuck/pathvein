from dataclasses import dataclass, field
from typing import Iterable, Self, Any
import shutil
from fnmatch import fnmatch
from pathlib import Path
import json
from copy import deepcopy
import logging

logger = logging.getLogger(__name__)


@dataclass
class FileStructureRequirement:
    """
    A class to represent a file structure requirements

    This class also supports a builder pattern as any intermediate state is also valid.
    """

    directory_name: str | None = None
    files: list[str] = field(default_factory=list)
    directories: list[Self] = field(default_factory=list)
    optional_files: list[str] = field(default_factory=list)
    optional_directories: list[Self] = field(default_factory=list)

    def __key(self: Self):
        return (
            self.directory_name,
            hash(tuple(self.files)),
            hash(tuple(self.directories)),
            hash(tuple(self.optional_files)),
            hash(tuple(self.optional_directories)),
        )

    def __hash__(self: Self):
        return hash(self.__key())

    def __eq__(self: Self, other: Any):
        if isinstance(other, FileStructureRequirement):
            return self.__key() == other.__key()
        return NotImplemented

    @classmethod
    def load_json(cls, json_path: Path) -> Self:
        json_str = json_path.read_text()
        return cls.from_json(json_str)

    @classmethod
    def from_json(cls, spec_str: str) -> Self:
        spec = json.loads(spec_str)
        return (
            cls()
            .set_name(spec.get("directory_name"))
            .add_files(spec.get("files", []), required=True)
            .add_files(spec.get("optional_files", []), required=False)
            .add_directories(
                (
                    cls.from_json(subdirectory_spec)
                    for subdirectory_spec in spec.get("directories", [])
                ),
                required=True,
            )
            .add_directories(
                (
                    cls.from_json(subdirectory_spec)
                    for subdirectory_spec in spec.get("optional_directories", [])
                ),
                required=False,
            )
        )

    def to_json(self: Self) -> str:
        # Deepcopy prevents mutating self during serialization.
        # self__dict__ and dictionary point to the same object otherwise.
        dictionary = deepcopy(self.__dict__)
        dictionary["directories"] = [
            directory.to_json() for directory in self.directories
        ]
        dictionary["optional_directories"] = [
            directory.to_json() for directory in self.optional_directories
        ]
        return json.dumps(dictionary)

    def add_directory(self: Self, directory: Self, required: bool = True) -> Self:
        """
        Add a FileStructureRequirement entry to the (optional) directory list

        This method uses deepcopy to prevent recursive references. This means it supports
        ```python
        requirement = FileStructureRequirement()
        requirement.add_directory(requirement)
        ```
        This keeps the two requirements as separate objects so as to not create a reference loop.
        """
        if required:
            self.directories.append(deepcopy(directory))
        else:
            self.optional_directories.append(deepcopy(directory))
        return self

    def add_directories(
        self: Self, directories: Iterable[Self], required: bool = True
    ) -> Self:
        for directory in directories:
            self.add_directory(directory, required)
        return self

    def add_file(self: Self, file: str, required: bool = True) -> Self:
        if required:
            self.files.append(file)
        else:
            self.optional_files.append(file)
        return self

    def add_files(self: Self, files: Iterable[str], required: bool = True) -> Self:
        for file in files:
            self.add_file(file, required)
        return self

    def set_name(self: Self, name: str | None) -> Self:
        self.directory_name = name
        return self

    @property
    def all_files(self: Self) -> list[str]:
        return list(set(self.files) | set(self.optional_files))

    @property
    def all_directories(self: Self) -> list[Self]:
        return list(set(self.directories) | set(self.optional_directories))

    def matches(
        self: Self, walk_args: tuple[Path, list[str], list[str]], depth: int = 1
    ) -> bool:
        """Check if a provided diryath, dirnames, and filenames set matches the requirements"""

        # Unpack Path.walk outputs. Taking this as a tuple simplifies the recursion callsite below
        dirpath, dirnames, filenames = walk_args

        lpad = "#" * depth

        logger.debug("%s Evaluting match for %s", lpad, dirpath)
        logger.debug("%s Against %s", lpad, self)

        # Short circuit check for directory name pattern match
        if self.directory_name and not dirpath.match(self.directory_name):
            logger.debug(
                "%s x Failed match on directory name: Expected: %s, Found: %s",
                lpad,
                self.directory_name,
                dirpath,
            )
            return False

        # Short circuit check for required file patterns
        for pattern in self.files:
            # If all input filenames do not match a pattern, then its a missed pattern, and not a match
            # The failing case is when no files match a pattern, aka all files do not match.
            if all(not fnmatch(filename, pattern) for filename in filenames):
                logger.debug(
                    "%s x Failed match on required file pattern. Required %s, Found: %s, Directory: %s",
                    lpad,
                    pattern,
                    filenames,
                    dirpath,
                )
                return False

        # Recurse into required subdirectory branches (if they exist)
        for branch in self.directories:
            # The failing case is when no directories match the requirement, aka all directories do not match the branch
            if all(
                not branch.matches(next((dirpath / directory).walk()), depth + 1)
                for directory in dirnames
            ):
                logger.debug(
                    "%s x Failed on subdirectory match. Required %s, Found: %s, Directory: %s",
                    lpad,
                    branch,
                    dirnames,
                    dirpath,
                )
                return False

        # Passing all previous checks implies:
        # 1. The directory_name matches or is not a requirement
        # 2. The directory_name_pattern matches or is not a requirement
        # 3. The required files are present
        # 4. The required file patterns are matched
        # 5. The required directories are matched (recursively)
        # In this case, this directory structure meets the requirements!
        logger.info("%s + Matched: %s on %s!", lpad, dirpath, self)
        return True

    def copy(
        self: Self,
        source: Path,
        destination: Path,
        overwrite: bool = False,
        dryrun: bool = False,
    ) -> None:
        """Copy all files and folders from source that match the file requirements patterns to the destionation path"""

        dryrun_pad = "(dryrun) " if dryrun else ""

        if not dryrun:
            destination.mkdir(parents=True, exist_ok=overwrite)

        # Copy all files in this top level that match a required or optional file pattern
        files = (file for file in source.iterdir() if file.is_file())
        for file in files:
            if any(file.match(pattern) for pattern in self.all_files):
                if not dryrun:
                    shutil.copy2(file, destination / file.name)
                logger.debug(
                    "%sCopied %s to %s", dryrun_pad, file, destination / file.name
                )

        # Recurse into any directories at this level that match a required or optional directory pattern
        directories = (
            directory for directory in source.iterdir() if directory.is_dir()
        )
        for directory in directories:
            for branch in self.all_directories:
                if branch.matches(next(directory.walk())):
                    branch.copy(
                        directory,
                        destination / directory.name,
                        overwrite=overwrite,
                        dryrun=dryrun,
                    )

        logger.info("%sFinished copying %s to %s", dryrun_pad, source, destination)


IVER_REQUIREMENTS = FileStructureRequirement(
    directories=[
        FileStructureRequirement(directory_name="Mission", files=["*.misx"]),
        FileStructureRequirement(directory_name="Logs", files=["*.log"]),
    ],
    optional_directories=[
        FileStructureRequirement(directory_name="Sonar", files=["*"]),
        FileStructureRequirement(directory_name="Sensor", files=["*"]),
    ],
)

REMUS_REQUIREMENTS = FileStructureRequirement(
    directories=[
        FileStructureRequirement(
            files=["*State.csv"],
            optional_files=["*FaultLog.txt", "*Faults.txt", "*Battery.csv"],
        )
    ],
    optional_directories=[FileStructureRequirement(files=["*.rmf"])],
    optional_files=["*.csv"],
)
