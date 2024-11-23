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

## CLI usage

If you install the CLI, it currently implements the `shuffle_to` API with the single destination
provided in the command line.

This library does not yet have a settled method for dynamically computing the destination folder
and providing that via commandline interface.

If you need to use the dynamic destination feature of the library, you should not use the CLI and
should instead write a script to employ the library `shuffle_with` or `shuffle` features.

```shell
# Install using your favorite python package installer (pip or pipx)
$ pipx install 'pathvein[cli]'
# or 
$ uv pip install 'pathvein[cli]'


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

