# Core Functions

This page documents the main functions in pathvein.

## scan

::: pathvein.lib.scan
    options:
      show_root_heading: true
      show_source: true

## assess

::: pathvein.lib.assess
    options:
      show_root_heading: true
      show_source: true

## shuffle

::: pathvein.lib.shuffle
    options:
      show_root_heading: true
      show_source: true

## shuffle_to

::: pathvein.lib.shuffle_to
    options:
      show_root_heading: true
      show_source: true

## shuffle_with

::: pathvein.lib.shuffle_with
    options:
      show_root_heading: true
      show_source: true

## Usage Examples

### Scanning

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

print(f"Found {len(matches)} matches")
```

### Assessing

```python
from pathlib import Path
from pathvein import assess, FileStructurePattern

patterns = [
    FileStructurePattern(directory_name="exp_*", files=["*.csv"]),
    FileStructurePattern(directory_name="backup_*", files=["*.csv"])
]

file = Path("data/exp_001/results.csv")

for result in assess(file, patterns):
    print(f"Pattern: {result.pattern.directory_name}")
    print(f"Root: {result.source}")
```

### Shuffling

```python
from pathlib import Path
from pathvein import scan, shuffle_to, FileStructurePattern

# Find matches
pattern = FileStructurePattern(files=["*.csv"])
matches = scan(Path("data"), [pattern])

# Copy to destination
results = shuffle_to(
    matches=matches,
    destination=Path("organized"),
    overwrite=False,
    dryrun=False
)

print(f"Copied {len(results)} directories")
```
