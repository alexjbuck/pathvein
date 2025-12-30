# Scanning Directories

The `scan()` function recursively searches directories to find structures that match your patterns.

## Basic Scanning

```python
from pathlib import Path
from pathvein import scan, FileStructurePattern

pattern = FileStructurePattern(
    directory_name="experiment_*",
    files=["data.csv"]
)

matches = scan(
    source=Path("data"),
    patterns=[pattern]
)

for match in matches:
    print(f"Found: {match.source}")
```

## Return Value

`scan()` returns a `Set[ScanResult]`, where each `ScanResult` is a named tuple with:

- `source: Path` - The directory that matched
- `pattern: FileStructurePattern` - Which pattern it matched

```python
from pathvein import ScanResult

for match in matches:
    print(f"Directory: {match.source}")
    print(f"Pattern: {match.pattern.directory_name}")
```

## Multiple Patterns

You can search for multiple patterns simultaneously:

```python
python_project = FileStructurePattern(
    files=["pyproject.toml", "setup.py"]
)

rust_project = FileStructurePattern(
    files=["Cargo.toml"]
)

matches = scan(
    source=Path("projects"),
    patterns=[python_project, rust_project]
)

# Each match tells you which pattern it matched
for match in matches:
    if match.pattern == python_project:
        print(f"Python project: {match.source}")
    else:
        print(f"Rust project: {match.source}")
```

## Performance

### Rust Backend

By default, `scan()` uses the Rust backend for local filesystems, providing 5-10x faster directory traversal:

```python
# Check which backend is active
from pathvein import get_backend_info
print(get_backend_info())  # 'rust' or 'python'
```

### Cloud Storage

For cloud storage paths (S3, GCS, etc.), pathvein automatically uses the Python backend with fsspec:

```python
from upath import UPath

# Automatically uses Python backend for S3
matches = scan(
    source=UPath("s3://my-bucket/data/"),
    patterns=[pattern]
)
```

Install S3 support with:

```shell
pip install 'pathvein[s3]'
```

### Caching

Pathvein caches directory listings internally, which dramatically improves performance for network filesystems or repeated scans:

- Local filesystems: ~2x speedup from caching
- Network filesystems: ~100x+ speedup from caching

The cache is thread-safe and automatically managed.

## Filtering Results

Since `scan()` returns a set, you can use standard Python set operations:

```python
# Filter by directory name
matched_2023 = {m for m in matches if "2023" in m.source.name}

# Filter by pattern
python_matches = {m for m in matches if m.pattern == python_project}

# Get just the paths
paths = {m.source for m in matches}
```

## Working with Results

### Counting Matches

```python
print(f"Found {len(matches)} matching directories")
```

### Grouping by Pattern

```python
from collections import defaultdict

by_pattern = defaultdict(list)
for match in matches:
    by_pattern[match.pattern].append(match.source)

for pattern, paths in by_pattern.items():
    print(f"Pattern {pattern.directory_name}: {len(paths)} matches")
```

### Sorting Results

```python
# Sort by path name
sorted_matches = sorted(matches, key=lambda m: m.source.name)

# Sort by modification time
sorted_matches = sorted(matches, key=lambda m: m.source.stat().st_mtime)
```

## Advanced: The assess() Function

While `scan()` searches directories top-down, `assess()` works backwards from a file to find which patterns it belongs to:

```python
from pathlib import Path
from pathvein import assess, FileStructurePattern

patterns = [
    FileStructurePattern(
        directory_name="experiment_*",
        files=["data.csv", "results.csv"]
    ),
    FileStructurePattern(
        directory_name="backup_*",
        files=["*.csv"]
    )
]

# Given a file, find which pattern it belongs to
file = Path("data/experiment_001/results.csv")

for result in assess(file, patterns):
    print(f"File belongs to pattern: {result.pattern.directory_name}")
    print(f"Pattern root: {result.source}")
```

### Use Cases for assess()

**Validation**: Check if a file is in the right place

```python
file = Path("data/experiment_001/results.csv")
results = list(assess(file, [experiment_pattern]))

if results:
    print(f"✓ File is in valid experiment directory: {results[0].source}")
else:
    print("✗ File is not in a valid experiment directory")
```

**Discovery**: Find the root directory of a pattern

```python
# You have a file deep in the structure
deep_file = Path("projects/myapp/src/lib/utils/helpers.py")

# Find the project root
for result in assess(deep_file, [python_project_pattern]):
    project_root = result.source
    print(f"Project root: {project_root}")
```

**Reverse Engineering**: Determine file organization

```python
unknown_file = Path("data/some_directory/output.csv")

for result in assess(unknown_file, known_patterns):
    print(f"This file follows the '{result.pattern.directory_name}' pattern")
```

## Examples

### Find All Python Projects

```python
from pathlib import Path
from pathvein import scan, FileStructurePattern

python_pattern = FileStructurePattern(
    files=["pyproject.toml"],
    directories=[
        FileStructurePattern(
            directory_name="src",
            files=["*.py"]
        )
    ]
)

matches = scan(
    source=Path("~/projects").expanduser(),
    patterns=[python_pattern]
)

print(f"Found {len(matches)} Python projects:")
for match in matches:
    print(f"  {match.source}")
```

### Find Incomplete Experiments

```python
complete_pattern = FileStructurePattern(
    directory_name="exp_*",
    files=["config.json", "results.csv", "summary.txt"]
)

incomplete_pattern = FileStructurePattern(
    directory_name="exp_*",
    files=["config.json"],
    optional_files=["results.csv", "summary.txt"]
)

complete = scan(Path("experiments"), [complete_pattern])
all_exps = scan(Path("experiments"), [incomplete_pattern])

incomplete = all_exps - complete

print(f"Complete experiments: {len(complete)}")
print(f"Incomplete experiments: {len(incomplete)}")
for exp in incomplete:
    print(f"  {exp.source.name}")
```

### Find Projects by Technology

```python
patterns = {
    "Python": FileStructurePattern(files=["pyproject.toml"]),
    "Rust": FileStructurePattern(files=["Cargo.toml"]),
    "Node.js": FileStructurePattern(files=["package.json"]),
    "Go": FileStructurePattern(files=["go.mod"])
}

for tech, pattern in patterns.items():
    matches = scan(Path("projects"), [pattern])
    print(f"{tech} projects: {len(matches)}")
```

## Best Practices

### Start Specific, Then Broaden

Start with specific patterns and loosen them if needed:

```python
# Start specific
pattern = FileStructurePattern(
    directory_name="experiment_[0-9][0-9][0-9]",
    files=["config.yaml", "results.csv"]
)

# If too restrictive, make optional
pattern = FileStructurePattern(
    directory_name="experiment_*",
    files=["config.yaml"],
    optional_files=["results.csv"]  # May not exist yet
)
```

### Handle Empty Results

Always check if you got matches:

```python
matches = scan(source, patterns)

if not matches:
    print("No matches found. Check your patterns and source directory.")
else:
    print(f"Found {len(matches)} matches")
```

### Use Logging for Debugging

Enable logging to see what pathvein is doing:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
matches = scan(source, patterns)
```
