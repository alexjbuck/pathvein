# Write test for ../pathvein/pattern.py using pytest

import copy
import json

from hypothesis import given
from hypothesis import strategies as st
from upath import UPath

from pathvein import FileStructurePattern


@st.composite
def pattern_base_strategy(draw, max_name_size: int = 50, max_list_size: int = 50):
    """
    A composite strategy for generating FileStructurePattern instances with no children.
    """
    name = st.text(min_size=0, max_size=max_name_size)
    return FileStructurePattern(
        directory_name=draw(st.one_of(st.none(), name)),
        files=draw(st.lists(name, max_size=max_list_size)),
        optional_files=draw(st.lists(name, max_size=max_list_size)),
    )


@st.composite
def pattern_strategy(
    draw,
    max_list_size: int = 50,
    max_name_size: int = 50,
    max_branches: int = 2,
    max_leaves: int = 30,
):
    """
    A composite strategy for generating FileStructurePattern instances
    """
    name = st.text(min_size=0, max_size=max_name_size)
    name_list = st.lists(name, max_size=max_list_size)
    pattern_strategy = st.recursive(
        pattern_base_strategy(),
        lambda children: st.builds(
            FileStructurePattern,
            directory_name=name,
            files=name_list,
            directories=st.lists(children, min_size=0, max_size=max_branches),
            optional_files=name_list,
            optional_directories=st.lists(children, min_size=0, max_size=max_branches),
        ),
        max_leaves=max_leaves,
    )
    return draw(pattern_strategy)


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
    pattern: FileStructurePattern, additions: list[FileStructurePattern]
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
def test_add_files(pattern: FileStructurePattern, additions: list[str]):
    length = len(pattern.files)
    pattern.add_files(additions)
    assert len(pattern.files) == length + len(additions)
    assert all(addition in pattern.files for addition in additions)

    optional_length = len(pattern.optional_files)
    pattern.add_files(additions, is_optional=True)
    assert len(pattern.optional_files) == optional_length + len(additions)
    assert all(addition in pattern.optional_files for addition in additions)
