from typing import Tuple
import fsspec
from fsspec import AbstractFileSystem
from hypothesis import strategies as st

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


@st.composite
def fs_with_pattern(draw) -> Tuple[AbstractFileSystem, FileStructurePattern]:
    f = fsspec.filesystem("memory")
    return (f, draw(pattern_strategy()))
