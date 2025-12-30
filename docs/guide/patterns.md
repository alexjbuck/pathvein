# Working with Patterns

File structure patterns are the core of pathvein. They define what you're looking for in your file system.

## Pattern Components

A `FileStructurePattern` has five main components:

| Component | Type | Description |
|-----------|------|-------------|
| `directory_name` | `str` | Glob pattern for the directory name (default: `"*"`) |
| `files` | `List[str]` | Required file patterns that must exist |
| `directories` | `List[FileStructurePattern]` | Required subdirectories that must exist |
| `optional_files` | `List[str]` | Optional file patterns |
| `optional_directories` | `List[FileStructurePattern]` | Optional subdirectories |

## Creating Patterns

### Basic Pattern

```python
from pathvein import FileStructurePattern

pattern = FileStructurePattern(
    directory_name="experiment_*",
    files=["data.csv", "metadata.json"]
)
```

### Using Builder Methods

Patterns support a fluent builder interface:

```python
pattern = (
    FileStructurePattern()
    .set_directory_name("project_*")
    .add_file("README.md")
    .add_files(["setup.py", "pyproject.toml"])
    .add_file("notes.txt", is_optional=True)
)
```

### Nested Patterns

Create deep hierarchy requirements:

```python
src_pattern = FileStructurePattern(
    directory_name="src",
    files=["__init__.py", "main.py"]
)

test_pattern = FileStructurePattern(
    directory_name="tests",
    files=["test_*.py"]
)

project_pattern = FileStructurePattern(
    directory_name="my_project",
    files=["README.md"],
    directories=[src_pattern, test_pattern]
)
```

## Glob Patterns

Pathvein uses glob-style pattern matching for filenames and directory names.

### Common Glob Patterns

| Pattern | Matches | Example |
|---------|---------|---------|
| `*` | Any characters | `*.csv` matches `data.csv`, `results.csv` |
| `?` | Single character | `test?.py` matches `test1.py`, `testA.py` |
| `[abc]` | Any character in brackets | `data[123].txt` matches `data1.txt`, `data2.txt` |
| `[!abc]` | Any character NOT in brackets | `data[!0].txt` matches `data1.txt` but not `data0.txt` |
| `[a-z]` | Character range | `exp_[0-9].csv` matches `exp_0.csv` through `exp_9.csv` |

### Examples

```python
# Match any Python file
pattern = FileStructurePattern(
    directory_name="*",
    files=["*.py"]
)

# Match numbered experiment directories
pattern = FileStructurePattern(
    directory_name="experiment_[0-9][0-9]",
    files=["data_*.csv"]
)

# Match multiple file types
pattern = FileStructurePattern(
    directory_name="*",
    files=["report.*"]  # Matches report.pdf, report.docx, etc.
)
```

## Required vs Optional

The distinction between required and optional components is important:

### Required Components

Must be present for a match:

```python
pattern = FileStructurePattern(
    files=["config.yaml"],  # Must exist
    directories=[           # At least one must exist
        FileStructurePattern(directory_name="data")
    ]
)
```

### Optional Components

May or may not be present:

```python
pattern = FileStructurePattern(
    files=["config.yaml"],
    optional_files=["notes.txt"],  # Nice to have, but not required
    optional_directories=[
        FileStructurePattern(directory_name="backup")
    ]
)
```

## Pattern Validation

Patterns validate directory structures by checking:

1. **Directory name** matches the pattern
2. **All required files** exist (at least one match per pattern)
3. **All required subdirectories** exist and match their patterns
4. **Optional components** are ignored if missing

## JSON Serialization

Patterns can be saved and loaded as JSON:

### Saving Patterns

```python
pattern = FileStructurePattern(
    directory_name="experiment_*",
    files=["data.csv", "config.yaml"]
)

# Convert to JSON string
json_str = pattern.to_json()

# Save to file
from pathlib import Path
Path("pattern.json").write_text(json_str)
```

### Loading Patterns

```python
from pathlib import Path
from pathvein import FileStructurePattern

# Load from file
pattern = FileStructurePattern.load_json(Path("pattern.json"))

# Load from string
pattern = FileStructurePattern.from_json(json_str)
```

### JSON Format

Here's what the JSON looks like:

```json
{
  "directory_name": "experiment_*",
  "files": ["data.csv", "config.yaml"],
  "directories": [
    {
      "directory_name": "raw",
      "files": ["*.csv"],
      "directories": [],
      "optional_files": [],
      "optional_directories": []
    }
  ],
  "optional_files": ["notes.txt"],
  "optional_directories": []
}
```

## Pattern Matching Behavior

### File Pattern Matching

When matching file patterns, at least one file must match each required pattern:

```python
pattern = FileStructurePattern(
    files=["*.csv", "*.json"]
)
```

This requires:
- At least one `.csv` file AND
- At least one `.json` file

### Directory Pattern Matching

For required subdirectories, at least one directory must match each pattern:

```python
pattern = FileStructurePattern(
    directories=[
        FileStructurePattern(directory_name="data_*")
    ]
)
```

This requires at least one directory whose name matches `data_*`.

## Advanced: Reverse Pattern Matching

The `parents_of()` method finds candidate root directories for a file:

```python
from pathlib import Path

pattern = FileStructurePattern(
    directory_name="experiment_*",
    files=["data.csv", "results.csv"]
)

# Find possible root directories for this file
file = Path("data/experiment_001/results.csv")
candidates = pattern.parents_of(file)

# candidates might include: {Path("data/experiment_001")}
```

This is useful with the `assess()` function to determine which pattern a file belongs to.

## Best Practices

### Be Specific

Prefer specific patterns over wildcards when possible:

```python
# Good - specific
pattern = FileStructurePattern(
    directory_name="experiment_*",
    files=["config.yaml", "results.csv"]
)

# Less good - too broad
pattern = FileStructurePattern(
    directory_name="*",
    files=["*"]
)
```

### Use Optional Wisely

Only mark components as optional if they're truly optional:

```python
pattern = FileStructurePattern(
    files=["config.yaml"],  # Always required
    optional_files=["debug.log"]  # Only in debug runs
)
```

### Document Your Patterns

Add comments or save patterns with descriptive filenames:

```python
# experiments/pattern.json
experimental_run_pattern = FileStructurePattern(
    directory_name="run_[0-9][0-9][0-9]",
    files=["config.yaml", "results.csv"],
    optional_files=["error.log"]
)
```

## Examples

### Python Project Pattern

```python
python_project = FileStructurePattern(
    directory_name="*",
    files=["pyproject.toml"],
    directories=[
        FileStructurePattern(
            directory_name="src",
            files=["__init__.py"]
        )
    ],
    optional_files=["README.md", "LICENSE"],
    optional_directories=[
        FileStructurePattern(directory_name="tests"),
        FileStructurePattern(directory_name="docs")
    ]
)
```

### Data Science Experiment Pattern

```python
experiment_pattern = FileStructurePattern(
    directory_name="exp_*",
    files=["config.json", "results.csv"],
    directories=[
        FileStructurePattern(
            directory_name="data",
            files=["*.parquet"]
        ),
        FileStructurePattern(
            directory_name="models",
            files=["model_*.pkl"]
        )
    ],
    optional_files=["notes.md", "plot_*.png"],
    optional_directories=[
        FileStructurePattern(directory_name="checkpoints")
    ]
)
```
