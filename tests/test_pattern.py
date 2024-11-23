import copy
import json
from typing import List

from hypothesis import given
from hypothesis import strategies as st
from upath import UPath

from pathvein import FileStructurePattern

from .strategies import pattern_base_strategy, pattern_strategy


@given(pattern_strategy())
def test_create_blank_file_structure_pattern(pattern: FileStructurePattern):
    assert pattern is not None


@given(pattern_strategy(), st.text(), st.integers(), st.floats())
def test_eq_hash_key(pattern, string, int_number, float_number):
    pattern_clone = copy.deepcopy(pattern)
    assert pattern == pattern_clone
    assert pattern != string
    assert pattern != int_number
    assert pattern != float_number


@given(pattern_base_strategy())
def test_base_to_json(pattern: FileStructurePattern):
    expected = f'{{"directory_name": {json.dumps(pattern.directory_name)}, "files": {json.dumps(pattern.files)}, "directories": [], "optional_files": {json.dumps(pattern.optional_files)}, "optional_directories": []}}'
    print(expected)
    assert expected == pattern.to_json()


@given(pattern_strategy())
def test_to_json(pattern: FileStructurePattern):
    pattern_json = pattern.to_json()
    assert isinstance(pattern_json, str)
    assert FileStructurePattern.from_json(pattern_json) == pattern


@given(pattern_strategy())
def test_load_json(pattern: FileStructurePattern):
    pattern_json = pattern.to_json()
    file = UPath("file.config", protocol="memory")
    file.write_text(pattern_json)
    assert pattern == FileStructurePattern.load_json(file)


@given(pattern_strategy())
def test_all_files(pattern: FileStructurePattern):
    all_files = pattern.all_files
    for file in pattern.files:
        assert file in all_files
    for file in pattern.optional_files:
        assert file in all_files
    assert len(all_files) <= len(pattern.files) + len(pattern.optional_files)


@given(pattern_strategy())
def test_all_directories(pattern: FileStructurePattern):
    all_directories = pattern.all_directories
    for directory in pattern.directories:
        assert directory in all_directories
    for directory in pattern.optional_directories:
        assert directory in all_directories
    assert len(all_directories) <= len(pattern.directories) + len(
        pattern.optional_directories
    )


@given(pattern_strategy(), st.text())
def test_set_directory_name(pattern: FileStructurePattern, name: str):
    pattern.set_directory_name(name)
    assert pattern.directory_name == name


@given(pattern_strategy(), pattern_base_strategy())
def test_add_directory(pattern: FileStructurePattern, addition: FileStructurePattern):
    length = len(pattern.directories)
    pattern.add_directory(addition)
    assert len(pattern.directories) == length + 1
    assert addition in pattern.directories

    optional_length = len(pattern.optional_directories)
    pattern.add_directory(addition, is_optional=True)
    assert len(pattern.optional_directories) == optional_length + 1
    assert addition in pattern.optional_directories


@given(pattern_strategy(), st.lists(pattern_base_strategy()))
def test_add_directories(
    pattern: FileStructurePattern, additions: List[FileStructurePattern]
):
    length = len(pattern.directories)
    pattern.add_directories(additions)
    assert len(pattern.directories) == length + len(additions)
    assert all(addition in pattern.directories for addition in additions)

    optional_length = len(pattern.optional_directories)
    pattern.add_directories(additions, is_optional=True)
    assert len(pattern.optional_directories) == optional_length + len(additions)
    assert all(addition in pattern.optional_directories for addition in additions)


@given(pattern_strategy(), st.text())
def test_add_file(pattern: FileStructurePattern, addition: str):
    length = len(pattern.files)
    pattern.add_file(addition)
    assert len(pattern.files) == length + 1
    assert addition in pattern.files

    optional_length = len(pattern.optional_files)
    pattern.add_file(addition, is_optional=True)
    assert len(pattern.optional_files) == optional_length + 1
    assert addition in pattern.optional_files


@given(pattern_strategy(), st.lists(st.text()))
def test_add_files(pattern: FileStructurePattern, additions: List[str]):
    length = len(pattern.files)
    pattern.add_files(additions)
    assert len(pattern.files) == length + len(additions)
    assert all(addition in pattern.files for addition in additions)

    optional_length = len(pattern.optional_files)
    pattern.add_files(additions, is_optional=True)
    assert len(pattern.optional_files) == optional_length + len(additions)
    assert all(addition in pattern.optional_files for addition in additions)
