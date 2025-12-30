# Data Types

Pathvein uses named tuples for data transfer objects.

## ScanResult

::: pathvein.lib.ScanResult
    options:
      show_root_heading: true
      show_source: true

Returned by `scan()` and `assess()` functions.

### Fields

- `source: Path` - The directory that matched the pattern
- `pattern: FileStructurePattern` - The pattern that was matched

### Usage

```python
from pathvein import scan, FileStructurePattern
from pathlib import Path

pattern = FileStructurePattern(files=["*.csv"])
matches = scan(Path("data"), [pattern])

for match in matches:
    print(f"Directory: {match.source}")
    print(f"Pattern: {match.pattern.directory_name}")
```

## ShuffleInput

::: pathvein.lib.ShuffleInput
    options:
      show_root_heading: true
      show_source: true

Input to the `shuffle()` function.

### Fields

- `source: Path` - Source directory to copy from
- `destination: Path` - Destination directory to copy to
- `pattern: FileStructurePattern` - Pattern defining what to copy

### Usage

```python
from pathvein import shuffle, ShuffleInput, FileStructurePattern
from pathlib import Path

pattern = FileStructurePattern(files=["*.csv"])

shuffle_def = [
    ShuffleInput(
        source=Path("data/exp_001"),
        destination=Path("backup/exp_001"),
        pattern=pattern
    )
]

results = shuffle(shuffle_def)
```

### Creating from ScanResults

```python
from pathvein import scan, shuffle, ShuffleInput

matches = scan(Path("data"), [pattern])

shuffle_def = [
    ShuffleInput(
        source=match.source,
        destination=Path("backup") / match.source.name,
        pattern=match.pattern
    )
    for match in matches
]

results = shuffle(shuffle_def)
```

## ShuffleResult

::: pathvein.lib.ShuffleResult
    options:
      show_root_heading: true
      show_source: true

Returned by `shuffle()`, `shuffle_to()`, and `shuffle_with()` functions.

### Fields

- `source: Path` - Source directory that was copied
- `destination: Path` - Destination directory where it was copied to
- `pattern: FileStructurePattern` - Pattern that was used for copying

### Usage

```python
from pathvein import scan, shuffle_to
from pathlib import Path

matches = scan(Path("data"), [pattern])
results = shuffle_to(matches, Path("backup"))

for result in results:
    print(f"Copied: {result.source} -> {result.destination}")
```

### Checking Success

```python
results = shuffle_to(matches, Path("backup"))

print(f"Successfully copied {len(results)} directories")

for result in results:
    if result.destination.exists():
        print(f"✓ {result.destination}")
    else:
        print(f"✗ {result.destination}")
```

## Type Annotations

All types are exported from the main package and can be used for type hints:

```python
from pathlib import Path
from typing import Set, List
from pathvein import (
    ScanResult,
    ShuffleInput,
    ShuffleResult,
    FileStructurePattern
)

def find_experiments(root: Path) -> Set[ScanResult]:
    pattern = FileStructurePattern(files=["experiment.yaml"])
    from pathvein import scan
    return scan(root, [pattern])

def backup_experiments(matches: Set[ScanResult]) -> List[ShuffleResult]:
    from pathvein import shuffle_to
    return shuffle_to(matches, Path("backup"))
```

## Working with Named Tuples

### Unpacking

```python
for source, destination, pattern in results:
    print(f"{source} -> {destination}")
```

### Converting to Dict

```python
result_dict = result._asdict()
# {'source': Path('...'), 'destination': Path('...'), 'pattern': FileStructurePattern(...)}
```

### Creating from Dicts

```python
from pathvein import ShuffleInput

data = {
    'source': Path('data/exp_001'),
    'destination': Path('backup/exp_001'),
    'pattern': pattern
}

shuffle_input = ShuffleInput(**data)
```
