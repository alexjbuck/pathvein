from typing import Tuple
import fsspec
from fsspec import AbstractFileSystem
from hypothesis import strategies as st

from pathvein import FileStructurePattern


def valid_name_strategy(
    min_size: int = 1, max_size: int = 50
) -> st.SearchStrategy[str]:
    """
    Generate valid filesystem names (no path separators).

    Generates strings that are valid for file/directory names:
    - No forward or backward slashes
    - Non-empty (by default)
    - Printable ASCII characters
    - Not special directory names (., ..)
    """
    return st.text(
        alphabet=st.characters(
            min_codepoint=32,  # Space
            max_codepoint=126,  # Tilde
            blacklist_characters="/\\",  # No path separators
        ),
        min_size=min_size,
        max_size=max_size,
    ).filter(lambda s: s.strip() and s not in (".", ".."))  # No whitespace-only names or special dirs


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
def valid_pattern_base_strategy(draw, max_name_size: int = 50, max_list_size: int = 50):
    """
    Generate valid FileStructurePattern with valid filesystem names.

    Unlike pattern_base_strategy, this only generates patterns with:
    - Valid directory names (no path separators, non-empty)
    - Valid file names (no path separators)
    """
    return FileStructurePattern(
        directory_name=draw(valid_name_strategy(min_size=1, max_size=max_name_size)),
        files=draw(
            st.lists(
                valid_name_strategy(max_size=max_name_size), max_size=max_list_size
            )
        ),
        optional_files=draw(
            st.lists(
                valid_name_strategy(max_size=max_name_size), max_size=max_list_size
            )
        ),
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


@st.composite
def fs_with_pattern(draw) -> Tuple[AbstractFileSystem, FileStructurePattern]:
    f = fsspec.filesystem("memory")
    return (f, draw(pattern_strategy()))
