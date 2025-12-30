# Quick Start

This guide will walk you through the basics of using pathvein.

## Basic Concepts

Pathvein works with three main concepts:

1. **Patterns**: Definitions of file structure requirements
2. **Scanning**: Finding directories that match patterns
3. **Shuffling**: Copying matched structures to organized destinations

## Your First Pattern

Let's create a simple pattern that matches directories containing specific files:

```python
from pathvein import FileStructurePattern

# A simple experiment directory pattern
pattern = FileStructurePattern(
    directory_name="experiment_*",  # Must start with "experiment_"
    files=["data.csv", "config.yaml"],  # Must have these files
    optional_files=["notes.txt"]  # May have this file
)
```

## Scanning for Matches

Now let's scan a directory to find all matches:

```python
from pathlib import Path
from pathvein import scan

# Scan the data directory
matches = scan(
    source=Path("data"),
    patterns=[pattern]
)

# Print all matches
for match in matches:
    print(f"Found: {match.source}")
```

## Organizing Matches

Once you have matches, you can copy them to an organized destination:

```python
from pathvein import shuffle_to

# Copy all matches to a single destination
results = shuffle_to(
    matches=matches,
    destination=Path("organized_data"),
    overwrite=False,  # Don't overwrite existing files
    dryrun=False  # Actually perform the copy
)

# See what was copied
for result in results:
    print(f"Copied {result.source} to {result.destination}")
```

## Nested Patterns

Patterns can be nested to match complex directory structures:

```python
pattern = FileStructurePattern(
    directory_name="project_*",
    files=["README.md"],
    directories=[
        FileStructurePattern(
            directory_name="src",
            files=["__init__.py"]
        ),
        FileStructurePattern(
            directory_name="tests",
            files=["test_*.py"]
        )
    ],
    optional_directories=[
        FileStructurePattern(
            directory_name="docs"
        )
    ]
)
```

This pattern matches directories like:

```
project_foo/
├── README.md
├── src/
│   └── __init__.py
└── tests/
    └── test_main.py
```

## Using Wildcards

Pathvein supports glob patterns for file and directory names:

```python
pattern = FileStructurePattern(
    directory_name="*",  # Any directory name
    files=["*.csv", "config.*"],  # Any CSV file and config file with any extension
    optional_files=["data_[0-9][0-9].txt"]  # Optional numbered data files
)
```

## Loading Patterns from JSON

You can save and load patterns as JSON:

```python
# Save pattern
pattern_json = pattern.to_json()
Path("pattern.json").write_text(pattern_json)

# Load pattern
loaded_pattern = FileStructurePattern.load_json(Path("pattern.json"))
```

## Advanced: Custom Destinations

Use `shuffle_with` for custom destination logic:

```python
from pathvein import shuffle_with

def compute_destination(scan_result):
    """Sort experiments by year"""
    # Extract year from directory name like "experiment_2023_01"
    year = scan_result.source.name.split("_")[1]
    return Path(f"organized/{year}/{scan_result.source.name}")

results = shuffle_with(
    matches=matches,
    destination_fn=compute_destination
)
```

## Command Line Usage

If you installed with `[cli]`, you can use pathvein from the command line:

```shell
# Scan for matches
pathvein scan data/ --pattern pattern.json

# Scan and copy
pathvein shuffle data/ organized_data/ --pattern pattern.json
```

## Next Steps

- Learn more about [patterns](../guide/patterns.md)
- Explore [scanning options](../guide/scanning.md)
- Master [shuffling strategies](../guide/shuffling.md)
- Check out the full [API Reference](../api/index.md)
