"""
Pathvein: Rich and deep file structure pattern matching.

This package provides tools for scanning directories and matching file structures
against defined patterns. It supports both required and optional file/directory
matching, with powerful pattern matching capabilities.
"""

from pathvein.pattern import FileStructurePattern as FileStructurePattern
from pathvein.lib import scan as scan
from pathvein.lib import shuffle as shuffle
from pathvein.lib import shuffle_to as shuffle_to
from pathvein.lib import shuffle_with as shuffle_with
from pathvein.lib import assess as assess
from pathvein.lib import ShuffleInput as ShuffleInput
from pathvein.lib import ShuffleResult as ShuffleResult
from pathvein.lib import ScanResult as ScanResult

__all__ = [
    "FileStructurePattern",
    "scan",
    "shuffle",
    "shuffle_to",
    "shuffle_with",
    "assess",
    "ShuffleInput",
    "ShuffleResult",
    "ScanResult",
]
