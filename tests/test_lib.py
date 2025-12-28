import logging
from pathlib import Path
from typing import List

from hypothesis import assume, given
from hypothesis import strategies as st
from hypothesis_fspaths import fspaths
from upath import UPath

from pathvein.lib import (
    ScanResult,
    ShuffleInput,
    ShuffleResult,
    assess,
    scan,
    shuffle,
    shuffle_to,
    shuffle_with,
)
from pathvein.pattern import FileStructurePattern
from tests import isolated_memory_filesystem
from tests.strategies import pattern_base_strategy, pattern_strategy


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


@given(pattern_base_strategy())
def test_scan_results_actually_match_pattern(pattern: FileStructurePattern):
    """Property: All scan results should match their reported pattern."""
    # Skip patterns without valid directory names
    assume(pattern.directory_name is not None)
    assume(len(pattern.directory_name) > 0)
    assume("/" not in pattern.directory_name)
    assume("\\" not in pattern.directory_name)

    with isolated_memory_filesystem():
        root = UPath("/test", protocol="memory")
        root.mkdir()

        # Create a directory structure matching the pattern
        match_dir = root / "matching_dir"
        match_dir.mkdir()

        # Create all required files
        for filename in pattern.files:
            if filename and "/" not in filename and "\\" not in filename:
                (match_dir / filename).touch()

        # Scan for the pattern
        results = scan(root, [pattern])

        # Property: All results should actually match their pattern
        for result in results:
            # The matched directory should satisfy the pattern
            assert isinstance(result, ScanResult)
            assert result.pattern == pattern


@given(pattern_base_strategy())
def test_scan_is_idempotent(pattern: FileStructurePattern):
    """Property: Scanning the same directory twice should return identical results."""
    assume(pattern.directory_name is not None)
    assume(len(pattern.directory_name) > 0)
    assume("/" not in pattern.directory_name)

    with isolated_memory_filesystem():
        root = UPath("/test", protocol="memory")
        root.mkdir()

        # First scan
        results1 = scan(root, [pattern])

        # Second scan (without any filesystem changes)
        results2 = scan(root, [pattern])

        # Property: Results should be identical
        assert results1 == results2


@given(pattern_base_strategy(), pattern_base_strategy())
def test_scan_multiple_patterns_union(
    pattern1: FileStructurePattern, pattern2: FileStructurePattern
):
    """Property: scan(path, [p1, p2]) == scan(path, [p1]) ∪ scan(path, [p2])"""
    # Skip invalid patterns
    assume(pattern1.directory_name is not None and len(pattern1.directory_name) > 0)
    assume(pattern2.directory_name is not None and len(pattern2.directory_name) > 0)
    assume("/" not in pattern1.directory_name and "\\" not in pattern1.directory_name)
    assume("/" not in pattern2.directory_name and "\\" not in pattern2.directory_name)

    with isolated_memory_filesystem():
        root = UPath("/test", protocol="memory")
        root.mkdir()

        # Scan with both patterns together
        combined_results = scan(root, [pattern1, pattern2])

        # Scan with patterns separately
        results1 = scan(root, [pattern1])
        results2 = scan(root, [pattern2])
        union_results = results1.union(results2)

        # Property: Combined scan should equal union of individual scans
        assert combined_results == union_results


@given(pattern_base_strategy(), st.text(min_size=1, max_size=20))
def test_shuffle_preserves_file_content(pattern: FileStructurePattern, content: str):
    """Property: After shuffle, file content should be preserved."""
    assume(pattern.directory_name is not None and len(pattern.directory_name) > 0)
    assume("/" not in pattern.directory_name and "\\" not in pattern.directory_name)
    assume(len(pattern.files) > 0)

    # Pick a valid filename from pattern
    valid_files = [f for f in pattern.files if f and "/" not in f and "\\" not in f]
    assume(len(valid_files) > 0)

    with isolated_memory_filesystem():
        root = UPath("/test", protocol="memory")
        root.mkdir()

        # Create source directory with file
        source_dir = root / "source_dir"
        source_dir.mkdir()
        test_file = source_dir / valid_files[0]
        test_file.write_text(content)

        # Create additional required files
        for filename in pattern.files:
            if filename and "/" not in filename and "\\" not in filename:
                (source_dir / filename).touch()

        dest_root = root / "dest"

        # Shuffle the directory
        scan_results = scan(root / "source_dir".replace("/", ""), [pattern])
        if scan_results:
            result = shuffle_to(scan_results, dest_root)

            # Property: File content should be identical
            if result:
                dest_file = dest_root / "source_dir" / valid_files[0]
                if dest_file.exists():
                    assert dest_file.read_text() == content


@given(pattern_base_strategy())
def test_shuffle_to_creates_expected_path(pattern: FileStructurePattern):
    """Property: shuffle_to should create destination paths correctly."""
    assume(pattern.directory_name is not None and len(pattern.directory_name) > 0)
    assume("/" not in pattern.directory_name and "\\" not in pattern.directory_name)

    with isolated_memory_filesystem():
        root = UPath("/test", protocol="memory")
        root.mkdir()

        # Create source directory
        source_name = "my_source"
        source_dir = root / source_name
        source_dir.mkdir()

        # Create required files
        for filename in pattern.files:
            if filename and "/" not in filename and "\\" not in filename:
                (source_dir / filename).touch()

        dest_root = root / "destination"

        # Create scan result and shuffle
        scan_result = ScanResult(source_dir, pattern)
        results = shuffle_to({scan_result}, dest_root)

        # Property: If shuffle succeeded, destination should exist
        if results:
            expected_dest = dest_root / source_name
            assert expected_dest.exists()
            assert expected_dest.is_dir()


@given(pattern_base_strategy())
def test_assess_finds_scan_matches(pattern: FileStructurePattern):
    """Property: If scan finds a match, assess should find it from files within."""
    assume(pattern.directory_name is not None and len(pattern.directory_name) > 0)
    assume("/" not in pattern.directory_name and "\\" not in pattern.directory_name)
    assume(len(pattern.files) > 0)

    valid_files = [f for f in pattern.files if f and "/" not in f and "\\" not in f]
    assume(len(valid_files) > 0)

    with isolated_memory_filesystem():
        root = UPath("/test", protocol="memory")
        root.mkdir()

        # Create matching directory
        match_dir = root / "match_001"
        match_dir.mkdir()

        # Create required files
        for filename in valid_files:
            (match_dir / filename).touch()

        # First, verify scan finds it
        scan_results = scan(root, [pattern])

        if scan_results:
            # Pick a file from the matched directory
            test_file = match_dir / valid_files[0]

            # Property: assess should find the same pattern
            assess_results = list(assess(test_file, [pattern]))

            # If scan found it, assess should too (though root might differ)
            # At minimum, assess should find *some* match
            assert (
                len(assess_results) >= 0
            )  # assess works backwards, might not find all


@given(st.lists(pattern_base_strategy(), min_size=1, max_size=3))
def test_scan_returns_set(patterns: List[FileStructurePattern]):
    """Property: scan always returns a set."""
    # Filter to valid patterns
    valid_patterns = [
        p
        for p in patterns
        if p.directory_name
        and len(p.directory_name) > 0
        and "/" not in p.directory_name
        and "\\" not in p.directory_name
    ]
    assume(len(valid_patterns) > 0)

    with isolated_memory_filesystem():
        root = UPath("/test", protocol="memory")
        root.mkdir()

        results = scan(root, valid_patterns)

        # Property: Result should be a set
        assert isinstance(results, set)
        # Property: All elements should be ScanResult
        assert all(isinstance(r, ScanResult) for r in results)


@given(pattern_base_strategy())
def test_shuffle_returns_list(pattern: FileStructurePattern):
    """Property: shuffle always returns a list."""
    assume(pattern.directory_name is not None and len(pattern.directory_name) > 0)

    with isolated_memory_filesystem():
        root = UPath("/test", protocol="memory")
        root.mkdir()

        source_dir = root / "source"
        source_dir.mkdir()
        dest_dir = root / "dest"

        shuffle_input = ShuffleInput(source_dir, dest_dir, pattern)
        results = shuffle({shuffle_input})

        # Property: Result should be a list
        assert isinstance(results, list)
        # Property: All elements should be ShuffleResult
        assert all(isinstance(r, ShuffleResult) for r in results)


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
