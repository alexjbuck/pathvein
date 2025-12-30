# Shuffling (Copying) Matched Structures

After scanning for matches, you often want to copy them to organized destinations. Pathvein provides three "shuffle" functions for different use cases.

## Overview

| Function | Use Case | Destination |
|----------|----------|-------------|
| `shuffle_to()` | Copy all matches to one location | Single directory, flat structure |
| `shuffle_with()` | Custom destination logic | Computed per-match |
| `shuffle()` | Full control | Explicitly specified |

## shuffle_to(): Simple Consolidation

Copy all matches into a single destination directory:

```python
from pathlib import Path
from pathvein import scan, shuffle_to, FileStructurePattern

pattern = FileStructurePattern(
    directory_name="experiment_*",
    files=["results.csv"]
)

matches = scan(Path("data"), [pattern])

results = shuffle_to(
    matches=matches,
    destination=Path("organized"),
    overwrite=False,
    dryrun=False
)
```

### Resulting Structure

```
organized/
├── experiment_001/
│   └── results.csv
├── experiment_002/
│   └── results.csv
└── experiment_003/
    └── results.csv
```

Each matched directory becomes a subdirectory of the destination with its original name preserved.

## shuffle_with(): Custom Logic

Use a function to compute destinations dynamically:

```python
from pathvein import shuffle_with

def organize_by_year(scan_result):
    """Sort experiments by year from the directory name"""
    # Extract year from "experiment_2023_01"
    parts = scan_result.source.name.split("_")
    year = parts[1] if len(parts) > 1 else "unknown"
    return Path(f"organized/{year}/{scan_result.source.name}")

results = shuffle_with(
    matches=matches,
    destination_fn=organize_by_year,
    overwrite=False,
    dryrun=False
)
```

### Resulting Structure

```
organized/
├── 2023/
│   ├── experiment_2023_01/
│   └── experiment_2023_02/
├── 2024/
│   ├── experiment_2024_01/
│   └── experiment_2024_02/
└── unknown/
    └── experiment_old/
```

## shuffle(): Maximum Control

Explicitly specify source and destination for each copy:

```python
from pathvein import shuffle, ShuffleInput

# Build shuffle inputs manually
shuffle_def = [
    ShuffleInput(
        source=Path("data/exp_001"),
        destination=Path("results/group_a/exp_001"),
        pattern=pattern
    ),
    ShuffleInput(
        source=Path("data/exp_002"),
        destination=Path("results/group_b/exp_002"),
        pattern=pattern
    )
]

results = shuffle(
    shuffle_def=shuffle_def,
    overwrite=False,
    dryrun=False
)
```

Or convert scan results:

```python
shuffle_def = [
    ShuffleInput(
        source=match.source,
        destination=compute_dest(match),
        pattern=match.pattern
    )
    for match in matches
]

results = shuffle(shuffle_def, overwrite=False, dryrun=False)
```

## Common Options

All shuffle functions accept these options:

### overwrite: bool = False

Whether to overwrite existing files at the destination:

```python
results = shuffle_to(
    matches=matches,
    destination=Path("backup"),
    overwrite=True  # Overwrite existing files
)
```

**Default**: `False` - Raises `FileExistsError` if destination exists

### dryrun: bool = False

Preview what would be copied without actually copying:

```python
results = shuffle_to(
    matches=matches,
    destination=Path("backup"),
    dryrun=True  # Don't actually copy
)

print(f"Would copy {len(results)} directories")
for result in results:
    print(f"  {result.source} -> {result.destination}")
```

### use_threading: bool = False

Enable parallel file copying for better performance:

```python
results = shuffle_to(
    matches=matches,
    destination=Path("backup"),
    use_threading=True,  # Copy files in parallel
    max_workers=4
)
```

**Best for**: Large numbers of small-to-medium files

**Not recommended for**: Very large files (network bandwidth becomes bottleneck)

### max_workers: int = 4

Number of worker threads when `use_threading=True`:

```python
results = shuffle_to(
    matches=matches,
    destination=Path("backup"),
    use_threading=True,
    max_workers=8  # Use 8 threads
)
```

## Return Value

All shuffle functions return `List[ShuffleResult]`, where each `ShuffleResult` is a named tuple:

```python
from pathvein import ShuffleResult

for result in results:
    print(f"Source: {result.source}")
    print(f"Destination: {result.destination}")
    print(f"Pattern: {result.pattern}")
```

## Pattern-Based Copying

Shuffling only copies files and directories that match the pattern:

```python
pattern = FileStructurePattern(
    directory_name="experiment_*",
    files=["*.csv"],
    optional_files=["*.txt"],
    directories=[
        FileStructurePattern(
            directory_name="data",
            files=["*.parquet"]
        )
    ]
)

# Only copies:
# - .csv files (required)
# - .txt files if present (optional)
# - data/ subdirectory with .parquet files
results = shuffle_to(matches, Path("backup"))
```

Files not matching the pattern are **not copied**.

## Examples

### Organize by Date

```python
from datetime import datetime

def organize_by_date(scan_result):
    """Organize by modification date"""
    mtime = scan_result.source.stat().st_mtime
    date = datetime.fromtimestamp(mtime)
    year_month = date.strftime("%Y-%m")
    return Path(f"archive/{year_month}/{scan_result.source.name}")

results = shuffle_with(matches, organize_by_date)
```

Result:
```
archive/
├── 2024-01/
│   ├── experiment_001/
│   └── experiment_002/
└── 2024-02/
    └── experiment_003/
```

### Organize by Size

```python
def organize_by_size(scan_result):
    """Organize by directory size"""
    size = sum(
        f.stat().st_size
        for f in scan_result.source.rglob("*")
        if f.is_file()
    )

    if size > 1_000_000_000:  # > 1GB
        bucket = "large"
    elif size > 100_000_000:  # > 100MB
        bucket = "medium"
    else:
        bucket = "small"

    return Path(f"organized/{bucket}/{scan_result.source.name}")

results = shuffle_with(matches, organize_by_size)
```

### Flatten Structure

```python
def flatten(scan_result):
    """Remove directory hierarchy, just use directory name"""
    return Path(f"flat/{scan_result.source.name}")

results = shuffle_with(matches, flatten)
```

Before:
```
data/
├── 2023/
│   └── experiment_001/
└── 2024/
    └── experiment_002/
```

After:
```
flat/
├── experiment_001/
└── experiment_002/
```

### Selective Copying

```python
def selective_copy(scan_result):
    """Only copy experiments that succeeded"""
    success_file = scan_result.source / "success.txt"
    if success_file.exists():
        return Path(f"successful/{scan_result.source.name}")
    else:
        return Path(f"failed/{scan_result.source.name}")

results = shuffle_with(matches, selective_copy)
```

### Incremental Backup

```python
from datetime import datetime

backup_dir = Path(f"backups/{datetime.now().strftime('%Y%m%d')}")

results = shuffle_to(
    matches=matches,
    destination=backup_dir,
    overwrite=False  # Skip if already backed up
)

print(f"Backed up {len(results)} directories to {backup_dir}")
```

## Error Handling

### File Exists Error

```python
try:
    results = shuffle_to(
        matches=matches,
        destination=Path("backup"),
        overwrite=False
    )
except FileExistsError as e:
    print(f"Destination already exists: {e}")
    # Either delete it or use overwrite=True
```

### Check Before Copying

```python
# Preview with dryrun
preview = shuffle_to(matches, dest, dryrun=True)

# Check for conflicts
conflicts = [
    r for r in preview
    if r.destination.exists()
]

if conflicts:
    print(f"Found {len(conflicts)} conflicts:")
    for r in conflicts:
        print(f"  {r.destination}")

    if input("Overwrite? (y/n): ").lower() == "y":
        shuffle_to(matches, dest, overwrite=True)
else:
    shuffle_to(matches, dest, overwrite=False)
```

## Performance Tips

### Use Threading for Many Small Files

```python
results = shuffle_to(
    matches=matches,
    destination=Path("backup"),
    use_threading=True,
    max_workers=8
)
```

### Avoid Threading for Large Files

For very large files, threading doesn't help much:

```python
# Single-threaded for large files
results = shuffle_to(
    matches=matches,
    destination=Path("backup"),
    use_threading=False
)
```

### Cloud Storage

For S3 or other cloud storage, install the s3 extra:

```shell
pip install 'pathvein[s3]'
```

Then use UPath:

```python
from upath import UPath

results = shuffle_to(
    matches=matches,
    destination=UPath("s3://my-bucket/backups/")
)
```

## Best Practices

### Always Use dryrun First

```python
# 1. Preview
preview = shuffle_to(matches, dest, dryrun=True)
print(f"Would copy {len(preview)} directories")

# 2. Review
for r in preview:
    print(f"  {r.source.name} -> {r.destination}")

# 3. Execute
if input("Proceed? (y/n): ").lower() == "y":
    shuffle_to(matches, dest, dryrun=False)
```

### Check Disk Space

```python
import shutil

# Estimate size
total_size = sum(
    sum(f.stat().st_size for f in m.source.rglob("*") if f.is_file())
    for m in matches
)

# Check available space
stat = shutil.disk_usage(dest)
if stat.free < total_size * 1.1:  # 10% buffer
    print("Insufficient disk space!")
else:
    shuffle_to(matches, dest)
```

### Log Results

```python
import logging
from datetime import datetime

logging.basicConfig(
    filename=f'shuffle_{datetime.now():%Y%m%d_%H%M%S}.log',
    level=logging.INFO
)

results = shuffle_to(matches, dest)

logging.info(f"Copied {len(results)} directories")
for r in results:
    logging.info(f"  {r.source} -> {r.destination}")
```
