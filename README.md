<!-- markdownlint-disable MD033 MD041 -->
<div align="center">
  <picture>
    <img alt="" src="logo.png" width="128">
  </picture>
  <p>
    <b>Pathvein</b>
    <br />
    Rich and deep file structure pattern matching
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
<!-- markdownlint-restore MD033 MD041 -->

## Documentation

📚 **[Full documentation available at alexjbuck.github.io/pathvein](https://alexjbuck.github.io/pathvein/)**

- [Installation Guide](https://alexjbuck.github.io/pathvein/getting-started/installation/)
- [Quick Start Tutorial](https://alexjbuck.github.io/pathvein/getting-started/quick-start/)
- [API Reference](https://alexjbuck.github.io/pathvein/api/)

## Installation

```shell
# Full installation with CLI (recommended)
$ pip install 'pathvein[cli]'
$ pipx install 'pathvein[cli]'
$ uvx --with 'pathvein[cli]' pathvein

# Library only (for programmatic use)
$ pip install pathvein
```

## Library usage

If you wish to integrate the `scan` or `shuffle` functions into your application you likely want
to use `pathvein` as a library. Follow the example below for how to use this API.

```python
from pathvein import scan, shuffle, shuffle_to, shuffle_with, FileStructurePattern

# Construct a FileStructurePattern
pattern = FileStructurePattern(
    directory_name = "...",                            # str
    files = ["*.csv","*.config"],                      # list[str]
    directories = [FileStructurePattern(...)],         # list[Self]
    optional_files = ["*.py", "main.rs"],              # list[str]
    optional_directories = [FileStructurePattern(...)] # list[Self]
)
# Export a pattern to a file
Path("pattern.config").write_text(pattern.to_json())

# Recursively scan a directory path for directory structures that match the requirements
matches = scan(
    source=Path("source"),                      # Path
    pattern_spec_paths=[Path("pattern.config")] # Iterable[Path]
) 
# Recursively scan a source path for pattern-spec directory structures and copy them to the destination
# This copies all matching directories into a flat structre inside of `destination`.
results = shuffle_to(
    matches=matches,          # Set[ScanResult]
    destination=Path("dest"), # Path
    overwrite=False,          # bool
    dryrun=False              # bool
)
```

If instead you want to have some logic over what destination folder a scan match goes to
You can use the `shuffle_with` command and inject a function

```python
def compute_destination_from_scan_result(scan_result:ScanResult) -> Path:
    """Example function that sorts all scan results into two bins based on the first letter"""
    first = "[a-m]"
    second = "[n-z]"
    if scan_result.source.name.lower()[0] < "n":
        return Path(first) / scan_result.source.name
    else:
        return Path(second) / scan_result.source.name

results = shuffle_with(
    matches=matches,                                     # Set[ScanResult]
    destination_fn=compute_destination_from_scan_result, # Callable[[ScanResult],Path]
    overwrite=False,                                     # bool
    dryrun=False                                         # bool
)
```

Finally, maybe you just want to compute the destination elsewhere and simply want to pass
a list of shuffle inputs:

```python
shuffle_def = set(
    map(
        lambda scan_result: ShuffleInput(
            scan_result.source, some_destination_fn(scan_result), scan_result.pattern
        ),
        matches,
    )
)
results = shuffle(
    shuffle_def=shuffle_def, # Set[ShuffleInput]
    overwrite=False,         # bool
    dryrun=False             # bool
)
```

### Advanced: Pattern Assessment

The `assess()` function works backwards from a file to determine which patterns it belongs to:

```python
from pathvein import assess, FileStructurePattern

# Given a file deep in a directory structure, find which pattern it matches
patterns = [pattern1, pattern2, pattern3]

for result in assess(Path("data/experiment_1/results/output.csv"), patterns):
    print(f"File belongs to pattern: {result.pattern}")
    print(f"Pattern root directory: {result.source}")
```

This is useful for:
- **Validation**: Check if a file belongs to a known pattern
- **Discovery**: Find the root directory of a pattern given any file within it
- **Reverse engineering**: Determine what pattern an existing file structure follows

## CLI usage

The CLI implements the `shuffle_to` API with a single destination provided in the command line.

**Note**: The CLI requires the `[cli]` extra: `pip install 'pathvein[cli]'`

This library does not yet have a settled method for dynamically computing the destination folder
and providing that via commandline interface.

If you need to use the dynamic destination feature of the library, you should not use the CLI and
should instead write a script to employ the library `shuffle_with` or `shuffle` features.

```shell
# View the commandline interface help
$ pathvein --help
pathvein -h

 Usage: pathvein [OPTIONS] COMMAND [ARGS]...

╭─ Options ─────────────────────────────────────────────────────────────────────────────╮
│ --install-completion            Install completion for the current shell.             │
│ --show-completion               Show completion for the current shell, to copy it or  │
│                                 customize the installation.                           │
│ --help                -h        Show this message and exit.                           │
╰───────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ────────────────────────────────────────────────────────────────────────────╮
│ scan                                                                                  │
│ shuffle                                                                               │
╰───────────────────────────────────────────────────────────────────────────────────────╯

# Scan a directory path
# pathvein scan <scan path> --pattern <pattern file>
$ pathvein scan source_dir --pattern pattern.config
/source_dir/first/match/path
/source_dir/second/match/path
/source_dir/third/match/path
...


# Scan a directory path and move all matches to a destination directory
# pathvein shuffle <scan path> <dest path> -p <pattern file>
pathvein shuffle source_dir dest_dir -p pattern.config -p additional.config
```

## Performance Notes

This library makes use of caching to improve performance. While iterating through the search directories, the results of `path.iterdir()` are cached into a thread-safe cache.
This program behaves in a way that causes multiple calls to `path.iterdir()` for each path in the tree. When this involves network requests, the cached function can be several
orders of magnitude faster. Even for local file system calls (i.e. `path` is a POSIX path) this can be over 100x faster by caching.

### Rust Backend

For maximum performance, pathvein includes a Rust backend that provides:
- **5-10x faster** directory walking with parallel traversal
- **3-5x faster** pattern matching with compiled globs
- Automatic fallback to pure Python if Rust extension not available

The Rust backend is built automatically if you have the Rust toolchain installed. If Rust is not available, pathvein falls back to pure Python seamlessly.

```shell
# Install from PyPI (when available)
$ pip install pathvein

# Build from source (builds with Rust if cargo available)
$ pip install .

# Check which backend is active
$ python -c "from pathvein import get_backend_info; print(get_backend_info())"
```

**Note**: Requires Rust toolchain (`cargo`) for building from source. If not installed, falls back to pure Python automatically.
