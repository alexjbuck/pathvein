import json
import logging
from copy import deepcopy
from dataclasses import dataclass, field
from fnmatch import fnmatch
from pathlib import Path
from typing import Any, Iterable, List, Optional, Tuple

from typing_extensions import Self

from ._path_utils import stream_copy, walk

logger = logging.getLogger(__name__)


def none_of(iter: Iterable[bool]) -> bool:
    # Return True if all are False otherwise return False
    return all(not value for value in iter)


def next_step(path: Path) -> Tuple[Path, List[str], List[str]]:
    """Get the next tuple from a directory walk iterator."""
    return next(walk(path))


@dataclass
class FileStructurePattern:
    """
    A representation of a file structure pattern with required and optional components.

    This class also supports a builder pattern as any intermediate state is also valid.
    """

    directory_name: Optional[str] = None
    files: List[str] = field(default_factory=list)
    directories: List[Self] = field(default_factory=list)
    optional_files: List[str] = field(default_factory=list)
    optional_directories: List[Self] = field(default_factory=list)

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
        if isinstance(other, FileStructurePattern):
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
            .set_directory_name(spec.get("directory_name"))
            .add_files(spec.get("files", []))
            .add_files(spec.get("optional_files", []), is_optional=True)
            .add_directories(
                (
                    cls.from_json(subdirectory_spec)
                    for subdirectory_spec in spec.get("directories", [])
                )
            )
            .add_directories(
                (
                    cls.from_json(subdirectory_spec)
                    for subdirectory_spec in spec.get("optional_directories", [])
                ),
                is_optional=True,
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

    def add_directory(self: Self, directory: Self, is_optional: bool = False) -> Self:
        """
        Add a FileStructureRequirement entry to the (optional) directory list

        This method uses deepcopy to prevent recursive references. This means it supports
        ```python
        requirement = FileStructureRequirement()
        requirement.add_directory(requirement)
        ```
        This keeps the two requirements as separate objects so as to not create a reference loop.
        """
        if is_optional:
            self.optional_directories.append(deepcopy(directory))
        else:
            self.directories.append(deepcopy(directory))
        return self

    def add_directories(
        self: Self, directories: Iterable[Self], is_optional: bool = False
    ) -> Self:
        for directory in directories:
            self.add_directory(directory, is_optional)
        return self

    def add_file(self: Self, file: str, is_optional: bool = False) -> Self:
        if is_optional:
            self.optional_files.append(file)
        else:
            self.files.append(file)
        return self

    def add_files(self: Self, files: Iterable[str], is_optional: bool = False) -> Self:
        for file in files:
            self.add_file(file, is_optional)
        return self

    def set_directory_name(self: Self, name: Optional[str]) -> Self:
        self.directory_name = name
        return self

    @property
    def all_files(self: Self) -> List[str]:
        return list(set(self.files) | set(self.optional_files))

    @property
    def all_directories(self: Self) -> List[Self]:
        return list(set(self.directories) | set(self.optional_directories))

    def matches(
        self: Self, walk_args: Tuple[Path, List[str], List[str]], depth: int = 1
    ) -> bool:
        """Check if a provided dirpath, dirnames, and filenames set matches the requirements"""

        # Unpack Path.walk outputs. Taking this as a tuple simplifies the recursion callsite below
        dirpath, dirnames, filenames = walk_args

        lpad = "#" * depth

        logger.debug("%s Evaluting match for %s against %s", lpad, dirpath, self)

        # Short circuit check for directory name pattern match
        if self.directory_name and not fnmatch(dirpath.name, self.directory_name):
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
            if none_of(fnmatch(filename, pattern) for filename in filenames):
                logger.debug(
                    "%s x Failed match on required file pattern. Required %s, Found: %s, Directory: %s",
                    lpad,
                    pattern,
                    filenames,
                    dirpath,
                )
                return False

        # NOTE: This could be written as a double nested list comprehension that includes the
        # self.directories iterations as well, but its rather confusing to read, leaving that
        # as an outer for-loop is easier to read.
        #
        # Recurse into required subdirectory branches (if they exist)
        for branch_pattern in self.directories:
            # Evaluate if any actual directories from dirnames match the given pattern
            if none_of(
                branch_pattern.matches(next_step(dirpath / directory), depth + 1)
                for directory in dirnames
            ):
                logger.debug(
                    "%s x Failed on subdirectory match. Required %s, Found: %s, Directory: %s",
                    lpad,
                    branch_pattern,
                    dirnames,
                    dirpath,
                )
                return False

        # Passing all previous checks implies:
        # 1. The directory_name matches or is not a requirement
        # 2. The required file patterns are matched
        # 3. The required directories are matched (recursively)
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
        """Copy all files and folders from inside source that match the file requirements patterns into the destination path.

        Before:
        Source:
        source_dir/
            file1.txt
            nested/
                file2.txt

        Destination:
        dest_dir/

        After:
        Source:
        source_dir/
            file1.txt
            nested/
                file2.txt

        Destination:
        dest_dir/
        source_dir/
            file1.txt
            nested/
                file2.txt
        """

        dryrun_pad = "(dryrun) " if dryrun else ""

        if not dryrun:
            destination.mkdir(parents=True, exist_ok=overwrite)
        logger.debug("%s %s", source, destination)
        # Copy all files in this top level that match a required or optional file pattern
        files = (file for file in source.iterdir() if file.is_file())
        for file in files:
            logger.debug("Checking file %s against %s", file, self.all_files)
            logger.debug(
                "matches: %s",
                [fnmatch(file.name, pattern) for pattern in self.all_files],
            )
            if any(fnmatch(file.name, pattern) for pattern in self.all_files):
                logger.debug("Matched!")
                if not dryrun:
                    logger.debug("Beginning copy...")
                    target = destination / file.name
                    stream_copy(file, target)
                    logger.debug(
                        "%sCopied %s to %s", dryrun_pad, file, destination / file.name
                    )

        # Recurse into any directories at this level that match a required or optional directory pattern
        paths = (path for path in source.iterdir() if path.is_dir())
        for path in paths:
            for branch_pattern in self.all_directories:
                if branch_pattern.matches(next_step(path)):
                    branch_pattern.copy(
                        path,
                        destination / path.name,
                        overwrite=overwrite,
                        dryrun=dryrun,
                    )

        logger.info("%sFinished copying %s to %s", dryrun_pad, source, destination)
