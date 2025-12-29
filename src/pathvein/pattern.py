"""
Pattern matching implementation for Pathvein.

This module provides the core FileStructurePattern class that enables matching
and copying of file structures based on pattern specifications. It supports both
required and optional components, with a builder pattern for easy construction.
"""

import json
import logging
from time import time
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, List, Set, Tuple
from concurrent.futures import ThreadPoolExecutor, Future, wait

from typing_extensions import Self

from ._path_utils import iterdir, stream_copy
from ._backend import match_pattern, PatternMatcher

logger = logging.getLogger(__name__)


def _none_of(iter: Iterable[bool]) -> bool:
    # Return True if all are False otherwise return False
    return all(not value for value in iter)


@dataclass
class FileStructurePattern:
    """
    A representation of a file structure pattern with required and optional components.

    This class also supports a builder pattern as any intermediate state is also valid.
    """

    directory_name: str = "*"
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
        """Load a FileStructurePattern from a JSON file

        Args:
            json_path: Path to JSON file containing pattern specification

        Returns:
            FileStructurePattern instance

        Raises:
            FileNotFoundError: If json_path does not exist
            json.JSONDecodeError: If file contains invalid JSON
            ValueError: If JSON structure is invalid for pattern specification
        """
        try:
            json_str = json_path.read_text()
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Pattern file not found: {json_path}") from e
        except Exception as e:
            raise ValueError(f"Error reading pattern file {json_path}: {e}") from e
        return cls.from_json(json_str)

    @classmethod
    def from_json(cls, spec_str: str) -> Self:
        """Create a FileStructurePattern from a JSON string

        Args:
            spec_str: JSON string containing pattern specification

        Returns:
            FileStructurePattern instance

        Raises:
            json.JSONDecodeError: If spec_str is not valid JSON
            ValueError: If JSON structure is invalid for pattern specification
        """
        try:
            spec = json.loads(spec_str)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Invalid JSON in pattern specification: {e.msg}", e.doc, e.pos
            ) from e

        if not isinstance(spec, dict):
            raise ValueError(
                f"Pattern specification must be a JSON object, got {type(spec).__name__}"
            )

        try:
            return (
                cls()
                .set_directory_name(spec.get("directory_name", "*"))
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
        except (TypeError, AttributeError) as e:
            raise ValueError(f"Invalid pattern specification structure: {e}") from e

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

    def set_directory_name(self: Self, name: str) -> Self:
        self.directory_name = name
        return self

    @property
    def all_files(self: Self) -> List[str]:
        return list(set(self.files) | set(self.optional_files))

    @property
    def all_directories(self: Self) -> List[Self]:
        return list(set(self.directories) | set(self.optional_directories))

    def parents_of(self: Self, file: Path, parent: Path = Path()) -> Set[Path]:
        """Find all possible parent directories that could contain the given file based on the pattern.

        This method will complete a recursive search through all the required and
        optional files in the pattern through all directory tree branches.

        Each level constructs the pattern for the optional and required files
        to include the parents of the current directory pattern and compares that
        to the full path of the provided file. If the pattern matches then we
        compute the root directory of the pattern that would contain that file by
        evaluating the depth of the pattern and backing off that many layers from
        the input file. That path gets added to a set of possible parent directories.

        Its possible to have multiple possible parent directories at this point of
        evaluation. As a trivial example imagine a pattern with optional files at
        **/a/b/file.txt and **/b/file.txt. When provided an input file of:

        /input/a/b/file.txt it will match on both patterns. The two possible parent
        or root directories are /input and /input/a. Without evaluating the full
        pattern from that root directory we cannot yet be sure if either is actually
        a valid parent/root directory. We only have the context of this single input
        file. From that alone, either directory _could_ be the root with this pattern.
        """
        candidates = set()
        prefix = "**/"
        for file_pattern in self.all_files:
            pattern = prefix + str(parent / file_pattern)
            # UPath.match doesn't seem to work reliably, cast to a Path type explicitly
            # and use its glob-style pattern matching.
            # This turns s3://bucket/prefix into /bucket/prefix so any glob pattern as
            # the only difference is the absence of the s3:/ protocol prefix.
            if Path(file).match(pattern):
                # patterns are ** / <directories> / file
                # so the directory depth is length of parts - 2
                # Minus 1 for the ** and minus 1 for the file
                # The directory depth is the number of "parents" that we need to go up.
                depth = len(Path(pattern).parts) - 2
                candidates.add(file.parents[depth])

        for directory in self.all_directories:
            candidates |= directory.parents_of(file, parent / directory.directory_name)

        return candidates

    def matches(
        self: Self, walk_args: Tuple[Path, List[str], List[str]], depth: int = 1
    ) -> bool:
        """Check if a provided dirpath, dirnames, and filenames set matches the requirements"""

        # Unpack Path.walk outputs. Taking this as a tuple simplifies the recursion callsite below
        dirpath, dirnames, filenames = walk_args

        lpad = "#" * depth

        logger.debug("%s Evaluating match for %s against %s", lpad, dirpath, self)

        # Short circuit check for directory name pattern match
        if self.directory_name and not match_pattern(dirpath.name, self.directory_name):
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
            #
            # NOTE(Performance): match_pattern uses Rust backend with LRU cache for fast matching
            # This means its beneficial to reuse the same pattern multiple times in a row, so it is preferred
            # to first iterate over the patterns, and then iterate over the filenames instead of the other way around.
            if _none_of(match_pattern(filename, pattern) for filename in filenames):
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
            if _none_of(
                branch_pattern.matches(iterdir(dirpath / directory), depth + 1)
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
        start_time = time()

        dryrun_pad = "(dryrun) " if dryrun else ""

        if not dryrun:
            destination.mkdir(parents=True, exist_ok=overwrite)
        # Copy all files in this top level that match a required or optional file pattern
        _, directories, files = iterdir(source)
        # Use PatternMatcher for efficient multi-pattern matching
        file_matcher = PatternMatcher(self.all_files) if self.all_files else None
        for file in files:
            path = source / file
            logger.debug(
                "Checking file against patterns",
                extra={"file": file, "pattern": self.all_files},
            )
            if file_matcher and file_matcher.matches(path.name):
                logger.debug("Found match")
                if not dryrun:
                    logger.debug("Beginning copy")
                    target = destination / path.name
                    stream_copy(path, target)
                    logger.debug(
                        "Copied file",
                        extra={
                            "file": path.as_posix(),
                            "destination": destination / path.name,
                        },
                    )
        # Recurse into any directories at this level that match a required or optional directory pattern
        for directory in directories:
            path = source / directory
            for branch_pattern in self.all_directories:
                if branch_pattern.matches(iterdir(path)):
                    branch_pattern.copy(
                        path,
                        destination / path.name,
                        overwrite=overwrite,
                        dryrun=dryrun,
                    )

        logger.info(
            "%s Directory copied",
            dryrun_pad,
            extra={
                "source": source,
                "destination": destination,
                "duration": time() - start_time,
            },
        )

    def threaded_copy(
        self: Self,
        source: Path,
        destination: Path,
        overwrite: bool = False,
        dryrun: bool = False,
        max_workers: int = 4,
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
        start_time = time()

        futures: Set[Future] = set()
        with ThreadPoolExecutor(
            max_workers=max_workers
        ) as executor:  # Adjust based on your needs

            def recursive_scan(src: Path, dest: Path, pattern: Self = self):
                if not dryrun:
                    dest.mkdir(parents=True, exist_ok=overwrite)
                # Copy all files in this top level that match a required or optional file pattern
                _, directories, files = iterdir(src)
                # Use PatternMatcher for efficient multi-pattern matching
                file_matcher = (
                    PatternMatcher(pattern.all_files) if pattern.all_files else None
                )
                logger.debug(
                    "Beginning copy operation",
                    extra={
                        "source": src,
                        "directories": directories,
                        "files": files,
                        "pattern": pattern,
                    },
                )
                for file in files:
                    path = src / file
                    logger.debug(
                        "Checking file against patterns",
                        extra={"file": path.name, "pattern": pattern.all_files},
                    )
                    if file_matcher and file_matcher.matches(path.name):
                        logger.debug("Found match")
                        if not dryrun:
                            target = dest / path.name
                            logger.debug(
                                "Submitting copy task",
                                extra={"source": path, "destination": target},
                            )
                            future = executor.submit(stream_copy, path, target)
                            futures.add(future)
                # Recurse into any directories at this level that match a required or optional directory pattern
                for directory in directories:
                    path = src / directory
                    for branch_pattern in self.all_directories:
                        if branch_pattern.matches(iterdir(path)):
                            recursive_scan(path, dest / path.name, branch_pattern)

            recursive_scan(source, destination)

            logger.debug("Waiting for futures", extra={"count": len(futures)})
            done, _ = wait(futures)
            for future in done:
                try:
                    future.result()
                except Exception as e:
                    logger.error("Copy operation failed", exc_info=e)

        logger.info(
            "%s Directory copied",
            "(dryrun) " if dryrun else "",
            extra={
                "source": source,
                "destination": destination,
                "duration": time() - start_time,
            },
        )
