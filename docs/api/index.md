# API Reference

Welcome to the Pathvein API reference documentation.

## Overview

Pathvein's API is organized into several modules:

- **[Core Functions](functions.md)**: Main functions like `scan()`, `shuffle()`, `assess()`
- **[FileStructurePattern](pattern.md)**: Pattern definition and matching
- **[Data Types](types.md)**: Named tuples like `ScanResult`, `ShuffleInput`, `ShuffleResult`
- **[Backend](backend.md)**: Backend information and utilities

## Quick Reference

### Scanning

```python
from pathvein import scan, assess

# Scan directory for patterns
matches = scan(source, patterns)

# Assess which pattern a file belongs to
results = assess(file, patterns)
```

### Shuffling

```python
from pathvein import shuffle, shuffle_to, shuffle_with

# Copy to single destination
shuffle_to(matches, destination)

# Copy with custom logic
shuffle_with(matches, destination_fn)

# Full control
shuffle(shuffle_def)
```

### Patterns

```python
from pathvein import FileStructurePattern

# Create pattern
pattern = FileStructurePattern(
    directory_name="*",
    files=["*.csv"],
    directories=[nested_pattern]
)

# Load from JSON
pattern = FileStructurePattern.load_json(path)

# Check match
if pattern.matches((dirpath, dirnames, filenames)):
    print("Matched!")
```

## Type Annotations

Pathvein is fully type-annotated. Use with mypy or other type checkers:

```python
from pathlib import Path
from typing import Set
from pathvein import scan, FileStructurePattern, ScanResult

def find_matches(root: Path, pattern: FileStructurePattern) -> Set[ScanResult]:
    return scan(root, [pattern])
```

## Import Reference

All public APIs are exported from the top-level package:

```python
from pathvein import (
    # Functions
    scan,
    assess,
    shuffle,
    shuffle_to,
    shuffle_with,
    get_backend_info,

    # Classes
    FileStructurePattern,

    # Types
    ScanResult,
    ShuffleInput,
    ShuffleResult,
)
```
