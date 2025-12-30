# FileStructurePattern

The `FileStructurePattern` class is the core of pathvein's pattern matching system.

::: pathvein.pattern.FileStructurePattern
    options:
      show_root_heading: true
      show_source: true
      members:
        - __init__
        - load_json
        - from_json
        - to_json
        - add_directory
        - add_directories
        - add_file
        - add_files
        - set_directory_name
        - all_files
        - all_directories
        - parents_of
        - matches
        - copy
        - threaded_copy

## Usage Examples

### Creating Patterns

```python
from pathvein import FileStructurePattern

# Constructor
pattern = FileStructurePattern(
    directory_name="experiment_*",
    files=["config.yaml", "data.csv"],
    optional_files=["notes.txt"]
)

# Builder pattern
pattern = (
    FileStructurePattern()
    .set_directory_name("exp_*")
    .add_file("config.yaml")
    .add_files(["data.csv", "results.csv"])
    .add_file("notes.txt", is_optional=True)
)
```

### Nested Patterns

```python
src_pattern = FileStructurePattern(
    directory_name="src",
    files=["__init__.py"]
)

project_pattern = FileStructurePattern(
    directory_name="my_project",
    files=["README.md"],
    directories=[src_pattern]
)
```

### JSON Serialization

```python
from pathlib import Path

# Save
json_str = pattern.to_json()
Path("pattern.json").write_text(json_str)

# Load from file
pattern = FileStructurePattern.load_json(Path("pattern.json"))

# Load from string
pattern = FileStructurePattern.from_json(json_str)
```

### Pattern Matching

```python
from pathlib import Path
from pathvein._path_utils import iterdir

path = Path("data/experiment_001")
dirpath, dirnames, filenames = iterdir(path)

if pattern.matches((dirpath, dirnames, filenames)):
    print("Match!")
```

### Finding Parent Directories

```python
from pathlib import Path

file = Path("data/experiment_001/results.csv")
candidates = pattern.parents_of(file)

for candidate in candidates:
    print(f"Possible root: {candidate}")
```

### Copying with Patterns

```python
from pathlib import Path

# Single-threaded copy
pattern.copy(
    source=Path("data/exp_001"),
    destination=Path("backup/exp_001"),
    overwrite=False,
    dryrun=False
)

# Multi-threaded copy (faster for many small files)
pattern.threaded_copy(
    source=Path("data/exp_001"),
    destination=Path("backup/exp_001"),
    overwrite=False,
    dryrun=False,
    max_workers=4
)
```

## Pattern Components

### directory_name

Glob pattern for the directory name. Default: `"*"` (matches any name)

```python
# Match exact name
pattern = FileStructurePattern(directory_name="src")

# Match with wildcard
pattern = FileStructurePattern(directory_name="experiment_*")

# Match any name
pattern = FileStructurePattern(directory_name="*")
```

### files

List of required file patterns. At least one file must match each pattern.

```python
pattern = FileStructurePattern(
    files=["*.csv", "config.yaml"]
)
# Requires: at least one .csv file AND config.yaml
```

### directories

List of required subdirectory patterns. At least one directory must match each pattern.

```python
pattern = FileStructurePattern(
    directories=[
        FileStructurePattern(directory_name="data"),
        FileStructurePattern(directory_name="models")
    ]
)
# Requires: at least one "data" directory AND at least one "models" directory
```

### optional_files

List of optional file patterns. Not required for a match.

```python
pattern = FileStructurePattern(
    files=["config.yaml"],
    optional_files=["notes.txt", "debug.log"]
)
# Requires config.yaml, but notes.txt and debug.log are optional
```

### optional_directories

List of optional subdirectory patterns. Not required for a match.

```python
pattern = FileStructurePattern(
    directories=[
        FileStructurePattern(directory_name="src")
    ],
    optional_directories=[
        FileStructurePattern(directory_name="docs"),
        FileStructurePattern(directory_name="tests")
    ]
)
# Requires src/, but docs/ and tests/ are optional
```
