import logging
from pathlib import Path
from typing import List

from hypothesis import given
from hypothesis_fspaths import fspaths
from upath import UPath

from pathvein.lib import (
    ScanResult,
    ShuffleInput,
    ShuffleResult,
    scan,
    shuffle,
    shuffle_to,
    shuffle_with,
)
from pathvein.pattern import FileStructurePattern
from tests import isolated_memory_filesystem
from tests.strategies import pattern_strategy


@given(fspaths(), fspaths(), pattern_strategy())
def test_tuples(source: Path, dest: Path, pattern: FileStructurePattern):
    scan_result = ScanResult(source, pattern)
    assert scan_result is not None
    assert isinstance(scan_result, tuple)
    assert scan_result.source == source
    assert scan_result.pattern == pattern

    shuffle_input = ShuffleInput(source, dest, pattern)
    assert shuffle_input is not None
    assert isinstance(shuffle_input, tuple)
    assert shuffle_input.source == source
    assert shuffle_input.destination == dest
    assert shuffle_input.pattern == pattern

    shuffle_result = ShuffleResult(source, dest, pattern)
    assert shuffle_result is not None
    assert isinstance(shuffle_result, tuple)
    assert shuffle_result.source == source
    assert shuffle_result.destination == dest
    assert shuffle_result.pattern == pattern


def test_scan_simple(caplog):
    with isolated_memory_filesystem():
        file = UPath("/dir/file.txt", protocol="memory")
        match = file.parent
        file.touch()
        pattern = FileStructurePattern("dir", files=["file.txt"])
        root = UPath("/", protocol="memory")
        with caplog.at_level(logging.DEBUG):
            result = scan(root, [pattern])
        assert isinstance(result, set)
        assert all(isinstance(r, ScanResult) for r in result)
        assert len(result) == 1
        assert result == {ScanResult(match, pattern)}


def test_scan_local_fs():
    filename = "strategies.py"
    dirname = "tests"
    pycache = FileStructurePattern(
        "__pycache__", files=["*.pyc"], optional_files=["__init__.*"]
    )
    pattern = FileStructurePattern(
        dirname,
        files=[filename],
        optional_files=["test_lib.py"],
        optional_directories=[pycache],
    )
    match = Path(dirname).resolve()
    result = scan(match, [pattern])
    assert isinstance(result, set)
    assert all(isinstance(r, ScanResult) for r in result)
    assert len(result) == 1
    assert result == {ScanResult(match, pattern)}


def test_shuffle_simple():
    with isolated_memory_filesystem():
        filename = "file.txt"
        dirname = "dir"
        destprefix = "dest"
        root = UPath("/", protocol="memory")
        source = root / dirname
        file = root / dirname / filename
        dest = root / destprefix / dirname
        dir_after_copy = root / destprefix / dirname
        file_after_copy = root / destprefix / dirname / filename

        # Define the search pattern to match the source file/directory
        pattern = FileStructurePattern("dir", files=["file.txt"])

        # Ensure the source file/directories exist in the memory filesystem
        source.mkdir()
        file.write_text("Hello World!")

        # Assert that the file does not yet exist in the destination
        assert file.exists()
        assert file_after_copy.exists() is False
        assert dest.exists() is False

        input: ShuffleInput = ShuffleInput(source, dest, pattern)
        result = shuffle({input})

        # Validate the result
        assert isinstance(result, List)
        assert all(isinstance(r, ShuffleResult) for r in result)
        assert len(result) == 1
        assert result == [ShuffleResult(source, dest, pattern)]
        assert dir_after_copy.exists()
        assert dir_after_copy.is_dir()
        assert file_after_copy.exists()
        assert file_after_copy.is_file()


def test_shuffle_exception_file_exists(caplog):
    with isolated_memory_filesystem():
        # Instantiate the source file and directory
        filename = "file.txt"
        dirname = "dir"
        destprefix = "dest"
        root = UPath("/", protocol="memory")
        source = root / dirname
        filepath = root / dirname / filename
        dest = root / destprefix / dirname
        dir_after_copy = root / destprefix / dirname
        file_after_copy = root / destprefix / dirname / filename

        # Create the pattern to match the source file/directory so it will match
        pattern = FileStructurePattern(dirname, files=[filename])

        # Ensure the files and paths exist in the memory filesystem
        # /dir
        # /dir/file.txt
        source.mkdir()
        filepath.touch()

        # Instantiate the a directory where the source will be copied to, this should cause an exception.
        # The exception is captured by shuffle with an error log and the directory is skipped.
        # /dest/dir
        dest.mkdir()

        # Assert that the file does not yet exist in the destination
        assert not file_after_copy.exists()
        assert dest.exists()

        # Set the log capture caplog to Error level
        with caplog.at_level(logging.DEBUG):
            # Prepare the input and call shuffle
            input: ShuffleInput = ShuffleInput(source, dest, pattern)
            result = shuffle({input}, overwrite=False)

        # Validate result

        assert (
            "pathvein.lib",
            logging.ERROR,
            f"Destination folder already exists: {dest}. Skipping: {source.name}",
        ) in caplog.record_tuples
        assert (
            "pathvein.lib",
            logging.DEBUG,
            f"{source} copied to {dest}",
        ) not in caplog.record_tuples
        assert isinstance(result, List)
        assert len(result) == 0
        assert file_after_copy.exists() is False
        # dir_after_copy should exist, as this is why the copy was aborted
        assert dir_after_copy.exists()


def test_shuffle_with():
    with isolated_memory_filesystem():
        filename = "file.txt"
        dirname = "dir"
        destprefix = "dest"
        root = UPath("/", protocol="memory")
        source = root / dirname
        file = root / dirname / filename
        dest = root / destprefix / dirname
        dir_after_copy = root / destprefix / dirname
        file_after_copy = root / destprefix / dirname / filename

        # Define the search pattern to match the source file/directory
        pattern = FileStructurePattern("dir", files=["file.txt"])

        # Ensure the source file/directories exist in the memory filesystem
        source.mkdir()
        file.write_text("Hello World!")

        # Assert that the file does not yet exist in the destination
        assert file.exists()
        assert file_after_copy.exists() is False
        assert dest.exists() is False

        input: ScanResult = ScanResult(source, pattern)
        result = shuffle_with({input}, lambda _: dest)

        # Validate the result
        assert isinstance(result, List)
        assert all(isinstance(r, ShuffleResult) for r in result)
        assert len(result) == 1
        assert result == [ShuffleResult(source, dest, pattern)]
        assert dir_after_copy.exists()
        assert dir_after_copy.is_dir()
        assert file_after_copy.exists()
        assert file_after_copy.is_file()


def test_shuffle_to():
    with isolated_memory_filesystem():
        filename = "file.txt"
        dirname = "dir"
        destprefix = "dest"
        root = UPath("/", protocol="memory")
        source = root / dirname
        file = root / dirname / filename
        dest = root / destprefix / dirname
        dir_after_copy = root / destprefix / dirname
        file_after_copy = root / destprefix / dirname / filename

        # Define the search pattern to match the source file/directory
        pattern = FileStructurePattern("dir", files=["file.txt"])

        # Ensure the source file/directories exist in the memory filesystem
        source.mkdir()
        file.write_text("Hello World!")

        # Assert that the file does not yet exist in the destination
        assert file.exists()
        assert file_after_copy.exists() is False
        assert dest.exists() is False

        input: ScanResult = ScanResult(source, pattern)
        result = shuffle_to({input}, root / destprefix)

        # Validate the result
        assert isinstance(result, List)
        assert all(isinstance(r, ShuffleResult) for r in result)
        assert len(result) == 1
        assert result == [ShuffleResult(source, dest, pattern)]
        assert dir_after_copy.exists()
        assert dir_after_copy.is_dir()
        assert file_after_copy.exists()
        assert file_after_copy.is_file()
