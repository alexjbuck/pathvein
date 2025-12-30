# Pathvein

<div align="center">
  <img alt="Pathvein Logo" src="https://raw.githubusercontent.com/alexjbuck/pathvein/main/logo.png" width="128">
  <p>
    <b>Rich and deep file structure pattern matching</b>
  </p>
  <p>
    <a href="https://github.com/alexjbuck/pathvein/actions/workflows/check.yaml">
      <img alt="Checks" src="https://github.com/alexjbuck/pathvein/actions/workflows/check.yaml/badge.svg">
    </a>
    <a href="https://pypi.org/project/pathvein/">
      <img alt="PyPI" src="https://img.shields.io/pypi/v/pathvein?color=yellow">
    </a>
  </p>
</div>

## Overview

Pathvein is a high-performance Python library for pattern matching against file system structures. It combines the expressiveness of Python with the speed of Rust to provide a powerful tool for:

- **Scanning** directories for complex structural patterns
- **Validating** file organization against requirements
- **Copying** matched structures to organized destinations
- **Assessing** which patterns individual files belong to

## Key Features

- **Rich Pattern Matching**: Define complex file structure requirements with required and optional components
- **Rust-Powered Performance**: 5-10x faster directory walking and 3-5x faster pattern matching
- **Cloud Storage Support**: Works with S3 and other cloud storage via fsspec
- **Python Fallback**: Automatically falls back to pure Python if Rust unavailable
- **Type Safe**: Full type annotations with runtime validation using Pydantic
- **CLI & Library**: Use programmatically or from the command line

## Quick Example

```python
from pathlib import Path
from pathvein import scan, shuffle_to, FileStructurePattern

# Define a pattern for an experiment directory
pattern = FileStructurePattern(
    directory_name="experiment_*",
    files=["config.yaml", "results.csv"],
    optional_files=["notes.txt"]
)

# Find all matching directories
matches = scan(
    source=Path("data"),
    patterns=[pattern]
)

# Copy matches to organized destination
shuffle_to(
    matches=matches,
    destination=Path("organized_data")
)
```

## Performance

Pathvein includes a Rust backend that provides significant performance improvements:

- **5-10x faster** directory walking with parallel traversal
- **3-5x faster** pattern matching with compiled globs
- **100x+ faster** for network filesystems via caching

The Rust backend is built automatically when installed from source with cargo available, or included in PyPI wheels.

## Get Started

Ready to dive in? Check out the [installation guide](getting-started/installation.md) and [quick start tutorial](getting-started/quick-start.md).

For detailed API documentation, see the [API Reference](api/index.md).
